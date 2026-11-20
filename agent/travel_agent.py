import os
import re
import json
import requests
from pathlib import Path

from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.flight_tool import search_flights
from tools.hotel_tool import search_hotels
from tools.places_tool import search_places, build_itinerary
from tools.weather_tool import get_weather, get_weather_forecast
from tools.budget_tool import calculate_budget

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is missing from .env")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)

@tool
def flight_search(source: str, destination: str):
    """Find flights between two cities, sorted by cheapest price."""

    results = search_flights(source, destination)

    return json.dumps(results, ensure_ascii=False)

@tool
def hotel_search(city: str, min_stars: int = 1):
    """Find hotels in a city with a minimum star rating, sorted by price."""

    results = search_hotels(city, min_stars)

    return json.dumps(results, ensure_ascii=False)

@tool
def places_search(city: str, place_type: str = None, min_rating: float = 4.0):
    """Find tourist attractions in a city, optionally filtering by type and rating."""

    results = search_places(city, place_type, min_rating)

    return json.dumps(results, ensure_ascii=False)


@tool
def itinerary_search(city: str, number_of_days: int, min_rating: float = 4.0):
    """Create a day-wise tourist attraction itinerary for a city."""

    result = build_itinerary(city, number_of_days, min_rating)

    return json.dumps(result, ensure_ascii=False)


@tool
def weather_search(city: str):
    """Find current weather conditions for a given city."""

    url = "https://geocoding-api.open-meteo.com/v1/search"

    response = requests.get(
        url,
        params={"name": city, "count": 1, "language": "en"},
        timeout=10
    )

    response.raise_for_status()

    locations = response.json().get("results", [])

    if not locations:
        return f"No location found for {city}."

    location = locations[0]

    weather = get_weather(
        location["latitude"],
        location["longitude"]
    )

    return json.dumps(weather, ensure_ascii=False)


@tool
def weather_forecast_search(city: str, forecast_days: int = 3):
    """Get the daily weather forecast for a city for up to 7 days."""

    if not 1 <= forecast_days <= 7:
        return "Forecast days must be between 1 and 7."

    url = "https://geocoding-api.open-meteo.com/v1/search"

    response = requests.get(
        url,
        params={
            "name": city,
            "count": 1,
            "language": "en"
        },
        timeout=10
    )

    response.raise_for_status()

    locations = response.json().get("results", [])

    if not locations:
        return f"No location found for {city}."

    location = locations[0]

    forecast = get_weather_forecast(
        location["latitude"],
        location["longitude"],
        forecast_days
    )

    return json.dumps(forecast, ensure_ascii=False)

@tool
def trip_budget(
    flight_price: float,
    hotel_price_per_night: float,
    number_of_nights: int,
    daily_expenses: float,
    number_of_days: int
):
    """
    Calculate total trip cost using flight price,
    hotel price, number of nights and daily expenses.
    """

    result = calculate_budget(
        flight_price,
        hotel_price_per_night,
        number_of_nights,
        daily_expenses,
        number_of_days
    )

    return json.dumps(result, ensure_ascii=False)

