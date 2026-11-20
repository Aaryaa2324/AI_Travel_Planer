import json
from pathlib import Path
from datetime import datetime

# Find the project folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Locate flights.json
FLIGHTS_FILE = PROJECT_ROOT / "data" / "flights.json"


def load_flights():
    with open(FLIGHTS_FILE, "r", encoding="utf-8") as file:
        flights = json.load(file)

    return flights

def search_flights(source, destination):

    flights = load_flights()

    matching_flights = []

    for flight in flights:

        if (
            flight["from"].lower() == source.lower()
            and flight["to"].lower() == destination.lower()
        ):
            matching_flights.append(flight)

    matching_flights.sort(key=lambda flight: flight["price"])

    return matching_flights

def display_flights(flights):

    if not flights:
        print("No flights found.")
        return

    print("\n========== FLIGHT SEARCH RESULTS ==========\n")

    for flight in flights:

        departure = datetime.fromisoformat(flight["departure_time"])
        arrival = datetime.fromisoformat(flight["arrival_time"])

        duration = arrival - departure

        print(f"Airline       : {flight['airline']}")
        print(f"Flight ID     : {flight['flight_id']}")
        print(f"From          : {flight['from']}")
        print(f"To            : {flight['to']}")
        print(f"Departure     : {departure.strftime('%I:%M %p')}")
        print(f"Arrival       : {arrival.strftime('%I:%M %p')}")
        print(f"Duration      : {duration}")
        print(f"Price         : ₹{flight['price']}")
        print("-------------------------------------------")

    print("\n===========================================")

if __name__ == "__main__":

    results = search_flights("Hyderabad", "Delhi")

    display_flights(results)

