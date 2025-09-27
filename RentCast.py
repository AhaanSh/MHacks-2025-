import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
import json

# Load environment variables from .env file
load_dotenv()

def get_sale_listings(city: str, state: str, limit: int = 500, **filters) -> pd.DataFrame:
    """
    Get sale listings from RentCast API.
    
    Args:
        city: City name
        state: State abbreviation  
        limit: Max results (up to 500)
        **filters: Additional filters like price, bedrooms, etc.
    
    Returns:
        DataFrame with raw sale listings data
    """
    
    # Load API key from .env
    API_KEY = os.getenv("RENTCAST_API_KEY")
    if not API_KEY:
        raise ValueError("RENTCAST_API_KEY missing from .env file")
    
    # Setup API request
    headers = {
        "Accept": "application/json", 
        "X-Api-Key": API_KEY
    }
    
    url = "https://api.rentcast.io/v1/listings/sale"
    
    # Base parameters
    params = {
        "city": city,
        "state": state, 
        "limit": limit,
        "offset": 0
    }
    
    # Add any additional filters
    params.update(filters)
    
    print(f"Fetching sale listings from {city}, {state}...")
    print(f"Requesting up to {limit} results")
    
    # Make API call
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Handle response format
        if isinstance(data, list):
            listings = data
        else:
            listings = data.get('data', [])
        
        print(f"Retrieved {len(listings)} listings")
        
        if not listings:
            print("No listings found")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(listings)
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return pd.DataFrame()

def flatten_nested_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten nested JSON objects into separate columns.
    
    Args:
        df: Raw DataFrame from API
        
    Returns:
        DataFrame with flattened nested data
    """
    
    if df.empty:
        return df
    
    df_flat = df.copy()
    
    # Flatten HOA data
    if 'hoa' in df_flat.columns:
        hoa_df = pd.json_normalize(df_flat['hoa'])
        hoa_df.columns = ['hoa_' + col for col in hoa_df.columns]
        df_flat = pd.concat([df_flat.drop('hoa', axis=1), hoa_df], axis=1)
    
    # Flatten listing agent data
    if 'listingAgent' in df_flat.columns:
        agent_df = pd.json_normalize(df_flat['listingAgent'])
        agent_df.columns = ['agent_' + col for col in agent_df.columns]
        df_flat = pd.concat([df_flat.drop('listingAgent', axis=1), agent_df], axis=1)
    
    # Flatten listing office data
    if 'listingOffice' in df_flat.columns:
        office_df = pd.json_normalize(df_flat['listingOffice'])
        office_df.columns = ['office_' + col for col in office_df.columns]
        df_flat = pd.concat([df_flat.drop('listingOffice', axis=1), office_df], axis=1)
    
    # Flatten builder data
    if 'builder' in df_flat.columns:
        builder_df = pd.json_normalize(df_flat['builder'])
        builder_df.columns = ['builder_' + col for col in builder_df.columns]
        df_flat = pd.concat([df_flat.drop('builder', axis=1), builder_df], axis=1)
    
    # Convert history to JSON string (too complex to flatten properly)
    if 'history' in df_flat.columns:
        df_flat['history'] = df_flat['history'].apply(
            lambda x: json.dumps(x) if x else None
        )
    
    return df_flat

def save_data(df: pd.DataFrame, city: str, state: str, formats: list = ['csv']):
    """
    Save DataFrame to specified formats.
    
    Args:
        df: DataFrame to save
        city: City name for filename
        state: State for filename
        formats: List of formats ['csv', 'excel', 'json']
    """
    
    if df.empty:
        print("No data to save")
        return
    
    # Create filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"{city.lower().replace(' ', '_')}_{state.lower()}_sale_listings_{timestamp}"
    
    print(f"Saving {len(df)} listings...")
    
    # Save CSV
    if 'csv' in formats:
        csv_file = f"{base_filename}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Saved CSV: {csv_file}")
    
    # Save Excel
    if 'excel' in formats:
        excel_file = f"{base_filename}.xlsx"
        df.to_excel(excel_file, index=False)
        print(f"Saved Excel: {excel_file}")
    
    # Save JSON
    if 'json' in formats:
        json_file = f"{base_filename}.json"
        df.to_json(json_file, orient='records', indent=2)
        print(f"Saved JSON: {json_file}")

def main():
    """
    Main function to extract RentCast sale listings data.
    """
    
    print("RentCast Sale Listings Data Extraction")
    print("=" * 50)
    
    # Configuration - modify as needed
    CITY = "Austin"
    STATE = "TX"
    LIMIT = 500  # Maximum per API call
    
    # Optional filters - uncomment/modify as needed
    filters = {
        'status': 'Active'  # Only active listings
        # 'price': '200000:800000',        # Price range
        # 'bedrooms': '2:*',               # 2+ bedrooms
        # 'propertyType': 'Single Family', # Property type
        # 'daysOld': '60'                  # Listed within 60 days
    }
    
    try:
        # Step 1: Get data from API
        raw_df = get_sale_listings(CITY, STATE, LIMIT, **filters)
        
        if raw_df.empty:
            print("No data retrieved. Exiting.")
            return
        
        # Step 2: Flatten nested data
        print("Flattening nested data...")
        clean_df = flatten_nested_data(raw_df)
        
        # Step 3: Save to files
        save_data(clean_df, CITY, STATE, ['csv', 'excel'])
        
        # Show basic info
        print(f"\nData Summary:")
        print(f"Total listings: {len(clean_df)}")
        print(f"Columns: {len(clean_df.columns)}")
        
        # Show column names
        print(f"\nColumns available:")
        for col in sorted(clean_df.columns):
            print(f"  {col}")
        
        print(f"\nData extraction complete!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()