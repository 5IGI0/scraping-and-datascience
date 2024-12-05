from urllib.parse import ParseResult, urlparse, parse_qs

def _sanitize_url(url: ParseResult) -> (ParseResult, bool):
    # some facebook links has this format: https://www.facebook.com/sharer/sharer.php?u=<url> (or p[url] in some cases)
    if url.hostname and url.hostname in ("www.facebook.com", "facebook.com") and url.path.lower() == "/sharer/sharer.php":
        params = {k.strip().lower(): v for k, v in parse_qs(url.query).items()}
        if "u" in params:
            return urlparse(params["u"][0]), True
        elif "p[url]" in params:
            return urlparse(params["p[url]"][0]), True
    return url, False

def sanitize_url(url: ParseResult) -> ParseResult:
    sanitized = True
    while sanitized:
        url, sanitized = _sanitize_url(url)
    return url

def is_blacklisted(url: ParseResult) -> bool:
    # block blogger's images
    if url.hostname and url.hostnames.endswith(".googleusercontent.com") and url.path.startswith("/blogger_img_proxy/"):
        return True
    return url.hostname == 'blogger.googleusercontent.com'

if __name__ == "__main__":
   import sys

   if sys.argv[1] == "domains":
        try:
            while True:
                url = input("")
                u = urlparse(url)
                u = sanitize_url(u)
                if u.hostname and not is_blacklisted(u):
                    print(u.hostname)
        except EOFError:
            pass
            