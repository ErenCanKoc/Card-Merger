import requests
from bs4 import BeautifulSoup
import json
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_universal(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    # 1️⃣ JSON-LD Product
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]

            if data.get("@type") == "Product":
                title = data.get("name")

                offers = data.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0]

                price = offers.get("price")
                if title and price:
                    return title.strip(), float(price)
        except:
            pass

    # 2️⃣ OpenGraph
    og_title = soup.find("meta", property="og:title")
    og_price = soup.find("meta", property="product:price:amount")

    if og_title and og_price:
        return og_title["content"], float(og_price["content"])

    # 3️⃣ HTML price heuristic
    text = soup.get_text(" ", strip=True)
    matches = re.findall(r"(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})?)\s*(₺|TL|TRY|€|\$)", text)

    if matches:
        raw_price = matches[0][0]
        price = raw_price.replace(".", "").replace(",", ".")
        title = soup.title.text if soup.title else "Unknown product"
        return title.strip(), float(price)

    raise Exception("Ürün adı / fiyat bulunamadı")
