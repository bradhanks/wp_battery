import sqlite3
import logging
import datetime
from contextlib import contextmanager
from config import DB_NAME

# Set up a logger for this module
logger = logging.getLogger(__name__)

# --- Database Schema ---
# All table definitions are kept in a single, clear dictionary.
TABLES = {
    'sites': """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            scan_date TEXT NOT NULL
        );
    """,
    'page_metrics': """
        CREATE TABLE IF NOT EXISTS page_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            status_code INTEGER,
            word_count INTEGER,
            internal_links INTEGER,
            external_links INTEGER,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,
    'seo_issues': """
        CREATE TABLE IF NOT EXISTS seo_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,
    'hardening_results': """
        CREATE TABLE IF NOT EXISTS hardening_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            check_name TEXT NOT NULL,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,
    'local_seo_info': """
        CREATE TABLE IF NOT EXISTS local_seo_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT NOT NULL,
            found_nap TEXT,
            has_reviews_schema BOOLEAN,
            has_faq_schema BOOLEAN,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """,
    'wp_stats': """
        CREATE TABLE IF NOT EXISTS wp_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            post_count INTEGER DEFAULT 0,
            page_count INTEGER DEFAULT 0,
            media_count INTEGER DEFAULT 0,
            category_count INTEGER DEFAULT 0,
            tag_count INTEGER DEFAULT 0,
            product_count INTEGER DEFAULT 0,
            product_category_count INTEGER DEFAULT 0,
            has_yoast_seo BOOLEAN DEFAULT 0,
            has_woocommerce BOOLEAN DEFAULT 0,
            scan_date TEXT NOT NULL,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
    """
}

# --- Database Functions ---

@contextmanager
def db_connection():
    """Provides a managed database connection, ensuring it's always closed."""
    conn = None
    try:
        # The `check_same_thread=False` is essential for multi-threaded access.
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
    finally:
        if conn:
            conn.close()

def initialize_database():
    """Creates all necessary tables in the SQLite database if they don't exist."""
    logger.info(f"Initializing database '{DB_NAME}'...")
    with db_connection() as conn:
        # FIX: Added a check to ensure the connection was successful before proceeding.
        if not conn:
            logger.critical("Database connection could not be established. Halting initialization.")
            return

        cursor = conn.cursor()
        for table_name, create_sql in TABLES.items():
            try:
                cursor.execute(create_sql)
            except sqlite3.Error as e:
                logger.error(f"Failed to create table {table_name}: {e}")
        conn.commit()
    logger.info("Database initialization complete.")

def get_or_create_site_id(conn: sqlite3.Connection, domain: str) -> int:
    """
    Retrieves the site ID for a domain, creating a new entry in a thread-safe way.

    This function uses an "Easier to Ask for Forgiveness than Permission" (EAFP) approach
    to prevent race conditions. It tries to insert first, and if that fails due to a
    UNIQUE constraint, it then fetches the ID of the existing entry.
    """
    cursor = conn.cursor()
    try:
        # Attempt to insert the new domain first.
        scan_date = datetime.datetime.now().isoformat()
        cursor.execute("INSERT INTO sites (domain, scan_date) VALUES (?, ?)", (domain, scan_date))
        conn.commit()
        logger.debug(f"Created new site entry for {domain} with ID {cursor.lastrowid}.")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # This block runs if the INSERT failed because the domain already exists.
        logger.debug(f"Domain {domain} already exists. Fetching its ID.")
        cursor.execute("SELECT id FROM sites WHERE domain = ?", (domain,))
        data = cursor.fetchone()
        if data:
            return data[0]
        else:
            # This is a fallback for an unlikely edge case.
            logger.error(f"Failed to create or find site ID for {domain} after integrity error.")
            raise
