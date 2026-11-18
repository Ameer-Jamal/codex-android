//! dns using the [`hickory_resolver`] crate

use std::net::Ipv4Addr;
use std::net::Ipv6Addr;
use std::sync::Arc;

pub use hickory_resolver as resolver;
use hickory_resolver::TokioResolver;
use hickory_resolver::config::CLOUDFLARE;
use hickory_resolver::config::GOOGLE;
use hickory_resolver::config::QUAD9;
use hickory_resolver::config::ResolverConfig;
use hickory_resolver::lookup::Lookup;
use hickory_resolver::net::runtime::TokioRuntimeProvider;
use hickory_resolver::proto::rr::Name;
use hickory_resolver::proto::rr::RData;
use hickory_resolver::proto::rr::rdata::A;
use hickory_resolver::proto::rr::rdata::AAAA;

use rama_core::error::ErrorContext;
use rama_core::error::OpaqueError;
use rama_core::telemetry::tracing;
use rama_net::address::Domain;
use rama_utils::macros::generate_set_and_with;

use crate::DnsResolver;

#[derive(Debug, Clone)]
/// [`DnsResolver`] using the [`hickory_resolver`] crate
pub struct HickoryDns(Arc<TokioResolver>);

impl Default for HickoryDns {
    #[cfg(any(target_family = "unix", target_os = "windows"))]
    fn default() -> Self {
        Self::try_new_system().unwrap_or_else(|err| {
            tracing::warn!(
                "fail to create system HickoryDns client: fallback to cloudflare: {err}"
            );
            Self::new_cloudflare()
        })
    }

    #[cfg(not(any(target_family = "unix", target_os = "windows")))]
    fn default() -> Self {
        Self::new_cloudflare()
    }
}

impl HickoryDns {
    #[inline]
    /// Construct a [`HickoryDnsBuilder`] used to build
    /// a custom [`HickoryDns`] instead of the default [`HickoryDns::new`].
    #[must_use]
    pub fn builder() -> HickoryDnsBuilder {
        HickoryDnsBuilder::default()
    }

    #[inline]
    /// Construct a new [`HickoryDns`] instance with the [`Default`] setup.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    #[inline]
    /// Construct a new non-shared [`HickoryDns`] instance using Google's nameservers.
    ///
    /// Creates a default configuration, using `8.8.8.8`, `8.8.4.4` and `2001:4860:4860::8888`,
    /// `2001:4860:4860::8844` (thank you, Google).
    ///
    /// Please see Google's [privacy
    /// statement](https://developers.google.com/speed/public-dns/privacy) for important information
    /// about what they track, many ISP's track similar information in DNS.
    ///
    /// To use the system configuration see: [`Self::new_system`].
    pub fn new_google() -> Self {
        tracing::trace!("create HickoryDns resolver using default google config");
        Self::builder()
            .with_config(ResolverConfig::udp_and_tcp(&GOOGLE))
            .build()
    }

    #[inline]
    /// Construct a new non-shared [`HickoryDns`] instance using Cloudflare's nameservers.
    ///
    /// Creates a default configuration, using `1.1.1.1`, `1.0.0.1` and `2606:4700:4700::1111`, `2606:4700:4700::1001` (thank you, Cloudflare).
    ///
    /// Please see: <https://www.cloudflare.com/dns/>
    ///
    /// To use the system configuration see: [`Self::new_system`].
    pub fn new_cloudflare() -> Self {
        tracing::trace!("create HickoryDns resolver using default cloudflare config");
        Self::builder()
            .with_config(ResolverConfig::udp_and_tcp(&CLOUDFLARE))
            .build()
    }

