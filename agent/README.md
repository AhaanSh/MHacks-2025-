# Rental Recommender Agent

Reads a CSV of property listings and recommends matches from natural-language criteria (budget, beds, city, HOA, etc.).
Implements the ASI Chat Protocol for interoperability and is discoverable on Agentverse.

## Inputs (free text)
Examples:
- "Max $2,000/mo in Austin, at least 2 beds, low HOA"
- "$450k budget in 94110, 3bd 2ba, >1500 sqft"

## Data columns
formattedAddress,addressLine1,city,state,zipCode,county,latitude,longitude,propertyType,bedrooms,bathrooms,squareFootage,status,price,listingType,listedDate,daysOnMarket,hoa_fee,agent_name,agent_phone,agent_email,office_name,office_phone,office_email,office_website

## Health
GET /ping → {"status":"ok", "agent_address": "..."}
