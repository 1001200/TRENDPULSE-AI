"""
Dataset Generator for 'NEO-STREET ATELIER' — Realistic D2C Fashion E-Commerce Dataset.

Generates a 3,200+ row, 28-column dataset with realistic fashion domain complexity,
messy real-world data patterns (mixed date formats, dirty sizes, messy colors,
currency symbols, discount bleed, multi-item baskets, returns, and inventory levels)
specifically crafted for TrendPulse's Data Engine & ML Suite.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Seed for reproducible realism
random.seed(42)
np.random.seed(42)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "neo_street_atelier_ecommerce_sales.csv"
XLSX_PATH = OUTPUT_DIR / "neo_street_atelier_ecommerce_sales.xlsx"

# ── Catalog Definition ──────────────────────────────────────────

CATALOG = [
    {
        "sku": "TEE-Y2K-ACID-01",
        "title": "Y2K Cyber Acid-Wash Heavyweight Oversized Tee",
        "category": "T-Shirts & Tops",
        "subcategory": "Oversized Tees",
        "mrp": 1799,
        "base_price": 1499,
        "cost": 380,
        "fit": "Oversized Drop-Shoulder",
        "fabric": "100% Combed Cotton 240 GSM Acid-Washed",
        "colors": ["Washed Black", "washed black", "CHARCOAL / BLACK", "Vintage Olive", "Cobalt Blue"],
        "sizes": ["S", "Small", "s", "M", "Medium", "m", "L", "Large", "XL", "2XL", "XXL"],
        "aesthetic": "Y2K Streetwear",
        "base_stock": 25,
        "virality": 92,
    },
    {
        "sku": "CRG-GRP-TACT-02",
        "title": "Gorpcore Tactical Waterproof Cargo Pants with D-Ring",
        "category": "Bottoms & Pants",
        "subcategory": "Cargos & Parachute",
        "mrp": 3499,
        "base_price": 2799,
        "cost": 850,
        "fit": "Wide Leg Baggy",
        "fabric": "Water-Repellent Taslan Nylon Ripstop",
        "colors": ["Matte Black", "Sage Green", "Vintage Olive", "Desert Khaki"],
        "sizes": ["30x30", "32x30", "34x32", "S", "M", "L", "XL"],
        "aesthetic": "Gorpcore Utility",
        "base_stock": 14,
        "virality": 88,
    },
    {
        "sku": "FLN-90S-BOX-01",
        "title": "90s Kurt Boxy Plaid Flannel Overshirt",
        "category": "Shirts",
        "subcategory": "Flannels & Overshirts",
        "mrp": 2499,
        "base_price": 1999,
        "cost": 580,
        "fit": "Boxy Relaxed",
        "fabric": "Heavy Brushed Cotton Flannel 220 GSM",
        "colors": ["Forest Green Plaid", "Wine Red / Navy", "Espresso Brown", "Monochrome Shadow"],
        "sizes": ["Small", "M", "Medium", "L", "Large", "XL", "X-Large"],
        "aesthetic": "90s Grunge",
        "base_stock": 42,
        "virality": 76,
    },
    {
        "sku": "KNT-OLD-POLO-03",
        "title": "Old Money Ribbed Cotton Polo Knit",
        "category": "Knitwear",
        "subcategory": "Polo Knits",
        "mrp": 2999,
        "base_price": 2499,
        "cost": 720,
        "fit": "Relaxed Regular",
        "fabric": "100% Pima Cotton Fine Ribbed Knit",
        "colors": ["Bone / Off-White", "Ecru", "Espresso Brown", "Navy Blue", "Olive Green"],
        "sizes": ["S", "M", "L", "XL"],
        "aesthetic": "Old Money Luxury",
        "base_stock": 35,
        "virality": 81,
    },
    {
        "sku": "HOD-VNT-WSH-01",
        "title": "Vintage Washed Black Drop-Shoulder Hoodie 400 GSM",
        "category": "Hoodies & Sweats",
        "subcategory": "Heavyweight Hoodies",
        "mrp": 3999,
        "base_price": 3299,
        "cost": 980,
        "fit": "Extreme Oversized",
        "fabric": "100% French Terry Cotton 400 GSM Vintage Pigment Dyed",
        "colors": ["Washed Charcoal", "Faded Pine Green", "Espresso Brown", "Clay Burgundy"],
        "sizes": ["S", "M", "L", "XL", "2XL"],
        "aesthetic": "Vintage Streetwear",
        "base_stock": 8, # Low stock / stockout alert
        "virality": 95,
    },
    {
        "sku": "TEE-COQ-RBN-02",
        "title": "Coquette Ribbon Detail Ribbed Baby Tee",
        "category": "T-Shirts & Tops",
        "subcategory": "Baby Tees & Crops",
        "mrp": 1299,
        "base_price": 999,
        "cost": 240,
        "fit": "Boxy Crop Fitted",
        "fabric": "Ribbed Modal Cotton Blend with Satin Bows",
        "colors": ["Baby Pink", "Off-White", "Dusty Lilac", "Pitch Black"],
        "sizes": ["XS", "S", "Small", "M", "L"],
        "aesthetic": "Coquette Aesthetic",
        "base_stock": 60,
        "virality": 89,
    },
    {
        "sku": "PNT-STR-PRC-01",
        "title": "Streetwear Parachute Baggy Track Pants",
        "category": "Bottoms & Pants",
        "subcategory": "Track Pants",
        "mrp": 2799,
        "base_price": 2199,
        "cost": 620,
        "fit": "Ultra Wide Parachute",
        "fabric": "Lightweight Crinkle Nylon with Bungee Cinch Hem",
        "colors": ["Washed Black", "Matte Grey", "Sage Green", "Silver Ice"],
        "sizes": ["Free Size", "OSFA", "S", "M", "L", "XL"],
        "aesthetic": "Y2K Streetwear",
        "base_stock": 30,
        "virality": 85,
    },
    {
        "sku": "SHR-MIN-LIN-01",
        "title": "Minimalist Japanese Cotton Linen Camp Collar Shirt",
        "category": "Shirts",
        "subcategory": "Camp Collar Shirts",
        "mrp": 2599,
        "base_price": 2099,
        "cost": 590,
        "fit": "Relaxed Resort",
        "fabric": "55% Linen 45% Organic Cotton",
        "colors": ["Natural Linen Beige", "Olive Sage", "Midnight Navy", "Terracotta"],
        "sizes": ["S", "M", "L", "XL"],
        "aesthetic": "Minimalist Clean",
        "base_stock": 48,
        "virality": 71,
    },
    {
        "sku": "DEN-RET-CRP-01",
        "title": "Distressed Vintage Carpenter Denim Jeans",
        "category": "Bottoms & Pants",
        "subcategory": "Denim & Jeans",
        "mrp": 3799,
        "base_price": 2999,
        "cost": 920,
        "fit": "Straight Leg Loose",
        "fabric": "14.5oz Rigid Cotton Denim with Hammer Loop",
        "colors": ["Vintage Mid Wash Blue", "Bleached Acid Blue", "Washed Black Denim"],
        "sizes": ["28x30", "30x30", "32x30", "34x32", "36x32"],
        "aesthetic": "90s Thrift Vintage",
        "base_stock": 19,
        "virality": 79,
    },
    {
        "sku": "VST-FLC-SHR-01",
        "title": "Gorpcore Fleece Sherpa Mountain Zip Vest",
        "category": "Outerwear & Jackets",
        "subcategory": "Vests & Gilets",
        "mrp": 2999,
        "base_price": 2299,
        "cost": 710,
        "fit": "Boxy Layering",
        "fabric": "Bonded Polar Sherpa Fleece 320 GSM with Contrast Pocket",
        "colors": ["Oatmeal / Hunter Green", "All Black", "Purple / Teal Retro"],
        "sizes": ["M", "L", "XL"],
        "aesthetic": "Gorpcore Utility",
        "base_stock": 5, # Low stock
        "virality": 67,
    },
    {
        "sku": "TEE-COR-OVB-01",
        "title": "Core Essential Heavyweight Oversized Tee - Bone White",
        "category": "T-Shirts & Tops",
        "subcategory": "Essentials",
        "mrp": 1499,
        "base_price": 1199,
        "cost": 290,
        "fit": "Oversized Boxy",
        "fabric": "100% Single Jersey Cotton 260 GSM Pre-Shrunk",
        "colors": ["Bone White", "Washed Charcoal", "Muted Olive", "Mocha Brown"],
        "sizes": ["S", "M", "L", "XL", "2XL"],
        "aesthetic": "Minimalist Streetwear",
        "base_stock": 110,
        "virality": 74,
    },
    {
        "sku": "HOD-GRG-DST-02",
        "title": "90s Distressed Raw-Hem Zip Hoodie",
        "category": "Hoodies & Sweats",
        "subcategory": "Zip Hoodies",
        "mrp": 3499,
        "base_price": 2399,
        "cost": 910,
        "fit": "Oversized Crop Raw Hem",
        "fabric": "Loopback French Terry 360 GSM Hand-Distressed",
        "colors": ["Washed Moss", "Vintage Ash Grey", "Faded Burgundy"],
        "sizes": ["S", "M", "L"],
        "aesthetic": "90s Grunge",
        "base_stock": 52, # Overstocked / Underperformer candidate
        "virality": 58,
    },
    {
        "sku": "ACC-STR-CP01",
        "title": "Acid-Washed Embroidered Vintage Dad Cap",
        "category": "Accessories",
        "subcategory": "Hats & Caps",
        "mrp": 999,
        "base_price": 799,
        "cost": 160,
        "fit": "Adjustable Strapback",
        "fabric": "100% Washed Cotton Twill with Antiqued Brass Clasp",
        "colors": ["Washed Forest Green", "Washed Slate Black", "Faded Navy", "Sandstone"],
        "sizes": ["Free Size", "OSFA"],
        "aesthetic": "Vintage Streetwear",
        "base_stock": 75,
        "virality": 65,
    },
    {
        "sku": "ACC-TOT-CNV",
        "title": "Heavyweight Raw Canvas Screenprinted Tote Bag",
        "category": "Accessories",
        "subcategory": "Bags & Totes",
        "mrp": 799,
        "base_price": 599,
        "cost": 120,
        "fit": "One Size Heavyweight Tote",
        "fabric": "16oz Natural Unbleached Cotton Canvas",
        "colors": ["Raw Natural Cream", "Washed Black Canvas"],
        "sizes": ["Free Size", "OSFA"],
        "aesthetic": "Minimalist Clean",
        "base_stock": 90,
        "virality": 70,
    }
]

# ── Customer Profiles (RFM & Geography) ──────────────────────────

CITIES = [
    ("Mumbai", "Maharashtra"),
    ("Bengaluru", "Karnataka"),
    ("Delhi", "Delhi NCR"),
    ("Pune", "Maharashtra"),
    ("Hyderabad", "Telangana"),
    ("Jaipur", "Rajasthan"),
    ("Kolkata", "West Bengal"),
    ("Chandigarh", "Punjab / Haryana"),
    ("Kochi", "Kerala"),
    ("Ahmedabad", "Gujarat"),
    ("Gurugram", "Haryana"),
    ("Goa", "Goa"),
    ("Indore", "Madhya Pradesh"),
]

CUSTOMERS = [
    {"id": f"CUST-{1000 + i}", "name": name, "city": city, "state": state, "email": email}
    for i, (name, city, state, email) in enumerate([
        ("Aryan Sharma", "Mumbai", "Maharashtra", "aryan.sharma99@gmail.com"),
        ("Rhea Mehta", "Bengaluru", "Karnataka", "rhea.m@outlook.com"),
        ("Kabir Malhotra", "Delhi", "Delhi NCR", "kabir.malhotra@yahoo.com"),
        ("Ananya Sen", "Kolkata", "West Bengal", "ananya.sen@gmail.com"),
        ("Devika Nair", "Kochi", "Kerala", "devika.nair24@gmail.com"),
        ("Rohan Verma", "Pune", "Maharashtra", "rohan.v@gmail.com"),
        ("Tanvi Kulkarni", "Pune", "Maharashtra", "tanvik@rediffmail.com"),
        ("Aditya Rao", "Bengaluru", "Karnataka", "aditya.rao@corp.in"),
        ("Meera Joshi", "Jaipur", "Rajasthan", "meera.j@gmail.com"),
        ("Siddharth Kapoor", "Mumbai", "Maharashtra", "sid.kapoor@gmail.com"),
        ("Tara Deshmukh", "Mumbai", "Maharashtra", "tara.desh@gmail.com"),
        ("Vikram Singhania", "Delhi", "Delhi NCR", "vikram.s@singhania.in"),
        ("Ishaan Mukherjee", "Kolkata", "West Bengal", "ishaan.mukh@gmail.com"),
        ("Zoya Khan", "Hyderabad", "Telangana", "zoya.khan@gmail.com"),
        ("Kunal Bhattacharya", "Ahmedabad", "Gujarat", "kunal.b@gmail.com"),
        ("Sneha Pillai", "Bengaluru", "Karnataka", "sneha.p@gmail.com"),
        ("Arjun Grover", "Chandigarh", "Punjab / Haryana", "arjun.grover@gmail.com"),
        ("Natasha D'Souza", "Goa", "Goa", "natashadsouza@gmail.com"),
        ("Varun Saxena", "Indore", "Madhya Pradesh", "varun.saxena@gmail.com"),
        ("Pooja Hegde", "Bengaluru", "Karnataka", "pooja.hegde@gmail.com"),
    ])
]

# Add more random occasional customers (pool of 180 customers)
for i in range(21, 180):
    city, state = random.choice(CITIES)
    first_names = ["Akash", "Bhavna", "Chirag", "Divya", "Eshan", "Farhan", "Gauri", "Harsh", "Isha", "Jatin", "Kritika", "Laksh", "Manish", "Nidhi", "Omkar", "Prachi", "Rishabh", "Sakshi", "Tushar", "Urvi"]
    last_names = ["Patel", "Reddy", "Gupta", "Choudhury", "Bose", "Menon", "Jain", "Bansal", "Chopra", "Dutta", "Nanda", "Aggarwal", "Iyer", "Ranganathan", "Purohit"]
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    CUSTOMERS.append({
        "id": f"CUST-{1000 + i}",
        "name": f"{fn} {ln}",
        "city": city,
        "state": state,
        "email": f"{fn.lower()}.{ln.lower()}{random.randint(10,999)}@gmail.com"
    })

CHANNELS = ["Shopify Web", "Instagram Direct Drop", "WhatsApp VIP Concierge", "Meta Ad Campaign", "Pop-Up Flash Event"]
CHANNEL_WEIGHTS = [0.65, 0.18, 0.09, 0.06, 0.02]

PAYMENT_METHODS = ["UPI (GooglePay / PhonePe)", "Razorpay (Credit/Debit Card)", "Cash on Delivery (COD)", "Net Banking", "Paytm / Wallets"]
PAYMENT_WEIGHTS = [0.55, 0.25, 0.12, 0.05, 0.03]

DISCOUNT_CODES = [
    ("NONE", 0.0),
    ("FIRST10", 0.10),
    ("Y2KDROP", 0.15),
    ("FLASH20", 0.20),
    ("VIPCLUB", 0.15),
    ("STREETPULSE", 0.12),
    ("SUMMER500", 0.25),
]

RETURN_REASONS = [
    "Wrong size - fits too oversized",
    "Fabric handfeel not as expected",
    "Color variance under home lighting",
    "Delayed courier delivery",
    "Changed mind / Buyer remorse",
    "Defective stitching / hardware"
]


def generate_dataset(num_rows: int = 3400) -> pd.DataFrame:
    """Generate rich, realistic e-commerce clothing records with deliberate real-world messiness."""
    
    rows = []
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2026, 3, 31)
    date_range_days = (end_date - start_date).days

    # Order ID counter
    order_num = 10450
    current_order_id = f"NSA-2025-{order_num}"

    # Weights for products: Popularity distribution
    prod_weights = [0.18, 0.14, 0.10, 0.09, 0.12, 0.07, 0.08, 0.05, 0.06, 0.03, 0.05, 0.01, 0.01, 0.005]

    for i in range(num_rows):
        # Basket multi-item logic: 35% chance to be part of previous order
        if i > 0 and random.random() < 0.32:
            order_id = current_order_id
            order_dt = rows[-1]["_dt_obj"]
            cust = rows[-1]["_cust_obj"]
            channel = rows[-1]["Sales Channel"]
            payment = rows[-1]["Payment Method"]
        else:
            order_num += 1
            order_id = f"NSA-2025-{order_num}" if order_num < 12000 else f"NSA-2026-{order_num}"
            current_order_id = order_id
            
            # Non-uniform date distribution: Higher in Oct-Nov (festive) & Dec-Jan (winter)
            day_offset = random.randint(0, date_range_days)
            order_dt = start_date + timedelta(
                days=day_offset,
                hours=random.randint(9, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            # Pick customer: VIPs have higher probability
            if random.random() < 0.40:
                cust = random.choice(CUSTOMERS[:20]) # Top VIP repeat buyers
            else:
                cust = random.choice(CUSTOMERS[20:])
                
            channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
            payment = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]

        # Select product
        item = random.choices(CATALOG, weights=prod_weights[:len(CATALOG)])[0]
        color = random.choice(item["colors"])
        size = random.choice(item["sizes"])

        # Realistic Quantity: 1 is 84%, 2 is 13%, 3 is 3%
        qty = random.choices([1, 2, 3], weights=[0.84, 0.13, 0.03])[0]

        # Pricing & Discount
        code, disc_rate = random.choice(DISCOUNT_CODES)
        unit_price = round(item["base_price"] * (1 - disc_rate))
        unit_cost = item["cost"]
        mrp = item["mrp"]
        discount_amount = (item["base_price"] - unit_price) * qty
        line_total = unit_price * qty

        # Inventory simulation (countdown / stock status)
        stock = max(0, item["base_stock"] - random.randint(0, min(10, item["base_stock"])))

        # Status & returns (approx 6-8% return rate for clothing)
        status_rand = random.random()
        if status_rand < 0.06:
            order_status = "Returned"
            return_reason = random.choice(RETURN_REASONS)
        elif status_rand < 0.09:
            order_status = "Exchange Requested"
            return_reason = "Wrong size - fits too oversized"
        elif status_rand < 0.11:
            order_status = "Cancelled"
            return_reason = "Customer cancelled before dispatch"
        else:
            order_status = "Delivered"
            return_reason = ""

        # Social Trend Data
        virality_score = min(100, max(20, int(item["virality"] + np.random.normal(0, 8))))
        social_tag = f"#{item['aesthetic'].replace(' ', '').lower()} #d2cstreetwear #{item['subcategory'].replace(' ', '').lower()}"

        # ── Introduce deliberate real-world "dirtiness" / edge cases ──

        # 1. Date formatting messiness: ISO vs DD-MM-YYYY vs YYYY/MM/DD
        date_format_choice = random.random()
        if date_format_choice < 0.50:
            formatted_date = order_dt.strftime("%Y-%m-%d %H:%M:%S")
        elif date_format_choice < 0.75:
            formatted_date = order_dt.strftime("%d/%m/%Y")
        elif date_format_choice < 0.90:
            formatted_date = order_dt.strftime("%Y/%m/%d")
        else:
            formatted_date = order_dt.strftime("%d-%m-%Y %I:%M %p")

        # 2. Currency symbol messiness in 15% of records
        if random.random() < 0.15:
            display_price = f"₹ {unit_price:,}.00"
            display_revenue = f"₹ {line_total:,}.00"
        elif random.random() < 0.08:
            display_price = f"Rs. {unit_price}"
            display_revenue = f"Rs. {line_total}"
        else:
            display_price = float(unit_price)
            display_revenue = float(line_total)

        # 3. Trimmable whitespace in customer email or name (approx 8% of rows)
        cust_email = cust["email"]
        cust_name = cust["name"]
        if random.random() < 0.08:
            cust_email = f"  {cust_email}  "
        if random.random() < 0.05:
            cust_name = cust_name.lower()

        row = {
            "Order ID": order_id,
            "Order Date": formatted_date,
            "Customer ID": cust["id"],
            "Customer Name": cust_name,
            "Customer Email": cust_email,
            "Shipping City": cust["city"],
            "Shipping State": cust["state"],
            "Sales Channel": channel,
            "Product SKU": item["sku"],
            "Product Title": item["title"],
            "Category": item["category"],
            "Subcategory": item["subcategory"],
            "Size": size,
            "Color": color,
            "Fit Silhouette": item["fit"],
            "Fabric Material": item["fabric"],
            "Quantity": qty,
            "Cost Price": unit_cost,
            "MRP": mrp,
            "Selling Price": display_price,
            "Discount Amount": discount_amount,
            "Discount Code": code if code != "NONE" else "",
            "Total Revenue": display_revenue,
            "Stock Remaining": stock,
            "Payment Method": payment,
            "Order Status": order_status,
            "Return Reason": return_reason,
            "Social Virality Score": virality_score,
            "Trending Aesthetic Tag": item["aesthetic"],
            "Social Hashtags": social_tag,
            "_dt_obj": order_dt,
            "_cust_obj": cust,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # ── Inject a small handful of realistic anomaly records for Data Quality testing ──
    # 1. Two rows with missing customer ID
    df.loc[120, "Customer ID"] = np.nan
    df.loc[450, "Customer ID"] = ""
    # 2. One negative quantity (return return-log glitch)
    df.loc[280, "Quantity"] = -1
    # 3. One zero price sample
    df.loc[610, "Selling Price"] = "₹ 0.00"
    # 4. Two exact duplicate transaction rows
    df.iloc[890] = df.iloc[889].copy()

    # Drop internal helper columns
    df = df.drop(columns=["_dt_obj", "_cust_obj"])

    return df


def main():
    print("[*] Generating Neo-Street Atelier e-commerce dataset (3,400 rows x 28 columns)...")
    df = generate_dataset(3400)

    # Save as CSV
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print(f"[OK] Generated CSV: {CSV_PATH} ({len(df)} rows, {len(df.columns)} columns)")

    # Save as Excel XLSX
    try:
        df.to_excel(XLSX_PATH, index=False, engine="openpyxl", sheet_name="Orders_Intelligence")
        print(f"[OK] Generated Excel: {XLSX_PATH} ({len(df)} rows)")
    except Exception as e:
        print(f"[WARNING] Excel export warning: {e}")

    # Summary statistics
    print("\n--- DATASET PROFILE SUMMARY ---")
    print(f"Total Rows: {len(df):,}")
    print(f"Total Features / Columns: {len(df.columns)}")
    print("Columns List:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:02d}. {col}")

    print("\nSample Preview (first 3 rows):")
    print(df[["Order ID", "Order Date", "Product Title", "Size", "Color", "Selling Price", "Total Revenue"]].head(3))


if __name__ == "__main__":
    main()
