import os
import re
import sys
import ssl
import json
import base64
import hashlib
import socket
import webbrowser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, quote, unquote

import requests
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def banner():
    console.print(
        Panel(
            "[bold red]OSINT MASTER SUITE - EXTENDED RECON & INTELLIGENCE[/bold red]\n"
            "[cyan]Repo: https://github.com/vedansh73/osint-.git | Developer: Vedansh Srivastava[/cyan]",
            border_style="yellow",
        )
    )


def fetch_ip_data(ip_query=""):
    """Reliable multi-source IP lookup with fallback so IP checks don't fail easily."""
    target = ip_query.strip()
    sources = [
        f"http://ip-api.com/json/{target}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query,hosting,proxy",
        f"https://ipapi.co/{target + '/' if target else ''}json/",
        f"https://ipinfo.io/{target + '/' if target else ''}json",
    ]

    for url in sources:
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=6)
            if resp.status_code != 200:
                continue
            data = resp.json()

            if "status" in data:
                if data.get("status") == "success":
                    return {
                        "ip": data.get("query"),
                        "city": data.get("city"),
                        "region": data.get("regionName"),
                        "country": data.get("country"),
                        "postal": data.get("zip"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "timezone": data.get("timezone"),
                        "isp": data.get("isp"),
                        "org": data.get("org"),
                        "asn": data.get("as"),
                        "proxy_hosting": f"Proxy: {data.get('proxy')} | Hosting: {data.get('hosting')}",
                    }
                continue

            if "ip" in data and not data.get("error"):
                return {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "postal": data.get("postal"),
                    "lat": data.get("latitude"),
                    "lon": data.get("longitude"),
                    "timezone": data.get("timezone"),
                    "isp": data.get("org"),
                    "org": data.get("org"),
                    "asn": data.get("asn"),
                    "proxy_hosting": "N/A",
                }

            if "ip" in data and "loc" in data:
                loc_parts = str(data.get("loc", ",")).split(",")
                return {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "postal": data.get("postal"),
                    "lat": loc_parts[0] if len(loc_parts) > 0 else "N/A",
                    "lon": loc_parts[1] if len(loc_parts) > 1 else "N/A",
                    "timezone": data.get("timezone"),
                    "isp": data.get("org"),
                    "org": data.get("org"),
                    "asn": data.get("org"),
                    "proxy_hosting": "N/A",
                }
        except Exception:
            continue
    return None


def get_number_type_label(num):
    t = number_type(num)
    mapping = {
        PhoneNumberType.MOBILE: "Mobile",
        PhoneNumberType.FIXED_LINE: "Fixed Line",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
        PhoneNumberType.TOLL_FREE: "Toll Free",
        PhoneNumberType.PREMIUM_RATE: "Premium Rate",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
        PhoneNumberType.PAGER: "Pager",
        PhoneNumberType.UAN: "UAN",
        PhoneNumberType.VOICEMAIL: "Voicemail",
    }
    return mapping.get(t, "Unknown")


# [1] Deep Phone Number OSINT
def phone_osint_deep():
    console.print("\n[bold yellow][1] Deep Phone Number OSINT Intelligence[/bold yellow]")
    raw = console.input("Enter phone with country code (e.g., +919876543210): ").strip()
    try:
        parsed = phonenumbers.parse(raw, None)
        possible = phonenumbers.is_possible_number(parsed)
        valid = phonenumbers.is_valid_number(parsed)
        region = geocoder.description_for_number(parsed, "en") or "Unknown"
        sim_carrier = carrier.name_for_number(parsed, "en") or "Unknown / Ported"
        tz_list = timezone.time_zones_for_number(parsed)
        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        natl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        ntype = get_number_type_label(parsed)
        digits_only = re.sub(r"\D", "", e164)

        table = Table(title="Phone Intelligence Report", border_style="cyan")
        table.add_column("Field", style="green")
        table.add_column("Details", style="white")
        table.add_row("E.164 Format", e164)
        table.add_row("International", intl)
        table.add_row("National Format", natl)
        table.add_row("Country Code", f"+{parsed.country_code}")
        table.add_row("National Number", str(parsed.national_number))
        table.add_row("Is Possible", str(possible))
        table.add_row("Is Valid", str(valid))
        table.add_row("Line Type", ntype)
        table.add_row("Region / State", region)
        table.add_row("Carrier / Operator", sim_carrier)
        table.add_row("Timezones", ", ".join(tz_list) if tz_list else "Unknown")
        table.add_row("WhatsApp Check", f"https://wa.me/{digits_only}")
        table.add_row("Telegram Search", f"https://t.me/+{digits_only}")
        table.add_row("Google Dork", f'https://www.google.com/search?q="{e164}"+OR+"{intl}"')
        console.print(table)
    except Exception as e:
        console.print(f"[red][-] Phone analysis error: {e}[/red]")


# [2] Wide Username OSINT (25+ Platforms)
def username_osint_wide():
    console.print("\n[bold yellow][2] Wide Social & Developer Username OSINT[/bold yellow]")
    username = console.input("Enter target username: ").strip()
    if not username:
        console.print("[red][-] Username cannot be empty.[/red]")
        return

    platforms = {
        "GitHub": f"https://github.com/{username}",
        "GitLab": f"https://gitlab.com/{username}",
        "Bitbucket": f"https://bitbucket.org/{username}/",
        "Reddit": f"https://www.reddit.com/user/{username}/",
        "Instagram": f"https://www.instagram.com/{username}/",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Medium": f"https://medium.com/@{username}",
        "Dev.to": f"https://dev.to/{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Twitch": f"https://www.twitch.tv/{username}",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "SoundCloud": f"https://soundcloud.com/{username}",
        "Spotify": f"https://open.spotify.com/user/{username}",
        "Keybase": f"https://keybase.io/{username}",
        "DockerHub": f"https://hub.docker.com/u/{username}",
        "HackerNews": f"https://news.ycombinator.com/user?id={username}",
        "ProductHunt": f"https://www.producthunt.com/@{username}",
        "About.me": f"https://about.me/{username}",
        "Replit": f"https://replit.com/@{username}",
        "Kaggle": f"https://www.kaggle.com/{username}",
        "CodePen": f"https://codepen.io/{username}",
        "TryHackMe": f"https://tryhackme.com/p/{username}",
        "Patreon": f"https://www.patreon.com/{username}",
        "Slideshare": f"https://www.slideshare.net/{username}",
        "Vimeo": f"https://vimeo.com/{username}",
    }

    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    console.print(f"[cyan][*] Scanning {len(platforms)} platforms for '{username}'...[/cyan]\n")

    found_count = 0
    for site, url in platforms.items():
        try:
            resp = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
            final_url = resp.url.lower()
            body_low = resp.text.lower()

            false_positive = (
                resp.status_code != 200
                or "page not found" in body_low
                or "user not found" in body_low
                or "doesn't exist" in body_low
                or "sorry, nobody on reddit goes by that name" in body_low
                or (site == "Instagram" and ("login" in final_url or "accounts/login" in final_url))
            )

            if not false_positive:
                found_count += 1
                console.print(f"    [bold green][+] {site:<14}:[/bold green] {url}")
            else:
                console.print(f"    [dim red][-] {site:<14}: Not Found / Private / Auth Wall[/dim red]")
        except Exception:
            console.print(f"    [yellow][!] {site:<14}: Timeout / Blocked[/yellow]")

    console.print(f"\n[bold cyan][*] Summary: {found_count}/{len(platforms)} potential public matches found.[/bold cyan]")


# [3] IP Geolocation & Network Intelligence
def ip_intelligence():
    console.print("\n[bold yellow][3] IP Address Geolocation & Network Intelligence[/bold yellow]")
    ip = console.input("Enter public IP address (leave blank for your own public IP): ").strip()
    info = fetch_ip_data(ip)
    if not info:
        console.print("[red][-] Could not retrieve IP details from providers. Check internet/IP.[/red]")
        return

    table = Table(title="IP Intelligence Report", border_style="green")
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="white")
    for k, v in info.items():
        table.add_row(str(k).upper(), str(v if v not in (None, "") else "N/A"))
    if info.get("lat") and info.get("lon") and info.get("lat") != "N/A":
        table.add_row("GOOGLE MAPS", f"https://www.google.com/maps?q={info['lat']},{info['lon']}")
    console.print(table)


