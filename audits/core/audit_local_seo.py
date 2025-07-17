import logging
import re
import json
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

# Set up a logger for this module
logger = logging.getLogger(__name__)

# --- Data Structures for Clarity ---
# Using simple dictionaries for now, but could be expanded to dataclasses
# for even more structure.

# --- Main Audit Function ---

def run_local_seo_audits(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Audits a single page's BeautifulSoup object for multiple local SEO signals.

    This function acts as an orchestrator, calling specialized functions to extract
    structured data and returns a dictionary of all findings for this page.

    Args:
        soup: A BeautifulSoup object representing the page's HTML.

    Returns:
        A dictionary containing all extracted local SEO data for the page.
    """
    page_findings = {
        "local_business_schema": _extract_local_business_schema(soup),
        "review_schema": _extract_review_schema(soup),
        "faq_schema": _extract_faq_schema(soup),
        "found_phone_numbers_in_text": _find_phones_in_text(soup)
    }
    return page_findings

# --- Data Extraction Functions ---

def _extract_local_business_schema(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Finds and extracts key data from LocalBusiness or its subtypes (e.g., Dentist).

    This is the most reliable way to find NAP and leadership info.
    """
    schema_data = _find_json_ld_schema(soup, ["LocalBusiness", "Dentist", "Physician"])
    if not schema_data:
        return None

    # Extract key information, using .get() to avoid errors if a key is missing.
    address = schema_data.get('address', {})
    founder = schema_data.get('founder', {})

    return {
        "type": schema_data.get('@type'),
        "name": schema_data.get('name'),
        "telephone": schema_data.get('telephone'),
        "url": schema_data.get('url'),
        "address": {
            "streetAddress": address.get('streetAddress'),
            "addressLocality": address.get('addressLocality'),
            "addressRegion": address.get('addressRegion'),
            "postalCode": address.get('postalCode')
        },
        "founder": {
            "name": founder.get('name'),
            "jobTitle": founder.get('jobTitle'),
            "sameAs": founder.get('sameAs', [])
        },
        "social_profiles": schema_data.get('sameAs', [])
    }

def _extract_review_schema(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """Finds and extracts data from AggregateRating schema."""
    schema_data = _find_json_ld_schema(soup, "AggregateRating")
    if not schema_data:
        return None

    return {
        "ratingValue": schema_data.get('ratingValue'),
        "reviewCount": schema_data.get('reviewCount'),
        "bestRating": schema_data.get('bestRating', '5') # Default to 5 if not specified
    }

def _extract_faq_schema(soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
    """Finds and extracts all questions and answers from FAQPage schema."""
    schema_data = _find_json_ld_schema(soup, "FAQPage")
    if not schema_data or 'mainEntity' not in schema_data:
        return None

    faq_list = []
    for item in schema_data['mainEntity']:
        if item.get('@type') == 'Question':
            question = item.get('name')
            answer = item.get('acceptedAnswer', {}).get('text')
            if question and answer:
                faq_list.append({"question": question, "answer": answer})
    return faq_list if faq_list else None

def _find_phones_in_text(soup: BeautifulSoup) -> List[str]:
    """A fallback function to find phone numbers in plain text if no schema exists."""
    phone_regex = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    page_text = soup.get_text(" ", strip=True)
    # Use a set to get unique phone numbers, then convert to a list
    unique_phones = set(phone_regex.findall(page_text))
    return list(unique_phones)

# --- Helper Function ---

def _find_json_ld_schema(soup: BeautifulSoup, target_types: Any) -> Optional[Dict[str, Any]]:
    """
    A generic helper to find a specific type of JSON-LD schema in a page.

    Args:
        soup: The BeautifulSoup object for the page.
        target_types: A string or list of strings of the schema @type to find.
    """
    if isinstance(target_types, str):
        target_types = [target_types]

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            # Handle schema that is a list (e.g., @graph)
            if '@graph' in data:
                for item in data['@graph']:
                    if item.get('@type') in target_types:
                        return item
            # Handle single schema objects
            if data.get('@type') in target_types:
                return data
        except (json.JSONDecodeError, AttributeError, TypeError):
            # Ignore scripts that are not valid JSON or don't have the expected structure
            continue
    return None

# --- Example of how this would be used in your main analyzer ---
# This part would go in your main script, not here.

def aggregate_and_log_site_results(conn, site_id: int, all_page_audits: List[Dict]):
    """
    Analyzes the collected data for all pages to create a site-wide summary.
    This function demonstrates how you would use the audit results.
    """
    # Initialize site-wide findings
    site_has_faq = False
    site_has_reviews = False
    primary_nap = "Not Found"

    # Find the first valid LocalBusiness schema to use as the primary NAP
    for page_audit in all_page_audits:
        if page_audit.get("local_business_schema"):
            primary_nap = json.dumps(page_audit["local_business_schema"])
            break # Stop after finding the first one

    # Check if any page had FAQ or Review schema
    for page_audit in all_page_audits:
        if page_audit.get("faq_schema"):
            site_has_faq = True
        if page_audit.get("review_schema"):
            site_has_reviews = True

    logger.info(f"Site-wide summary for site_id {site_id}: Has FAQ? {site_has_faq}, Has Reviews? {site_has_reviews}")

    # Now, log this summarized data to the database
    try:
        cursor = conn.cursor()
        # This assumes you have a table designed for site-wide summaries.
        # The schema would need to be updated in database.py.
        cursor.execute(
            """INSERT INTO site_level_local_seo (site_id, primary_nap_json, has_faq_schema, has_reviews_schema)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(site_id) DO UPDATE SET
               primary_nap_json=excluded.primary_nap_json,
               has_faq_schema=excluded.has_faq_schema,
               has_reviews_schema=excluded.has_reviews_schema;
            """,
            (site_id, primary_nap, site_has_faq, site_has_reviews)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"DB Error logging site-wide summary for site ID {site_id}: {e}")
