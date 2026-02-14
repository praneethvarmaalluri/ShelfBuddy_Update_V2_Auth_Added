import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create products table (if it doesn't exist)
c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    shelf_life_room_closed INTEGER,
    shelf_life_room_opened INTEGER,
    shelf_life_refrigerated_closed INTEGER,
    shelf_life_refrigerated_opened INTEGER,
    shelf_life_frozen_closed INTEGER,
    shelf_life_frozen_opened INTEGER
)
''')

# --- Master Product List ---
# This list is consolidated and corrected based on your request.
# 3650 = 10 Years (for "indefinite" items)
# 0 = Not Recommended / Unsafe

master_product_list = [
    # (Name, Cat, Room-C, Room-O, Ref-C, Ref-O, Fro-C, Fro-O)

    # --- Food: Pantry Staples ---
    ("Rice", "food", 180, 90, 365, 180, 0, 0),
    ("Wheat Flour (Atta)", "food", 180, 60, 365, 180, 730, 365),
    ("Sugar", "food", 3650, 3650, 3650, 3650, 0, 0),
    ("Salt", "food", 3650, 3650, 3650, 3650, 0, 0),
    ("Cooking Oil (Vegetable)", "food", 365, 180, 0, 0, 0, 0),
    ("Ghee", "food", 365, 180, 365, 180, 0, 0),
    ("Lentils (Dal)", "food", 365, 180, 365, 180, 0, 0),
    ("Chickpeas (Dry)", "food", 730, 365, 730, 365, 0, 0),
    ("Kidney Beans (Rajma)", "food", 730, 365, 730, 365, 0, 0),
    ("Tea Powder", "food", 365, 180, 365, 180, 0, 0),
    ("Coffee Powder", "food", 365, 60, 365, 60, 0, 0),
    ("Dry Fruits (Almonds, Cashews)", "food", 180, 60, 365, 180, 0, 0),
    ("Peanuts", "food", 180, 60, 365, 180, 0, 0),
    
    # --- Food: Dairy & Perishables ---
    ("Butter", "food", 1, 0, 180, 30, 365, 180),
    ("Milk", "food", 0, 0, 5, 3, 0, 0), # Based on pasteurized milk (worst-case)
    ("Curd (Yogurt)", "food", 0, 0, 14, 5, 0, 0),
    ("Cheese (Hard Block)", "food", 0, 0, 180, 30, 240, 180),
    ("Paneer", "food", 0, 0, 5, 2, 90, 30),
    ("Eggs", "food", 7, 0, 30, 0, 0, 0),

    # --- Food: Meat & Fish ---
    ("Fish (Raw)", "food", 0, 0, 2, 2, 240, 120),
    ("Chicken (Raw)", "food", 0, 0, 2, 2, 365, 180),
    ("Mutton (Raw)", "food", 0, 0, 3, 3, 365, 180),

    # --- Food: Produce ---
    ("Onion", "food", 30, 14, 60, 14, 0, 0),
    ("Potato", "food", 60, 0, 0, 0, 0, 0),
    ("Tomato", "food", 7, 0, 14, 7, 0, 0),
    ("Garlic", "food", 120, 30, 120, 30, 365, 180),
    ("Ginger", "food", 21, 0, 30, 14, 180, 180),
    ("Coconut (Fresh)", "food", 2, 0, 7, 3, 180, 30),
    ("Coconut (Dry)", "food", 180, 90, 365, 180, 0, 0),

    # --- Food: Snacks & Condiments ---
    ("Bread", "food", 5, 5, 14, 14, 90, 30),
    ("Biscuits (Dry)", "food", 180, 30, 0, 0, 0, 0),
    ("Snacks (Namkeen)", "food", 120, 14, 0, 0, 0, 0),
    ("Pickles (Achar)", "food", 365, 180, 365, 180, 0, 0),
    ("Jam (Fruit)", "food", 365, 0, 365, 90, 0, 0),
    ("Honey", "food", 3650, 3650, 3650, 3650, 0, 0),
    ("Jaggery (Gud)", "food", 180, 90, 365, 180, 0, 0),
    ("Tamarind (Block/Paste)", "food", 365, 180, 365, 180, 0, 0),

    # --- Food: Spices ---
    ("Spices (Whole, e.g. Cumin)", "food", 730, 365, 730, 365, 0, 0),
    ("Spices (Powder, e.g. Turmeric)", "food", 365, 180, 365, 180, 0, 0),
    ("Chilli Powder", "food", 365, 180, 730, 365, 0, 0),
    
    # --- Food: Frozen & Drinks ---
    ("Frozen Vegetables", "food", 0, 0, 0, 0, 365, 30),
    ("Frozen Paratha", "food", 0, 0, 0, 0, 270, 30),
    ("Ice Cream", "food", 0, 0, 0, 0, 270, 0), # Loses quality, don't refreeze
    ("Soft Drinks (Sealed)", "food", 270, 0, 270, 3, 0, 0),
    ("Juice (UHT/Packaged)", "food", 180, 0, 180, 7, 0, 0),
    ("Instant Noodles (Dry)", "food", 365, 365, 0, 0, 0, 0),

    # --- Medicine ---
    ("Paracetamol (Tablets)", "medicine", 730, 365, 730, 365, 0, 0),
    ("Cough Syrup", "medicine", 730, 180, 730, 180, 0, 0),
    ("Antibiotic (Tablets)", "medicine", 730, 0, 730, 0, 0, 0),
    ("Pain Relief Balm", "medicine", 730, 365, 730, 365, 0, 0),
    ("Antacid (Tablets)", "medicine", 730, 365, 730, 365, 0, 0),
    ("Multivitamin (Tablets)", "medicine", 730, 365, 730, 365, 0, 0),
    ("Eye Drops", "medicine", 730, 30, 730, 30, 0, 0),
    ("Insulin (Unopened)", "medicine", 0, 0, 365, 30, 0, 0),
    ("Antiseptic Cream", "medicine", 730, 365, 730, 365, 0, 0),
    ("Bandages (Sterile)", "medicine", 1095, 0, 1095, 0, 0, 0),
    ("Antiseptic Liquid", "medicine", 730, 365, 730, 365, 0, 0),
    ("Pain Relief Spray", "medicine", 730, 730, 730, 730, 0, 0),
    ("Nasal Spray", "medicine", 730, 90, 730, 90, 0, 0),
    ("ORS Powder (Sachet)", "medicine", 730, 0, 730, 0, 0, 0),
    ("ORS (Reconstituted)", "medicine", 1, 1, 1, 1, 0, 0),
    ("Allergy Tablets", "medicine", 730, 365, 730, 365, 0, 0),

    # --- Personal Care ---
    ("Toothpaste", "personal_care", 730, 365, 0, 0, 0, 0),
    ("Toothbrush", "personal_care", 3650, 0, 3650, 0, 0, 0),
    ("Shampoo", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Hair Oil", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Face Wash", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Soap (Bar)", "personal_care", 1095, 1095, 0, 0, 0, 0),
    ("Body Lotion", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Deodorant", "personal_care", 1095, 1095, 0, 0, 0, 0),
    ("Perfume", "personal_care", 1095, 730, 0, 0, 0, 0),
    ("Lip Balm", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Sunscreen", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Moisturizer", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Shaving Cream", "personal_care", 1095, 365, 0, 0, 0, 0),
    ("Razor Blades", "personal_care", 3650, 0, 3650, 0, 0, 0),
    ("Sanitary Pads", "personal_care", 1095, 0, 1095, 0, 0, 0),
    ("Hand Sanitizer", "personal_care", 730, 365, 0, 0, 0, 0),

    # --- Household ---
    ("Detergent (Powder)", "household", 365, 180, 0, 0, 0, 0),
    ("Dishwash Liquid", "household", 365, 180, 0, 0, 0, 0),
    ("Floor Cleaner", "household", 730, 365, 0, 0, 0, 0),
    ("Bleach", "household", 365, 180, 0, 0, 0, 0),
    ("Toilet Cleaner", "household", 730, 365, 0, 0, 0, 0),
    ("Air Freshener", "household", 730, 730, 0, 0, 0, 0),
    ("Garbage Bags", "household", 3650, 3650, 0, 0, 0, 0),
    ("Mosquito Repellent", "household", 730, 730, 0, 0, 0, 0),
    ("Batteries (Alkaline)", "household", 2555, 0, 0, 0, 0, 0),
    ("Candles", "household", 3650, 3650, 0, 0, 0, 0),
    ("Matchsticks", "household", 3650, 3650, 0, 0, 0, 0),
    ("Tissue Paper", "household", 3650, 3650, 0, 0, 0, 0),
    ("Aluminium Foil", "household", 3650, 3650, 0, 0, 0, 0)
]


# --- Insert all products from the master list ---
try:
    c.executemany('''
    INSERT OR IGNORE INTO products (
        name, category,
        shelf_life_room_closed, shelf_life_room_opened,
        shelf_life_refrigerated_closed, shelf_life_refrigerated_opened,
        shelf_life_frozen_closed, shelf_life_frozen_opened
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', master_product_list)
    
    # Get the number of rows actually inserted
    inserted_count = c.rowcount
    conn.commit()
    
    # Provide a clear, accurate report
    print(f"Database population complete.")
    print(f"Total items in master list: {len(master_product_list)}")
    print(f"Successfully inserted {inserted_count} new unique items.")

except sqlite3.Error as e:
    print(f"An error occurred: {e}")
    conn.rollback() # Roll back changes if an error occurs

finally:
    conn.close()
    print("Database connection closed.")