# [4] Email OSINT & Mail Server Check
def email_osint():
    console.print("\n[bold yellow][4] Email Address & Domain Intelligence[/bold yellow]")
    email = console.input("Enter email address: ").strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        console.print("[red][-] Invalid email format.[/red]")
        return
    user_part, domain = email.split("@", 1)
    console.print(f"[green][+] Local Part   :[/green] {user_part}")
    console.print(f"[green][+] Domain       :[/green] {domain}")
    console.print(f"[green][+] MD5 Hash     :[/green] {hashlib.md5(email.lower().encode()).hexdigest()}")
    console.print(f"[green][+] SHA256 Hash  :[/green] {hashlib.sha256(email.lower().encode()).hexdigest()}")
    try:
        ip = socket.gethostbyname(domain)
        console.print(f"[green][+] Domain A IP  :[/green] {ip}")
    except Exception:
        console.print("[yellow][!] Could not resolve A record.[/yellow]")
    console.print(f"[green][+] Google Dork  :[/green] https://www.google.com/search?q={quote('\"' + email + '\"')}")


# [5] DNS Records Lookup (A, AAAA)
def dns_lookup():
    console.print("\n[bold yellow][5] DNS & IPv6 Resolution Lookup[/bold yellow]")
    domain = console.input("Enter domain (e.g., example.com): ").strip()
    domain = urlparse(domain).netloc if "://" in domain else domain.split("/")[0]
    try:
        ipv4 = socket.gethostbyname(domain)
        console.print(f"[green][+] IPv4 (A)     :[/green] {ipv4}")
    except Exception as e:
        console.print(f"[red][-] IPv4 error   :[/red] {e}")
    try:
        addr_info = socket.getaddrinfo(domain, None, socket.AF_INET6)
        ipv6s = sorted({item[4][0] for item in addr_info})
        console.print(f"[green][+] IPv6 (AAAA)  :[/green] {', '.join(ipv6s) if ipv6s else 'None'}")
    except Exception:
        console.print("[yellow][!] IPv6 (AAAA)  : None / Not resolved[/yellow]")


