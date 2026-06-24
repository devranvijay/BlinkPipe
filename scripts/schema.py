"""Blinkit data platform — source schema definitions and reference data."""

CITIES = [
    {"city": "Mumbai",    "tier": 1, "state": "Maharashtra"},
    {"city": "Delhi",     "tier": 1, "state": "Delhi"},
    {"city": "Bangalore", "tier": 1, "state": "Karnataka"},
    {"city": "Hyderabad", "tier": 1, "state": "Telangana"},
    {"city": "Chennai",   "tier": 1, "state": "Tamil Nadu"},
    {"city": "Pune",      "tier": 1, "state": "Maharashtra"},
    {"city": "Jaipur",    "tier": 2, "state": "Rajasthan"},
    {"city": "Lucknow",   "tier": 2, "state": "Uttar Pradesh"},
    {"city": "Ahmedabad", "tier": 2, "state": "Gujarat"},
    {"city": "Kolkata",   "tier": 2, "state": "West Bengal"},
]

DARK_STORES = [
    {"store_id": "DS001", "city": "Mumbai",    "zone": "Andheri",      "lat": 19.1136, "lon": 72.8697},
    {"store_id": "DS002", "city": "Mumbai",    "zone": "Bandra",       "lat": 19.0596, "lon": 72.8295},
    {"store_id": "DS003", "city": "Mumbai",    "zone": "Powai",        "lat": 19.1197, "lon": 72.9051},
    {"store_id": "DS004", "city": "Delhi",     "zone": "Connaught",    "lat": 28.6315, "lon": 77.2167},
    {"store_id": "DS005", "city": "Delhi",     "zone": "Lajpat Nagar", "lat": 28.5680, "lon": 77.2439},
    {"store_id": "DS006", "city": "Delhi",     "zone": "Rohini",       "lat": 28.7177, "lon": 77.1062},
    {"store_id": "DS007", "city": "Bangalore", "zone": "Koramangala",  "lat": 12.9352, "lon": 77.6244},
    {"store_id": "DS008", "city": "Bangalore", "zone": "Indiranagar",  "lat": 12.9784, "lon": 77.6408},
    {"store_id": "DS009", "city": "Hyderabad", "zone": "Hitech City",  "lat": 17.4435, "lon": 78.3772},
    {"store_id": "DS010", "city": "Hyderabad", "zone": "Banjara Hills","lat": 17.4156, "lon": 78.4347},
    {"store_id": "DS011", "city": "Chennai",   "zone": "T Nagar",      "lat": 13.0418, "lon": 80.2341},
    {"store_id": "DS012", "city": "Chennai",   "zone": "Anna Nagar",   "lat": 13.0850, "lon": 80.2101},
    {"store_id": "DS013", "city": "Pune",      "zone": "Kothrud",      "lat": 18.5074, "lon": 73.8077},
    {"store_id": "DS014", "city": "Jaipur",    "zone": "Vaishali",     "lat": 26.9124, "lon": 75.7873},
    {"store_id": "DS015", "city": "Lucknow",   "zone": "Hazratganj",   "lat": 26.8467, "lon": 80.9462},
    {"store_id": "DS016", "city": "Ahmedabad", "zone": "CG Road",      "lat": 23.0274, "lon": 72.5650},
    {"store_id": "DS017", "city": "Kolkata",   "zone": "Park Street",  "lat": 22.5553, "lon": 88.3517},
]