tools = [
    flight_search,
    hotel_search,
    places_search,
    itinerary_search,
    weather_search,
    weather_forecast_search,
    trip_budget
]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
    You are an intelligent AI travel planning assistant.

    Your responsibilities:
    1. Understand the user's travel requirements.
    2. Use available tools to search for flights, hotels and attractions.
    3. Retrieve weather information when relevant.
    4. Calculate the estimated trip budget.
    5. Recommend suitable options based on the user's preferences.
    6. Never invent flight, hotel or attraction information.
    7. Clearly explain when information is unavailable.
    8. Remember that flight, hotel and attraction data comes
       from a sample JSON dataset, not live booking services.
    9. Weather information comes from Open-Meteo.
    10. Present the final result in a clear, organized format.
    11. Never invent a daily expense budget. If the user has not specified daily expenses, ask the user before calculating the final budget.
    12. Clearly distinguish between travel days and hotel nights.
    13. When the user requests attractions rated above a threshold, exclude attractions equal to that threshold.
    14. Always display weather measurements using the units returned by the weather API.
    15. When planning a multi-day trip, use itinerary_search to distribute available attractions across the travel days.
    16. Present attractions under Day 1, Day 2, Day 3, etc.
    17. Never invent attraction timings, distances, opening hours or unavailable attractions.
    18. If there are fewer attractions than travel days, clearly mention that some days have no available attractions.
    19. Explain that the itinerary is a suggested plan based on the supplied sample dataset.
    20. Use weather_forecast_search for upcoming travel dates when a forecast is available.
    21. Include daily minimum and maximum temperatures and precipitation probability in the itinerary when available.
    22. Never claim that a forecast is available for historical dates.
    23. Clearly distinguish current weather from daily forecasts.
    24. For a complete trip plan, provide both:
        A. A readable travel plan with headings.
        B. A valid JSON object containing the same information.
    25. The JSON object must use this structure:
        {
            "trip_overview": {
            "source": "",
            "destination": "",
            "travel_days": 0,
            "hotel_nights": 0
            },
            "flight": {},
            "hotel": {},
            "attractions": [],
            "day_wise_itinerary": [],
            "weather_forecast": [],
            "budget": {
                "flight_cost": 0,
                "hotel_cost": 0,
                "daily_expenses": 0,
                "total_cost": 0
            }
        }
    26. Use null for information that is unavailable. Never invent missing values.
    27. The JSON must be valid and parseable. Do not include comments or trailing commas. Do not put Markdown formatting inside the JSON.
    28. Always distinguish sample dataset flight dates from live weather forecast dates.
    29. Never imply that a weather forecast corresponds to a flight date unless the dates actually match.
    30. If the flight date is historical or outside the forecast period, clearly disclose this limitation.
    31. ALWAYS use itinerary_search when generating a day-wise itinerary.
    32. NEVER add attractions from memory or invent additional attractions.
    33. Every attraction in the itinerary must have a rating strictly greater than the requested minimum rating.
    34. The day-wise itinerary must contain only attractions returned by itinerary_search.
    """
)


def validate_and_save_json(response_text):

    try:
        # Step 1: Extract JSON
        match = re.search(
            r"```json\s*(\{[\s\S]*\})\s*```",
            response_text,
            re.IGNORECASE
        )

        if match:
            json_text = match.group(1)
            data = json.loads(json_text)

        else:
            # Handle JSON without Markdown code fences
            start = response_text.find("{")

            if start == -1:
                print("\nNo JSON object found in the response.")
                return

            decoder = json.JSONDecoder()
            data, end_position = decoder.raw_decode(
                response_text[start:]
            )

        # Step 2: Check JSON structure
        if not isinstance(data, dict):
            print("\nInvalid JSON: Expected a JSON object.")
            return

        
        # Step 3: Remove attractions that do not meet the rating threshold
        min_rating = 4.0

        original_count = len(data.get("attractions", []))

        data["attractions"] = [
            attraction
            for attraction in data.get("attractions", [])
            if isinstance(attraction.get("rating"), (int, float))
            and attraction["rating"] > min_rating
        ]

        # Clean day-wise itinerary
        for day in data.get("day_wise_itinerary", []):
            day["attractions"] = [
                attraction
                for attraction in day.get("attractions", [])
                if isinstance(attraction.get("rating"), (int, float))
                and attraction["rating"] > min_rating
            ]

        corrected_count = original_count - len(data["attractions"])

        if corrected_count > 0:
            print(
                f"\nWarning: Removed {corrected_count} "
                "attraction(s) with ratings of 4.0 or below."
            )


        # Step 5: Save JSON
        project_root = Path(__file__).resolve().parents[1]
        output_file = project_root / "trip_plan.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print("\nJSON validation successful!")
        print(f"Trip plan saved successfully: {output_file}")

    except json.JSONDecodeError as e:
        print(f"\nInvalid JSON format: {e}")

    except Exception as e:
        print(f"\nError saving JSON: {e}")


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    messages = []

    print("\n========== AI TRAVEL PLANNER ==========")
    print("Ask me anything about your trip.")
    print("Type 'exit' to quit.")
    print("======================================")

    while True:

        query = input("\nYou: ").strip()

        if query.lower() in ["exit", "quit"]:
            print("\nThank you for using AI Travel Planner!")
            break

        if not query:
            print("Please enter a question.")
            continue

        messages.append({
            "role": "user",
            "content": query
        })

        try:

            response = agent.invoke({
                "messages": messages
            })

            messages = response["messages"]

            final_message = messages[-1]

            print("\n========== AI TRAVEL ASSISTANT ==========\n")

            # Extract assistant response
            if isinstance(final_message.content, str):

                response_text = final_message.content
                print(response_text)

            else:

                response_text = ""

                for block in final_message.content:

                    if block.get("type") == "text":
                        response_text += block["text"] + "\n"

                print(response_text)

            # Validate and save JSON
            if "{" in response_text and "}" in response_text:

                validate_and_save_json(response_text)

            print("\n=========================================")

        except Exception as e:

            print(f"\nError: {e}")
