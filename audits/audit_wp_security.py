import logging
import requests
import re
import json
from typing import Dict, List, Tuple, Optional
from database import get_or_create_site_id

logger = logging.getLogger(__name__)

class WordPressSecurityauditer:
    """Enhanced WordPress Security auditing Suite"""

    def __init__(self, conn, session: requests.Session, domain: str):
        self.conn = conn
        self.session = session
        self.domain = domain
        self.site_id = get_or_create_site_id(conn, domain)
        self.base_url = f"https://{domain}"

    def run_comprehensive_security_audits(self):
        """Run all security audits"""
        logger.info(f"[{self.domain}] Running comprehensive WordPress security audit...")

        # Core Security audits
        self._audit_user_enumeration()
        self._audit_sensitive_file_access()
        self._audit_directory_protection()
        self._audit_version_disclosure()
        self._audit_security_headers()
        self._audit_login_protection()
        self._audit_xmlrpc_security()
        self._audit_rest_api_security()
        self._audit_admin_exposure()
        self._audit_backup_files()
        self._audit_debug_info_disclosure()
        self._audit_plugin_enumeration()
        self._audit_theme_enumeration()
        self._audit_upload_security()
        self._audit_ssl_configuration()

        logger.info(f"[{self.domain}] Security audit completed")

    def _log_result(self, check: str, status: str, details: str, severity: str = "INFO"):
        """Log security audit results to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO hardening_results (site_id, check_name, status, details, severity, timestamp)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (self.site_id, check, status, details, severity))
            self.conn.commit()
        except Exception as e:
            logger.error(f"DB Error logging result for {check}: {e}")

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with error handling"""
        try:
            kwargs.setdefault('timeout', 10)
            kwargs.setdefault('verify', False)
            kwargs.setdefault('allow_redirects', True)

            if method.upper() == "GET":
                return self.session.get(url, **kwargs)
            elif method.upper() == "POST":
                return self.session.post(url, **kwargs)
            elif method.upper() == "HEAD":
                return self.session.head(url, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request failed for {url}: {e}")
            return None

    def _audit_user_enumeration(self):
        """audit for user enumeration vulnerabilities"""
        vulnerabilities = []

        # audit REST API user enumeration
        api_url = f"{self.base_url}/wp-json/wp/v2/users"
        response = self._make_request(api_url)
        if response and response.status_code == 200:
            try:
                users = response.json()
                if users and len(users) > 0:
                    usernames = [user.get('slug', 'unknown') for user in users]
                    vulnerabilities.append(f"REST API exposes {len(users)} users: {', '.join(usernames[:5])}")
            except:
                pass

        # audit author parameter enumeration
        for user_id in range(1, 6):  # audit first 5 potential users
            author_url = f"{self.base_url}/?author={user_id}"
            response = self._make_request(author_url, allow_redirects=False)
            if response and response.status_code in (301, 302):
                location = response.headers.get('location', '')
                username_match = re.search(r'/author/([^/]+)', location)
                if username_match:
                    username = username_match.group(1)
                    vulnerabilities.append(f"Author enumeration reveals username: {username}")

        # audit oembed endpoint
        oembed_url = f"{self.base_url}/wp-json/oembed/1.0/embed?url={self.base_url}"
        response = self._make_request(oembed_url)
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'author_name' in data:
                    vulnerabilities.append(f"oEmbed endpoint reveals author: {data['author_name']}")
            except:
                pass

        status = "FAIL" if vulnerabilities else "PASS"
        details = "; ".join(vulnerabilities) if vulnerabilities else "User enumeration vectors appear secure"
        severity = "HIGH" if vulnerabilities else "INFO"
        self._log_result("User Enumeration", status, details, severity)

    def _audit_sensitive_file_access(self):
        """audit access to sensitive WordPress files"""
        sensitive_files = [
            ("wp-config.php", "CRITICAL"),
            ("wp-config.php.bak", "CRITICAL"),
            ("wp-config.php~", "CRITICAL"),
            ("wp-config.php.save", "CRITICAL"),
            (".htaccess", "HIGH"),
            ("readme.html", "MEDIUM"),
            ("license.txt", "LOW"),
            ("wp-config-sample.php", "MEDIUM"),
            ("wp-admin/install.php", "HIGH"),
            ("wp-admin/upgrade.php", "HIGH"),
            ("xmlrpc.php", "MEDIUM"),
            ("wp-cron.php", "MEDIUM")
        ]

        accessible_files = []
        for filename, severity in sensitive_files:
            url = f"{self.base_url}/{filename}"
            response = self._make_request(url)
            if response and response.status_code == 200:
                file_size = len(response.content)
                accessible_files.append(f"{filename} ({file_size} bytes, {severity} risk)")

        status = "FAIL" if accessible_files else "PASS"
        details = f"Accessible files: {'; '.join(accessible_files)}" if accessible_files else "No sensitive files publicly accessible"
        severity = "CRITICAL" if any("CRITICAL" in f for f in accessible_files) else "HIGH" if accessible_files else "INFO"
        self._log_result("Sensitive File Access", status, details, severity)

    def _audit_directory_protection(self):
        """audit directory listing protection"""
        directories = [
            "wp-content/",
            "wp-includes/",
            "wp-admin/",
            "wp-content/uploads/",
            "wp-content/themes/",
            "wp-content/plugins/"
        ]

        browseable_dirs = []
        for directory in directories:
            url = f"{self.base_url}/{directory}"
            response = self._make_request(url)
            if response and response.status_code == 200:
                # Check for directory listing indicators
                content = response.text.lower()
                if any(indicator in content for indicator in ["index of", "parent directory", "<title>index of"]):
                    browseable_dirs.append(directory)

        status = "FAIL" if browseable_dirs else "PASS"
        details = f"Browseable directories: {', '.join(browseable_dirs)}" if browseable_dirs else "Directory listing properly restricted"
        severity = "MEDIUM" if browseable_dirs else "INFO"
        self._log_result("Directory Protection", status, details, severity)

    def _audit_version_disclosure(self):
        """audit for WordPress version disclosure"""
        version_sources = []

        # Check generator meta tag
        response = self._make_request(self.base_url)
        if response and response.status_code == 200:
            generator_match = re.search(r'<meta name="generator" content="WordPress ([^"]+)"', response.text, re.IGNORECASE)
            if generator_match:
                version_sources.append(f"Generator meta tag: {generator_match.group(1)}")

        # Check readme.html
        readme_url = f"{self.base_url}/readme.html"
        response = self._make_request(readme_url)
        if response and response.status_code == 200:
            version_match = re.search(r'Version (\d+\.\d+(?:\.\d+)?)', response.text)
            if version_match:
                version_sources.append(f"readme.html: {version_match.group(1)}")

        # Check RSS feed
        rss_url = f"{self.base_url}/feed/"
        response = self._make_request(rss_url)
        if response and response.status_code == 200:
            generator_match = re.search(r'<generator>.*?WordPress ([^<]+)', response.text, re.IGNORECASE)
            if generator_match:
                version_sources.append(f"RSS feed: {generator_match.group(1)}")

        status = "FAIL" if version_sources else "PASS"
        details = "; ".join(version_sources) if version_sources else "WordPress version not publicly disclosed"
        severity = "MEDIUM" if version_sources else "INFO"
        self._log_result("Version Disclosure", status, details, severity)

    def _audit_security_headers(self):
        """audit for security-related HTTP headers"""
        response = self._make_request(self.base_url)
        if not response:
            self._log_result("Security Headers", "ERROR", "Could not retrieve headers", "LOW")
            return

        headers = response.headers
        missing_headers = []
        weak_headers = []

        # Check for important security headers
        security_headers = {
            'X-Frame-Options': 'Clickjacking protection',
            'X-Content-Type-Options': 'MIME sniffing protection',
            'X-XSS-Protection': 'XSS protection',
            'Strict-Transport-Security': 'HTTPS enforcement',
            'Content-Security-Policy': 'Content injection protection',
            'Referrer-Policy': 'Referrer information control'
        }

        for header, description in security_headers.items():
            if header not in headers:
                missing_headers.append(f"{header} ({description})")

        # Check for information disclosure headers
        disclosure_headers = ['Server', 'X-Powered-By', 'X-Pingback']
        disclosed_info = []
        for header in disclosure_headers:
            if header in headers:
                disclosed_info.append(f"{header}: {headers[header]}")

        issues = []
        if missing_headers:
            issues.append(f"Missing headers: {', '.join(missing_headers)}")
        if disclosed_info:
            issues.append(f"Information disclosure: {', '.join(disclosed_info)}")

        status = "FAIL" if issues else "PASS"
        details = "; ".join(issues) if issues else "Security headers properly configured"
        severity = "MEDIUM" if issues else "INFO"
        self._log_result("Security Headers", status, details, severity)

    def _audit_login_protection(self):
        """audit WordPress login security"""
        login_url = f"{self.base_url}/wp-login.php"
        admin_url = f"{self.base_url}/wp-admin/"

        vulnerabilities = []

        # audit if login page is accessible
        response = self._make_request(login_url)
        if response and response.status_code == 200:
            # Check for login protection indicators
            content = response.text.lower()
            if 'login' in content and 'password' in content:
                vulnerabilities.append("Login page is publicly accessible")

        # audit admin redirect behavior
        response = self._make_request(admin_url, allow_redirects=False)
        if response and response.status_code == 302:
            location = response.headers.get('location', '')
            if 'wp-login.php' in location:
                vulnerabilities.append("Admin area redirects to login (normal behavior)")

        # audit for common weak credentials (basic audit)
        weak_creds = [('admin', 'admin'), ('admin', 'password'), ('admin', '123456')]
        for username, password in weak_creds:
            data = {
                'log': username,
                'pwd': password,
                'wp-submit': 'Log In',
                'redirect_to': admin_url,
                'auditcookie': '1'
            }
            response = self._make_request(login_url, method="POST", data=data, allow_redirects=False)
            if response and response.status_code == 302:
                location = response.headers.get('location', '')
                if 'wp-admin' in location and 'wp-login.php' not in location:
                    vulnerabilities.append(f"Weak credentials detected: {username}:{password}")

        status = "FAIL" if any("weak credentials" in v.lower() for v in vulnerabilities) else "PASS"
        details = "; ".join(vulnerabilities) if vulnerabilities else "Login security appears adequate"
        severity = "CRITICAL" if any("weak credentials" in v.lower() for v in vulnerabilities) else "INFO"
        self._log_result("Login Security", status, details, severity)

    def _audit_xmlrpc_security(self):
        """audit XML-RPC security"""
        xmlrpc_url = f"{self.base_url}/xmlrpc.php"
        response = self._make_request(xmlrpc_url, method="POST", data="<?xml version='1.0'?>")

        if response and response.status_code == 200:
            content = response.text
            if 'xml-rpc server accepts post requests only' in content.lower():
                # audit for system.listMethods
                list_methods_payload = """<?xml version="1.0"?>
                <methodCall>
                    <methodName>system.listMethods</methodName>
                    <params></params>
                </methodCall>"""

                response = self._make_request(xmlrpc_url, method="POST",
                                            data=list_methods_payload,
                                            headers={'Content-Type': 'text/xml'})

                if response and 'wp.getUsersBlogs' in response.text:
                    status = "FAIL"
                    details = "XML-RPC is enabled and exposes methods that could be abused"
                    severity = "HIGH"
                else:
                    status = "WARN"
                    details = "XML-RPC is enabled but methods are limited"
                    severity = "MEDIUM"
            else:
                status = "PASS"
                details = "XML-RPC appears to be disabled or restricted"
                severity = "INFO"
        else:
            status = "PASS"
            details = "XML-RPC is not accessible"
            severity = "INFO"

        self._log_result("XML-RPC Security", status, details, severity)

    def _audit_rest_api_security(self):
        """audit REST API security"""
        api_base = f"{self.base_url}/wp-json/wp/v2"

        vulnerabilities = []

        # audit unauthenticated access to posts
        response = self._make_request(f"{api_base}/posts")
        if response and response.status_code == 200:
            try:
                posts = response.json()
                if posts:
                    vulnerabilities.append(f"REST API exposes {len(posts)} posts without authentication")
            except:
                pass

        # audit media access
        response = self._make_request(f"{api_base}/media")
        if response and response.status_code == 200:
            try:
                media = response.json()
                if media:
                    vulnerabilities.append(f"REST API exposes {len(media)} media files")
            except:
                pass

        # audit comments access
        response = self._make_request(f"{api_base}/comments")
        if response and response.status_code == 200:
            try:
                comments = response.json()
                if comments:
                    vulnerabilities.append(f"REST API exposes {len(comments)} comments")
            except:
                pass

        status = "FAIL" if vulnerabilities else "PASS"
        details = "; ".join(vulnerabilities) if vulnerabilities else "REST API access properly restricted"
        severity = "MEDIUM" if vulnerabilities else "INFO"
        self._log_result("REST API Security", status, details, severity)

    def _audit_admin_exposure(self):
        """audit for admin area exposure"""
        admin_paths = [
            "wp-admin/",
            "wp-admin/admin-ajax.php",
            "wp-admin/admin-post.php",
            "wp-admin/install.php",
            "wp-admin/upgrade.php"
        ]

        exposed_paths = []
        for path in admin_paths:
            url = f"{self.base_url}/{path}"
            response = self._make_request(url)
            if response and response.status_code == 200:
                # Check if it's actually accessible (not redirected to login)
                if 'wp-login.php' not in response.url:
                    exposed_paths.append(path)

        status = "FAIL" if exposed_paths else "PASS"
        details = f"Exposed admin paths: {', '.join(exposed_paths)}" if exposed_paths else "Admin area properly protected"
        severity = "HIGH" if exposed_paths else "INFO"
        self._log_result("Admin Exposure", status, details, severity)

    def _audit_backup_files(self):
        """audit for backup file exposure"""
        backup_patterns = [
            "wp-config.php.bak",
            "wp-config.php~",
            "wp-config.php.save",
            "wp-config.php.orig",
            "backup.zip",
            "backup.tar.gz",
            "database.sql",
            "dump.sql",
            "site.zip"
        ]

        found_backups = []
        for pattern in backup_patterns:
            url = f"{self.base_url}/{pattern}"
            response = self._make_request(url)
            if response and response.status_code == 200:
                size = len(response.content)
                found_backups.append(f"{pattern} ({size} bytes)")

        status = "FAIL" if found_backups else "PASS"
        details = f"Accessible backup files: {', '.join(found_backups)}" if found_backups else "No backup files found"
        severity = "CRITICAL" if found_backups else "INFO"
        self._log_result("Backup File Exposure", status, details, severity)

    def _audit_debug_info_disclosure(self):
        """audit for debug information disclosure"""
        debug_indicators = []

        # audit main page for debug info
        response = self._make_request(self.base_url)
        if response and response.status_code == 200:
            content = response.text

            # Check for PHP errors
            if re.search(r'(fatal error|warning|notice):', content, re.IGNORECASE):
                debug_indicators.append("PHP error messages in HTML")

            # Check for debug mode indicators
            if 'wp_debug' in content.lower():
                debug_indicators.append("WP_DEBUG references in output")

            # Check for SQL queries
            if re.search(r'select.*from.*wp_', content, re.IGNORECASE):
                debug_indicators.append("SQL queries in HTML output")

        # audit debug.log file
        debug_log_url = f"{self.base_url}/wp-content/debug.log"
        response = self._make_request(debug_log_url)
        if response and response.status_code == 200:
            debug_indicators.append("debug.log file is publicly accessible")

        status = "FAIL" if debug_indicators else "PASS"
        details = "; ".join(debug_indicators) if debug_indicators else "No debug information disclosure detected"
        severity = "MEDIUM" if debug_indicators else "INFO"
        self._log_result("Debug Information", status, details, severity)

    def _audit_plugin_enumeration(self):
        """audit for plugin enumeration"""
        common_plugins = [
            "akismet", "jetpack", "woocommerce", "yoast", "wordfence",
            "elementor", "contact-form-7", "wp-super-cache", "all-in-one-seo-pack"
        ]

        detected_plugins = []
        for plugin in common_plugins:
            # Check plugin directory
            plugin_url = f"{self.base_url}/wp-content/plugins/{plugin}/"
            response = self._make_request(plugin_url)
            if response and response.status_code == 200:
                detected_plugins.append(plugin)
                continue

            # Check for plugin files in HTML
            response = self._make_request(self.base_url)
            if response and response.status_code == 200:
                if f"/wp-content/plugins/{plugin}/" in response.text:
                    detected_plugins.append(f"{plugin} (referenced in HTML)")

        status = "FAIL" if detected_plugins else "PASS"
        details = f"Enumerable plugins: {', '.join(detected_plugins)}" if detected_plugins else "Plugin enumeration is restricted"
        severity = "MEDIUM" if detected_plugins else "INFO"
        self._log_result("Plugin Enumeration", status, details, severity)

    def _audit_theme_enumeration(self):
        """audit for theme enumeration"""
        # Check active theme from HTML
        response = self._make_request(self.base_url)
        if not response or response.status_code != 200:
            self._log_result("Theme Enumeration", "ERROR", "Could not retrieve page", "LOW")
            return

        content = response.text
        theme_indicators = []

        # Look for theme references in HTML
        theme_matches = re.findall(r'/wp-content/themes/([^/]+)/', content)
        if theme_matches:
            unique_themes = list(set(theme_matches))
            theme_indicators.append(f"Themes detected in HTML: {', '.join(unique_themes)}")

        # Check theme directory listing
        themes_url = f"{self.base_url}/wp-content/themes/"
        response = self._make_request(themes_url)
        if response and response.status_code == 200:
            if "index of" in response.text.lower():
                theme_indicators.append("Theme directory is browseable")

        status = "FAIL" if theme_indicators else "PASS"
        details = "; ".join(theme_indicators) if theme_indicators else "Theme enumeration is restricted"
        severity = "LOW" if theme_indicators else "INFO"
        self._log_result("Theme Enumeration", status, details, severity)

    def _audit_upload_security(self):
        """audit upload directory security"""
        uploads_url = f"{self.base_url}/wp-content/uploads/"
        response = self._make_request(uploads_url)

        vulnerabilities = []

        if response and response.status_code == 200:
            content = response.text.lower()
            if "index of" in content:
                vulnerabilities.append("Upload directory is browseable")

        # audit for common upload vulnerabilities
        audit_files = ["audit.php", "shell.php", "upload.asp"]
        for audit_file in audit_files:
            url = f"{uploads_url}{audit_file}"
            response = self._make_request(url)
            if response and response.status_code == 200:
                vulnerabilities.append(f"Executable file accessible: {audit_file}")

        status = "FAIL" if vulnerabilities else "PASS"
        details = "; ".join(vulnerabilities) if vulnerabilities else "Upload security appears adequate"
        severity = "HIGH" if vulnerabilities else "INFO"
        self._log_result("Upload Security", status, details, severity)

    def _audit_ssl_configuration(self):
        """audit SSL/TLS configuration"""
        if not self.base_url.startswith("https://"):
            self._log_result("SSL Configuration", "FAIL", "Site not using HTTPS", "HIGH")
            return

        response = self._make_request(self.base_url)
        if not response:
            self._log_result("SSL Configuration", "ERROR", "Could not audit SSL", "LOW")
            return

        ssl_issues = []

        # Check for mixed content
        if response.status_code == 200:
            content = response.text
            http_resources = re.findall(r'http://[^"\s]+', content)
            if http_resources:
                ssl_issues.append(f"Mixed content detected: {len(http_resources)} HTTP resources")

        # Check HSTS header
        if 'Strict-Transport-Security' not in response.headers:
            ssl_issues.append("HSTS header missing")

        status = "FAIL" if ssl_issues else "PASS"
        details = "; ".join(ssl_issues) if ssl_issues else "SSL configuration appears secure"
        severity = "MEDIUM" if ssl_issues else "INFO"
        self._log_result("SSL Configuration", status, details, severity)


# Updated main function to use the new class
def run_security_audits(conn, session: requests.Session, domain: str):
    """Run comprehensive WordPress security audits"""
    auditer = WordPressSecurityauditer(conn, session, domain)
    auditer.run_comprehensive_security_audits()


# Database schema update (run this to update your database)
def update_database_schema(conn):
    """Update database schema to support enhanced security auditing"""
    cursor = conn.cursor()

    # Add new columns if they don't exist
    try:
        cursor.execute("""
            ALTER TABLE hardening_results
            ADD COLUMN severity TEXT DEFAULT 'INFO'
        """)
    except:
        pass  # Column might already exist

    try:
        cursor.execute("""
            ALTER TABLE hardening_results
            ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        """)
    except:
        pass  # Column might already exist

    conn.commit()