# [6] Reverse DNS (PTR) Lookup
def reverse_dns():
    console.print("\n[bold yellow][6] Reverse DNS (PTR) Lookup[/bold yellow]")
    ip = console.input("Enter IP address: ").strip()
    try:
        host, aliases, _ = socket.gethostbyaddr(ip)
        console.print(f"[green][+] Hostname     :[/green] {host}")
        console.print(f"[green][+] Aliases      :[/green] {', '.join(aliases) if aliases else 'None'}")
    except Exception as e:
        console.print(f"[red][-] Reverse DNS failed: {e}[/red]")


# [7] HTTP Headers & Security Audit
def http_headers_audit():
    console.print("\n[bold yellow][7] HTTP Response & Security Headers Audit[/bold yellow]")
    target = console.input("Enter URL or domain: ").strip()
    url = target if target.startswith(("http://", "https://")) else f"https://{target}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8)
        console.print(f"[green][+] Final URL    :[/green] {resp.url}")
        console.print(f"[green][+] Status Code  :[/green] {resp.status_code}")
        for h in [
            "Server",
            "X-Frame-Options",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "Referrer-Policy",
        ]:
            val = resp.headers.get(h, "MISSING")
            color = "green" if val != "MISSING" else "red"
            console.print(f"    [{color}]• {h:<28}: {val}[/{color}]")
    except Exception as e:
        console.print(f"[red][-] Request failed: {e}[/red]")


# [8] WAF & CDN Detector
def waf_detector():
    console.print("\n[bold yellow][8] WAF / CDN Detection[/bold yellow]")
    target = console.input("Enter domain or URL: ").strip()
    url = target if target.startswith(("http://", "https://")) else f"https://{target}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8)
        hdrs_str = str(resp.headers).lower()
        server = resp.headers.get("Server", "").lower()
        detected = []
        signatures = {
            "Cloudflare": ["cloudflare", "cf-ray"],
            "AWS CloudFront": ["cloudfront", "x-amz-cf-id"],
            "Akamai": ["akamai", "akamai-ghost"],
            "Fastly": ["fastly", "x-fastly-request-id"],
            "Sucuri": ["sucuri", "x-sucuri-id"],
            "Imperva / Incapsula": ["incapsula", "imperva"],
        }
        for waf_name, markers in signatures.items():
            if any(m in hdrs_str or m in server for m in markers):
                detected.append(waf_name)
        if detected:
            console.print(f"[bold green][+] Detected WAF/CDN:[/bold green] {', '.join(detected)}")
        else:
            console.print(f"[yellow][!] No major WAF signature detected (Server: {resp.headers.get('Server', 'Unknown')})[/yellow]")
    except Exception as e:
        console.print(f"[red][-] WAF check failed: {e}[/red]")


# [9] Common TCP Port Scanner
def common_port_scanner():
    console.print("\n[bold yellow][9] Common TCP Port Scanner[/bold yellow]")
    target = console.input("Enter domain or IP: ").strip()
    host = urlparse(target).netloc if "://" in target else target.split("/")[0]
    try:
        ip = socket.gethostbyname(host)
    except Exception as e:
        console.print(f"[red][-] Host resolution failed: {e}[/red]")
        return

    ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8000, 8080, 8443]
    console.print(f"[cyan][*] Scanning {len(ports)} ports on {ip}...[/cyan]")
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.8)
        if s.connect_ex((ip, p)) == 0:
            console.print(f"    [bold green][+] Port {p:<5} OPEN[/bold green]")
        s.close()


# [10] Subdomain Quick Bruteforce
def subdomain_scanner():
    console.print("\n[bold yellow][10] Quick Subdomain Enumeration[/bold yellow]")
    domain = console.input("Enter root domain (e.g., example.com): ").strip()
    domain = urlparse(domain).netloc if "://" in domain else domain.split("/")[0]
    words = [
        "www", "mail", "ftp", "api", "dev", "staging", "test", "admin",
        "portal", "blog", "shop", "cdn", "ns1", "ns2", "vpn", "m", "docs"
    ]
    console.print(f"[cyan][*] Checking {len(words)} common subdomains for {domain}...[/cyan]")
    for sub in words:
        fqdn = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(fqdn)
            console.print(f"    [bold green][+] {fqdn:<28} -> {ip}[/bold green]")
        except Exception:
            pass


