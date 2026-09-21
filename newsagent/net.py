"""Bounded public-page fetching; model endpoints use a separate explicit path."""
import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urljoin, urlsplit, urlunsplit


def safe_url(url):
    if not isinstance(url, str) or len(url) > 4096 or any(ord(c) < 33 for c in url):
        raise ValueError("Invalid URL")
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("Use a public http(s) URL without credentials")
    if p.port not in (None, 80, 443):
        raise ValueError("Public source URLs must use port 80 or 443")
    if p.hostname.lower() in ("localhost", "localhost.localdomain") or p.hostname.endswith(".local"):
        raise ValueError("Private source URLs are not allowed")
    try:
        addr = ipaddress.ip_address(p.hostname)
    except ValueError:
        pass
    else:
        if not addr.is_global:
            raise ValueError("Private source URLs are not allowed")
    return urlunsplit((p.scheme, p.netloc, p.path or "/", p.query, ""))


def public_addresses(host, port):
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("Source resolves to a non-public address")
    return addresses


def fetch(url, limit=2_000_000, redirects=4):
    """Pin the validated address for this connection, including every redirect."""
    url = safe_url(url)
    p = urlsplit(url)
    port = p.port or (443 if p.scheme == "https" else 80)
    addresses = public_addresses(p.hostname, port)
    family, socktype, proto, _, address = addresses[0]
    sock = socket.socket(family, socktype, proto)
    sock.settimeout(20)
    conn = http.client.HTTPConnection(p.hostname, port, timeout=20)
    try:
        sock.connect(address)
        if p.scheme == "https":
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=p.hostname)
        conn.sock = sock
        conn.request("GET", urlunsplit(("", "", p.path or "/", p.query, "")),
                     headers={"User-Agent": "NewsAgentBuilder/0.1 (personal briefing)",
                              "Accept-Encoding": "identity"})
        response = conn.getresponse()
        if response.status in (301, 302, 303, 307, 308):
            if redirects <= 0:
                raise ValueError("Too many redirects")
            return fetch(urljoin(url, response.getheader("Location", "")), limit, redirects - 1)
        if response.status != 200:
            raise ValueError(f"Source returned HTTP {response.status}")
        content_type = response.getheader("Content-Type", "")
        if not any(x in content_type.lower() for x in ("text/", "xml", "json")):
            raise ValueError("Source did not return text, XML, or JSON")
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ValueError("Source exceeded download limit")
        return body.decode("utf-8", errors="replace"), url
    finally:
        conn.close()
        sock.close()
