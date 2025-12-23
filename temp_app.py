import os
import atexit
import psycopg2
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from aliexpress_api import AliexpressApi, models
from apscheduler.schedulers.background import BackgroundScheduler

# --- CONFIGURATION ---
app = Flask(__name__)
CORS(app)

# SECURITY NOTE: These keys come from your .env file.
DB_URL = os.getenv("DATABASE_URL")
ALI_KEY = os.getenv("ALI_KEY")
ALI_SECRET = os.getenv("ALI_SECRET")
TRACKING_ID = "ai_store_bot_v1"

# Initialize AliExpress API
aliexpress = AliexpressApi(ALI_KEY, ALI_SECRET, models.Language.EN, models.Currency.EUR, TRACKING_ID)

# --- DATABASE SETUP ---
def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                external_id VARCHAR(50) UNIQUE,
                title TEXT NOT NULL,
                price VARCHAR(20),
                image_url TEXT,
                affiliate_link TEXT,
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ SYSTEM: Database connection established.")
    except Exception as e:
        print(f"❌ SYSTEM ERROR: Database connection failed. {e}")

# --- THE AUTOMATED AI TASK (24/7 AGENT) ---
def scheduled_market_scan():
    """This function runs automatically every 6 hours."""
    print("⏰ AI WAKE UP: Starting scheduled market scan...")
    keywords = ["smart watch", "wireless earbuds", "drone", "gaming accessories"]
    
    # Pick a random category to keep store fresh
    import random
    selected_keyword = random.choice(keywords)
    
    try:
        # Scan AliExpress
        response = aliexpress.get_products(
            keywords=selected_keyword, 
            max_sale_price=10000, 
            page_size=5
        )
        
        # Save to DB
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        count = 0
        for item in response.products:
            # Generate Link
            link = item.promotion_link if hasattr(item, 'promotion_link') else item.product_detail_url
            
            cur.execute("""
                INSERT INTO products (external_id, title, price, image_url, affiliate_link, category)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_id) DO NOTHING;
            """, (str(item.product_id), item.product_title, item.target_sale_price, item.product_main_image_url, link, selected_keyword))
            count += 1
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ AI UPDATE: Added {count} new items for '{selected_keyword}'.")
        
    except Exception as e:
        print(f"⚠️ AI WARNING: Scan failed. {e}")

# Start the Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_market_scan, trigger="interval", hours=6)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# --- WEBSITE ROUTES ---

@app.route('/')
def home():
    """Serves your HTML file"""
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    """Frontend asks for products here"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT title, price, image_url, affiliate_link, category FROM products ORDER BY created_at DESC LIMIT 50;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                "name": row[0],
                "price": row[1],
                "img": row[2],
                "link": row[3],
                "tag": row[4]
            })
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    init_db()
    # Run first scan immediately on startup so store isn't empty
    scheduled_market_scan()
    app.run(host='0.0.0.0', port=8080)