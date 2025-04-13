import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()
GOOGLE_API_KEY = os.getenv("Google_Key")

def fetch_restaurants(lat, lng, radius=1000, max_results=60):
    all_restaurants = []
    seen_place_ids = set()

    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=restaurant&key={GOOGLE_API_KEY}"
    while url and len(all_restaurants) < max_results:
        response = requests.get(url)
        data = response.json()

        if "results" in data:
            for place in data["results"]:
                if place["place_id"] not in seen_place_ids:
                    all_restaurants.append(place)
                    seen_place_ids.add(place["place_id"])

        next_page_token = data.get("next_page_token")
        if next_page_token:
            time.sleep(2)  # <-- Wait for token to become active
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={next_page_token}&key={GOOGLE_API_KEY}"
        else:
            break

    return all_restaurants[:max_results]

def get_place_details(place_id):
    url = (
        "https://maps.googleapis.com/maps/api/place/details/json?"
        f"place_id={place_id}&fields=name,rating,formatted_address,reviews,geometry&key={GOOGLE_API_KEY}"
    )
    response = requests.get(url)
    return response.json().get("result")