# [11] YouTube Channel OSINT (Extended Username / Handle Details)
def youtube_osint():
    console.print("\n[bold yellow][11] YouTube Channel Extended OSINT[/bold yellow]")
    yt_in = console.input("Enter YouTube username or @handle: ").strip()
    if not yt_in:
        console.print("[red][-] Input cannot be empty.[/red]")
        return

    clean_handle = yt_in.lstrip("@").strip()
    url = f"https://www.youtube.com/@{clean_handle}" if not yt_in.startswith("http") else yt_in.rstrip("/")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        console.print(f"[cyan][*] Fetching public channel intelligence for @{clean_handle}...[/cyan]")
        resp = requests.get(url, headers=headers, timeout=10)
        html = resp.text

        title_match = re.search(r"<title>(.*?)</title>", html)
        raw_title = title_match.group(1).strip() if title_match else "Unknown"
        channel_name = raw_title.replace(" - YouTube", "").strip()

        desc_match = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html)
        description = desc_match.group(1).strip() if desc_match else "Not found / Hidden"

        kw_match = re.search(r'<meta\s+name="keywords"\s+content="(.*?)"', html)
        keywords = kw_match.group(1).strip() if kw_match else "Not found"

        id_patterns = [
            r'"channelId"\s*:\s*"(UC[\w-]+)"',
            r'"externalId"\s*:\s*"(UC[\w-]+)"',
            r'"browseId"\s*:\s*"(UC[\w-]+)"',
            r'itemprop="channelId"\s+content="(UC[\w-]+)"',
            r'https://www\.youtube\.com/channel/(UC[\w-]+)',
        ]
        channel_id = None
        for pat in id_patterns:
            m = re.search(pat, html)
            if m:
                channel_id = m.group(1)
                break

        table = Table(title=f"YouTube OSINT: @{clean_handle}", border_style="red")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Channel Name", channel_name)
        table.add_row("Handle", f"@{clean_handle}")
        table.add_row("Channel URL", url)
        table.add_row("Channel ID", channel_id or "Not found in static HTML")
        table.add_row("Description", description[:180] + ("..." if len(description) > 180 else ""))
        table.add_row("Keywords", keywords[:140] + ("..." if len(keywords) > 140 else ""))

        if channel_id:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            table.add_row("Direct Channel URL", f"https://www.youtube.com/channel/{channel_id}")
            table.add_row("RSS Feed URL", rss_url)

        table.add_row("Videos / Shorts / Live", f"{url}/videos | {url}/shorts | {url}/streams")
        table.add_row("Channels / About", f"{url}/channels | {url}/about")
        table.add_row("Google Mentions Dork", f'https://www.google.com/search?q={quote(f"@{clean_handle} site:youtube.com")}')
        console.print(table)

        if channel_id:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            try:
                rss_resp = requests.get(rss_url, headers=headers, timeout=8)
                if rss_resp.status_code == 200 and "<feed" in rss_resp.text:
                    root = ET.fromstring(rss_resp.text)
                    ns = {
                        "atom": "http://www.w3.org/2005/Atom",
                        "yt": "http://www.youtube.com/xml/schemas/yt/2015",
                    }
                    entries = root.findall("atom:entry", ns)[:5]
                    if entries:
                        console.print("\n[bold green][+] Recent Public Uploads (via RSS):[/bold green]")
                        for idx, entry in enumerate(entries, 1):
                            v_title = entry.findtext("atom:title", default="Untitled", namespaces=ns)
                            v_id = entry.findtext("yt:videoId", default="", namespaces=ns)
                            pub_date = entry.findtext("atom:published", default="", namespaces=ns)[:10]
                            v_link = f"https://www.youtube.com/watch?v={v_id}" if v_id else "N/A"
                            console.print(f"    {idx}. [{pub_date}] {v_title} -> {v_link}")
                    else:
                        console.print("[yellow][!] RSS feed has no public video entries.[/yellow]")
            except Exception as rss_err:
                console.print(f"[yellow][!] RSS parse note: {rss_err}[/yellow]")

    except Exception as e:
        console.print(f"[red][-] YouTube OSINT error: {e}[/red]")


# [12] GitHub User OSINT
def github_osint():
    console.print("\n[bold yellow][12] GitHub Profile & Repo OSINT[/bold yellow]")
    user = console.input("Enter GitHub username: ").strip()
    try:
        r = requests.get(f"https://api.github.com/users/{user}", headers={"User-Agent": USER_AGENT}, timeout=8)
        if r.status_code != 200:
            console.print("[red][-] GitHub user not found or API limit hit.[/red]")
            return
        d = r.json()
        console.print(f"[green][+] Name         :[/green] {d.get('name')}")
        console.print(f"[green][+] Bio          :[/green] {d.get('bio')}")
        console.print(f"[green][+] Company      :[/green] {d.get('company')}")
        console.print(f"[green][+] Location     :[/green] {d.get('location')}")
        console.print(f"[green][+] Blog/URL     :[/green] {d.get('blog')}")
        console.print(f"[green][+] Public Repos :[/green] {d.get('public_repos')}")
        console.print(f"[green][+] Followers    :[/green] {d.get('followers')} | Following: {d.get('following')}")
    except Exception as e:
        console.print(f"[red][-] Error: {e}[/red]")


# [13] Reddit User OSINT
def reddit_osint():
    console.print("\n[bold yellow][13] Reddit Account OSINT[/bold yellow]")
    user = console.input("Enter Reddit username: ").strip()
    try:
        r = requests.get(f"https://www.reddit.com/user/{user}/about.json", headers={"User-Agent": USER_AGENT}, timeout=8)
        if r.status_code != 200:
            console.print("[red][-] Reddit profile not accessible/found.[/red]")
            return
        d = r.json().get("data", {})
        console.print(f"[green][+] Name         :[/green] {d.get('name')}")
        console.print(f"[green][+] Link Karma   :[/green] {d.get('link_karma')}")
        console.print(f"[green][+] Comment Karma:[/green] {d.get('comment_karma')}")
        console.print(f"[green][+] Verified Mail:[/green] {d.get('has_verified_email')}")
    except Exception as e:
        console.print(f"[red][-] Error: {e}[/red]")


