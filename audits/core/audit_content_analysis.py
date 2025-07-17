import logging
from urllib3.util import parse_url
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def run_content_analysis(conn, site_id: int, url: str, soup: BeautifulSoup):
    word_count = _count_words(soup)
    internal_links, external_links = _analyze_links(url, soup)

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE page_metrics SET word_count = ?, internal_links = ?, external_links = ? WHERE site_id = ? AND url = ?",
            (word_count, internal_links, external_links, site_id, url)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"DB Error updating page metrics for site ID {site_id}: {e}")

def _count_words(soup: BeautifulSoup) -> int:
    return len(soup.get_text(strip=True).split())

def _analyze_links(base_url: str, soup: BeautifulSoup) -> (int, int):
    internal_count = 0
    external_count = 0
    base_domain = parse_url(base_url).netloc

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue

        link_domain = parse_url(href).netloc
        if link_domain and base_domain in link_domain:
            internal_count += 1
        elif not link_domain:
            internal_count += 1
        else:
            external_count += 1

    return internal_count, external_count
