
import requests


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(latitude, longitude):

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "apparent_temperature,weather_code,wind_speed_10m"
        )
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    weather_data = response.json()

    return weather_data["current"]


def get_weather_forecast(latitude, longitude, forecast_days=7):

    if not 1 <= forecast_days <= 7:
        raise ValueError("Forecast days must be between 1 and 7.")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max,"
            "weather_code"
        ),
        "forecast_days": forecast_days,
        "timezone": "auto"
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    weather_data = response.json()

    return weather_data["daily"]


if __name__ == "__main__":

    latitude = 28.6139
    longitude = 77.2090

    print("\n========== CURRENT WEATHER ==========\n")

    weather = get_weather(latitude, longitude)

    print(f"Temperature : {weather['temperature_2m']} °C")
    print(f"Feels Like  : {weather['apparent_temperature']} °C")
    print(f"Humidity    : {weather['relative_humidity_2m']} %")
    print(f"Wind Speed  : {weather['wind_speed_10m']} km/h")
    print(f"Weather Code: {weather['weather_code']}")

    print("\n========== 7-DAY WEATHER FORECAST ==========\n")

    forecast = get_weather_forecast(latitude, longitude)

    for i, date in enumerate(forecast["time"]):

        print(f"\nDate: {date}")
        print(f"Maximum Temperature: {forecast['temperature_2m_max'][i]} °C")
        print(f"Minimum Temperature: {forecast['temperature_2m_min'][i]} °C")
        print(
            "Rain Probability: "
            f"{forecast['precipitation_probability_max'][i]} %"
        )
        print(f"Weather Code: {forecast['weather_code'][i]}")

    print("\n===========================================")
