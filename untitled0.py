# -*- coding: utf-8 -*-
"""
Created on Fri May 15 11:52:47 2026

@author: Lovisa
"""

import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
import pandas as pd


GOODREADS_PATH = ""
df = pd.read_csv(GOODREADS_PATH)
df = df[df["Bookshelves"] == "to-read"]
searches = df["Author, Title"].tolist()

# ----------------------------------------
# Base URL
# ----------------------------------------
base_url = "https://www.bokborsen.se/"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}
all_rows = []
# ----------------------------------------
# Loop through searches
# ----------------------------------------
for search in searches:
    author = urllib.parse.quote(search[0].strip())
    title = urllib.parse.quote(search[1].strip())


    print("\n" + "=" * 80)
    print(f"SEARCH: {search}")
    print("=" * 80)
    found_any = False
    for page in range(0, 10):

        if page == 0:
            url = (
                f"{base_url}"
                f"?g=0&c=0&q=&qa={author}"
                f"&qt={title}&qi=&qs=&f=1&fi=&fd=&fs=&pb="
                f"&_s=price&_d=asc"
            )
        else:
            url = (
                f"{base_url}"
                f"?_d=asc&_p={page}&_s=price"
                f"&f=1&qa={author}&qt={title}"
            )

        print(f"\nChecking page {page}:")
        print(url)


        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            listings = soup.find_all("div", class_="item")

            # Stop if no more listings
            if not listings:
                print("No listings found on this page.")

                # if first page has none, continue to next search
                if page == 0:
                    break

                # otherwise stop pagination
                else:
                    break

            found_any = True

            for listing in listings[:10]:

                # ----------------------------------------
                # TITLE
                # ----------------------------------------
                title_tag = listing.find("span", itemprop="name")
                title = title_tag.get_text(strip=True) if title_tag else "Unknown title"

                # ----------------------------------------
                # SELLER
                # ----------------------------------------
                seller_tag = listing.find("p", class_="seller")

                seller = "Unknown seller"

                if seller_tag:
                    seller_link = seller_tag.find("span")
                    if seller_link:
                        seller = seller_link.get_text(strip=True)

                # ----------------------------------------
                # PRICE
                # ----------------------------------------
                price_button = listing.find("button", class_="buy")

                price = "Unknown price"

                if price_button:
                    price_span = price_button.find("span", class_="price")
                    if price_span:
                        price = price_span.get_text(strip=True)
                # -----------------------------
                # LINK
                # -----------------------------
                link = None

                link_tag = listing.find("h2")

                if link_tag:
                    a = link_tag.find("a")
                    if a and a.get("href"):
                        link = "https://www.bokborsen.se" + a.get("href")
                        
                if price is not None and seller is not None:

                    all_rows.append({
                        "search": search,
                        "title": title,
                        "seller": seller,
                        "price": price,
                        "link": link
                    })
                # ----------------------------------------
                # PRINT
                # ----------------------------------------
                print(f"Title  : {title}")
                print(f"Seller : {seller}")
                print(f"Price  : {price}")
                print("-" * 40)

        except requests.RequestException as e:
            print(f"Request failed: {e}")

        # Avoid hammering server
        time.sleep(2)

# --------------------------------------------------
# CREATE DATAFRAME
# --------------------------------------------------
df = pd.DataFrame(all_rows)

print("\nTotal listings collected:", len(df))

# --------------------------------------------------
# FILTER:
# Keep only listings within min price + 63 SEK
# --------------------------------------------------
filtered_groups = []
df["price"] = pd.to_numeric(df["price"].str.replace(" SEK", ""), errors="coerce")

for search, group in df.groupby("search"):

    min_price = group["price"].min()

    filtered = group[group["price"] <= min_price + 63]

    filtered_groups.append(filtered)

filtered_df = pd.concat(filtered_groups)

print("\nListings after filtering:", len(filtered_df))# --------------------------------------------------
# SMART SELLER OPTIMIZATION
# Goal:
# Minimize TOTAL COST including shipping
# --------------------------------------------------

SHIPPING = 62

# --------------------------------------------------
# Start with absolute cheapest copy of every book
# --------------------------------------------------

selected_rows = []

for search, group in filtered_df.groupby("search"):

    cheapest = group.sort_values("price").iloc[0]

    selected_rows.append(cheapest)

current_df = pd.DataFrame(selected_rows)

# --------------------------------------------------
# Calculate current total
# --------------------------------------------------

def compute_total(df):

    book_total = df["price"].sum()

    n_sellers = df["seller"].nunique()

    shipping_total = SHIPPING * n_sellers

    return book_total + shipping_total


current_total = compute_total(current_df)

improved = True

# --------------------------------------------------
# Iteratively test replacing books
# with one seller to reduce shipping
# --------------------------------------------------

while improved:

    improved = False

    best_candidate_df = current_df
    best_candidate_total = current_total

    # Try every seller
    for seller, seller_group in filtered_df.groupby("seller"):

        candidate_rows = []

        # For each book:
        for search in current_df["search"].unique():

            # Option 1:
            # cheapest from this seller
            seller_options = seller_group[
                seller_group["search"] == search
            ]

            if not seller_options.empty:

                chosen = seller_options.sort_values("price").iloc[0]

            else:
                # keep current cheapest
                chosen = current_df[
                    current_df["search"] == search
                ].iloc[0]

            candidate_rows.append(chosen)

        candidate_df = pd.DataFrame(candidate_rows)

        candidate_total = compute_total(candidate_df)

        # Keep best improvement
        if candidate_total < best_candidate_total:

            best_candidate_total = candidate_total
            best_candidate_df = candidate_df
            improved = True

    current_df = best_candidate_df
    current_total = best_candidate_total

# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------

final_df = current_df.sort_values(
    ["seller", "search", "price"]
)

print("\n" + "=" * 80)
print("RECOMMENDED PURCHASE PLAN")
print("=" * 80)

grand_books = 0

for seller, group in final_df.groupby("seller"):

    print(f"\nSELLER: {seller}")

    subtotal = 0

    for _, row in group.iterrows():

        print(
            f"  {row['search']} | "
            f"{row['price']} SEK"
        )

        print(f"     {row['link']}")

        subtotal += row["price"]

    grand_books += subtotal

    print(f"  Seller subtotal: {subtotal} SEK")
    print(f"  Shipping: {SHIPPING} SEK")

grand_total = grand_books + SHIPPING * final_df["seller"].nunique()

print("\n" + "-" * 40)
print(f"Books total   : {grand_books} SEK")
print(f"Shipping total: {SHIPPING * final_df['seller'].nunique()} SEK")
print(f"GRAND TOTAL   : {grand_total} SEK")