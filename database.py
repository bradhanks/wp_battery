import sqlite3
import logging
import datetime
from contextlib import contextmanager
from config import DB_NAME

logger = logging.getLogger(__name__)

# Enhanced database schema with comprehensive tables
ENHANCED_TABLES = {
    'clients': """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company TEXT,
            primary_domain TEXT,
            account_manager TEXT,
            contract_start_date TEXT,
            contract_end_date TEXT,
            monthly_budget REAL,
            target_nap TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,

    'sites': """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            client_id INTEGER,
            site_type TEXT DEFAULT 'wordpress',
            scan_date TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            wordpress_version TEXT,
            theme_name TEXT,
            is_child_theme BOOLEAN DEFAULT 0,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        );
    """,

    'audit_schedules': """
        CREATE TABLE IF NOT EXISTS audit_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            audit_type TEXT NOT NULL,
            frequency TEXT NOT NULL, -- daily, weekly, monthly
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'schema_markup_audit': """
        CREATE TABLE IF NOT EXISTS schema_markup_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            schema_type TEXT,
            schema_data TEXT,
            validation_status TEXT,
            validation_errors TEXT,
            completeness_score INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'core_vitals_audit': """
        CREATE TABLE IF NOT EXISTS core_vitals_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            lcp_score REAL,
            fid_score REAL,
            cls_score REAL,
            fcp_score REAL,
            ttfb_score REAL,
            overall_score TEXT,
            device_type TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'accessibility_audit': """
        CREATE TABLE IF NOT EXISTS accessibility_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            wcag_level TEXT,
            violations_count INTEGER,
            warnings_count INTEGER,
            accessibility_score INTEGER,
            color_contrast_issues TEXT,
            keyboard_navigation_issues TEXT,
            screen_reader_issues TEXT,
            image_alt_issues TEXT,
            heading_structure_issues TEXT,
            form_issues TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'competitor_analysis': """
        CREATE TABLE IF NOT EXISTS competitor_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            competitor_domain TEXT NOT NULL,
            competitor_rank INTEGER,
            shared_keywords INTEGER,
            competitor_backlinks INTEGER,
            competitor_domain_authority INTEGER,
            content_gap_analysis TEXT,
            pricing_comparison TEXT,
            feature_comparison TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'backlink_profile': """
        CREATE TABLE IF NOT EXISTS backlink_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            total_backlinks INTEGER,
            referring_domains INTEGER,
            domain_authority INTEGER,
            spam_score INTEGER,
            toxic_links INTEGER,
            new_links_last_30_days INTEGER,
            lost_links_last_30_days INTEGER,
            top_anchor_texts TEXT,
            top_referring_domains TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'keyword_optimization': """
        CREATE TABLE IF NOT EXISTS keyword_optimization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            target_keyword TEXT NOT NULL,
            current_position INTEGER,
            search_volume INTEGER,
            keyword_difficulty INTEGER,
            title_optimization_score INTEGER,
            meta_description_optimization_score INTEGER,
            content_optimization_score INTEGER,
            url_optimization_score INTEGER,
            internal_linking_score INTEGER,
            recommendations TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'technical_seo_audit': """
        CREATE TABLE IF NOT EXISTS technical_seo_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            crawl_errors_count INTEGER,
            broken_links_count INTEGER,
            duplicate_content_count INTEGER,
            missing_meta_tags_count INTEGER,
            robots_txt_status TEXT,
            sitemap_status TEXT,
            ssl_certificate_status TEXT,
            page_speed_score INTEGER,
            mobile_friendly_score INTEGER,
            structured_data_errors INTEGER,
            hreflang_errors INTEGER,
            canonical_errors INTEGER,
            redirect_chains INTEGER,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'content_quality_audit': """
        CREATE TABLE IF NOT EXISTS content_quality_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            word_count INTEGER,
            readability_score INTEGER,
            spelling_errors_count INTEGER,
            grammar_errors_count INTEGER,
            duplicate_content_percentage REAL,
            content_freshness_score INTEGER,
            topic_relevance_score INTEGER,
            semantic_keywords_count INTEGER,
            content_structure_score INTEGER,
            image_optimization_score INTEGER,
            video_optimization_score INTEGER,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'local_seo_audit': """
        CREATE TABLE IF NOT EXISTS local_seo_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            nap_consistency_score INTEGER,
            google_my_business_optimization_score INTEGER,
            local_citations_count INTEGER,
            review_count INTEGER,
            average_rating REAL,
            local_schema_markup_score INTEGER,
            local_keyword_optimization_score INTEGER,
            local_backlinks_count INTEGER,
            directory_listings_count INTEGER,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'social_signals_audit': """
        CREATE TABLE IF NOT EXISTS social_signals_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            facebook_shares INTEGER,
            twitter_shares INTEGER,
            linkedin_shares INTEGER,
            pinterest_shares INTEGER,
            social_media_presence_score INTEGER,
            social_media_engagement_score INTEGER,
            social_media_integration_score INTEGER,
            social_proof_elements_count INTEGER,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'conversion_optimization': """
        CREATE TABLE IF NOT EXISTS conversion_optimization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            cta_count INTEGER,
            form_optimization_score INTEGER,
            landing_page_score INTEGER,
            trust_signals_score INTEGER,
            user_experience_score INTEGER,
            mobile_conversion_score INTEGER,
            page_load_impact_score INTEGER,
            conversion_funnel_score INTEGER,
            a_b_test_opportunities TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'analytics_tracking': """
        CREATE TABLE IF NOT EXISTS analytics_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            google_analytics_status TEXT,
            google_tag_manager_status TEXT,
            google_search_console_status TEXT,
            facebook_pixel_status TEXT,
            conversion_tracking_status TEXT,
            goal_setup_status TEXT,
            ecommerce_tracking_status TEXT,
            custom_dimensions_count INTEGER,
            tracking_errors TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'spelling_errors': """
        CREATE TABLE IF NOT EXISTS spelling_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            error_word TEXT NOT NULL,
            suggested_correction TEXT,
            context_sentence TEXT,
            error_location TEXT,
            severity TEXT,
            is_fixed BOOLEAN DEFAULT 0,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'nap_consistency': """
        CREATE TABLE IF NOT EXISTS nap_consistency (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            expected_name TEXT,
            found_name TEXT,
            expected_address TEXT,
            found_address TEXT,
            expected_phone TEXT,
            found_phone TEXT,
            consistency_score INTEGER,
            inconsistencies TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'content_changes': """
        CREATE TABLE IF NOT EXISTS content_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            content_type TEXT,
            old_content TEXT,
            new_content TEXT,
            change_type TEXT,
            change_reason TEXT,
            changed_by TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_at TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'audit_reports': """
        CREATE TABLE IF NOT EXISTS audit_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            report_type TEXT NOT NULL,
            report_data TEXT,
            pdf_path TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_to_client BOOLEAN DEFAULT 0,
            client_feedback TEXT,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'client_notifications': """
        CREATE TABLE IF NOT EXISTS client_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            notification_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        );
    """,

    'competitive_keywords': """
        CREATE TABLE IF NOT EXISTS competitive_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            keyword TEXT NOT NULL,
            our_position INTEGER,
            competitor_positions TEXT,
            search_volume INTEGER,
            keyword_difficulty INTEGER,
            opportunity_score INTEGER,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'citation_audit': """
        CREATE TABLE IF NOT EXISTS citation_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            directory_name TEXT NOT NULL,
            directory_url TEXT,
            citation_status TEXT,
            nap_accuracy_score INTEGER,
            listing_completeness_score INTEGER,
            issues_found TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'review_monitoring': """
        CREATE TABLE IF NOT EXISTS review_monitoring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            platform TEXT NOT NULL,
            review_id TEXT,
            rating INTEGER,
            review_text TEXT,
            reviewer_name TEXT,
            review_date TEXT,
            response_status TEXT,
            response_text TEXT,
            sentiment_score REAL,
            keywords_mentioned TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,

    'email_marketing_audit': """
        CREATE TABLE IF NOT EXISTS email_marketing_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            email_service_provider TEXT,
            list_size INTEGER,
            open_rate REAL,
            click_rate REAL,
            unsubscribe_rate REAL,
            bounce_rate REAL,
            deliverability_score INTEGER,
            email_template_score INTEGER,
            automation_setup_score INTEGER,
            segmentation_score INTEGER,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """
}

@contextmanager
def db_connection():
    """Provides a managed database connection, ensuring it's always closed."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
    finally:
        if conn:
            conn.close()

def initialize_enhanced_database():
    """Initialize enhanced database with all tables"""
    logger.info(f"Initializing enhanced database '{DB_NAME}'...")

    with db_connection() as conn:
        if not conn:
            logger.critical("Database connection could not be established.")
            return

        cursor = conn.cursor()

        # Create all enhanced tables
        for table_name, create_sql in ENHANCED_TABLES.items():
            try:
                cursor.execute(create_sql)
                logger.debug(f"Created/verified table: {table_name}")
            except sqlite3.Error as e:
                logger.error(f"Failed to create table {table_name}: {e}")

        conn.commit()

    logger.info("Enhanced database initialization complete.")

def get_or_create_site_id(conn: sqlite3.Connection, domain: str) -> int:
    """Get or create site ID for a domain"""
    cursor = conn.cursor()
    try:
        scan_date = datetime.datetime.now().isoformat()
        cursor.execute("INSERT INTO sites (domain, scan_date) VALUES (?, ?)", (domain, scan_date))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM sites WHERE domain = ?", (domain,))
        data = cursor.fetchone()
        if data:
            return data[0]
        else:
            raise

def get_or_create_client_id(conn: sqlite3.Connection, client_name: str, primary_domain: str) -> int:
    """Get or create client ID"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO clients (name, primary_domain) VALUES (?, ?)",
            (client_name, primary_domain)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM clients WHERE name = ? AND primary_domain = ?", (client_name, primary_domain))
        data = cursor.fetchone()
        if data:
            return data[0]
        else:
            raise

def link_site_to_client(conn: sqlite3.Connection, site_id: int, client_id: int):
    """Link a site to a client"""
    cursor = conn.cursor()
    cursor.execute("UPDATE sites SET client_id = ? WHERE id = ?", (client_id, site_id))
    conn.commit()

def get_client_sites(conn: sqlite3.Connection, client_id: int) -> list[dict]:
    """Get all sites for a client"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, domain, site_type, last_updated, status
        FROM sites
        WHERE client_id = ?
    """, (client_id,))

    columns = [description[0] for description in cursor.description]
    sites = []
    for row in cursor.fetchall():
        sites.append(dict(zip(columns, row)))

    return sites

def get_audit_summary(conn: sqlite3.Connection, site_id: int) -> dict:
    """Get audit summary for a site"""
    cursor = conn.cursor()

    # Get basic site info
    cursor.execute("SELECT domain, last_updated FROM sites WHERE id = ?", (site_id,))
    site_info = cursor.fetchone()

    if not site_info:
        return None

    # Get issue counts from various audit tables
    summary = {
        'domain': site_info[0],
        'last_updated': site_info[1],
        'seo_issues': 0,
        'security_issues': 0,
        'accessibility_issues': 0,
        'performance_issues': 0,
        'content_issues': 0
    }

    # Count SEO issues
    cursor.execute("SELECT COUNT(*) FROM seo_issues WHERE site_id = ?", (site_id,))
    summary['seo_issues'] = cursor.fetchone()[0]

    # Count security issues
