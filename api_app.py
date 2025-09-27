import io
import json
import os
from typing import List, Annotated

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError

# --- Pydantic Schemas for Three Extraction Processes (Simplified 15 Categories) ---
class BasicData(BaseModel):
    address: str = Field(description="The primary street address line (from addressLine1).")
    location: str = Field(description="The city and state (from city, state, zipCode).")
    propertyType: str = Field(description="The type of property (e.g., Single Family, Condo).")
    sq_ft: int | None = Field(description="Total property square footage.")
    bedrooms: int | None = Field(description="Number of bedrooms.")
    bathrooms: float | None = Field(description="Number of bathrooms (e.g., 2.5).")
    status: str = Field(description="The listing status (e.g., Active, Pending).")
    listingType: str = Field(description="The listing type (e.g., Standard, Auction).")

class BasicExtraction(BaseModel):
    extracted_properties: List[BasicData]

class ListingData(BaseModel):
    price: int | None = Field(description="The current list price of the property.")
    daysOnMarket: int | None = Field(description="The number of days the property has been on the market.")
    hoa_fee: float | None = Field(description="The HOA fee amount.")
    agent_phone: str | None = Field(description="The agent's phone number.")


class ListingExtraction(BaseModel):
    extracted_properties: List[ListingData]

class AgentData(BaseModel):
    agent_name: str | None = Field(description="The agent's full name.")
    agent_email: str | None = Field(description="The agent's email address.")
    office_contact: str = Field(description="The office's name, phone, and website combined.")

class AgentExtraction(BaseModel):
    extracted_properties: List[AgentData]


# --- FastAPI Application Setup ---
app = FastAPI(
    title="Gemini Multi-Process Data Parser API",
    description="API with separate endpoints for reliable, parallelized extraction of 15 key property fields."
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

try:
    client = genai.Client()
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None

# --- Helper Function for Common Logic (Chunking) ---

async def run_extraction(df: pd.DataFrame, schema: BaseModel, endpoint_name: str):
    CHUNK_SIZE = 100 
    all_extracted_data = []
    
    target_fields = ", ".join(schema.model_fields.keys())

    system_prompt = (
        f"You are an expert data parsing and consolidation tool. Analyze the provided JSON list of property records and "
        f"extract ONLY the following fields: {target_fields}. Consolidate related input columns (e.g., city, state, zipCode into 'location'). "
        "The output MUST be a JSON array of objects that strictly conforms to the provided schema. Do not include any text outside the JSON block."
    )

    for i in range(0, len(df), CHUNK_SIZE):
        df_chunk = df.iloc[i:i + CHUNK_SIZE]
        data_for_llm_chunk = df_chunk.to_json(orient='records')

        contents = [
            {"role": "user", "parts": [
                {"text": system_prompt},
                {"text": f"\n\nDATA TO PARSE:\n{data_for_llm_chunk}"}
            ]}
        ]

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )
            
            chunk_data = json.loads(response.text)
            all_extracted_data.extend(chunk_data['extracted_properties'])

        except APIError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Gemini API Error in {endpoint_name} processing chunk {i//CHUNK_SIZE}: {e.message}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"JSON Formatting Error in {endpoint_name} (Chunk {i//CHUNK_SIZE}): {str(e)}"
            )

    return {"extracted_properties": all_extracted_data}

# --- Core Request Handler (File Upload/Pandas Logic) ---

async def handle_file_upload(file: UploadFile, schema: BaseModel, endpoint_name: str):
    if client is None:
        raise HTTPException(
            status_code=500, 
            detail="Gemini API Key Error: Client failed to initialize. Check GEMINI_API_KEY environment variable."
        )
    
    file_content = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file_content.decode("utf-8")))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file content: {e}")
        
    return await run_extraction(df, schema, endpoint_name)


# ----------------------------------------------------------------------
# ENDPOINT 1: ROOT INTERFACE (HTML)
# ----------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "title": "Gemini Property Data Extractor (3 Processes)",
            "endpoints": {
                "basic": "/api/v1/extract_basic_data",
                "listing": "/api/v1/extract_listing_details",
                "agent": "/api/v1/extract_agent_details"
            }
        }
    )

# ----------------------------------------------------------------------
# ENDPOINT 2: BASIC DETAILS EXTRACTION
# ----------------------------------------------------------------------

@app.post("/api/v1/extract_basic_data", response_model=BasicExtraction)
async def extract_basic_data(
    file: Annotated[UploadFile, File(description="File for Basic Property Details (8 fields).")]
):
    return await handle_file_upload(file, BasicExtraction, "Basic Details")

# ----------------------------------------------------------------------
# ENDPOINT 3: LISTING DETAILS EXTRACTION
# ----------------------------------------------------------------------

@app.post("/api/v1/extract_listing_details", response_model=ListingExtraction)
async def extract_listing_details(
    file: Annotated[UploadFile, File(description="File for Listing and Financial Details (4 fields).")]
):
    return await handle_file_upload(file, ListingExtraction, "Listing Details")

# ----------------------------------------------------------------------
# ENDPOINT 4: AGENT DETAILS EXTRACTION
# ----------------------------------------------------------------------

@app.post("/api/v1/extract_agent_details", response_model=AgentExtraction)
async def extract_agent_details(
    file: Annotated[UploadFile, File(description="File for Agent and Office Contact Details (3 fields).")]
):
    return await handle_file_upload(file, AgentExtraction, "Agent Details")

# ----------------------------------------------------------------------

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)