//! Cross-process file locks. Android supports flock, but Rust's File locking API
//! currently excludes Android and returns Unsupported without a system call.

use std::fs::File;
use std::fs::TryLockError;
use std::io;

/// Hold an exclusive lock until the file is closed.
pub fn lock_exclusive(file: &File) -> io::Result<()> {
    #[cfg(target_os = "android")]
    return flock(file, libc::LOCK_EX);
    #[cfg(not(target_os = "android"))]
    file.lock()
}

/// Hold a shared lock until the file is closed.
pub fn lock_shared(file: &File) -> io::Result<()> {
    #[cfg(target_os = "android")]
    return flock(file, libc::LOCK_SH);
    #[cfg(not(target_os = "android"))]
    file.lock_shared()
}

/// Release a lock held on this handle.
pub fn unlock(file: &File) -> io::Result<()> {
    #[cfg(target_os = "android")]
    return flock(file, libc::LOCK_UN);
    #[cfg(not(target_os = "android"))]
    file.unlock()
}

/// Try to hold an exclusive lock until the file is closed.
pub fn try_lock_exclusive(file: &File) -> Result<(), TryLockError> {
    #[cfg(target_os = "android")]
    return try_flock(file, libc::LOCK_EX);
    #[cfg(not(target_os = "android"))]
    file.try_lock()
}

/// Try to hold a shared lock until the file is closed.
pub fn try_lock_shared(file: &File) -> Result<(), TryLockError> {
    #[cfg(target_os = "android")]
    return try_flock(file, libc::LOCK_SH);
    #[cfg(not(target_os = "android"))]
    file.try_lock_shared()
}

#[cfg(any(target_os = "android", all(test, unix)))]
fn flock(file: &File, operation: libc::c_int) -> io::Result<()> {
    use std::os::fd::AsRawFd;
    loop {
        // SAFETY: the borrowed file owns a valid descriptor for this call. flock
        // neither consumes it nor accesses Rust memory. Closing releases the lock.
        if unsafe { libc::flock(file.as_raw_fd(), operation) } == 0 {
            return Ok(());
        }
        let error = io::Error::last_os_error();
        if error.kind() != io::ErrorKind::Interrupted {
            return Err(error);
        }
    }
}

#[cfg(any(target_os = "android", all(test, unix)))]
fn try_flock(file: &File, operation: libc::c_int) -> Result<(), TryLockError> {
    flock(file, operation | libc::LOCK_NB).map_err(|error| {
        if error.kind() == io::ErrorKind::WouldBlock {
            TryLockError::WouldBlock
        } else {
            TryLockError::Error(error)
        }
    })
}

#[cfg(all(test, unix))]
mod tests {
    use super::*;

    // A fork/exec in another test briefly inherits open descriptors, which can
    // postpone release of flock locks. Serialize these tests around child spawn.
    static TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    #[test]
    fn exclusive_lock_blocks_independent_handle_until_close() {
        let _serial = TEST_LOCK.lock().unwrap();
        let first = tempfile::NamedTempFile::new().unwrap();
        let second = File::open(first.path()).unwrap();
        flock(first.as_file(), libc::LOCK_EX).unwrap();
        assert!(matches!(
            try_flock(&second, libc::LOCK_EX),
            Err(TryLockError::WouldBlock)
        ));
        assert!(matches!(
            try_flock(&second, libc::LOCK_SH),
            Err(TryLockError::WouldBlock)
        ));
        drop(first);
        try_flock(&second, libc::LOCK_EX).unwrap();
    }

    #[test]
    fn shared_locks_coexist_and_block_writer() {
        let _serial = TEST_LOCK.lock().unwrap();
        let first = tempfile::NamedTempFile::new().unwrap();
        let second = File::open(first.path()).unwrap();
        let writer = File::open(first.path()).unwrap();
        try_flock(first.as_file(), libc::LOCK_SH).unwrap();
        try_flock(&second, libc::LOCK_SH).unwrap();
        assert!(matches!(
            try_flock(&writer, libc::LOCK_EX),
            Err(TryLockError::WouldBlock)
        ));
        drop(first);
        assert!(matches!(
            try_flock(&writer, libc::LOCK_EX),
            Err(TryLockError::WouldBlock)
        ));
        drop(second);
        try_flock(&writer, libc::LOCK_EX).unwrap();
    }

    #[test]
    fn lock_contender_process() {
        let Some(path) = std::env::var_os("CODEX_LOCK_TEST_PATH") else {
            return;
        };
        let file = File::open(path).unwrap();
        assert!(matches!(
            try_flock(&file, libc::LOCK_EX),
            Err(TryLockError::WouldBlock)
        ));
    }

    #[test]
    fn exclusive_lock_excludes_other_processes() {
        let _serial = TEST_LOCK.lock().unwrap();
        let file = tempfile::NamedTempFile::new().unwrap();
        flock(file.as_file(), libc::LOCK_EX).unwrap();
        let status = std::process::Command::new(std::env::current_exe().unwrap())
            .arg("lock_contender_process")
            .arg("--test-threads=1")
            .env("CODEX_LOCK_TEST_PATH", file.path())
            .status()
            .unwrap();
        assert!(status.success());
    }

    #[test]
    fn explicit_unlock_releases_a_borrowed_handle() {
        let _serial = TEST_LOCK.lock().unwrap();
        let owner = tempfile::NamedTempFile::new().unwrap();
        let contender = File::open(owner.path()).unwrap();
        flock(owner.as_file(), libc::LOCK_SH).unwrap();
        assert!(matches!(
            try_flock(&contender, libc::LOCK_EX),
            Err(TryLockError::WouldBlock)
        ));
        flock(owner.as_file(), libc::LOCK_UN).unwrap();
        try_flock(&contender, libc::LOCK_EX).unwrap();
        // The original handle remains open: this tests explicit unlock, not close.
        assert!(owner.as_file().metadata().is_ok());
    }

    #[test]
    fn invalid_lock_operation_is_an_error() {
        let _serial = TEST_LOCK.lock().unwrap();
        let file = tempfile::tempfile().unwrap();
        assert!(flock(&file, 0).is_err());
    }
}
