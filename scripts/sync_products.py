import requests
from supabase import create_client, Client
import os
import json
import logging

# Set up logging for better tracking
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
MEMBER_ID = os.environ.get("MEMBER_ID")
API_URL = os.environ.get("API_URL")

if not all([SUPABASE_URL, SUPABASE_KEY, MEMBER_ID, API_URL]):
    logging.error("Missing one or more required environment variables.")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to fetch products from iChannels API
def fetch_products():
    try:
        # Construct the API request URL for the product list
        # We use a static API_URL for now, assuming the API provides a product feed
        logging.info(f"Fetching products from API: {API_URL}")
        
        response = requests.get(API_URL)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        
        products_data = response.json()
        return products_data.get('items', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching products from API: {e}")
        return []

# Function to upsert data into Supabase
def upsert_products(products):
    if not products:
        logging.info("No products to upsert.")
        return
        
    # We will assume a product list with keys:
    # id, title, url, image, price, currency, stock, source, member_id
    
    # Add member_id to each product item for proper link generation
    for product in products:
        product['member_id'] = MEMBER_ID

    logging.info(f"Upserting {len(products)} products into Supabase...")
    
    # Use upsert to handle new products and update existing ones
    # The 'on_conflict' list should match the primary key column(s) in your table
    response = supabase.from_('products').upsert(products, on_conflict=['id']).execute()
    
    if response.data:
        logging.info(f"Successfully upserted {len(response.data)} products.")
    else:
        logging.error(f"Failed to upsert products. Response: {response.error}")

if __name__ == "__main__":
    products = fetch_products()
    if products:
        upsert_products(products)
    else:
        logging.warning("No products fetched. Exiting.")
