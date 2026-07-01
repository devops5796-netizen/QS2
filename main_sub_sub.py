import sys
import time
from detect_utils import analyze_category_with_products
import links_scraper
import products_scraper
import flatten
import excel_writer
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

MULTI_CATEGORIES = {
    "home_appliances":
        "https://qatarsale.com/ar/products/home_appliances?basic_search:StatusFilter=0",
    "services":
        "https://qatarsale.com/ar/products/services?basic_search:StatusFilter=0",
    "mobile_telephone_and_tablets":
        "https://qatarsale.com/ar/products/mobile_telephone_and_tablets?basic_search:StatusFilter=0",
    "furniture_dcor":
        "https://qatarsale.com/ar/products/furniture_dcor?basic_search:StatusFilter=0",
    "electronics":
        "https://qatarsale.com/ar/products/electronics?basic_search:StatusFilter=0",
    "sportswear_equipment":
        "https://qatarsale.com/ar/products/sportswear_equipment?basic_search:StatusFilter=0"
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
        print(f"Total Time: {minutes}m {seconds}s")

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