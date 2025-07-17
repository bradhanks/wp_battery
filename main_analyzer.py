import logging
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

from config import DOMAINS_TO_SCAN, MAX_WORKERS, REQUEST_TIMEOUT, USER_AGENT
import database
import reporting
from stats import stats_collector
from audits import audit_wp_security, audit_basic_seo, audit_local_seo, audit_content_analysis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('full_analysis.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def discover_pages(session: requests.Session, domain: str) -> set:
    sitemap_url = f"https://{domain}/sitemap.xml"
    page_urls = set()
    try:
        response = session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            for loc in soup.find_all("loc"):
                page_urls.add(loc.text)
    except requests.RequestException as e:
        logging.error(f"[{domain}] Could not fetch sitemap: {e}")

    if not page_urls:
        page_urls.add(f"https://{domain}/")

    return page_urls

def analyze_single_page(conn, session, site_id, url, domain):
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        status_code = response.status_code
    except requests.RequestException as e:
        status_code = -1
        logging.warning(f"[{domain}] Failed to fetch page {url}: {e}")

    cursor = conn.cursor()
    cursor.execute("INSERT INTO page_metrics (site_id, url, status_code) VALUES (?, ?, ?)", (site_id, url, status_code))
    conn.commit()

    if status_code >= 400 or status_code == -1:
        cursor.execute("INSERT INTO seo_issues (site_id, url, issue_type, details) VALUES (?, ?, ?, ?)", (site_id, url, "Broken Link", f"HTTP Status: {status_code}"))
        conn.commit()
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    audit_basic_seo.run_basic_seo_audits(conn, site_id, url, soup)
    audit_local_seo.run_local_seo_audits(conn, site_id, url, soup)
    audit_content_analysis.run_content_audit(conn, site_id, url, soup)

def run_full_analysis_on_domain(domain: str):
    logging.info(f"Starting full analysis for {domain}")

    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})

    with database.db_connection() as conn:
        site_id = database.get_or_create_site_id(conn, domain)

        # Run WordPress stats collection first
        try:
            stats_collector.collect_wordpress_stats(domain)
        except Exception as e:
            logging.error(f"[{domain}] WordPress stats collection failed: {str(e)}")

        audit_wp_security.run_security_audits(conn, session, domain)
        pages_to_check = discover_pages(session, domain)
        logging.info(f"[{domain}] Found {len(pages_to_check)} pages to analyze.")

        for url in pages_to_check:
            analyze_single_page(conn, session, site_id, url, domain)
            time.sleep(0.1)

    logging.info(f"Completed analysis for {domain}")
    return domain

def main():
    """
    Main entry point for the master analysis process.

    This function initializes the database, starts parallel analysis of domains using a thread pool,
    handles exceptions from worker threads, generates CSV reports upon completion, and logs the total
    execution time and output location.

    Steps performed:
    1. Initializes the database.
    2. Logs the start of the analysis, including the number of domains and workers.
    3. Runs full analysis on each domain concurrently using ThreadPoolExecutor.
    4. Handles and logs any exceptions raised by worker threads.
    5. Generates CSV reports after all analysis tasks are complete.
    6. Logs the total time taken and the report output prefix.
    """
    start_time = time.time()
    database.initialize_database()

    logging.info(f"🚀 Starting Master Analysis for {len(DOMAINS_TO_SCAN)} domains with {MAX_WORKERS} workers...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix='Worker') as executor:
        futures = [executor.submit(run_full_analysis_on_domain, domain) for domain in DOMAINS_TO_SCAN]

        for future in as_completed(futures):
            try:
                result_domain = future.result()
                logging.info(f"✅ Thread for {result_domain} finished successfully.")
            except Exception as e:
                logging.error(f"A thread generated an unhandled exception: {e}", exc_info=True)

    logging.info("--- All analysis tasks complete. Generating reports... ---")

    output_prefix = f"analysis_{time.strftime('%Y%m%d-%H%M%S')}"
    reporting.generate_csv_reports(output_prefix)

    total_time = time.time() - start_time
    logging.info(f"🎉 All operations finished in {total_time:.2f} seconds. Reports are saved with prefix '{output_prefix}'.")

if __name__ == "__main__":
    main()
