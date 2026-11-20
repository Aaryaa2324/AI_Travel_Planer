# AI Travel Planner

An AI-powered travel planning assistant built using Python, LangChain, Google Gemini, and Streamlit. It helps users plan trips by finding flights, hotels, tourist attractions, weather forecasts, and estimated travel budgets.

## Features

- **Flight Search:** Searches available flights between two cities using a JSON dataset.
- **Hotel Search:** Finds hotels based on destination and minimum star rating.
- **Attraction Search:** Finds tourist attractions using city, type, and rating filters.
- **Day-wise Itinerary:** Organizes available attractions into a multi-day travel plan.
- **Weather Information:** Retrieves current weather and forecasts using the Open-Meteo API.
- **Budget Calculation:** Estimates flight costs, hotel costs, daily expenses, and total trip costs.
- **AI Agent:** Uses LangChain and Google Gemini to understand travel requests and select appropriate tools.
- **JSON Output:** Generates a structured trip plan and saves it as `trip_plan.json`.
- **Streamlit Interface:** Provides a simple interactive interface for generating and viewing travel plans.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| LangChain | AI agent and tool integration |
| Google Gemini | Large Language Model |
| Streamlit | Web-based user interface |
| Open-Meteo API | Weather and forecast information |
| JSON | Sample flight, hotel, and attraction datasets |

## Project Structure

```text
AI_Travel_Planner/
│
├── agent/
│   ├── __init__.py
│   ├── test_gemini.py
│   └── travel_agent.py
│
├── data/
│   ├── flights.json
│   ├── hotels.json
│   └── places.json
│
├── tools/
│   ├── __init__.py
│   ├── flight_tool.py
│   ├── hotel_tool.py
│   ├── places_tool.py
│   ├── weather_tool.py
│   └── budget_tool.py
│
├── app.py
├── explore_data.py
├── trip_plan.json
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone or download the project

Open the project folder in Visual Studio Code.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Google Gemini API key

Create a `.env` file in the project root and add:

```env
GOOGLE_API_KEY=your_google_gemini_api_key
```

Replace the placeholder with your own API key.

Do not upload your `.env` file to GitHub or share your API key publicly.

## Running the Application

### Option 1: Streamlit Web Application

Run:

```bash
streamlit run app.py
```

Streamlit will start the application and provide a local browser address.

Enter:
- Starting city
- Destination city
- Number of travel days
- Daily expense budget

Click **Generate My Trip Plan** to receive the travel plan.

### Option 2: Command-Line Interface

Run:

```bash
python -m agent.travel_agent
```

Enter your travel requirements in the terminal. Type `exit` to close the application.

## Example User Request

```text
Plan a 3-day trip from Hyderabad to Delhi.

Find a flight, hotel, tourist attractions,
weather forecast, and estimated budget.

My daily expense budget is 1500 rupees.
```

## Weather API

This project uses the Open-Meteo API for weather information.

Website: https://open-meteo.com/

The application uses Open-Meteo geocoding to identify a destination and retrieve weather information and forecasts.

## Data Sources and Limitations

- Flight information is retrieved from the supplied sample JSON dataset.
- Hotel information is retrieved from the supplied sample JSON dataset.
- Tourist attractions are retrieved from the supplied sample JSON dataset.
- Flight and hotel prices are sample values, not live booking prices.
- The application does not book flights or hotels.
- Weather information is retrieved from Open-Meteo.
- Weather forecast availability depends on the requested dates and API forecast range.
- The estimated budget depends on the available sample prices and the user's daily expense input.

## Output

The application provides:

1. A readable travel plan.
2. Flight and hotel details.
3. Tourist attractions and a day-wise itinerary.
4. Weather forecast information.
5. Estimated trip budget.
6. A structured JSON trip plan saved as `trip_plan.json`.

The Streamlit interface also provides an option to download the generated JSON plan.

## Error Handling and Validation

- Checks whether the Google Gemini API key is configured.
- Handles missing or unavailable destination data.
- Validates the generated JSON structure before saving.
- Filters attractions that do not meet the configured rating threshold.
- Handles errors during agent execution and API requests.

## Future Improvements

- Integrate live flight and hotel booking APIs.
- Add maps and route optimization.
- Add user preferences for travel style and accommodation.
- Add more advanced budget optimization.
- Store and retrieve previous travel plans.

## Author

Developed as an academic project to demonstrate Agentic AI, LangChain tool integration, API usage, and interactive application development.

## User Accounts and Trip History

TravelMate AI includes a local account system and personal trip history.

### Account Features

- User registration and login.
- Password hashing using PBKDF2-HMAC-SHA256 with individual random salts.
- Logout functionality.
- User-specific trip history.

### Trip History

Successfully generated and validated JSON trip plans are saved in a local SQLite database.

Each saved trip contains:
- Starting city and destination.
- Number of travel days.
- Estimated total budget.
- Complete structured JSON trip plan.
- Date and time of creation.

Users can view their saved trips and download individual trip plans.

### Database

The application automatically creates `travel_history.db` in the project root.

The database contains:
- `users` — account information and password hashes.
- `trips` — saved trip plans linked to individual users.

### Security Limitations

This authentication system is intended for a local academic demonstration. It is not a substitute for production identity management. A public deployment would require additional protections such as HTTPS, secure session management, rate limiting, account recovery, and stronger operational database security.

The local database should not be shared publicly.
