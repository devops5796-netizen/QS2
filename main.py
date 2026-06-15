import sys
import time
import pandas as pd
import links_scraper
import products_scraper
import flatten
import subcategory_scraper
import excel_writer
from dotenv import load_dotenv
load_dotenv()

CATEGORIES = {
    "cars_for_rent":
        "https://qatarsale.com/ar/products/cars_for_rent?basic_search:StatusFilter=0",
    "special_numbers-plate_numbers":
        "https://qatarsale.com/ar/products/special_numbers-plate_numbers?basic_search:StatusFilter=0",
    "bikes":
        "https://qatarsale.com/ar/products/bikes?basic_search:StatusFilter=0",
    "caravan":
        "https://qatarsale.com/ar/products/caravan?basic_search:StatusFilter=0"
}

MULTI_CATEGORIES = {
    "car_spare_parts_accessories-automotive_exterior_accessories":
        "https://qatarsale.com/ar/products/car_spare_parts_accessories-automotive_exterior_accessories?basic_search:StatusFilter=0",
    "heavy_equipments":
        "https://qatarsale.com/ar/products/heavy_equipments?basic_search:StatusFilter=0",
    "car_spare_parts_accessories":
        "https://qatarsale.com/ar/products/car_spare_parts_accessories?basic_search:StatusFilter=0",
    "property":
        "https://qatarsale.com/ar/products/property?basic_search:StatusFilter=0",
}


def run_single_category(category: str, start: int, end: int):
    listing_url   = CATEGORIES[category]
    links_csv     = f"links_{category}_{start}_{end}.csv"
    products_json = f"products_{category}_{start}_{end}.jsonl"
    output_excel  = f"{category}_{start}_{end}.xlsx"

    elapsed_start = time.time()
    print("QatarSale Scraper - Single Category")
    print(f"Category: {category} | Pages: {start} to {end}")

    s1 = links_scraper.run(listing_url, start, end, links_csv)
    s2 = products_scraper.run(links_csv, products_json, workers=4)
    s3 = flatten.run(products_json)

    df = s3["df"]
    excel_writer.write_single(df, category[:31], output_excel)

    elapsed = time.time() - elapsed_start
    print(f"\nDONE: {s1['total_links']} links | {s2['success']} scraped | {s3['columns']} cols | {int(elapsed//60)}m {int(elapsed%60)}s")
    return output_excel


def run_multi_category(category: str):
    base_url      = MULTI_CATEGORIES[category]
    output_excel  = f"{category}.xlsx"
    elapsed_start = time.time()

    print("QatarSale Scraper - Multi Sub-Category")
    print(f"Category: {category}")

    subcats = subcategory_scraper.get_subcategories(base_url)
    if not subcats:
        print("No sub-categories found!")
        return

    sheets = {}

    for subcat in subcats:
        name  = subcat["name"]
        slug  = subcat["slug"]
        url   = subcat["url"] + "?basic_search:StatusFilter=0"

        print(f"\n{'='*50}")
        print(f"Sub-category: {name} ({slug})")
        print(f"{'='*50}")

        last_page     = subcategory_scraper.get_last_page(url)
        print(f"Pages: 1 to {last_page}")

        links_csv     = f"links_{category}_{slug}.csv"
        products_json = f"products_{category}_{slug}.jsonl"

        links_scraper.run(url, 1, last_page, links_csv)
        products_scraper.run(links_csv, products_json, workers=4)
        result = flatten.run(products_json)

        sheets[name] = result["df"]

    excel_writer.write(sheets, output_excel)

    elapsed = time.time() - elapsed_start
    print(f"\nDONE: {len(subcats)} sub-categories | {int(elapsed//60)}m {int(elapsed%60)}s")
    return output_excel


def main():
    if len(sys.argv) == 4:
        category = sys.argv[1]
        start    = int(sys.argv[2])
        end      = int(sys.argv[3])

        if category in CATEGORIES:
            run_single_category(category, start, end)
        elif category in MULTI_CATEGORIES:
            print("Multi-category mode — ignoring start/end pages")
            run_multi_category(category)
        else:
            print(f"Unknown category: {category}")
            sys.exit(1)

    elif len(sys.argv) == 2:
        category = sys.argv[1]
        if category in MULTI_CATEGORIES:
            run_multi_category(category)
        else:
            print(f"Unknown category: {category}")
            sys.exit(1)

    else:
        print("Usage:")
        print("  python main.py <category> <start_page> <end_page>")
        print("  python main.py <multi_category>")
        sys.exit(1)


if __name__ == "__main__":
    main()