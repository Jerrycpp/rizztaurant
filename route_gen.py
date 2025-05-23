from dotenv import load_dotenv, find_dotenv
import os
import googlemaps
import time
from datetime import datetime
import ast
from bs4 import BeautifulSoup
import folium
import polyline


load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("Google_Key"))

# Hardcoded values for the GPS location and camera orientation
latitude = 32.727496  # Latitude of the statue (example: University of Texas at Arlington)
longitude = -97.111582  # Longitude of the statue

def remove_html_tags(text):
    # Parse the HTML content and remove tags
    soup = BeautifulSoup(text, "html.parser")
    clean_text = soup.get_text()
    return clean_text

class WalkingRoute:
    def __init__(self, latitude, longitude, destination_name):
        self.latitude = latitude
        self.longitude = longitude
        self.origin = self._find_closest_address()
        self.destination = self._get_corrected_place_name(destination_name)
        self.leg_data = {}
        self.polyline = ""

    def _find_closest_address(self):
        reverse_geocode_result = gmaps.reverse_geocode(
            (self.latitude, self.longitude),
            result_type=['street_address'],
            location_type='ROOFTOP'
        )
        return reverse_geocode_result[0]['formatted_address']

    def _get_corrected_place_name(self, place_name):
        places = gmaps.places(query=place_name)
        result = places['results'][0]
        return result['formatted_address']

    def fetch_route(self):
        directions = gmaps.directions(
            self.origin,
            self.destination,
            mode="walking",
            departure_time="now",
        )

        if not directions:
            raise ValueError("No route found.")

        route = directions[0]
        self.polyline = route['overview_polyline']['points']
        leg = route['legs'][0]

        self.leg_data = {
            "start_address": remove_html_tags(leg["start_address"]),
            "end_address": remove_html_tags(leg["end_address"]),
            "duration": remove_html_tags(leg["duration"]["text"]),
            "distance": remove_html_tags(leg["distance"]["text"]),
            "steps": []
        }

        for step in leg["steps"]:
            step_data = {
                "instruction": remove_html_tags(step["html_instructions"]),
                "distance": remove_html_tags(step["distance"]["text"]),
                "duration": remove_html_tags(step["duration"]["text"]),
            }
            self.leg_data["steps"].append(step_data)

    def display_directions(self):
        print("=== WALKING DIRECTIONS ===")
        print(f"From: {self.leg_data['start_address']}")
        print(f"To:   {self.leg_data['end_address']}")
        print(f"Total Distance: {self.leg_data['distance']}")
        print(f"Estimated Time: {self.leg_data['duration']}\n")

        print("Steps:")
        for i, step in enumerate(self.leg_data["steps"], start=1):
            print(f"{i}. {step['instruction']}")
            print(f"   → Distance: {step['distance']}, Time: {step['duration']}\n")

    def display_route(self):
        # Your encoded polyline
        encoded_polyline = self.polyline

        # Decode polyline into list of (lat, lon) tuples
        decoded_points = polyline.decode(encoded_polyline)

        # Get center of the path for initial map focus
        center_lat, center_lng = decoded_points[len(decoded_points)//2]

        # Create a folium map centered at the midpoint
        m = folium.Map(location=[center_lat, center_lng], zoom_start=15)

        # Add polyline to the map
        folium.PolyLine(decoded_points, color="blue", weight=5, opacity=0.8).add_to(m)

        # Add markers at the start and end
        folium.Marker(decoded_points[0], tooltip="Start", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(decoded_points[-1], tooltip="End", icon=folium.Icon(color='red')).add_to(m)

        # Save to HTML and open in browser
        m.save("polyline_map.html")
        print("Map has been saved as 'polyline_map.html'")

def main():
    latitude = 32.727496
    longitude = -97.111582
    destination_name = "Zio Al's Pizza"

    route = WalkingRoute(latitude, longitude, destination_name)
    route.fetch_route()
    route.display_directions()
    print(route.polyline)
    route.display_route()

if __name__ == "__main__":
    main()