import csv
import logging
from database import db_connection

logger = logging.getLogger(__name__)

def generate_wp_stats_report(output_prefix: str):
    """Generate a CSV report of WordPress statistics"""
    logger.info("Generating WordPress stats report...")

    query = """
    SELECT
        s.domain,
        w.post_count,
        w.page_count,
        w.media_count,
        w.category_count,
        w.tag_count,
        w.has_yoast_seo,
        w.has_woocommerce,
        w.product_count,
        w.product_category_count,
        w.scan_date
    FROM wp_stats w
    JOIN sites s ON w.site_id = s.id
    """

    filename = f"{output_prefix}_wordpress_stats.csv"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                logger.warning("No WordPress stats data found")
                return

            header = [description[0] for description in cursor.description]

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows)

        logger.info(f"Successfully generated WordPress stats report: {filename}")
    except Exception as e:
        logger.error(f"Failed to generate WordPress stats report: {str(e)}")


def generate_csv_reports(output_prefix: str):
    logger.info("Generating CSV reports from database...")
    generate_wp_stats_report(output_prefix)

    report_map = {
        'full_page_metrics': "SELECT s.domain, p.url, p.status_code, p.word_count, p.internal_links, p.external_links FROM page_metrics p JOIN sites s ON p.site_id = s.id",
        'all_seo_issues': "SELECT s.domain, i.url, i.issue_type, i.details FROM seo_issues i JOIN sites s ON i.site_id = s.id",
        'all_hardening_results': "SELECT s.domain, h.check_name, h.status, h.details FROM hardening_results h JOIN sites s ON h.site_id = s.id",
        'all_local_seo_info': "SELECT s.domain, l.url, l.found_nap, l.has_reviews_schema, l.has_faq_schema FROM local_seo_info l JOIN sites s ON l.site_id = s.id"
    }

    with db_connection() as conn:
        for report_name, query in report_map.items():
            try:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                if not rows:
                    logger.warning(f"No data found for report '{report_name}'. Skipping CSV generation.")
                    continue

                header = [description[0] for description in cursor.description]
                filename = f"{output_prefix}_{report_name}.csv"

                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(rows)

                logger.info(f"Successfully generated report: {filename}")

            except Exception as e:
                logger.error(f"Failed to generate report for '{report_name}': {e}")
