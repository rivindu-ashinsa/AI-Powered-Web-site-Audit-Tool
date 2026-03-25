"""Metrics module: computes deterministic factual metrics from parsed HTML."""

from __future__ import annotations

from typing import Any, Dict
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


CTA_KEYWORDS = (
    "contact",
    "book",
    "buy",
    "start",
    "signup",
    "sign up",
    "get",
    "join",
    "try",
)


def _normalize_domain(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def _is_external_link(href: str, base_url: str) -> bool:
    absolute = urljoin(base_url, href)
    if absolute.startswith("mailto:") or absolute.startswith("tel:"):
        return True
    return _normalize_domain(absolute) != _normalize_domain(base_url)


def compute_metrics(soup: BeautifulSoup, text: str, base_url: str) -> Dict[str, Any]:
    """Compute website audit metrics from soup + extracted text."""
    words = [word for word in text.split() if word.strip()]
    word_count = len(words)

    h1_count = len(soup.find_all("h1"))
    h2_count = len(soup.find_all("h2"))
    h3_count = len(soup.find_all("h3"))

    buttons = soup.find_all("button")
    action_links = []
    for link in soup.find_all("a", href=True):
        link_text = (link.get_text(" ", strip=True) or "").lower()
        if any(keyword in link_text for keyword in CTA_KEYWORDS):
            action_links.append(link)
    cta_count = len(buttons) + len(action_links)

    internal_links = 0
    external_links = 0
    for link in soup.find_all("a", href=True):
        href = (link.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        if _is_external_link(href, base_url):
            external_links += 1
        else:
            internal_links += 1

    images = soup.find_all("img")
    image_count = len(images)
    missing_alt_count = 0
    for image in images:
        alt = image.get("alt")
        if alt is None or not alt.strip():
            missing_alt_count += 1

    missing_alt_pct = round((missing_alt_count / image_count) * 100, 2) if image_count else 0.0

    title_tag = soup.find("title")
    meta_description_tag = soup.find("meta", attrs={"name": "description"})

    return {
        "url": base_url,
        "word_count": word_count,
        "heading_counts": {"h1": h1_count, "h2": h2_count, "h3": h3_count},
        "cta_count": cta_count,
        "internal_links": internal_links,
        "external_links": external_links,
        "images": image_count,
        "images_missing_alt_pct": missing_alt_pct,
        "meta_title": title_tag.get_text(strip=True) if title_tag else "",
        "meta_description": meta_description_tag.get("content", "").strip() if meta_description_tag else "",
    }
