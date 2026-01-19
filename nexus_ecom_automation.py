import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 0. CONFIGURATION (The "Bulletproof" Barrier) ---
# If the website changes their HTML tags, you only update these variables!
BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"
HTML_TAGS = {
    "product_container": "article",
    "class_container": "product_pod",
    "price_tag": "p",
    "price_class": "price_color",
    "rating_class": "star-rating"
}
DATA_FILE = "Nexus_Full_Market_Intelligence.csv"

def run_live_scraper():
    """Level 2 Verification: Fetching fresh data directly from the web."""
    print(f"[{datetime.now()}] CSV not found or update requested. Starting Live Scrape...")
    all_books = []
    
    # Logic to handle dynamic stock (Checking pages until we hit a 404)
    page = 1
    while True:
        try:
            response = requests.get(BASE_URL.format(page), timeout=10)
            if response.status_code != 200:
                break # We've reached the end of the stock
            
            soup = BeautifulSoup(response.text, 'html.parser')
            books = soup.find_all(HTML_TAGS["product_container"], class_=HTML_TAGS["class_container"])
            
            for book in books:
                title = book.h3.a["title"]
                # Error Handling for specific tags
                try:
                    price_text = book.find(HTML_TAGS["price_tag"], class_=HTML_TAGS["price_class"]).text
                    price = float(price_text.replace('£', '').replace('Â', ''))
                except AttributeError:
                    price = 0.0 # Default if tag is missing
                
                rating = book.p["class"][1] # e.g., 'Three'
                all_books.append({"Title": title, "Price_GBP": price, "Rating": rating})
            
            print(f"Scraped Page {page}...", end="\r")
            page += 1
        except Exception as e:
            print(f"\nCritical Error on Page {page}: {e}")
            break

    df = pd.DataFrame(all_books)
    df.to_csv(DATA_FILE, index=False)
    print(f"\n[{datetime.now()}] Live Scrape Complete. {len(df)} products captured.")
    return df

def run_nexus_intelligence():
    # --- LEVEL 1 & 2 VERIFICATION ---
    if os.path.exists(DATA_FILE):
        print(f"[{datetime.now()}] Level 1: CSV Found. Loading cached data...")
        df = pd.read_csv(DATA_FILE)
    else:
        print(f"[{datetime.now()}] Level 1: CSV Missing.")
        df = run_live_scraper()

    # --- 1. CLARITY MAPPING ---
    rating_map = {"One": "1-Star", "Two": "2-Star", "Three": "3-Star", "Four": "4-Star", "Five": "5-Star"}
    df["Rating_Label"] = df["Rating"].map(rating_map)
    rating_order = ["1-Star", "2-Star", "3-Star", "4-Star", "5-Star"]

    # --- 2. THE NEXUS-9 NUMERIC PILLARS ---
    total_val = df["Price_GBP"].sum()
    avg_price = df["Price_GBP"].mean()
    stock_v = df["Rating_Label"].value_counts().reindex(rating_order)
    price_v = df.groupby("Rating_Label")["Price_GBP"].mean().reindex(rating_order)
    bargains = df[(df["Rating_Label"] == "5-Star") & (df["Price_GBP"] < 20)]
    
    top_20_count = int(len(df) * 0.20)
    top_anchors = df.nlargest(top_20_count, "Price_GBP")
    
    high_tier = df[df["Rating_Label"].isin(["4-Star", "5-Star"])].shape[0]
    low_tier = df[df["Rating_Label"].isin(["1-Star", "2-Star"])].shape[0]
    pareto_perc = (top_anchors["Price_GBP"].sum() / total_val) * 100

    def classify_segment(p):
        if p < 20: return "Budget"
        elif p <= 45: return "Standard"
        else: return "Luxury"
    df["Segment"] = df["Price_GBP"].apply(classify_segment)
    seg_dist = df["Segment"].value_counts().reindex(["Budget", "Standard", "Luxury"])

    price_95th = df["Price_GBP"].quantile(0.95)
    anomalies = df[(df["Price_GBP"] >= price_95th) & (df["Rating_Label"].isin(["1-Star", "2-Star"]))]

    # --- 3. EXPORT RESULTS ---
    top_anchors.to_csv("Nexus_Top_Revenue_Anchors_Automated.csv", index=False)
    anomalies.to_csv("Nexus_Risk_Audit_Automated.csv", index=False)
    
    # --- 4. GENERATE 9-PANEL VISUAL DASHBOARD ---
    plt.style.use('ggplot')
    fig, axes = plt.subplots(3, 3, figsize=(22, 18))
    fig.suptitle(f"NEXUS STRATEGIC COMMAND CENTER\nDATA SOURCE: {'CSV' if os.path.exists(DATA_FILE) else 'LIVE WEB'}", 
                 fontsize=26, fontweight="bold")

    # [Visuals 1-9]
    axes[0,0].text(0.5, 0.5, f"Value: £{total_val:,.0f}\nStock: {len(df)}", fontsize=20, ha='center', fontweight='bold')
    axes[0,0].set_title("1. Portfolio Overview")
    axes[0,0].axis('off')
    
    sns.barplot(x=stock_v.index, y=stock_v.values, ax=axes[0,1], hue=stock_v.index, palette="Blues_d", legend=False)
    axes[0,1].set_title("2. Stock Volume")

    sns.lineplot(x=price_v.index, y=price_v.values, ax=axes[0,2], marker="o", color="orange", linewidth=3)
    axes[0,2].set_title("3. Pricing Strategy")

    axes[1,0].bar(["Bargain Leads"], [len(bargains)], color="green")
    axes[1,0].set_title(f"4. 5-Star Deals: {len(bargains)}")

    sns.boxenplot(y=top_anchors["Price_GBP"], ax=axes[1,1], color="purple")
    axes[1,1].set_title("5. Top 20% Price Spread")

    axes[1,2].pie([high_tier, low_tier], labels=["High", "Low"], autopct='%1.1f%%', colors=['skyblue', 'salmon'])
    axes[1,2].set_title("6. Sentiment Balance")

    axes[2,0].pie([pareto_perc, 100-pareto_perc], labels=["Top 20%", "Others"], autopct='%1.1f%%', colors=['gold', 'silver'])
    axes[2,0].set_title(f"7. Pareto: {pareto_perc:.1f}% Value")

    sns.barplot(x=seg_dist.index, y=seg_dist.values, ax=axes[2,1], hue=seg_dist.index, palette="viridis", legend=False)
    axes[2,1].set_title("8. Affordability Index")

    axes[2,2].text(0.5, 0.5, f"RISKS: {len(anomalies)}", fontsize=24, color='red', ha='center', fontweight='bold')
    axes[2,2].set_title("9. Quality-Price Audit")
    axes[2,2].axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("Nexus_Ultimate_Dashboard.png")
    print(f"[{datetime.now()}] SUCCESS: Dashboards and CSVs updated.")

if __name__ == "__main__":
    run_nexus_intelligence()