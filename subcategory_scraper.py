from scrapling import StealthyFetcher

def get_subcategories(parent_url: str) -> list[dict]:
    """
    Returns list of:
    {
        "name": "سلة بضائع",
        "slug": "cargo_basket",
        "url": "https://qatarsale.com/ar/products/...-cargo_basket"
    }
    Excludes "الكل" (index 0)
    """
    print(f"Fetching sub-categories from: {parent_url}")
    page = StealthyFetcher.fetch(parent_url, headless=True, network_idle=True, timeout=30000)
    
    subcats = []
    links = page.find_all("[data-testid^='at-sub-category-']")
    
    for link in links:
        testid = link.attrib.get("data-testid", "")
        idx = testid.replace("at-sub-category-", "")
        if idx == "0":  # skip "الكل"
            continue
        
        href = link.attrib.get("href", "").strip()
        if not href:
            continue
        
        name_el = link.find("p")
        name = name_el.text.strip() if name_el else href.split("-")[-1]
        
        full_url = f"https://qatarsale.com{href}" if href.startswith("/") else href
        slug = href.rstrip("/").split("-")[-1]
        
        subcats.append({
            "name": name,
            "slug": slug,
            "url": full_url
        })
    
    print(f"Found {len(subcats)} sub-categories (excluding 'الكل')")
    return subcats


def get_last_page(url: str) -> int:
    page = StealthyFetcher.fetch(
        f"{url}&page=1",
        headless=True, network_idle=True, timeout=30000
    )
    
    # Get all page number buttons and extract from href
    numbers = []
    pagination_els = page.find_all("[data-testid^='at-paginator-page-']")
    for el in pagination_els:
        # Extract page number from href attribute
        href = el.find("a").attrib.get("href", "") if el.find("a") else ""
        if "page=" in href:
            try:
                num = int(href.split("page=")[-1])
                numbers.append(num)
            except ValueError:
                pass
    
    if numbers:
        return max(numbers)
    
    return 1