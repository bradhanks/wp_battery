import logging
from typing import Optional, Dict
from wpypress import WPClient
from database import db_connection, get_or_create_site_id
from config import REQUEST_TIMEOUT
import urllib3
import time
urllib3.disable_warnings()

logger = logging.getLogger(__name__)

# Common WordPress credentials to try (can be moved to config.py)
WP_CREDENTIALS = [
    {'username': 'admin', 'password': 'password123'},
    {'username': 'admin', 'password': 'admin'},
    {'username': 'wpadmin', 'password': 'wpadmin'},
]

class WordPressStatsCollector:
    def __init__(self, domain: str):
        self.domain = domain
        self.stats = {
            'post_count': 0,
            'page_count': 0,
            'media_count': 0,
            'category_count': 0,
            'tag_count': 0,
            'product_count': 0,
            'product_category_count': 0,
            'has_yoast_seo': False,
            'has_woocommerce': False,
            'scan_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.wp_client = None

    def connect(self) -> bool:
        """Try to connect using common credentials"""
        base_url = f"https://{self.domain}"

        for creds in WP_CREDENTIALS:
            try:
                self.wp_client = WPClient(
                    base_url=base_url,
                    username=creds['username'],
                    password=creds['password'],
                    timeout=REQUEST_TIMEOUT
                )
                # audit connection with a simple API call
                self.wp_client.posts.list(params={'per_page': 1})
                return True
            except Exception as e:
                logger.debug(f"[{self.domain}] Connection failed with {creds['username']}: {str(e)}")
                continue

        logger.warning(f"[{self.domain}] Could not authenticate with any known credentials")
        return False

    def collect_stats(self) -> Dict:
        """Collect all available WordPress statistics"""
        if not self.connect():
            return self.stats

        try:
            self._collect_content_stats()
            self._collect_seo_stats()
            self._collect_ecommerce_stats()
        except Exception as e:
            logger.error(f"[{self.domain}] Error collecting stats: {str(e)}")

        return self.stats

    def _collect_content_stats(self):
        """Collect posts, pages, media, and taxonomy stats"""
        # Posts
        posts, pagination = self.wp_client.posts.list(params={'per_page': 1})
        self.stats['post_count'] = pagination.get('total', 0)

        # Pages
        pages, pagination = self.wp_client.pages.list(params={'per_page': 1})
        self.stats['page_count'] = pagination.get('total', 0)

        # Media
        media, pagination = self.wp_client.media.list(params={'per_page': 1})
        self.stats['media_count'] = pagination.get('total', 0)

        # Categories
        categories, pagination = self.wp_client.categories.list(params={'per_page': 1})
        self.stats['category_count'] = pagination.get('total', 0)

        # Tags
        tags, pagination = self.wp_client.tags.list(params={'per_page': 1})
        self.stats['tag_count'] = pagination.get('total', 0)

    def _collect_seo_stats(self):
        """Check for Yoast SEO plugin"""
        try:
            self.stats['has_yoast_seo'] = self.wp_client.seo.is_yoast()
        except Exception as e:
            logger.debug(f"[{self.domain}] Yoast check failed: {str(e)}")

    def _collect_ecommerce_stats(self):
        """Check for WooCommerce and collect product stats"""
        try:
            if self.wp_client.products.isWoocommerce():
                self.stats['has_woocommerce'] = True
                products, pagination = self.wp_client.products.list(params={'per_page': 1})
                self.stats['product_count'] = pagination.get('total', 0)

                categories, pagination = self.wp_client.product_categories.list(params={'per_page': 1})
                self.stats['product_category_count'] = pagination.get('total', 0)
        except Exception as e:
            logger.debug(f"[{self.domain}] WooCommerce check failed: {str(e)}")

def save_wp_stats_to_db(domain: str, stats: Dict):
    """Save collected stats to database"""
    with db_connection() as conn:
        try:
            site_id = get_or_create_site_id(conn, domain)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO wp_stats (
                    site_id, post_count, page_count, media_count,
                    category_count, tag_count, product_count,
                    product_category_count, has_yoast_seo,
                    has_woocommerce, scan_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                site_id,
                stats['post_count'],
                stats['page_count'],
                stats['media_count'],
                stats['category_count'],
                stats['tag_count'],
                stats['product_count'],
                stats['product_category_count'],
                int(stats['has_yoast_seo']),
                int(stats['has_woocommerce']),
                stats['scan_date']
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"[{domain}] Failed to save stats to DB: {str(e)}")

def collect_wordpress_stats(domain: str):
    """Main function to collect and save WordPress stats"""
    logger.info(f"[{domain}] Starting WordPress stats collection")

    collector = WordPressStatsCollector(domain)
    stats = collector.collect_stats()
    save_wp_stats_to_db(domain, stats)

    logger.info(f"[{domain}] Completed WordPress stats collection")
