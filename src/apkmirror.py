import re
import json
import logging
import time
from bs4 import BeautifulSoup
from urllib.parse import quote
from curl_cffi import requests as cffi_requests

base_url = "https://www.apkmirror.com"
_blocked_by_cloudflare = False

# Browser fingerprints to rotate through on Cloudflare challenges.
# CF's bot detection is fingerprint-specific — a profile blocked by one TLS
# signature may sail through with another.
_CF_PROFILES = [
    "chrome124",
    "safari17_0",
    "chrome120",
    "firefox117",
    "chrome110",
    "safari15_6_1",
]


class ApkMirrorBlocked(RuntimeError):
    """APKMirror declined this runner before it served an application page."""


def _app_slug_candidates(config: dict) -> list[str]:
    """Return the small set of valid-looking APKMirror app slugs to try.

    On APKMirror the publisher slug and app slug are sometimes identical
    (for example ``/apk/pinterest/pinterest/``), while a human-readable app
    title can be much longer.  Trying the publisher as a final fallback fixes
    those genuine 404s without a site-wide search or browser automation.
    """
    candidates = [
        config.get("app_slug"),
        config.get("name"),
        config.get("org"),
    ]
    return list(dict.fromkeys(slug for slug in candidates if slug))


def _is_cf_challenge(response) -> bool:
    """Return True if the response looks like a Cloudflare bot-challenge page."""
    if response.status_code not in (403, 503):
        return False
    body = response.text[:3000].lower()
    return (
        response.headers.get("cf-mitigated") == "challenge"
        or "cf-ray" in response.headers
        or "just a moment" in body
        or "challenge-platform" in body
        or ("cloudflare" in body and "403" in body)
        or ("cloudflare" in body and "sorry" in body)
    )


def _cf_get(url, **kwargs):
    """Fetch from APKMirror with Cloudflare bypass via rotating curl_cffi impersonation.

    Strategy:
      1. Try each browser fingerprint profile in _CF_PROFILES in order.
      2. On a Cloudflare challenge (403/503 + CF headers/body markers), rotate to
         the next profile after a brief backoff delay.
      3. Only flag the entire source as permanently blocked once every profile has
         been tried and all returned challenges.
      4. Non-Cloudflare 4xx/5xx responses are passed back to the caller as-is.

    This replaces the old fail-fast behaviour that gave up on the first CF challenge.
    """
    global _blocked_by_cloudflare
    if _blocked_by_cloudflare:
        raise ApkMirrorBlocked("APKMirror blocked this runner earlier in the build")

    kwargs.setdefault("timeout", 25)

    for attempt, profile in enumerate(_CF_PROFILES):
        # Increasing polite delay — gives CF's rate-limiting some breathing room
        time.sleep(1.5 + attempt * 0.9)

        try:
            cf_sess = cffi_requests.Session(impersonate=profile)
            response = cf_sess.get(url, **kwargs)
        except Exception as exc:
            logging.debug(f"APKMirror [{profile}]: network error — {exc}")
            continue

        if response.status_code == 200:
            if attempt > 0:
                logging.info(
                    f"APKMirror: Cloudflare bypassed with profile '{profile}' "
                    f"(after {attempt} failed attempt(s))"
                )
            return response

        if _is_cf_challenge(response):
            logging.warning(
                f"APKMirror: CF challenge on profile '{profile}' "
                f"(attempt {attempt + 1}/{len(_CF_PROFILES)}), rotating..."
            )
            continue  # Try next profile

        # Non-challenge response (404, 429, 5xx, etc.) — return immediately
        return response

    # All profiles exhausted
    _blocked_by_cloudflare = True
    logging.error(
        f"APKMirror: Cloudflare defeated all {len(_CF_PROFILES)} impersonation profiles. "
        "APKMirror will be skipped for the rest of this build."
    )
    raise ApkMirrorBlocked("APKMirror Cloudflare challenge — all profiles exhausted")

