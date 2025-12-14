import json
import re
from typing import Iterable, Optional, Tuple

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


def _parse_price(value: str) -> Optional[float]:
    """Convert common price strings to a float.

    The scraper encounters both comma and dot decimal separators; this helper
    normalises them to a consistent float representation.
    """

    if not value:
        return None

    cleaned = value.strip().replace("\xa0", " ")
    # Strip common currency symbols/labels while keeping numbers intact.
    cleaned = re.sub(r"(₺|TL|TRY|€|\$|USD|EUR)", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_from_ld_json(data: dict) -> Optional[Tuple[str, float]]:
    """Attempt to pull product info from a parsed JSON-LD blob."""

    product_types: Iterable = data if isinstance(data, list) else [data]

    # Handle @graph payloads by flattening into the iterable.
    expanded: list = []
    for item in product_types:
        if isinstance(item, dict) and "@graph" in item and isinstance(item["@graph"], list):
            expanded.extend(item["@graph"])
        else:
            expanded.append(item)

    for entry in expanded:
        if not isinstance(entry, dict):
            continue

        if entry.get("@type") != "Product":
            continue

        title = entry.get("name")
        offers = entry.get("offers", {})
        if isinstance(offers, list) and offers:
            offers = offers[0]

        price_value = None
        if isinstance(offers, dict):
            price_value = offers.get("price") or offers.get("priceSpecification", {}).get("price")

        price = _parse_price(price_value) if price_value else None
        if title and price is not None:
            return title.strip(), price

    return None


def scrape_universal(url: str) -> Tuple[str, float]:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 1️⃣ JSON-LD Product
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue

        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        found = _extract_from_ld_json(data)
        if found:
            return found

    # 2️⃣ OpenGraph
    og_title = soup.find("meta", property="og:title")
    og_price = soup.find("meta", property="product:price:amount") or soup.find(
        "meta", property="product:sale_price:amount"
    )

    if og_title and og_price:
        parsed = _parse_price(og_price.get("content"))
        if parsed is not None:
            return og_title["content"], parsed

    # 3️⃣ HTML price heuristic (currency may be before or after the number)
    text = soup.get_text(" ", strip=True)
    matches = re.findall(
        r"(?:₺|TL|TRY|€|\$)?\s*(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})?)(?:\s*(?:₺|TL|TRY|€|\$))",
        text,
        flags=re.IGNORECASE,
    )

    if matches:
        price = _parse_price(matches[0])
        if price is not None:
            title = soup.title.text if soup.title else "Unknown product"
            return title.strip(), price

    raise ValueError("Ürün adı / fiyat bulunamadı")
