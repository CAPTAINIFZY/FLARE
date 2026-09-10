import asyncio
import os
import httpx
import sys

async def test_apify():
    api_token = os.getenv("APIFY_API_TOKEN", "")
    actor_id = "logiover~google-flights-scraper"
    base_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
    
    payload = {
        "legs": [
            {
                "origin": "DEL",
                "destination": "BOM",
                "date": "2024-12-15"
            }
        ],
        "adults": 1,
        "cabinClass": "economy",
        "currency": "INR"
    }

    params = {
        "token": api_token
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Sending request to Apify...")
        response = await client.post(base_url, params=params, json=payload)
        print(response.status_code)
        
        try:
            items = response.json()
            if isinstance(items, list) and len(items) > 0:
                print("First item keys:", items[0].keys())
                print("First item:", items[0])
            else:
                print("Response:", items)
        except Exception as e:
            print("Error parsing JSON:", e)
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_apify())
