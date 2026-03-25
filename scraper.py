"""Scraper module: fetches a webpage and extracts readable text content."""

from __future__ import annotations

import importlib
from typing import Any, Dict

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT_SECONDS = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> tuple[str, str]:
    """Fetch raw HTML and return HTML plus final resolved URL."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text, response.url


def extract_readable_text(html: str) -> str:
    """Extract main readable text using readability and BeautifulSoup fallback parsing."""
    article_html = html
    try:
        readability_module = importlib.import_module("readability")
        document_class = getattr(readability_module, "Document", None)
        if document_class is not None:
            doc = document_class(html)
            article_html = doc.summary(html_partial=True)
    except Exception:
        # Fallback keeps scraping functional when readability is unavailable.
        article_html = html

    article_soup = BeautifulSoup(article_html, "html.parser")

    # Keep text extraction simple and deterministic to avoid expensive downstream processing.
    return article_soup.get_text(separator=" ", strip=True)


def scrape_page(url: str) -> Dict[str, Any]:
    """Scrape a single webpage and return structured scraping artifacts."""
    html, final_url = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    text = extract_readable_text(html)

    return {
        "url": url,
        "final_url": final_url,
        "html": html,
        "soup": soup,
        "text": text,
    }
