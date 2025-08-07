import requests
from bs4 import BeautifulSoup

def fetch_url(url: str, timeout=5):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response

def parse_html(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.find('h1')
    title = soup.find('title')
    meta = soup.find('meta', attrs={'name': 'description'})

    return {
        'h1': h1.get_text(strip=True) if h1 else None,
        'title': title.get_text(strip=True) if title else None,
        'description': meta['content'].strip() if meta and meta.get('content') else None,
    }