    #[inline]
    /// Construct a new non-shared [`HickoryDns`] instance using Quad9's nameservers.
    ///
    /// Creates a configuration, using `9.9.9.9`, `149.112.112.112` and `2620:fe::fe`, `2620:fe::fe:9`,
    /// the "secure" variants of the quad9 settings (thank you, Quad9).
    ///
    /// Please see: <https://www.quad9.net/faq/>
    ///
    /// To use the system configuration see: [`Self::new_system`].
    pub fn new_quad9() -> Self {
        tracing::trace!("create HickoryDns resolver using default quad9 config");
        Self::builder()
            .with_config(ResolverConfig::udp_and_tcp(&QUAD9))
            .build()
    }

    #[cfg(any(target_family = "unix", target_os = "windows"))]
    /// Construct a new [`HickoryDns`] with the system configuration.
    ///
    /// This will use `/etc/resolv.conf` on Unix OSes and the registry on Windows.
    pub fn try_new_system() -> Result<Self, OpaqueError> {
        tracing::trace!("try to create HickoryDns resolver using system config");
        Ok(TokioResolver::builder_tokio()
            .context("build async dns resolver with system conf")
            .inspect_err(|err| {
                tracing::debug!("failed to create HickoryDns resolver using system config: {err:?}")
            })?
            .build()
            .context("initialize async dns resolver with system conf")?
            .into())
    }
}

impl From<TokioResolver> for HickoryDns {
    fn from(value: TokioResolver) -> Self {
        Self(Arc::new(value))
    }
}

#[derive(Debug, Clone, Default)]
/// A [`Builder`] to [`build`][`Self::build`] a [`HickoryDns`] instance.
pub struct HickoryDnsBuilder {
    config: Option<self::resolver::config::ResolverConfig>,
    options: Option<self::resolver::config::ResolverOpts>,
}

impl HickoryDnsBuilder {
    generate_set_and_with! {
        /// Define the [`ResolverConfig`][`config::ResolverConfig`] used.
        pub fn config(mut self, config: Option<self::resolver::config::ResolverConfig>) -> Self {
            self.config = config;
            self
        }
    }

    generate_set_and_with! {
        /// Define the [`ResolverOpts`][`config::ResolverOpts`] used.
        #[must_use]
        pub fn options(mut self, options: Option<self::resolver::config::ResolverOpts>) -> Self {
            self.options = options;
            self
        }
    }

    /// Build a [`HickoryDns`] instance, consuming [`self`].
    ///
    /// [`Clone`] the [`HickoryDnsBuilder`] prior to calling this method in case you
    /// still need the builder afterwards.
    pub fn build(self) -> HickoryDns {
        // Keep Rama's infallible constructor API. Our enabled Hickory features
        // exclude TLS, the only fallible initialization in ResolverBuilder::build.
        // Callers enabling additional features can use try_build to handle errors.
        self.try_build().expect("initialize Hickory DNS resolver")
    }

    /// Build a resolver and surface initialization failures from Hickory 0.26.
    pub fn try_build(self) -> Result<HickoryDns, OpaqueError> {
        let mut resolver_builder = TokioResolver::builder_with_config(
            self.config
                .unwrap_or_else(|| ResolverConfig::udp_and_tcp(&CLOUDFLARE)),
            TokioRuntimeProvider::default(),
        );
        if let Some(options) = self.options {
            *resolver_builder.options_mut() = options;
        }
        Ok(HickoryDns(Arc::new(
            resolver_builder
                .build()
                .context("initialize Hickory DNS resolver")?,
        )))
    }
}

impl DnsResolver for HickoryDns {
    type Error = OpaqueError;

    async fn txt_lookup(&self, domain: Domain) -> Result<Vec<Vec<u8>>, Self::Error> {
        let name = fqdn_from_domain(domain)?;

        let lookup = self.0.txt_lookup(name).await.context("lookup TXT entry")?;
        Ok(txt_values(&lookup))
    }

    async fn ipv4_lookup(&self, domain: Domain) -> Result<Vec<Ipv4Addr>, Self::Error> {
        let lookup = self
            .0
            .ipv4_lookup(fqdn_from_domain(domain)?)
            .await
            .context("lookup IPv4 address(es)")?;
        Ok(ipv4_addresses(&lookup))
    }

