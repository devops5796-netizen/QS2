import sys
import time
from detect_utils import analyze_category_with_products
import links_scraper
import products_scraper
import flatten
import excel_writer
from datetime import datetime, timezone, timedelta
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

MULTI_CATEGORIES = {
    "car_spare_parts_accessories-automotive_exterior_accessories":
        "https://qatarsale.com/ar/products/car_spare_parts_accessories-automotive_exterior_accessories?basic_search:StatusFilter=0",
    "heavy_equipments":
        "https://qatarsale.com/ar/products/heavy_equipments?basic_search:StatusFilter=0",
    "car_spare_parts_accessories":
        "https://qatarsale.com/ar/products/car_spare_parts_accessories?basic_search:StatusFilter=0",
    "jewellery":
        "https://qatarsale.com/ar/products/jewellery?basic_search:StatusFilter=0",
    "property":
        "https://qatarsale.com/ar/products/property?basic_search:StatusFilter=0",
    "watercrafts":
        "https://qatarsale.com/ar/products/watercrafts?basic_search:StatusFilter=0",
    "computers_and_parts":    
        "https://qatarsale.com/ar/products/computers_and_parts?basic_search:StatusFilter=0",
    "video_games":
        "https://qatarsale.com/ar/products/video_games?basic_search:StatusFilter=0",
    "wrist_watches":
        "https://qatarsale.com/ar/products/wrist_watches?basic_search:StatusFilter=0",
    "home_security_surveillance_systems":
        "https://qatarsale.com/ar/products/home_security_surveillance_systems?basic_search:StatusFilter=0",
    "health_beauty":
        "https://qatarsale.com/ar/products/health_beauty?basic_search:StatusFilter=0",
    "toys_games":
        "https://qatarsale.com/ar/products/toys_games?basic_search:StatusFilter=0",
    "kids":
        "https://qatarsale.com/ar/products/kids?basic_search:StatusFilter=0",
    "shoes_bags":
        "https://qatarsale.com/ar/products/shoes_bags?basic_search:StatusFilter=0",
    "arts_crafts_sewing":
        "https://qatarsale.com/ar/products/arts_crafts_sewing?basic_search:StatusFilter=0",
    "kitchen_dining_room":
        "https://qatarsale.com/ar/products/kitchen_dining_room?basic_search:StatusFilter=0",
    "education":
        "https://qatarsale.com/ar/products/education?basic_search:StatusFilter=0",
    "bikes_accessories":
        "https://qatarsale.com/ar/products/bikes_accessories?basic_search:StatusFilter=0",
    "clothes": 
        "https://qatarsale.com/ar/products/clothes?basic_search:StatusFilter=0",
    "camping":
        "https://qatarsale.com/ar/products/camping?basic_search:StatusFilter=0",
    "tools_home_improvement":
        "https://qatarsale.com/ar/products/tools_home_improvement?basic_search:StatusFilter=0",
    "men_accessories":
        "https://qatarsale.com/ar/products/men_accessories?basic_search:StatusFilter=0",
    "musical_instruments":
        "https://qatarsale.com/ar/products/musical_instruments?basic_search:StatusFilter=0"
}

def filter_yesterday_links(links_csv: str, filtered_csv: str) -> dict:
    df = pd.read_csv(links_csv)
    
    if "startDate" not in df.columns:
        print("⚠️ No startDate column found, using all links")
        df.to_csv(filtered_csv, index=False, encoding="utf-8")
        return {"total": len(df), "yesterday": len(df)}

    df["date_parsed"] = pd.to_datetime(df["startDate"], format="ISO8601", utc=True)
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    mask = df["date_parsed"].dt.date == yesterday
    df_yesterday = df[mask].drop(columns=["date_parsed"])

    print(f"  Total links:     {len(df)}")
    print(f"  Yesterday links: {len(df_yesterday)}")

    df_yesterday.to_csv(filtered_csv, index=False, encoding="utf-8")
    return {"total": len(df), "yesterday": len(df_yesterday)}

def run_subcat_pages(category: str, subcat_slug: str, start: int, end: int, subcat_url: str, subcat_name: str):
    last_page, has_products = analyze_category_with_products(subcat_url)
    if not has_products:
        print(f"⚠️ No products found in '{subcat_name}' — skipping.")
        return None

    links_csv     = f"links_{category}_{subcat_slug}_{start}_{end}.csv"
    filtered_csv  = f"links_yesterday_{category}_{subcat_slug}_{start}_{end}.csv"
    products_json = f"products_{category}_{subcat_slug}_{start}_{end}.jsonl"
    output_excel  = f"{category}_{subcat_slug}_{start}_{end}.xlsx"

    elapsed_start = time.time()
    print(f"QatarSale Scraper - Multi Sub-Category")
    print(f"Category: {category} | Sub-cat: {subcat_name} | Pages: {start} to {end}")

    s1 = links_scraper.run(subcat_url, start, end, links_csv)
    if s1['total_links'] == 0:
        print(f"⚠️ No links found for '{subcat_name}' — skipping.")
        return None
    
    
    print("\n" + "="*50)
    print("STEP 1.5: Filtering yesterday's links...")
    print("="*50)
    s_filter = filter_yesterday_links(links_csv, filtered_csv)

    if s_filter["yesterday"] == 0:
        print("\n" + "="*60)
        print("No listings found for yesterday.")
        print("Skipping product scraping and flattening.")
        print("="*60)

        elapsed = time.time() - elapsed_start
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"STEP 1   - Links:    {s1['success']} pages OK | {s1['failed']} failed | {s1['total_links']} total")
        print(f"STEP 1.5 - Filter:   0 yesterday / {s_filter['total']} total")
        print("STEP 2   - Products: Skipped")
        print("STEP 3   - Flatten:  Skipped")
        print(f"Total Time: {minutes}m {seconds}s")
        print("="*60)

        return
    
    s2 = products_scraper.run(filtered_csv, products_json, workers=4, category=category)
    if s2['success'] == 0:
        print(f"⚠️ No products scraped for '{subcat_name}' — skipping.")
        return None

    s3 = flatten.run(products_json)
    df = s3["df"]
    excel_writer.write_single(df, subcat_name[:31], output_excel)

    elapsed = time.time() - elapsed_start
    print(f"\nDONE: {s1['total_links']} links | {s2['success']} scraped | {int(elapsed//60)}m {int(elapsed%60)}s")
    return output_excel


def main():
    if len(sys.argv) == 7:
        category    = sys.argv[1]
        subcat_slug = sys.argv[2]
        start       = int(sys.argv[3])
        end         = int(sys.argv[4])
        subcat_url  = sys.argv[5]
        subcat_name = sys.argv[6]
        run_subcat_pages(category, subcat_slug, start, end, subcat_url, subcat_name)
    else:
        print("Usage:")
        print("  python main.py <category> <subcat_slug> <start> <end> <subcat_url> <subcat_name>")
        sys.exit(1)


if __name__ == "__main__":
    main()