# [14] Google Dork Generator
def google_dork_generator():
    console.print("\n[bold yellow][14] OSINT Google Dork Query Builder[/bold yellow]")
    target = console.input("Enter target keyword, domain, or name: ").strip()
    dorks = [
        f"site:{target}",
        f'intext:"{target}"',
        f'"{target}" filetype:pdf OR filetype:xls OR filetype:docx',
        f'"{target}" inurl:admin OR inurl:login',
        f'"{target}" site:github.com OR site:pastebin.com',
    ]
    for idx, q in enumerate(dorks, 1):
        console.print(f"    [cyan]{idx}.[/cyan] {q}")
        console.print(f"       https://www.google.com/search?q={quote(q)}")


# [15] Domain Tech / CMS Hint Checker
def tech_fingerprint():
    console.print("\n[bold yellow][15] Web Tech & CMS Fingerprinting[/bold yellow]")
    target = console.input("Enter URL or domain: ").strip()
    url = target if target.startswith(("http://", "https://")) else f"https://{target}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8)
        html = resp.text.lower()
        hdrs = str(resp.headers).lower()
        techs = []
        checks = {
            "WordPress": ["wp-content", "wp-includes"],
            "Shopify": ["cdn.shopify.com", "myshopify.com"],
            "React / Next.js": ["__next_data__", "react-dom"],
            "Bootstrap": ["bootstrap.min.css"],
            "Tailwind": ["tailwind"],
            "PHP": ["phpsessid", "x-powered-by': 'php"],
        }
        for name, signs in checks.items():
            if any(s in html or s in hdrs for s in signs):
                techs.append(name)
        console.print(f"[green][+] Detected Tech:[/green] {', '.join(techs) if techs else 'Basic / Custom Stack'}")
    except Exception as e:
        console.print(f"[red][-] Fingerprint error: {e}[/red]")


# [16] Robots.txt & Sitemap Checker
def robots_sitemap_check():
    console.print("\n[bold yellow][16] robots.txt & sitemap.xml Inspector[/bold yellow]")
    domain = console.input("Enter domain (e.g., example.com): ").strip()
    domain = urlparse(domain).netloc if "://" in domain else domain.split("/")[0]
    for path in ["/robots.txt", "/sitemap.xml"]:
        u = f"https://{domain}{path}"
        try:
            r = requests.get(u, headers={"User-Agent": USER_AGENT}, timeout=6)
            console.print(f"[green][+] {u} -> HTTP {r.status_code} ({len(r.text)} bytes)[/green]")
            if r.status_code == 200 and path == "/robots.txt":
                lines = r.text.splitlines()[:12]
                for ln in lines:
                    console.print(f"    [dim]{ln}[/dim]")
        except Exception:
            console.print(f"[yellow][!] {u} -> Unreachable[/yellow]")


# [17] HTTP Redirect Chain Tracer
def redirect_tracer():
    console.print("\n[bold yellow][17] HTTP Redirect Chain Tracer[/bold yellow]")
    target = console.input("Enter starting URL: ").strip()
    url = target if target.startswith(("http://", "https://")) else f"http://{target}"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8, allow_redirects=True)
        for i, hop in enumerate(r.history, 1):
            console.print(f"    [cyan]Hop {i}:[/cyan] {hop.status_code} -> {hop.url}")
        console.print(f"    [bold green]Final:[/bold green] {r.status_code} -> {r.url}")
    except Exception as e:
        console.print(f"[red][-] Redirect trace failed: {e}[/red]")


# [18] Hash Generator (MD5, SHA1, SHA256, SHA512)
def hash_generator():
    console.print("\n[bold yellow][18] Cryptographic Hash Generator[/bold yellow]")
    text = console.input("Enter text to hash: ")
    b = text.encode("utf-8")
    console.print(f"[green][+] MD5    :[/green] {hashlib.md5(b).hexdigest()}")
    console.print(f"[green][+] SHA1   :[/green] {hashlib.sha1(b).hexdigest()}")
    console.print(f"[green][+] SHA256 :[/green] {hashlib.sha256(b).hexdigest()}")
    console.print(f"[green][+] SHA512 :[/green] {hashlib.sha512(b).hexdigest()}")


# [19] Base64 Encode / Decode
def base64_tool():
    console.print("\n[bold yellow][19] Base64 Encoder / Decoder[/bold yellow]")
    mode = console.input("Choose (e)ncode or (d)ecode: ").strip().lower()
    data = console.input("Enter string: ").strip()
    try:
        if mode.startswith("e"):
            out = base64.b64encode(data.encode("utf-8")).decode("utf-8")
            console.print(f"[green][+] Encoded:[/green] {out}")
        else:
            out = base64.b64decode(data.encode("utf-8")).decode("utf-8")
            console.print(f"[green][+] Decoded:[/green] {out}")
    except Exception as e:
        console.print(f"[red][-] Base64 error: {e}[/red]")