    async fn ipv6_lookup(&self, domain: Domain) -> Result<Vec<Ipv6Addr>, Self::Error> {
        let lookup = self
            .0
            .ipv6_lookup(fqdn_from_domain(domain)?)
            .await
            .context("lookup IPv6 address(es)")?;
        Ok(ipv6_addresses(&lookup))
    }
}

// Hickory 0.26 returns an untyped Lookup. Filter answer records by the requested
// type; do not mistake CNAMEs or unrelated address records for query results.
fn ipv4_addresses(lookup: &Lookup) -> Vec<Ipv4Addr> {
    lookup
        .answers()
        .iter()
        .filter_map(|record| match &record.data {
            RData::A(A(ip)) => Some(*ip),
            _ => None,
        })
        .collect()
}

fn ipv6_addresses(lookup: &Lookup) -> Vec<Ipv6Addr> {
    lookup
        .answers()
        .iter()
        .filter_map(|record| match &record.data {
            RData::AAAA(AAAA(ip)) => Some(*ip),
            _ => None,
        })
        .collect()
}

fn txt_values(lookup: &Lookup) -> Vec<Vec<u8>> {
    lookup
        .answers()
        .iter()
        .filter_map(|record| match &record.data {
            RData::TXT(txt) => Some(txt),
            _ => None,
        })
        .flat_map(|txt| txt.txt_data.iter().map(|part| part.to_vec()))
        .collect()
}

fn fqdn_from_domain(domain: Domain) -> Result<Name, OpaqueError> {
    let mut name = Name::from_utf8(domain).context("try to consume a Domain as a Dns Name")?;
    name.set_fqdn(true);
    Ok(name)
}

#[cfg(test)]
mod tests {
    use super::*;
    use hickory_resolver::proto::op::Query;
    use hickory_resolver::proto::rr::Record;
    use hickory_resolver::proto::rr::RecordType;
    use hickory_resolver::proto::rr::rdata::CNAME;
    use hickory_resolver::proto::rr::rdata::TXT;

    #[test]
    fn untyped_answers_preserve_address_family_and_binary_txt_chunks() {
        let name = Name::from_utf8("example.test.").unwrap();
        let data = [
            RData::CNAME(CNAME(Name::from_utf8("alias.example.test.").unwrap())),
            RData::A(A(Ipv4Addr::new(192, 0, 2, 1))),
            RData::AAAA(AAAA(Ipv6Addr::LOCALHOST)),
            RData::TXT(TXT::from_bytes(vec![b"first", &[0, 255], b""])),
            RData::A(A(Ipv4Addr::new(192, 0, 2, 2))),
        ];
        let lookup = Lookup::new_with_max_ttl(
            Query::query(name.clone(), RecordType::ANY),
            data.into_iter()
                .map(|data| Record::from_rdata(name.clone(), 60, data)),
        );
        assert_eq!(
            ipv4_addresses(&lookup),
            [Ipv4Addr::new(192, 0, 2, 1), Ipv4Addr::new(192, 0, 2, 2)]
        );
        assert_eq!(ipv6_addresses(&lookup), [Ipv6Addr::LOCALHOST]);
        assert_eq!(
            txt_values(&lookup),
            [b"first".to_vec(), vec![0, 255], vec![]]
        );
    }

    #[test]
    fn empty_answers_do_not_invent_addresses() {
        let name = Name::from_utf8("example.test.").unwrap();
        let lookup = Lookup::new_with_max_ttl(Query::query(name, RecordType::A), []);
        assert!(ipv4_addresses(&lookup).is_empty());
        assert!(ipv6_addresses(&lookup).is_empty());
        assert!(txt_values(&lookup).is_empty());
    }

    #[tokio::test]
    async fn configured_compatibility_builders_initialize_without_network_queries() {
        HickoryDns::builder().try_build().unwrap();
        HickoryDns::new_google();
        HickoryDns::new_cloudflare();
        HickoryDns::new_quad9();
    }
}
