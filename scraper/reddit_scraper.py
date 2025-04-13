import requests

def search_reddit_reviews(query, limit=5):
    url = (
        "https://api.pushshift.io/reddit/search/submission/"
        f"?q={query}&size={limit}&sort=desc"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return []
    
    results = response.json().get("data", [])
    reviews = []

    for post in results:
        reviews.append({
            "title": post.get("title"),
            "selftext": post.get("selftext", ""),
            "url": f"https://reddit.com{post.get('permalink')}"
        })

    return reviews
