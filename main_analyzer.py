import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import json
import requests
from bs4 import BeautifulSoup

# Core imports
from config import DOMAINS_TO_SCAN, MAX_WORKERS, REQUEST_TIMEOUT, USER_AGENT
import database
import reporting
from utils import wp_api_client, content_manager, pdf_generator, spell_checker, schema_validator

# Import all audit modules
from audits.advanced import (
    audit_backlink_profile, audit_competitor_analysis, audit_conversion_optimization,
    audit_core_vitals, audit_local_citations, audit_review_management,
    audit_site_speed, audit_social_signals
)
from audits.core import (
    audit_accessibility, audit_basic_seo, audit_content_analysis,
    audit_content_quality, audit_local_seo, audit_mobile_optimization,
    audit_schema_markup
)
from audits.wordpress import (
    audit_analytics_tracking, audit_email_marketing, audit_keyword_optimization,
    audit_technical_seo, audit_wp_security
)

# Import utility modules
from utils import (
    wp_api_client, content_manager, backup_manager, site_monitor,
    client_manager, report_generator, notification_system,
    competitive_intelligence, keyword_research, schema_manager
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_audit.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MasterWordPressAuditor:
    """
    Master WordPress Auditor for comprehensive site analysis and management
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.base_url = f"https://{domain}"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.wp_client = None
        self.audit_results = {}

    def initialize_wp_client(self):
        """Initialize WordPress API client"""
        try:
            self.wp_client = wp_api_client.WordPressAPIClient(self.domain)
            if self.wp_client.authenticate():
                logger.info(f"[{self.domain}] WordPress API authenticated successfully")
                return True
            else:
                logger.warning(f"[{self.domain}] WordPress API authentication failed")
                return False
        except Exception as e:
            logger.error(f"[{self.domain}] WordPress API initialization failed: {e}")
            return False

    def run_comprehensive_audit(self) -> Dict:
        """
        Run all audit modules and return comprehensive results
        """
        logger.info(f"[{self.domain}] Starting comprehensive WordPress audit")

        with database.db_connection() as conn:
            site_id = database.get_or_create_site_id(conn, self.domain)

            # Initialize WordPress client
            wp_authenticated = self.initialize_wp_client()

            # Core audits (always run)
            self._run_core_audits(conn, site_id)

            # WordPress-specific audits (only if authenticated)
            if wp_authenticated:
                self._run_wordpress_audits(conn, site_id)

            # Advanced audits
            self._run_advanced_audits(conn, site_id)

            # Generate comprehensive report
            self._generate_audit_report(conn, site_id)

        logger.info(f"[{self.domain}] Comprehensive audit completed")
        return self.audit_results

    def _run_core_audits(self, conn, site_id):
        """Run core audits that don't require WordPress authentication"""

        # Discover all pages
        pages = self._discover_all_pages()

        for page_url in pages:
            try:
                response = self.session.get(page_url, timeout=REQUEST_TIMEOUT)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Basic SEO audits
                audit_basic_seo.run_basic_seo_audits(conn, site_id, page_url, soup)

                # Local SEO audits
                audit_local_seo.run_local_seo_audits(conn, site_id, page_url, soup)

                # Content analysis
                audit_content_analysis.run_content_analysis(conn, site_id, page_url, soup)

                # Schema markup audit
                audit_schema_markup.run_schema_audit(conn, site_id, page_url, soup)

                # Accessibility audit
                audit_accessibility.run_accessibility_audit(conn, site_id, page_url, soup)

                # Mobile optimization
                audit_mobile_optimization.run_mobile_audit(conn, site_id, page_url, soup)

                # Content quality audit
                audit_content_quality.run_content_quality_audit(conn, site_id, page_url, soup)

            except Exception as e:
                logger.error(f"[{self.domain}] Error auditing page {page_url}: {e}")
                continue

    def _run_wordpress_audits(self, conn, site_id):
        """Run WordPress-specific audits requiring API access"""

        # WordPress security audit
        audit_wp_security.run_security_audits(conn, self.session, self.domain)

        # Technical SEO audit
        audit_technical_seo.run_technical_seo_audit(conn, site_id, self.wp_client)

        # Keyword optimization audit
        audit_keyword_optimization.run_keyword_audit(conn, site_id, self.wp_client)

        # Analytics tracking audit
        audit_analytics_tracking.run_analytics_audit(conn, site_id, self.wp_client)

        # Email marketing audit
        audit_email_marketing.run_email_audit(conn, site_id, self.wp_client)

    def _run_advanced_audits(self, conn, site_id):
        """Run advanced audits"""

        # Core Web Vitals
        audit_core_vitals.run_core_vitals_audit(conn, site_id, self.domain)

        # Site speed audit
        audit_site_speed.run_speed_audit(conn, site_id, self.domain)

        # Competitor analysis
        audit_competitor_analysis.run_competitor_audit(conn, site_id, self.domain)

        # Backlink profile audit
        audit_backlink_profile.run_backlink_audit(conn, site_id, self.domain)

        # Social signals audit
        audit_social_signals.run_social_audit(conn, site_id, self.domain)

        # Local citations audit
        audit_local_citations.run_citations_audit(conn, site_id, self.domain)

        # Review management audit
        audit_review_management.run_review_audit(conn, site_id, self.domain)

        # Conversion optimization audit
        audit_conversion_optimization.run_conversion_audit(conn, site_id, self.domain)

    def _discover_all_pages(self) -> List[str]:
        """Discover all pages on the site"""
        pages = set()

        # Add homepage
        pages.add(self.base_url)

        # Try sitemap discovery
        sitemap_urls = self._get_sitemap_urls()
        pages.update(sitemap_urls)

        # Try WordPress API discovery
        if self.wp_client:
            wp_pages = self.wp_client.get_all_pages()
            pages.update(wp_pages)

        return list(pages)

    def _get_sitemap_urls(self) -> List[str]:
        """Get URLs from sitemap"""
        sitemap_urls = []

        # Common sitemap locations
        sitemap_locations = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/wp-sitemap.xml",
            f"{self.base_url}/sitemap-index.xml"
        ]

        for sitemap_url in sitemap_locations:
            try:
                response = self.session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "xml")

                    # Handle sitemap index
                    for sitemap in soup.find_all("sitemap"):
                        loc = sitemap.find("loc")
                        if loc:
                            sub_urls = self._parse_sitemap(loc.text)
                            sitemap_urls.extend(sub_urls)

                    # Handle regular sitemap
                    for url in soup.find_all("url"):
                        loc = url.find("loc")
                        if loc:
                            sitemap_urls.append(loc.text)

                    break  # Found a working sitemap

            except Exception as e:
                logger.debug(f"[{self.domain}] Failed to fetch sitemap {sitemap_url}: {e}")
                continue

        return sitemap_urls

    def _parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Parse individual sitemap"""
        urls = []
        try:
            response = self.session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "xml")
                for url in soup.find_all("url"):
                    loc = url.find("loc")
                    if loc:
                        urls.append(loc.text)
        except Exception as e:
            logger.debug(f"[{self.domain}] Failed to parse sitemap {sitemap_url}: {e}")

        return urls

    def _generate_audit_report(self, conn, site_id):
        """Generate comprehensive audit report"""
        try:
            # Generate PDF report
            report_generator.generate_comprehensive_pdf_report(
                conn, site_id, self.domain, self.audit_results
            )

            # Generate executive summary
            report_generator.generate_executive_summary(
                conn, site_id, self.domain
            )

            # Generate action plan
            report_generator.generate_action_plan(
                conn, site_id, self.domain
            )

        except Exception as e:
            logger.error(f"[{self.domain}] Failed to generate audit report: {e}")


def run_master_audit_on_domain(domain: str) -> Dict:
    """Run comprehensive audit on a single domain"""
    auditor = MasterWordPressAuditor(domain)
    return auditor.run_comprehensive_audit()


def main():
    """Main entry point for master audit system"""
    start_time = time.time()

    # Initialize database with new schema
    database.initialize_enhanced_database()

    logger.info(f"🚀 Starting Master WordPress Audit for {len(DOMAINS_TO_SCAN)} domains")

    # Run audits in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix='MasterAudit') as executor:
        futures = [executor.submit(run_master_audit_on_domain, domain) for domain in DOMAINS_TO_SCAN]

        completed_audits = []
        for future in as_completed(futures):
            try:
                result = future.result()
                completed_audits.append(result)
                logger.info(f"✅ Completed audit for domain")
            except Exception as e:
                logger.error(f"❌ Audit failed: {e}", exc_info=True)

    # Generate master reports
    logger.info("📊 Generating master reports...")
    reporting.generate_master_reports()

    # Send notifications
    notification_system.send_audit_completion_notifications(completed_audits)

    total_time = time.time() - start_time
    logger.info(f"🎉 Master audit completed in {total_time:.2f} seconds")


if __name__ == "__main__":
    main()
