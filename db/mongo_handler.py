from dotenv import load_dotenv, find_dotenv
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()


uri = f"mongodb+srv://anhtriet:{os.getenv('Mongo_Pass')}@cluster0.qzyryex.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Choose your database and collection
db = client["restaurants_db"]
collection = db["restaurants"]

def save_restaurant(data):
    """
    Save or update a restaurant document in MongoDB.
    Uniquely identified by its Google Place ID.
    """
    if not data.get("place_id"):
        raise ValueError("Data must include 'place_id'")

    result = collection.update_one(
        {"place_id": data["place_id"]},  # Match by unique Google Place ID
        {"$set": data},                  # Update with new data
        upsert=True                      # Insert if not found
    )
    return result

save_restaurant({
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "name": "Example Restaurant",
    "address": "123 Example St, City, Country",
    "rating": 2.4,
    "google_reviews": [],
    "location": {"lat": -33.867850, "lng": 151.207320},
    "reddit_reviews": []
})