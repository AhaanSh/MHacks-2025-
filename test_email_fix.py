import requests

url = "https://api.rentcast.io/v1/listings/rental/long-term?city=Austin&state=TX&status=Active&limit=1"

headers = {
    "accept": "application/json",
    "X-Api-Key": "8238e0150cdd4950b61e34f393b83bb6"
}

response = requests.get(url, headers=headers)

print(response.text)