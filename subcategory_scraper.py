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
    """
    Fetches the category page and finds the last page number.
    """
    page = StealthyFetcher.fetch(
        f"{url}&page=1",
        headless=True, network_idle=True, timeout=30000
    )
    
    # Try pagination elements
    pagination_els = page.find_all("[data-testid='at-pagination-page-number']")
    if pagination_els:
        numbers = []
        for el in pagination_els:
            try:
                numbers.append(int(el.text.strip()))
            except ValueError:
                pass
        if numbers:
            return max(numbers)
    
    # Fallback: look for last page button
    last_el = page.find("[data-testid='at-pagination-last-page']")
    if last_el:
        try:
            return int(last_el.text.strip())
        except ValueError:
            pass
    
    # If only 1 page
    return 1