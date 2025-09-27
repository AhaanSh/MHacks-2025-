import io
import json
import os
from typing import List, Annotated

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError

# --- Pydantic Schema for Structured Output ---
class PropertyData(BaseModel):
    """A structured model for a single extracted property record."""
    # Price field has been removed as it is not directly available in the input CSV.
    sq_ft: int = Field(description="The property's square footage, converted to an integer (using 'squareFootage' column).")
    location: str = Field(description="The complete formatted address, city, state, and zip code (using 'formattedAddress' column).")

class ExtractedData(BaseModel):
    extracted_properties: List[PropertyData] = Field(description="List of property records extracted by the AI.")


# --- FastAPI Application Setup ---
app = FastAPI(
    title="Gemini Property Data Parser API",
    description="API to upload a CSV/Excel file and use Gemini to extract structured property data."
)

# 1. Configure Static Files (for CSS/JS/images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Configure Templates (for HTML files)
templates = Jinja2Templates(directory="templates")

# 3. Initialize the Gemini Client
try:
    client = genai.Client()
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None


# ----------------------------------------------------------------------
# ENDPOINT 1: ROOT INTERFACE (HTML)
# ----------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the main interactive file upload page."""
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "title": "Gemini Property Data Extractor",
            "endpoint_url": "/api/v1/parse_property_data" 
        }
    )

# ----------------------------------------------------------------------
# ENDPOINT 2: DATA PARSING API (POST request handler)
# ----------------------------------------------------------------------

@app.post("/api/v1/parse_property_data", response_model=ExtractedData)
async def parse_property_data_endpoint(
    file: Annotated[UploadFile, File(description="Excel (.xlsx, .xls) or CSV file with property data.")]
):
    """
    Accepts an uploaded Excel or CSV file, reads the data using Pandas, 
    and uses the Gemini API with structured output to extract 
    Square Footage and Location from each record.
    """
    if client is None:
        raise HTTPException(
            status_code=500, 
            detail="Gemini API Key Error: Client failed to initialize. Check GEMINI_API_KEY environment variable."
        )

    # --- File Reading (Pandas) ---
    file_content = await file.read()
    filename = file.filename.lower()
    df: pd.DataFrame
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file_content.decode("utf-8")))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Please upload a CSV or Excel (xlsx/xls) file."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file content: {e}")

    data_for_llm = df.to_json(orient='records')

    # --- Gemini Prompt Engineering (Updated) ---
    system_prompt = (
        "You are an expert data parsing and cleansing tool. Analyze the provided JSON list of "
        "property records. Extract the 'sq_ft' (as a number) and 'location' (city and state/country) "
        "for every entry. Be intelligent about identifying and cleaning the data fields. "
        "The output MUST be a JSON array of objects that strictly conforms to the provided schema. Do not include any text outside the JSON block."
    )
    
    contents = [
        {"role": "user", "parts": [
            {"text": system_prompt},
            {"text": f"\n\nDATA TO PARSE:\n{data_for_llm}"}
        ]}
    ]

    # --- Gemini API Call with Structured Output ---
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": ExtractedData, 
            },
        )
        
        return json.loads(response.text)

    except APIError as e:
        raise HTTPException(
            status_code=502, 
            detail=f"Gemini API Error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal Server Error: {e}"
        )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)