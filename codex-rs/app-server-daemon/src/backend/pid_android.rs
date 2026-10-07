//! Android process identity uses kernel start ticks instead of toybox ps output.

use super::identity::parse_stat;
use anyhow::Context;
use anyhow::Result;

pub(super) async fn read_process_details(pid: u32) -> Result<(String, String)> {
    let stat = tokio::fs::read(format!("/proc/{pid}/stat"))
        .await
        .with_context(|| format!("failed to read /proc/{pid}/stat"))?;
    let (state, start_ticks) = parse_stat(&stat)?;
    Ok((state, start_ticks.to_string()))
}