# [20] URL Encode / Decode
def url_codec():
    console.print("\n[bold yellow][20] URL Encoder / Decoder[/bold yellow]")
    mode = console.input("Choose (e)ncode or (d)ecode: ").strip().lower()
    data = console.input("Enter text/URL: ").strip()
    if mode.startswith("e"):
        console.print(f"[green][+] Encoded:[/green] {quote(data)}")
    else:
        console.print(f"[green][+] Decoded:[/green] {unquote(data)}")


# [21] Local System & Network Info
def local_system_info():
    console.print("\n[bold yellow][21] Local Host & Network Info[/bold yellow]")
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "N/A"
    console.print(f"[green][+] Hostname :[/green] {hostname}")
    console.print(f"[green][+] Local IP :[/green] {local_ip}")
    console.print(f"[green][+] CWD      :[/green] {os.getcwd()}")


# [22] JSON Pretty Formatter
def json_formatter():
    console.print("\n[bold yellow][22] JSON Validator & Pretty Printer[/bold yellow]")
    raw = console.input("Paste raw JSON string: ").strip()
    try:
        parsed = json.loads(raw)
        console.print(json.dumps(parsed, indent=2))
    except Exception as e:
        console.print(f"[red][-] Invalid JSON: {e}[/red]")


# [23] Extract Emails & Links from Webpage
def webpage_link_email_extractor():
    console.print("\n[bold yellow][23] Webpage Links & Emails Scraper[/bold yellow]")
    target = console.input("Enter webpage URL: ").strip()
    url = target if target.startswith(("http://", "https://")) else f"https://{target}"
    try:
        html = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8).text
        emails = sorted(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)))
        links = sorted(set(re.findall(r'https?://[^\s"\'<>]+', html)))[:15]
        console.print(f"[green][+] Emails found ({len(emails)}):[/green] {', '.join(emails[:10]) if emails else 'None'}")
        console.print(f"[green][+] Sample Links ({len(links)}):[/green]")
        for lk in links:
            console.print(f"    • {lk}")
    except Exception as e:
        console.print(f"[red][-] Extraction failed: {e}[/red]")


# [24] Browser Permission Awareness Demo
def permission_awareness_demo():
    console.print("\n[bold yellow][24] Browser Permission Awareness Demo[/bold yellow]")
    html_content = """<!DOCTYPE html>
<html>
<head><title>OSINT Suite Permission Demo</title></head>
<body style="background:#0f172a;color:#38bdf8;font-family:sans-serif;padding:40px;">
  <h2>Browser Permission Prompt Demo</h2>
  <p>Tests standard browser prompts (Geolocation, Microphone, File input).</p>
  <button onclick="navigator.geolocation.getCurrentPosition(p=>alert('Lat:'+p.coords.latitude+' Lng:'+p.coords.longitude),e=>alert(e.message))">Test Geolocation</button>
  <button onclick="navigator.mediaDevices.getUserMedia({audio:true}).then(s=>{alert('Mic granted');s.getTracks().forEach(t=>t.stop())}).catch(e=>alert(e.message))">Test Microphone</button>
  <input type="file" onchange="alert('Selected: '+this.files[0]?.name)">
</body>
</html>"""
    fname = "permission_demo.html"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(html_content)
    console.print(f"[green][+] Created {fname} and opening browser...[/green]")
    webbrowser.open("file://" + os.path.abspath(fname))


# [25] Save Scan Note / Log
def save_note():
    console.print("\n[bold yellow][25] Save OSINT Investigation Note[/bold yellow]")
    note = console.input("Enter note or finding to save: ").strip()
    if note:
        with open("osint_notes.txt", "a", encoding="utf-8") as f:
            f.write(note + "\n")
        console.print("[green][+] Saved to osint_notes.txt[/green]")


# [26] Open Official ELVORIX Web Portal
def open_elvorix():
    console.print("\n[bold yellow][26] Opening ELVORIX Portal...[/bold yellow]")
    webbrowser.open("https://vedansh73.github.io/ELVORIX/")


# [27] Open Creator YouTube Channel
def open_youtube():
    console.print("\n[bold yellow][27] Opening YouTube Channel...[/bold yellow]")
    webbrowser.open("https://www.youtube.com/@vedanshsrivastava182")


# [28] Join Discord Community
def open_discord():
    console.print("\n[bold yellow][28] Opening Discord Server...[/bold yellow]")
    webbrowser.open("https://discord.com/invite/PUgqMfdWwB")


# [29] Join Telegram Security Channel
def open_telegram():
    console.print("\n[bold yellow][29] Opening Telegram Channel...[/bold yellow]")
    webbrowser.open("https://t.me/vedasecurity182")


# [30] Open GitHub Repository
def open_repo():
    console.print("\n[bold yellow][30] Opening GitHub Repo...[/bold yellow]")
    webbrowser.open("https://github.com/vedansh73/osint-.git")


