import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def run_basic_seo_audits(conn, site_id: int, url: str, soup: BeautifulSoup):
    _check_for_lorem_ipsum(conn, site_id, url, soup)
    _check_for_noindex(conn, site_id, url, soup)
    _check_title_tag(conn, site_id, url, soup)
    _check_meta_description(conn, site_id, url, soup)
    _check_h1_tag(conn, site_id, url, soup)
    _check_canonical_tag(conn, site_id, url, soup)
    _check_img_alt_attributes(conn, site_id, url, soup)
    _check_multiple_h1_tags(conn, site_id, url, soup)
    _check_empty_title(conn, site_id, url, soup)

def _log_issue(conn, site_id, url, issue_type, details):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO seo_issues (site_id, url, issue_type, details) VALUES (?, ?, ?, ?)",
            (site_id, url, issue_type, details)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"DB Error logging SEO issue for site ID {site_id}: {e}")

def _check_for_lorem_ipsum(conn, site_id, url, soup):
    if re.search(r'lorem ipsum', soup.get_text(), re.IGNORECASE):
        _log_issue(conn, site_id, url, "Lorem Ipsum", "Page contains placeholder text.")

def _check_for_noindex(conn, site_id, url, soup):
    noindex_tag = soup.find('meta', attrs={'name': 'robots', 'content': re.compile(r'noindex', re.I)})
    if noindex_tag:
        _log_issue(conn, site_id, url, "NoIndex Tag", "Page has a 'noindex' meta tag, preventing search engine indexing.")

def _check_title_tag(conn, site_id, url, soup):
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    if not title:
        _log_issue(conn, site_id, url, "Missing Title", "Page is missing a <title> tag or it is empty.")
    elif len(title) < 10 or len(title) > 70:
        _log_issue(conn, site_id, url, "Title Length", f"Title tag length is {len(title)} characters.")

def _check_meta_description(conn, site_id, url, soup):
    desc = soup.find('meta', attrs={'name': 'description'})
    content = desc['content'].strip() if desc and desc.has_attr('content') else ""
    if not content:
        _log_issue(conn, site_id, url, "Missing Meta Description", "Page is missing a meta description.")
    elif len(content) < 50 or len(content) > 160:
        _log_issue(conn, site_id, url, "Meta Description Length", f"Meta description length is {len(content)} characters.")

def _check_h1_tag(conn, site_id, url, soup):
    h1 = soup.find('h1')
    if not h1 or not h1.get_text(strip=True):
        _log_issue(conn, site_id, url, "Missing H1", "Page is missing an H1 tag or it is empty.")

def _check_multiple_h1_tags(conn, site_id, url, soup):
    h1_tags = soup.find_all('h1')
    if len(h1_tags) > 1:
        _log_issue(conn, site_id, url, "Multiple H1 Tags", f"Page has {len(h1_tags)} H1 tags.")

def _check_canonical_tag(conn, site_id, url, soup):
    canonical = soup.find('link', rel='canonical')
    if not canonical or not canonical.get('href'):
        _log_issue(conn, site_id, url, "Missing Canonical", "Page is missing a canonical link tag.")

def _check_img_alt_attributes(conn, site_id, url, soup):
    imgs = soup.find_all('img')
    for img in imgs:
        if not img.has_attr('alt') or not img['alt'].strip():
            _log_issue(conn, site_id, url, "Missing Image Alt", "Image missing alt attribute.")

def _check_empty_title(conn, site_id, url, soup):
    if soup.title and not soup.title.string.strip():
        _log_issue(conn, site_id, url, "Empty Title", "Title tag is present but empty.")
