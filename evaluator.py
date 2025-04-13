from scraper.google_maps import fetch_restaurants, get_place_details
from scraper.reddit_scraper import search_reddit_reviews
from db.mongo_handler import save_restaurant
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
from pymongo import MongoClient
import os
import re

class RestaurantScraper:
    def __init__(self, lat: float, lng: float, radius: int = 1000, max_results: int = 60):
        self.lat = lat
        self.lng = lng
        self.radius = radius
        self.max_results = max_results
        self.best_restaurants = []
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_sentiment(self, text: str):
        """Analyze the sentiment of a single text."""
        score = self.analyzer.polarity_scores(text)["compound"]
        if score >= 0.05:
            sentiment = "Positive"
        elif score <= -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        return sentiment, score

    def analyze_reviews(self, reviews: list, source: str = "") -> list:
        """Analyze a list of reviews and return the enriched reviews."""
        analyzed = []
        for review in reviews:
            text = review.get("text", "")
            if text:
                sentiment, score = self.analyze_sentiment(text)
                analyzed.append({
                    "text": text,
                    "sentiment": sentiment,
                    "score": score,
                    "url": review.get("url", ""),
                    "user": review.get("user", ""),
                    "source": source
                })
        return analyzed

    def process_place(self, place: dict) -> dict:
        """Build a document with detailed place info and sentiment-analyzed reviews."""
        place_id = place.get("place_id")
        details = get_place_details(place_id)
        if not details:
            return None

        name = details.get("name", "")

        # Google Reviews
        google_raw = details.get("reviews", [])
        google_reviews = [{
            "text": r.get("text", ""),
            "url": r.get("author_url", ""),
            "user": r.get("author_name", "")
        } for r in google_raw]
        analyzed_google = self.analyze_reviews(google_reviews, source="Google")

        # Reddit Reviews
        reddit_raw = search_reddit_reviews(name, limit=5)
        reddit_reviews = [{
            "text": r.get("selftext") or r.get("title", ""),
            "url": r.get("url", ""),
            "user": r.get("author", "reddit_user")
        } for r in reddit_raw]
        analyzed_reddit = self.analyze_reviews(reddit_reviews, source="Reddit")

        # Final document
        return {
            "place_id": place_id,
            "name": name,
            "address": details.get("formatted_address", ""),
            "rating": details.get("rating", ""),
            "location": details.get("geometry", {}).get("location", {}),
            "google_reviews": analyzed_google,
            "reddit_reviews": analyzed_reddit
        }

    def run(self):
        """Run the scraper for all places within the given area."""
        restaurants = fetch_restaurants(self.lat, self.lng, radius=self.radius, max_results=self.max_results)
        for place in restaurants:
            document = self.process_place(place)
            if document:
                save_restaurant(document)
                print(f"Saved: {document['name']}")
            time.sleep(1)  # Friendly delay to avoid API spamming

    def is_relevant(self, restaurant: dict, keyword: str) -> bool:
        """Check if the keyword appears in the restaurant name or any of its reviews."""
        keyword = keyword.lower()
        name = restaurant.get("name", "").lower()
        google_reviews = restaurant.get("google_reviews", [])
        reddit_reviews = restaurant.get("reddit_reviews", [])

        name_match = keyword in name
        review_match = any(keyword in review.get("text", "").lower() for review in google_reviews + reddit_reviews)

        return name_match or review_match

    def get_best_restaurant(self, keyword: str, top_k: int = 3):
        """Find the best restaurant matching a keyword using Google rating + sentiment."""
        client = MongoClient(f"mongodb+srv://anhtriet:{os.getenv('Mongo_Pass')}@cluster0.qzyryex.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        db = client["restaurants_db"]
        collection = db["restaurants"]

        keyword_re = re.compile(keyword, re.IGNORECASE)

        matches = collection.find({
            "$or": [
                {"name": keyword_re},
                {"google_reviews.text": keyword_re},
                {"reddit_reviews.text": keyword_re}
            ]
        })

        scored_restaurants = []
        for r in matches:
            all_reviews = r.get("google_reviews", []) + r.get("reddit_reviews", [])
            if not all_reviews:
                continue
            avg_score = sum([rev.get("score", 0) for rev in all_reviews]) / len(all_reviews)
            google_rating = float(r.get("rating", 0))
            combined_score = (google_rating * 0.6) + (avg_score * 5 * 0.4)
            scored_restaurants.append((r["name"], combined_score, r))

        if not scored_restaurants:
            print("No matching restaurants found.")
            self.best_restaurants = []
            return None

        top_restaurants = sorted(scored_restaurants, key=lambda x: x[1], reverse=True)[:top_k]

        self.best_restaurants = [{
            "name": r[2]["name"],
            "google_rating": float(r[2].get("rating", 0)),
            "sentiment_score": round(r[1], 2),
            "address": r[2].get("address", "")
        } for r in top_restaurants]

        for entry in self.best_restaurants:
            print(f"\n🏆 {entry['name']}")
            print(f"⭐ Google Rating: {entry['google_rating']}")
            print(f"💬 Sentiment Score: {entry['sentiment_score']}")
            print(f"📍 Address: {entry['address']}")

        return [r[2] for r in top_restaurants]

# Entry point
if __name__ == "__main__":
    scraper = RestaurantScraper(lat=27.7172, lng=85.324)
    print("\n🔍 Searching for best nepali places...\n")
    scraper.get_best_restaurant("nepali")
    
    # Give name
    print(scraper.best_restaurants[0]["name"])
    # Give address
    print(scraper.best_restaurants[0]["address"])
    # Give google rating
    print(scraper.best_restaurants[0]["google_rating"])
    # Give review score
    print(scraper.best_restaurants[0]["sentiment_score"])