# [31] Fast Multi-Threaded Username OSINT
def fast_username_osint():
    console.print("\n[bold yellow][31] Fast Multi-Threaded Username OSINT[/bold yellow]")
    username = console.input("Enter target username: ").strip()
    if not username:
        console.print("[red][-] Username cannot be empty.[/red]")
        return

    sites = {
        "GitHub": f"https://github.com/{username}",
        "GitLab": f"https://gitlab.com/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}/",
        "Instagram": f"https://www.instagram.com/{username}/",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Medium": f"https://medium.com/@{username}",
        "Dev.to": f"https://dev.to/{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Twitch": f"https://www.twitch.tv/{username}",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "SoundCloud": f"https://soundcloud.com/{username}",
        "Spotify": f"https://open.spotify.com/user/{username}",
        "Keybase": f"https://keybase.io/{username}",
        "DockerHub": f"https://hub.docker.com/u/{username}",
        "HackerNews": f"https://news.ycombinator.com/user?id={username}",
        "Replit": f"https://replit.com/@{username}",
        "Kaggle": f"https://www.kaggle.com/{username}",
        "CodePen": f"https://codepen.io/{username}",
        "TryHackMe": f"https://tryhackme.com/p/{username}",
        "Patreon": f"https://www.patreon.com/{username}",
        "Vimeo": f"https://vimeo.com/{username}",
        "Linktree": f"https://linktr.ee/{username}",
        "Chess.com": f"https://www.chess.com/member/{username}",
        "Scratch": f"https://scratch.mit.edu/users/{username}/",
    }

    def check_site(name, url):
        try:
            r = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
                timeout=6,
                allow_redirects=True,
            )
            low = r.text.lower()
            not_found = (
                r.status_code != 200
                or "page not found" in low
                or "user not found" in low
                or "doesn't exist" in low
                or "sorry, nobody on reddit goes by that name" in low
                or (name == "Instagram" and "accounts/login" in r.url.lower())
            )
            return name, url, (not not_found)
        except Exception:
            return name, url, False

    console.print(f"[cyan][*] Fast-scanning {len(sites)} platforms for '{username}'...[/cyan]\n")
    found = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(check_site, n, u) for n, u in sites.items()]
        for fut in as_completed(futures):
            name, url, ok = fut.result()
            if ok:
                found.append((name, url))
                console.print(f"    [bold green][+] {name:<14}:[/bold green] {url}")

    console.print(f"\n[bold cyan][*] Done! Found {len(found)}/{len(sites)} public matches.[/bold cyan]")