def get_build_number_for_version(version: str, config: dict) -> tuple[str | None, str]:
    """Fetch build number for a specific version from APKMirror.
    Returns (build_number, format_type) where format_type is 'parentheses' or 'build_suffix'.
    Returns the LOWEST build number found, since patches are typically made for initial builds."""
    try:
        main_url = f"{base_url}/apk/{config['org']}/{config['name']}/"
        response = _cf_get(main_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Collect all build numbers for this version
            builds_found = []
            for link in soup.find_all('a', href=True):
                text = link.get_text()
                if version in text:
                    # Format 1: "32.30.0(1575420)" -> parentheses
                    build_match = re.search(rf'{re.escape(version)}\((\d+)\)', text)
                    if build_match:
                        builds_found.append((build_match.group(1), 'parentheses'))
                    # Format 2: "6.6 build 006" -> build suffix
                    build_match = re.search(rf'{re.escape(version)}\s+build\s+(\d+)', text, re.IGNORECASE)
                    if build_match:
                        builds_found.append((build_match.group(1), 'build_suffix'))
            
            # Return the lowest build number (patches are typically for initial builds)
            if builds_found:
                # Sort by build number (as integer) and return the lowest
                builds_found.sort(key=lambda x: int(x[0]))
                return builds_found[0]
    except Exception as e:
        logging.debug(f"Could not fetch build number: {e}")
    return None, None

def discover_app_main_url(config: dict) -> str | None:
    """Use APKMirror's search endpoint to discover the correct main app page URL when
    the configured 'org/name' combination doesn't match APKMirror's actual URL slugs.
    
    For example, config has org='duolingo', name='duolingo' but the actual page is at
    /apk/duolingo/duolingo-duolingo/. This function searches APKMirror and finds the
    correct main page URL by matching the org and the package name (most reliable).
    
    Returns the full main page URL if found, or None if discovery fails."""
    try:
        org = config.get('org', '')
        name = config.get('name', '')
        package = config.get('package', '')
        
        # Build search query - use package name if available (most precise), else app name
        # Strip ".apk" or trailing dashes from name for cleaner search
        query_terms = []
        if package:
            query_terms.append(package)
        if name:
            query_terms.append(name.replace('-', ' '))
        
        for query in query_terms:
            search_url = f"{base_url}/?post_type=app_release&searchtype=app&s={quote(query)}"
            logging.info(f"Searching APKMirror for app: {search_url}")
            
            try:
                response = _cf_get(search_url)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Find all /apk/{org}/{slug}/ links - these are candidate main app pages
                # We prioritize matches under the same 'org' as the config
                found_links = set()
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Match pattern /apk/{org}/{slug}/ but NOT /apk/{org}/{slug}/{anything-else}
                    m = re.match(r'^(/apk/[a-z0-9._-]+/[a-z0-9._-]+/)$', href)
                    if m:
                        found_links.add(m.group(1))
                
                if not found_links:
                    continue
                
                # Prefer links under the configured org
                org_links = [link for link in found_links if link.startswith(f"/apk/{org}/")]
                
                # Among org-matching links, find the one most likely to be the right app
                # Strategy: pick one whose slug contains the configured name as a substring
                # If multiple, prefer the shorter slug (more "exact" match)
                candidates = org_links if org_links else list(found_links)
                
                # Filter candidates: prefer those containing 'name' in the slug
                name_matches = [link for link in candidates if name and name in link]
                if name_matches:
                    candidates = name_matches
                
                # Sort by slug length (shorter = more specific match)
                candidates.sort(key=lambda x: len(x))
                
                if candidates:
                    discovered = base_url + candidates[0]
                    logging.info(f"Discovered main app page via search: {discovered}")
                    return discovered
            except Exception as e:
                logging.debug(f"Error during search query '{query}': {e}")
                continue
        
        logging.debug("No matching app found via search")
        return None
        
    except Exception as e:
        logging.debug(f"Error in discover_app_main_url: {e}")
        return None

def _scrape_release_url_from_soup(soup, version: str, config: dict, build_number: str = None, build_format: str = None) -> str | None:
    """Scan a BeautifulSoup-parsed main app page for a release link matching the version.
    Returns the full release page URL if found, else None."""
    version_parts = version.split('.')
    valid_slugs = _app_slug_candidates(config)
    
    # Try full version first, then progressively strip parts, but never down to a single digit
    # (e.g. 6.77.5 -> 6.77, but stop at min_parts=2 so we never loosely match single digits like "9")
    min_parts = 2 if len(version_parts) >= 2 else 1
    for i in range(len(version_parts), min_parts - 1, -1):
        current_ver = ".".join(version_parts[:i])
        current_ver_dash = "-".join(version_parts[:i])
        
        # Build search patterns for matching
        search_patterns = [current_ver, current_ver_dash]
        if build_number and i == len(version_parts):
            if build_format == 'build_suffix':
                search_patterns.append(f"{current_ver} build {build_number}")
            else:
                search_patterns.append(f"{current_ver}({build_number})")
        
        # Find candidate release links (those containing the dashed version)
        # APKMirror release URLs look like: /apk/{org}/{app-slug}/{release-slug}-{version}-release/
        candidates = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith('/apk/'):
                continue
            # Ensure the link belongs to this application/org, not unrelated sidebar recommendations
            if not any(f"/{slug}/" in href or href.startswith(f"/apk/{slug}/") for slug in valid_slugs):
                continue

            # Must look like a release page: contain the dashed version
            # Use regex to check the version is properly bounded (not part of a longer number)
            # e.g., for "6-77-5", match -6-77-5- or -6-77-5/
            ver_pattern = re.escape(current_ver_dash)
            if re.search(rf'(?:^|[/-]){ver_pattern}(?:[/-]|$)', href):
                # Prefer URLs ending with -release/
                priority = 0 if href.rstrip('/').endswith('-release') else 1
                candidates.append((priority, href))
        
        if candidates:
            # Sort by priority (release pages first), then by length (shorter = more specific)
            candidates.sort(key=lambda x: (x[0], len(x[1])))
            chosen = candidates[0][1]
            full_url = base_url + chosen
            logging.info(f"Found release page on main listing for {current_ver}: {full_url}")
            return full_url
    
    return None

def find_release_page_from_main(version: str, config: dict, build_number: str = None, build_format: str = None) -> str | None:
    """Scrape the main app listing page on APKMirror to find the correct release page URL
    for a specific version. This avoids URL construction from config fields, which may not
    match APKMirror's actual URL slugs (e.g., 'duolingo' vs 'duolingo-language-lessons').
    
    Strategy:
    1. Try the configured main page (org/name from config)
    2. If that 404s, use APKMirror search to discover the correct main page URL
    3. Scrape release links from whichever main page works
    
    Returns the full release page URL if found, or None if scraping fails."""
    try:
        # Step 1: Try configured main page first (works for most apps)
        main_url = f"{base_url}/apk/{config['org']}/{config['name']}/"
        response = _cf_get(main_url)
        
        soup = None
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            result = _scrape_release_url_from_soup(soup, version, config, build_number, build_format)
            if result:
                return result
            logging.debug(f"Main page accessible but no version match: {main_url}")
        else:
            logging.info(f"Configured main page returned {response.status_code}: {main_url}")
        
        # Step 2: If configured main page failed or didn't yield a match, try discovering
        # the correct main page via APKMirror's search endpoint
        discovered_url = discover_app_main_url(config)
        if discovered_url and discovered_url != main_url:
            logging.info(f"Trying discovered main page: {discovered_url}")
            response = _cf_get(discovered_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                result = _scrape_release_url_from_soup(soup, version, config, build_number, build_format)
                if result:
                    return result
        
        logging.debug(f"Could not find release page URL from main listing for version {version}")
        return None
        
    except Exception as e:
        logging.debug(f"Error scraping main page for release URL: {e}")
        return None

def get_download_link(version: str, app_name: str, config: dict, arch: str = None) -> str:
    if not version:
        logging.error(f"No version provided for {app_name}")
        return None
        
    target_arch = arch if arch else config.get('arch', 'universal')
    
    criteria = [config['type'], target_arch, config['dpi']]
    
    # --- UNIVERSAL URL FINDER WITH VALIDATION ---
    # Extract build number if present (e.g., "32.30.0(1575420)" -> version="32.30.0", build="1575420")
    build_number = None
    build_format = None
    
    # Check for parentheses format: "32.30.0(1575420)"
    build_match = re.search(r'\((\d+)\)$', version)
    if build_match:
        build_number = build_match.group(1)
        build_format = 'parentheses'
        version = version[:build_match.start()]
    else:
        # Check for build suffix format: "6.6 build 002"
        build_match = re.search(r'\s+build\s+(\d+)$', version, re.IGNORECASE)
        if build_match:
            build_number = build_match.group(1)
            build_format = 'build_suffix'
            version = version[:build_match.start()]
        else:
            # Try to fetch build number from APKMirror for this version
            build_number, build_format = get_build_number_for_version(version, config)
            if build_number:
                logging.info(f"Found build number {build_number} for version {version} (format: {build_format})")
    
    version_parts = version.split('.')
    found_soup = None
    correct_version_page = False
    
    # --- PRIMARY APPROACH: Scrape the main app page for the correct release URL ---
    # This is more reliable than constructing URLs from config fields, because
    # APKMirror's actual URL slugs often differ from config values
    # (e.g., 'duolingo' slug vs 'duolingo-language-lessons' actual release name)
    scraped_url = find_release_page_from_main(version, config, build_number, build_format)
    if scraped_url:
        logging.info(f"Trying scraped release URL: {scraped_url}")
        try:
            response = _cf_get(scraped_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                page_text = soup.get_text()
                # Quick validation: check version appears on page
                if version in page_text or version.replace('.', '-') in page_text:
                    logging.info(f"Scraped release page validated: {response.url}")
                    found_soup = soup
                    correct_version_page = True
                else:
                    logging.warning(f"Scraped URL returned page but version {version} not found in content")
        except Exception as e:
            logging.warning(f"Error fetching scraped URL: {e}")

    # Once Cloudflare has challenged this runner, generated URL probes cannot
    # succeed. Stop here so one app does not emit misleading 404s for every
    # possible release slug and the configured fallback can run immediately.
    if _blocked_by_cloudflare:
        return None
    
    # --- FALLBACK: Construct URLs from config fields ---
    # Only used if scraping the main page didn't work
    if not correct_version_page:
        logging.info("Scraping didn't find the page, falling back to URL construction...")
        
        # Use release_prefix if available, otherwise use app name
        release_name = config.get('release_prefix', config['name'])
        app_slugs = _app_slug_candidates(config)
        
        # Loop backwards: Try full version, then strip parts
        for i in range(len(version_parts), 0, -1):
            current_ver_str = "-".join(version_parts[:i])
            
            # If build number exists, append it to the last version part in URL
            if build_number and i == len(version_parts):
                if build_format == 'build_suffix':
                    # e.g., "6-6" + "build-006" -> "6-6-build-006"
                    current_ver_str = current_ver_str + "-build-" + build_number
                else:
                    # e.g., "32-30-0" + "1575420" -> "32-30-01575420"
                    parts = version_parts[:i]
                    parts[-1] = parts[-1] + build_number
                    current_ver_str = "-".join(parts)
            
            # Generate ALL possible URL patterns in priority order
            url_patterns = []
            
            # URL-encode the release_name to handle unicode characters like ․
            encoded_release_name = quote(release_name, safe='')
            org = config.get('org', '')
            encoded_org = quote(org, safe='')

            for app_slug in app_slugs:
                encoded_name = quote(app_slug, safe='')

                # Prefer the explicit release slug; it is more stable than a
                # display name and supports apps whose title changes over time.
                url_patterns.append(f"{base_url}/apk/{org}/{encoded_name}/{encoded_release_name}-{current_ver_str}-release/")

                if release_name != app_slug:
                    url_patterns.append(f"{base_url}/apk/{org}/{encoded_name}/{encoded_name}-{current_ver_str}-release/")

                if org and org != release_name and org != app_slug:
                    url_patterns.append(f"{base_url}/apk/{org}/{encoded_name}/{encoded_org}-{current_ver_str}-release/")

                url_patterns.append(f"{base_url}/apk/{org}/{encoded_name}/{encoded_release_name}-{current_ver_str}/")

                if release_name != app_slug:
                    url_patterns.append(f"{base_url}/apk/{org}/{encoded_name}/{encoded_name}-{current_ver_str}/")

                if org and org != release_name and org != app_slug:
                    url_patterns.append(f"{base_url}/apk/{org}/{encoded_name}/{encoded_org}-{current_ver_str}/")
            
            # Remove duplicate patterns
            url_patterns = list(dict.fromkeys(url_patterns))
            
            for url in url_patterns:
                logging.info(f"Checking potential release URL: {url}")
                
                try:
                    response = _cf_get(url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, "html.parser")
                        page_text = soup.get_text()
                        
                        # VALIDATION: Check if this page is for our EXACT version
                        # Check multiple possible version formats
                        version_checks = [
                            version,  # 6.6
                            version.replace('.', '-'),  # 6-6
                            current_ver_str,  # 6-6-build-002 (if stripped)
                            ".".join(version_parts[:i])  # 6.6 (if stripped)
                        ]
                        
                        # Add build suffix format if we have a build number
                        if build_number:
                            if build_format == 'build_suffix':
                                version_checks.append(f"{version} build {build_number}")  # 6.6 build 002
                                version_checks.append(f"{version.replace('.', '-')}-build-{build_number}")  # 6-6-build-002
                            else:
                                version_checks.append(f"{version}({build_number})")  # 32.30.0(1575420)
                        
                        # Also check page title and headings for version
                        title_tag = soup.find('title')
                        headings = soup.find_all(['h1', 'h2', 'h3'])
                        
                        is_correct_page = False
                        
                        # Check in page text
                        for check in version_checks:
                            if check and check in page_text:
                                # Accept version match if it's the base version or includes build info
                                if check == version or check == version.replace('.', '-') or check == current_ver_str:
                                    is_correct_page = True
                                    break
                        
                        # Check in title and headings
                        if not is_correct_page:
                            for heading in headings:
                                heading_text = heading.get_text()
                                for check in version_checks:
                                    if check and check in heading_text:
                                        is_correct_page = True
                                        break
                                if is_correct_page:
                                    break
                        
                        if not is_correct_page and title_tag:
                            title_text = title_tag.get_text()
                            for check in version_checks:
                                if check and check in title_text:
                                    is_correct_page = True
                                    break
                        
                        if is_correct_page:
                            content_size = len(response.content)
                            logging.info(f"Correct version page found: {response.url}")
                            found_soup = soup
                            correct_version_page = True
                            break  # Found correct page!
                        else:
                            # Page exists but doesn't have our version as primary
                            logging.warning(f"Page found but not for version {version}: {url}")
                            # Save as fallback ONLY if we haven't found any page yet
                            if found_soup is None:
                                found_soup = soup
                                logging.warning(f"Saved as fallback page (may list multiple versions)")
                            continue
                            
                    elif response.status_code == 404:
                        logging.info(f"URL not found (404): {url}")
                        continue
                    else:
                        logging.warning(f"URL {url} returned status {response.status_code}")
                        continue
                        
                except Exception as e:
                    logging.warning(f"Error checking {url}: {str(e)[:50]}")
                    continue
            
            if correct_version_page:
                break  # Found correct page for this version part
    
    # If we didn't find the exact version page but found a fallback
    if not correct_version_page and found_soup:
        logging.warning(f"Using fallback page for {app_name} {version} (may contain multiple versions)")
    
    if not found_soup:
        logging.error(f"Could not find any release page for {app_name} {version}")
        return None
    
    # --- VARIANT FINDER (works with both exact pages and fallback pages) ---
    rows = found_soup.find_all('div', class_='table-row headerFont')
    download_page_url = None
    
    # Try preferred type first (e.g. "APK"), then fallback to "BUNDLE" if APK was requested but not found
    types_to_try = [config['type']]
    if config['type'] == 'APK':
        types_to_try.append('BUNDLE')

    for try_type in types_to_try:
        # Try to find exact version match first
        for row in rows:
            row_text = row.get_text()
            
            # Check if row contains our exact version
            if version in row_text or version.replace('.', '-') in row_text:
                type_match = try_type in row_text
                dpi_match = config['dpi'] in row_text
                if config['dpi'] == 'nodpi' and not dpi_match:
                    dpi_match = 'universal' in row_text or 'noarch' in row_text or 'dpi' in row_text or '-' in row_text
                    
                arch_match = target_arch in row_text
                if try_type == 'BUNDLE' and not arch_match:
                    arch_match = 'universal' in row_text or 'noarch' in row_text or 'arm64-v8a' in row_text
                
                if type_match and dpi_match and arch_match:
                    sub_url = row.find('a', class_='accent_color')
                    if sub_url:
                        download_page_url = base_url + sub_url['href']
                        # Opportunistically cache any versionCode visible in the row
                        try:
                            _vc = _extract_version_code_from_text(row_text, version)
                            if _vc and config.get("package"):
                                register_version_code(config["package"], version, _vc, target_arch)
                        except Exception:
                            pass
                        if try_type != config['type']:
                            logging.info(f"Fallback to {try_type} variant succeeded for {app_name} {version}")
                        break
        
        if download_page_url:
            break

        # If exact version not found, try to find any variant matching criteria
        for row in rows:
            row_text = row.get_text()
            type_match = try_type in row_text
            dpi_match = config['dpi'] in row_text
            if config['dpi'] == 'nodpi' and not dpi_match:
                dpi_match = 'universal' in row_text or 'noarch' in row_text or 'dpi' in row_text or '-' in row_text
                
            arch_match = target_arch in row_text
            if try_type == 'BUNDLE' and not arch_match:
                arch_match = 'universal' in row_text or 'noarch' in row_text or 'arm64-v8a' in row_text
                
            if type_match and dpi_match and arch_match:
                # Check if this looks like a variant row (has version numbers)
                if re.search(r'\d+(\.\d+)+', row_text):
                    sub_url = row.find('a', class_='accent_color')
                    if sub_url:
                        download_page_url = base_url + sub_url['href']
                        # Extract version for logging
                        match = re.search(r'(\d+(\.\d+)+(\.\w+)*)', row_text)
                        if match:
                            actual_version = match.group(1)
                            logging.warning(f"Using variant {actual_version} (criteria match, type={try_type})")
                        break

        if download_page_url:
            break
    
    if not download_page_url:
        logging.error(f"No variant found for {app_name} {version} with criteria {criteria}")
        # Debug: log what rows we found
        logging.debug(f"Found {len(rows)} rows total")
        for idx, row in enumerate(rows[:5]):  # First 5 rows
            logging.debug(f"Row {idx}: {row.get_text()[:100]}...")
        return None
    
    # --- STANDARD DOWNLOAD FLOW ---
    try:
        response = _cf_get(download_page_url)
        response.raise_for_status()
        content_size = len(response.content)
        logging.info(f"URL:{response.url} [{content_size}/{content_size}] -> Variant Page")
        soup = BeautifulSoup(response.content, "html.parser")

        want_bundle = config.get("type") == "BUNDLE"
        final_download_page_url = _pick_download_button(soup, want_bundle)
        if final_download_page_url:
            response = _cf_get(final_download_page_url)
            response.raise_for_status()
            content_size = len(response.content)
            logging.info(f"URL:{response.url} [{content_size}/{content_size}] -> Download Page")
            soup = BeautifulSoup(response.content, "html.parser")

            button = soup.find('a', id='download-link')
            if button:
                return base_url + button['href']
    except Exception as e:
        logging.error(f"Error in download flow: {e}")

    return None

def _pick_download_button(soup, want_bundle: bool) -> str | None:
    """Pick the right download button from an APKMirror variant page.

    Bundle variants expose two buttons: the full .apkm bundle
    (`.../download/?key=...`) and the base APK only
    (`.../download/?key=...&forcebaseapk=true`). Patch fingerprints are
    built against the full bundle, so BUNDLE requests must take the former —
    taking the base APK is exactly what causes mass fingerprint failures.
    """
    buttons = [
        a.get("href", "")
        for a in soup.find_all("a", class_="downloadButton")
        if a.get("href")
    ]
    if not buttons:
        return None
    if want_bundle:
        for href in buttons:
            if "forcebaseapk" not in href:
                return base_url + href
    else:
        for href in buttons:
            if "forcebaseapk" in href:
                return base_url + href
    return base_url + buttons[0]

def get_architecture_criteria(arch: str) -> dict:
    """Map architecture names to APKMirror criteria"""
    arch_mapping = {
        "arm64-v8a": "arm64-v8a",
        "armeabi-v7a": "armeabi-v7a", 
        "universal": "universal"
    }
    return arch_mapping.get(arch, "universal")
    
def get_latest_version(app_name: str, config: dict) -> str:
    # First try: get from main app page
    try:
        main_url = f"{base_url}/apk/{config['org']}/{config['name']}/"
        response = _cf_get(main_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Try to find version in the page
            version_elem = soup.find('span', string=re.compile(r'\d+\.\d+'))
            if version_elem:
                version_text = version_elem.text.strip()
                match = re.search(r'(\d+(\.\d+)+)', version_text)
                if match:
                    return match.group(1)
    except:
        pass  # If fails, continue to original method
    
    # Original method (keep exactly as you had it)
    url = f"{base_url}/uploads/?appcategory={config['name']}"
    
    response = _cf_get(url)
    response.raise_for_status()
    content_size = len(response.content)
    logging.info(f"URL:{response.url} [{content_size}/{content_size}] -> \"-\" [1]")
    soup = BeautifulSoup(response.content, "html.parser")

    app_rows = soup.find_all("div", class_="appRow")
    version_pattern = re.compile(r'\d+(\.\d+)*(-[a-zA-Z0-9]+(\.\d+)*)*')

    for row in app_rows:
        title_h5 = row.find("h5", class_="appRowTitle")
        if not title_h5 or not title_h5.a:
            continue
        version_text = title_h5.a.get_text(strip=True) or ""
        if "alpha" not in version_text.lower() and "beta" not in version_text.lower():
            match = version_pattern.search(version_text)
            if match:
                version = match.group()
                version_parts = version.split('.')
                base_version_parts = []
                for part in version_parts:
                    if part.isdigit():
                        base_version_parts.append(part)
                    else:
                        break
                if base_version_parts:
                    base_version = '.'.join(base_version_parts)
                    
                    # Check for build number in parentheses like "32.30.0(1575420)"
                    build_match = re.search(r'\((\d+)\)', version_text)
                    if build_match:
                        build_number = build_match.group(1)
                        return f"{base_version}({build_number})"
                    
                    return base_version

    return None


def _find_config_by_package(package: str) -> dict | None:
    """Find an APKMirror app config matching a package name.

    Scans apps/apkmirror/*.json for {"package": ...} == package.
    Returns the config dict or None. Never raises.
    """
    try:
        from pathlib import Path as _Path
        import json as _json
        for cfg_path in sorted((_Path("apps") / "apkmirror").glob("*.json")):
            try:
                with cfg_path.open(encoding="utf-8") as f:
                    cfg = _json.load(f)
                if cfg.get("package") == package:
                    return cfg
            except Exception:
                continue
    except Exception:
        pass
    return None


def _extract_version_code_from_text(text: str, version: str) -> int | None:
    """Extract a numeric versionCode near a version string in page text.

    Patterns (most reliable first):
      1. "Version 2.371.0 (29652157)" — parenthetical build next to version
      2. "versionCode: 29652157" / "version_code = 29652157"
      3. Any 7-11 digit number adjacent to the version string
    """
    if not text or not version:
        return None
    esc = re.escape(version)
    # 1. version followed by parenthetical code: "2.371.0 (29652157)"
    m = re.search(rf"{esc}\s*\((\d{{6,11}})\)", text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    # 2. explicit versionCode label
    m = re.search(r"version[_\s]?code\s*[:=]\s*(\d{6,11})", text, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    # 3. bare 7-11 digit number (APKMirror variant rows list the raw
    # versionCode, e.g. "8.2.4147.77 BUNDLE 1 S 541470077 ..."). The lower
    # bound excludes years/days; dotted version parts are excluded by the
    # boundary checks.
    for m in re.finditer(r"(?<![\d.])(\d{7,11})(?![\d.])", text):
        try:
            return int(m.group(1))
        except ValueError:
            continue
    return None


def register_version_code(package: str, version: str, code: int, arch: str = "universal"):
    """Cache a versionCode discovered from APKMirror into utils.cli_version_codes."""
    try:
        from src import utils as _utils
        key = (package, version)
        entry = _utils.cli_version_codes.get(key) or {}
        entry.setdefault((arch or "universal").lower(), int(code))
        _utils.cli_version_codes[key] = entry
    except Exception:
        pass


def get_version_code(package: str, version_name: str) -> int | None:
    """Scrape APKMirror for the versionCode of a specific version.

    No extra HTTP beyond the normal release-page flow: finds the release page
    via find_release_page_from_main(), then regex-scans variant rows and the
    variant page for a parenthetical build number / versionCode label.

    The result is cached into src.utils.cli_version_codes so later lookups
    (including Play Store resolution) are instant. Returns None on any
    failure (including Cloudflare block) — callers must fall through.
    """
    base_version = re.sub(r"\(\d+\)$", "", version_name).strip()
    try:
        from src import utils as _utils
        cached = _utils.get_cli_version_code(package, base_version)
        if cached:
            return cached
    except Exception:
        pass

    try:
        config = _find_config_by_package(package)
        if not config or not config.get("org") or not config.get("name"):
            return None
        release_url = find_release_page_from_main(base_version, config)
        if not release_url:
            return None
        resp = _cf_get(release_url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, "html.parser")
        page_text = soup.get_text(separator=" ")
        code = _extract_version_code_from_text(page_text, base_version)
        if code:
            register_version_code(package, base_version, code)
            register_version_code(package, version_name, code)
            logging.info(f"APKMirror: resolved {package} {version_name} → versionCode {code}")
            return code
        # Fallback: scan individual variant rows for a parenthetical code
        for row in soup.find_all("div", class_="table-row headerFont"):
            row_text = row.get_text(separator=" ")
            if base_version in row_text or base_version.replace(".", "-") in row_text:
                code = _extract_version_code_from_text(row_text, base_version)
                if code:
                    register_version_code(package, base_version, code)
                    register_version_code(package, version_name, code)
                    logging.info(f"APKMirror: resolved {package} {version_name} → versionCode {code} (variant row)")
                    return code
    except ApkMirrorBlocked:
        return None
    except Exception as e:
        logging.debug(f"APKMirror: versionCode scrape failed for {package} {version_name}: {e}")
    return None
