
from urllib.parse import unquote
import re

def google_decode(url):
    """
    Decode a google url.
    """
    if 'url=' not in url:
        return url
    url = re.sub(r'.*url=', '', url)
    url =re.sub(r'&.*', '', url)
    url = unquote(url)
    return url

def get_google_url(search_term: str, site: str|None = None, num_pages: int = 1) -> str|list:
    """
    Get a google url for a search term.
    Optionally, specify a domain to search (e.g 'linkedin.com').
    """
    url = f'https://www.google.com/search?q={search_term.replace(" ", "+")}'
    if site:
        url += f'+site%3A{site}'
    urls = [url]
    if num_pages > 1:
        for i in range(1, num_pages):
            urls.append(url + f'&start={i * 10}')
        return urls
    return url