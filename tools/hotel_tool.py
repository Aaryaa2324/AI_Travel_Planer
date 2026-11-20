import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

HOTELS_FILE = PROJECT_ROOT / "data" / "hotels.json"


def load_hotels():

    with open(HOTELS_FILE, "r", encoding="utf-8") as file:
        hotels = json.load(file)

    return hotels

def search_hotels(city, min_stars=1):

    hotels = load_hotels()

    matching_hotels = []

    for hotel in hotels:

        if (
            hotel["city"].lower() == city.lower()
            and hotel["stars"] >= min_stars
        ):
            matching_hotels.append(hotel)

    matching_hotels.sort(
        key=lambda hotel: hotel["price_per_night"]
    )

    return matching_hotels

if __name__ == "__main__":

    results = search_hotels("Delhi", 3)

    print("\n========== HOTEL SEARCH RESULTS ==========\n")

    if results:

        for hotel in results:

            print(f"Hotel Name : {hotel['name']}")
            print(f"City       : {hotel['city']}")
            print(f"Stars      : {hotel['stars']}")
            print(f"Price      : ₹{hotel['price_per_night']} per night")
            print(f"Amenities  : {', '.join(hotel['amenities'])}")

            print("-----------------------------------------")

    else:
        print("No hotels found.")
        