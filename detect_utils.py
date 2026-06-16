import json
from scrapling import StealthyFetcher

def get_last_page(url: str) -> int:
    page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=30000)
    numbers = []
    pagination_els = page.find_all("[data-testid^='at-paginator-page-']")
    for el in pagination_els:
        a = el.find("a")
        if not a:
            continue
        href = a.attrib.get("href", "")
        if "page=" in href:
            try:
                numbers.append(int(href.split("page=")[-1]))
            except ValueError:
                pass
    return max(numbers) if numbers else 1


def get_subcategories(base_url: str) -> list:
    page = StealthyFetcher.fetch(base_url, headless=True, network_idle=True, timeout=30000)
    subcats = []
    links = page.find_all("[data-testid^='at-sub-category-']")
    for link in links:
        testid = link.attrib.get("data-testid", "")
        idx = testid.replace("at-sub-category-", "")
        if idx == "0":
            continue
        href = link.attrib.get("href", "").strip()
        if not href:
            continue
        name_el = link.find("p")
        name = name_el.text.strip() if name_el else href.split("-")[-1]
        full_url = f"https://qatarsale.com{href}" if href.startswith("/") else href
        slug = href.rstrip("/").split("-")[-1]
        subcats.append({"name": name, "slug": slug, "url": full_url})
    return subcats


def analyze_category_with_products(url: str):
    page = StealthyFetcher.fetch(
        f"{url}&page=1",
        headless=True,
        network_idle=True,
        timeout=30000
    )

    # 1. check if products exist
    product_cards = page.find_all("qs-product-card-v2")
    if not product_cards:
        product_cards = page.find_all("qs-product-card-classic")
    
    # If no product cards at all → no products
    if not product_cards:
        return 0, False

    # 2. extract pagination
    numbers = []
    pagination_els = page.find_all("[data-testid^='at-paginator-page-']")
    for el in pagination_els:
        a = el.find("a")
        if not a:
            continue
        href = a.attrib.get("href", "")
        if "page=" in href:
            try:
                numbers.append(int(href.split("page=")[-1]))
            except ValueError:
                pass

    last_page = max(numbers) if numbers else 1
    return last_page, True