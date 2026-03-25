"""Scraper module: fetches webpage HTML and extracts readable text for analysis."""

from __future__ import annotations

import importlib
from typing import Any, Dict, Tuple

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT_SECONDS = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Tuple[str, str]:
    """Fetch raw HTML and return HTML plus the final resolved URL."""
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text, response.url


def extract_readable_text(html: str) -> str:
    """Extract readable text using readability-lxml when available, else fallback to full page text."""
    article_html = html
    try:
        readability_module = importlib.import_module("readability")
        document_class = getattr(readability_module, "Document", None)
        if document_class is not None:
            article_html = document_class(html).summary(html_partial=True)
    except Exception:
        article_html = html

    article_soup = BeautifulSoup(article_html, "html.parser")
    return article_soup.get_text(separator=" ", strip=True)


def scrape_page(url: str) -> Dict[str, Any]:
    """Scrape a single page and return structured artifacts for metrics + AI analysis."""
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