PRODUCTS = [
    # Dairy
    {"product_id": "P001", "name": "Amul Full Cream Milk 1L",       "category": "Dairy",         "subcategory": "Milk",       "mrp": 67.0},
    {"product_id": "P002", "name": "Amul Butter 500g",               "category": "Dairy",         "subcategory": "Butter",     "mrp": 275.0},
    {"product_id": "P003", "name": "Mother Dairy Curd 400g",         "category": "Dairy",         "subcategory": "Curd",       "mrp": 45.0},
    {"product_id": "P004", "name": "Amul Paneer 200g",               "category": "Dairy",         "subcategory": "Paneer",     "mrp": 90.0},
    {"product_id": "P005", "name": "Amul Mozzarella Cheese 200g",    "category": "Dairy",         "subcategory": "Cheese",     "mrp": 160.0},
    # Bakery
    {"product_id": "P006", "name": "Britannia Whole Wheat Bread",    "category": "Bakery",        "subcategory": "Bread",      "mrp": 45.0},
    {"product_id": "P007", "name": "Modern Sandwich Bread 400g",     "category": "Bakery",        "subcategory": "Bread",      "mrp": 40.0},
    {"product_id": "P008", "name": "Britannia Good Day Biscuits",    "category": "Bakery",        "subcategory": "Biscuits",   "mrp": 35.0},
    {"product_id": "P009", "name": "Parle-G Biscuits 800g",          "category": "Bakery",        "subcategory": "Biscuits",   "mrp": 80.0},
    # Grocery
    {"product_id": "P010", "name": "Fortune Basmati Rice 5kg",       "category": "Grocery",       "subcategory": "Rice",       "mrp": 449.0},
    {"product_id": "P011", "name": "Aashirvaad Atta 5kg",            "category": "Grocery",       "subcategory": "Flour",      "mrp": 285.0},
    {"product_id": "P012", "name": "Tata Salt 1kg",                  "category": "Grocery",       "subcategory": "Salt",       "mrp": 28.0},
    {"product_id": "P013", "name": "Fortune Sunflower Oil 1L",       "category": "Grocery",       "subcategory": "Oil",        "mrp": 160.0},
    {"product_id": "P014", "name": "MDH Chana Masala 100g",          "category": "Grocery",       "subcategory": "Spices",     "mrp": 62.0},
    # Beverages
    {"product_id": "P015", "name": "Coca-Cola 2L",                   "category": "Beverages",     "subcategory": "Soft Drinks","mrp": 95.0},
    {"product_id": "P016", "name": "Tropicana Orange Juice 1L",      "category": "Beverages",     "subcategory": "Juice",      "mrp": 130.0},
    {"product_id": "P017", "name": "Red Bull Energy Drink 250ml",    "category": "Beverages",     "subcategory": "Energy",     "mrp": 125.0},
    {"product_id": "P018", "name": "Bisleri Water 1L",               "category": "Beverages",     "subcategory": "Water",      "mrp": 20.0},
    {"product_id": "P019", "name": "Nescafe Classic 100g",           "category": "Beverages",     "subcategory": "Coffee",     "mrp": 280.0},
    # Snacks
    {"product_id": "P020", "name": "Lay's Classic Salted 80g",       "category": "Snacks",        "subcategory": "Chips",      "mrp": 30.0},
    {"product_id": "P021", "name": "Kurkure Masala Munch 90g",       "category": "Snacks",        "subcategory": "Namkeen",    "mrp": 20.0},
    {"product_id": "P022", "name": "Haldiram Aloo Bhujia 200g",      "category": "Snacks",        "subcategory": "Namkeen",    "mrp": 75.0},
    {"product_id": "P023", "name": "Cadbury Dairy Milk 80g",         "category": "Snacks",        "subcategory": "Chocolate",  "mrp": 65.0},
    {"product_id": "P024", "name": "Maggi 2-Minute Noodles 280g",    "category": "Snacks",        "subcategory": "Noodles",    "mrp": 70.0},
    # Personal Care
    {"product_id": "P025", "name": "Dove Shampoo 340ml",             "category": "Personal Care", "subcategory": "Shampoo",    "mrp": 285.0},
    {"product_id": "P026", "name": "Colgate MaxFresh 200g",          "category": "Personal Care", "subcategory": "Toothpaste", "mrp": 115.0},
    {"product_id": "P027", "name": "Dettol Soap 75g x4",             "category": "Personal Care", "subcategory": "Soap",       "mrp": 120.0},
    {"product_id": "P028", "name": "Whisper Ultra Clean XL 30s",     "category": "Personal Care", "subcategory": "Hygiene",    "mrp": 285.0},
    {"product_id": "P029", "name": "Gillette Mach3 Razor",           "category": "Personal Care", "subcategory": "Grooming",   "mrp": 250.0},
    # Household
    {"product_id": "P030", "name": "Surf Excel Matic Top Load 1kg",  "category": "Household",     "subcategory": "Detergent",  "mrp": 240.0},
    {"product_id": "P031", "name": "Vim Dishwash Bar 200g",          "category": "Household",     "subcategory": "Cleaning",   "mrp": 42.0},
    {"product_id": "P032", "name": "Harpic Power Plus 500ml",        "category": "Household",     "subcategory": "Cleaning",   "mrp": 152.0},
    {"product_id": "P033", "name": "Good Knight Fast Card",          "category": "Household",     "subcategory": "Repellent",  "mrp": 65.0},
    # Fresh
    {"product_id": "P034", "name": "Banana 1kg",                     "category": "Fresh",         "subcategory": "Fruits",     "mrp": 60.0},
    {"product_id": "P035", "name": "Tomato 500g",                    "category": "Fresh",         "subcategory": "Vegetables", "mrp": 30.0},
    {"product_id": "P036", "name": "Onion 1kg",                      "category": "Fresh",         "subcategory": "Vegetables", "mrp": 45.0},
    {"product_id": "P037", "name": "Apple Shimla 1kg",               "category": "Fresh",         "subcategory": "Fruits",     "mrp": 180.0},
    # Electronics / Accessories
    {"product_id": "P038", "name": "boAt BassHeads 100 Earphones",   "category": "Electronics",   "subcategory": "Audio",      "mrp": 449.0},
    {"product_id": "P039", "name": "Syska USB-C Cable 1m",           "category": "Electronics",   "subcategory": "Cables",     "mrp": 299.0},
    {"product_id": "P040", "name": "Ambrane Power Bank 10000mAh",    "category": "Electronics",   "subcategory": "Power",      "mrp": 999.0},
]

ORDER_STATUSES = ["delivered", "delivered", "delivered", "delivered", "delivered",
                  "delivered", "delivered", "cancelled", "cancelled", "returned"]

HOURLY_WEIGHTS = [
    0.5, 0.3, 0.2, 0.1, 0.1, 0.2,  # 0–5 AM (night)
    0.8, 1.5, 2.0, 1.5, 1.2, 1.0,  # 6–11 AM (morning peak)
    1.8, 2.0, 1.5, 1.2, 1.0, 1.5,  # 12–17 (lunch peak)
    2.5, 3.0, 2.8, 2.2, 1.8, 1.2,  # 18–23 (evening peak)
]

WEEKDAY_MULTIPLIER = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.1, 4: 1.2, 5: 1.5, 6: 1.4}
