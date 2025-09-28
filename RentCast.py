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
    """
    API_KEY = os.getenv("RENTCAST_API_KEY")
    if not API_KEY:
        raise ValueError("RENTCAST_API_KEY missing from .env file")
    
    headers = {
        "Accept": "application/json", 
        "X-Api-Key": API_KEY
    }
    url = "https://api.rentcast.io/v1/listings/sale"
    params = {"city": city, "state": state, "limit": limit, "offset": 0}
    params.update(filters)
    
    print(f"Fetching sale listings from {city}, {state}...")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        listings = data if isinstance(data, list) else data.get("data", [])
        print(f"Retrieved {len(listings)} listings")
        return pd.DataFrame(listings)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return pd.DataFrame()

def flatten_nested_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten nested JSON objects into separate columns.
    """
    if df.empty:
        return df
    
    df_flat = df.copy()
    
    if "hoa" in df_flat.columns:
        hoa_df = pd.json_normalize(df_flat["hoa"])
        hoa_df.columns = ["hoa_" + col for col in hoa_df.columns]
        df_flat = pd.concat([df_flat.drop("hoa", axis=1), hoa_df], axis=1)
    
    if "listingAgent" in df_flat.columns:
        agent_df = pd.json_normalize(df_flat["listingAgent"])
        agent_df.columns = ["agent_" + col for col in agent_df.columns]
        df_flat = pd.concat([df_flat.drop("listingAgent", axis=1), agent_df], axis=1)
    
    if "listingOffice" in df_flat.columns:
        office_df = pd.json_normalize(df_flat["listingOffice"])
        office_df.columns = ["office_" + col for col in office_df.columns]
        df_flat = pd.concat([df_flat.drop("listingOffice", axis=1), office_df], axis=1)
    
    if "builder" in df_flat.columns:
        builder_df = pd.json_normalize(df_flat["builder"])
        builder_df.columns = ["builder_" + col for col in builder_df.columns]
        df_flat = pd.concat([df_flat.drop("builder", axis=1), builder_df], axis=1)
    
    if "history" in df_flat.columns:
        df_flat["history"] = df_flat["history"].apply(
            lambda x: json.dumps(x) if x else None
        )
    
    return df_flat

def select_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the desired 38 columns and rename them consistently.
    """
    col_map = {
        "id": "id",
        "formattedAddress": "formattedAddress",
        "addressLine1": "addressLine1",
        "addressLine2": "addressLine2",
        "city": "city",
        "state": "state",
        "stateFips": "stateFips",
        "zipCode": "zipCode",
        "county": "county",
        "countyFips": "countyFips",
        "latitude": "latitude",
        "longitude": "longitude",
        "propertyType": "propertyType",
        "bedrooms": "bedrooms",
        "bathrooms": "bathrooms",
        "squareFootage": "squareFootage",
        "lotSize": "lotSize",
        "yearBuilt": "yearBuilt",
        "status": "status",
        "price": "price",
        "listingType": "listingType",
        "listedDate": "listedDate",
        "removedDate": "removedDate",
        "createdDate": "createdDate",
        "lastSeenDate": "lastSeenDate",
        "daysOnMarket": "daysOnMarket",
        "mlsName": "mlsName",
        "mlsNumber": "mlsNumber",
        "history": "history",
        "hoa_fee": "hoa_fee",
        "agent_name": "agent_name",
        "agent_phone": "agent_phone",
        "agent_email": "agent_email",
        "agent_website": "agent_website",
        "office_name": "office_name",
        "office_phone": "office_phone",
        "office_email": "office_email",
        "office_website": "office_website",
    }

    df_out = df.rename(columns=col_map)
    keep_cols = list(col_map.values())
    for col in keep_cols:
        if col not in df_out.columns:
            df_out[col] = None
    return df_out[keep_cols]

def save_data(df: pd.DataFrame, city: str, state: str, formats: list = ["csv"]):
    """
    Save DataFrame to specified formats.
    """
    if df.empty:
        print("No data to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{city.lower().replace(' ', '_')}_{state.lower()}_sale_listings_{timestamp}"
    
    if "csv" in formats:
        csv_file = f"{base_filename}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Saved CSV: {csv_file}")
    
    if "excel" in formats:
        excel_file = f"{base_filename}.xlsx"
        df.to_excel(excel_file, index=False)
        print(f"Saved Excel: {excel_file}")
    
    if "json" in formats:
        json_file = f"{base_filename}.json"
        df.to_json(json_file, orient="records", indent=2)
        print(f"Saved JSON: {json_file}")

def main():
    print("RentCast Sale Listings Data Extraction")
    print("=" * 50)
    
    CITY = "Ann Arbor"
    STATE = "MI"
    LIMIT = 500
    filters = {"status": "Active"}
    
    try:
        raw_df = get_sale_listings(CITY, STATE, LIMIT, **filters)
        if raw_df.empty:
            print("No data retrieved. Exiting.")
            return
        
        print("Flattening nested data...")
        clean_df = flatten_nested_data(raw_df)
        
        print("Selecting standard columns...")
        final_df = select_and_rename_columns(clean_df)
        
        save_data(final_df, CITY, STATE, ["csv", "excel"])
        
        print(f"\nData Summary:")
        print(f"Total listings: {len(final_df)}")
        print(f"Columns: {len(final_df.columns)}")
        print("\nColumns returned:")
        for col in final_df.columns:
            print(f"  {col}")
        
        print("\nData extraction complete!")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