# [32] SSL Certificate Inspector + crt.sh Subdomains
def ssl_and_crtsh_recon():
    console.print("\n[bold yellow][32] SSL Certificate & crt.sh Subdomain Recon[/bold yellow]")
    domain = console.input("Enter domain (e.g., example.com): ").strip()
    domain = urlparse(domain).netloc if "://" in domain else domain.split("/")[0]
    if not domain:
        console.print("[red][-] Domain cannot be empty.[/red]")
        return

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=6) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get("issuer", []))
                subject = dict(x[0] for x in cert.get("subject", []))
                console.print(f"[green][+] Cert Common Name :[/green] {subject.get('commonName', 'N/A')}")
                console.print(f"[green][+] Cert Issuer      :[/green] {issuer.get('organizationName', 'N/A')}")
                console.print(f"[green][+] Valid From       :[/green] {cert.get('notBefore', 'N/A')}")
                console.print(f"[green][+] Valid Until      :[/green] {cert.get('notAfter', 'N/A')}")
    except Exception as e:
        console.print(f"[yellow][!] SSL check note: {e}[/yellow]")

    try:
        r = requests.get(
            f"https://crt.sh/?q=%25.{quote(domain)}&output=json",
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        if r.status_code == 200:
            subs = set()
            for item in r.json():
                for line in str(item.get("name_value", "")).splitlines():
                    clean = line.strip().lstrip("*.")
                    if clean.endswith(domain):
                        subs.add(clean)
            sorted_subs = sorted(subs)[:20]
            console.print(f"[green][+] crt.sh Subdomains ({len(subs)} total, showing top {len(sorted_subs)}):[/green]")
            for s in sorted_subs:
                console.print(f"    • {s}")
    except Exception as e:
        console.print(f"[yellow][!] crt.sh lookup note: {e}[/yellow]")


# [33] Local Image File Metadata & Hash
def image_file_forensics():
    console.print("\n[bold yellow][33] Local Image File Metadata & Hash[/bold yellow]")
    img_path = console.input("Enter local image path (e.g., photo.jpg): ").strip().strip('"')
    if not os.path.isfile(img_path):
        console.print("[red][-] File not found.[/red]")
        return

    with open(img_path, "rb") as f:
        raw_bytes = f.read()

    console.print(f"[green][+] File Size :[/green] {len(raw_bytes)} bytes")
    console.print(f"[green][+] MD5       :[/green] {hashlib.md5(raw_bytes).hexdigest()}")
    console.print(f"[green][+] SHA256    :[/green] {hashlib.sha256(raw_bytes).hexdigest()}")

    try:
        from PIL import Image, ExifTags
        img = Image.open(img_path)
        console.print(f"[green][+] Format    :[/green] {img.format} | Size: {img.size} | Mode: {img.mode}")
        exif = img.getexif()
        if exif:
            for tag_id, val in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                console.print(f"    • {tag_name}: {val}")
        else:
            console.print("[yellow][!] No EXIF tags found in image.[/yellow]")
    except ImportError:
        console.print("[yellow][!] Tip: Install Pillow ('pip install Pillow') to read EXIF tags.[/yellow]")
    except Exception as e:
        console.print(f"[yellow][!] Image inspect note: {e}[/yellow]")


# [34] Deep WhatsApp Public Link & Dork Helper
def deep_whatsapp_osint():
    console.print("\n[bold yellow][34] Deep WhatsApp Public Link & Dork Helper[/bold yellow]")
    raw = console.input("Enter phone with country code (e.g., +919876543210): ").strip()
    try:
        parsed = phonenumbers.parse(raw, None)
        valid = phonenumbers.is_valid_number(parsed)
        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        digits = re.sub(r"\D", "", e164)
        region = geocoder.description_for_number(parsed, "en") or "Unknown"
        sim_carrier = carrier.name_for_number(parsed, "en") or "Unknown"

        wa_me = f"https://wa.me/{digits}"
        wa_api = f"https://api.whatsapp.com/send?phone={digits}"
        dork_wa_me = f"https://www.google.com/search?q={quote(f'site:wa.me/{digits}')}"
        dork_num = f"https://www.google.com/search?q={quote(f'\"{e164}\" OR \"{intl}\" OR \"{digits}\" whatsapp')}"

        table = Table(title="WhatsApp Public OSINT Helper", border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("E.164 Number", e164)
        table.add_row("Valid Format", str(valid))
        table.add_row("Region / Carrier", f"{region} | {sim_carrier}")
        table.add_row("wa.me Link", wa_me)
        table.add_row("API Send Link", wa_api)
        table.add_row("wa.me Google Dork", dork_wa_me)
        table.add_row("Public Mentions Dork", dork_num)
        console.print(table)
        console.print("[dim]Note: Private WhatsApp chats, contacts, and hidden profile details cannot be accessed via OSINT.[/dim]")
    except Exception as e:
        console.print(f"[red][-] WhatsApp helper error: {e}[/red]")


MENU_ACTIONS = {
    "1": ("Deep Phone Number OSINT", phone_osint_deep),
    "2": ("Wide Username OSINT (25+ Sites)", username_osint_wide),
    "3": ("IP Geolocation & Network Info", ip_intelligence),
    "4": ("Email & Domain OSINT", email_osint),
    "5": ("DNS & IPv6 Lookup", dns_lookup),
    "6": ("Reverse DNS (PTR) Lookup", reverse_dns),
    "7": ("HTTP & Security Headers Audit", http_headers_audit),
    "8": ("WAF / CDN Detector", waf_detector),
    "9": ("Common TCP Port Scanner", common_port_scanner),
    "10": ("Subdomain Enumeration", subdomain_scanner),
    "11": ("YouTube Channel Extended OSINT", youtube_osint),
    "12": ("GitHub Profile OSINT", github_osint),
    "13": ("Reddit Account OSINT", reddit_osint),
    "14": ("Google Dork Generator", google_dork_generator),
    "15": ("Web Tech / CMS Fingerprint", tech_fingerprint),
    "16": ("robots.txt & sitemap.xml Check", robots_sitemap_check),
    "17": ("HTTP Redirect Chain Tracer", redirect_tracer),
    "18": ("Hash Generator (MD5/SHA)", hash_generator),
    "19": ("Base64 Encode / Decode", base64_tool),
    "20": ("URL Encode / Decode", url_codec),
    "21": ("Local System & Network Info", local_system_info),
    "22": ("JSON Pretty Printer", json_formatter),
    "23": ("Webpage Links & Emails Scraper", webpage_link_email_extractor),
    "24": ("Browser Permission Demo", permission_awareness_demo),
    "25": ("Save Investigation Note", save_note),
    "26": ("Official ELVORIX Web Portal", open_elvorix),
    "27": ("Creator YouTube Channel", open_youtube),
    "28": ("Join Discord Community", open_discord),
    "29": ("Join Telegram Security Channel", open_telegram),
    "30": ("Open OSINT GitHub Repo", open_repo),
    "31": ("Fast Multi-Threaded Username OSINT", fast_username_osint),
    "32": ("SSL Certificate & crt.sh Recon", ssl_and_crtsh_recon),
    "33": ("Local Image File Metadata & Hash", image_file_forensics),
    "34": ("Deep WhatsApp Public Link & Dork Helper", deep_whatsapp_osint),
}


def main():
    while True:
        banner()
        for key in sorted(MENU_ACTIONS.keys(), key=lambda x: int(x)):
            label, _ = MENU_ACTIONS[key]
            console.print(f"[{key:>2}] {label}")
        console.print("[ 0] Exit")

        choice = console.input(f"\n[bold cyan]Select an option (0-{len(MENU_ACTIONS)}): [/bold cyan]").strip()
        if choice == "0":
            console.print("[bold red]Exiting OSINT Master Suite. Stay ethical![/bold red]")
            sys.exit(0)
        elif choice in MENU_ACTIONS:
            _, fn = MENU_ACTIONS[choice]
            fn()
        else:
            console.print(f"[red][-] Invalid option. Choose between 0 and {len(MENU_ACTIONS)}.[/red]")

        console.input("\n[dim]Press Enter to return to menu...[/dim]")


if __name__ == "__main__":
    main()
