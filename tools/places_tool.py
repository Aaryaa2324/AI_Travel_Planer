
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLACES_FILE = PROJECT_ROOT / "data" / "places.json"


def load_places():
    with open(PLACES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def search_places(city, place_type=None, min_rating=0):
    places = load_places()
    matching_places = []

    for place in places:
        if place["city"].lower() != city.lower():
            continue

        if place_type and place["type"].lower() != place_type.lower():
            continue

        # Strictly greater than the requested rating
        if place["rating"] <= min_rating:
            continue

        matching_places.append(place)

    matching_places.sort(
        key=lambda place: place["rating"],
        reverse=True
    )

    return matching_places


def build_itinerary(city, number_of_days, min_rating=4.0):
    if number_of_days < 1:
        raise ValueError("Number of days must be at least 1.")

    places = search_places(city, min_rating=min_rating)

    itinerary = [
        {"day": day, "attractions": []}
        for day in range(1, number_of_days + 1)
    ]

    # Distribute attractions across the trip
    for index, place in enumerate(places):
        day_index = index % number_of_days
        itinerary[day_index]["attractions"].append(place)

    return itinerary


if __name__ == "__main__":
    results = search_places("Delhi", min_rating=4.0)

    print("\n========== TOURIST PLACES ==========\n")

    for place in results:
        print(f"Place Name : {place['name']}")
        print(f"City       : {place['city']}")
        print(f"Type       : {place['type']}")
        print(f"Rating     : {place['rating']}")
        print("-----------------------------------")

    print("\n===================================")

    print("\n========== 3-DAY ITINERARY ==========\n")

    itinerary = build_itinerary("Delhi", 3)

    for day in itinerary:
        print(f"\nDay {day['day']}")

        if day["attractions"]:
            for place in day["attractions"]:
                print(f"- {place['name']} (Rating: {place['rating']})")
        else:
            print("No qualifying attractions available.")

    print("\n====================================")
