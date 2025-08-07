from urllib.parse import urlparse
from validators import url as validate_url


def is_valid_url(url: str) -> bool:
    return validate_url(url)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(path='', query='', fragment='').geturl()
    return normalized