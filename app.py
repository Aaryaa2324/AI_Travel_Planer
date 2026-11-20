
import json
import html
import sqlite3
import hashlib
import hmac
import secrets
from datetime import datetime
from pathlib import Path

import streamlit as st

from agent.travel_agent import agent, validate_and_save_json


# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="TravelMate AI",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "travel_history.db"
TRIP_FILE = ROOT / "trip_plan.json"

PBKDF2_ITERATIONS = 310_000


# =====================================================
# DATABASE
# =====================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                travel_days INTEGER NOT NULL,
                total_cost REAL,
                trip_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


initialize_database()


# =====================================================
# PASSWORD SECURITY
# =====================================================

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS
    ).hex()


def register_user(username, password):
    username = username.strip().lower()

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users
                (username, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    salt,
                    datetime.now().isoformat(timespec="seconds")
                )
            )

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "This username is already registered."


def authenticate_user(username, password):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, username, password_hash, salt
            FROM users
            WHERE username = ?
            """,
            (username.strip().lower(),)
        ).fetchone()

    if not user:
        return None

    user_id, stored_username, stored_hash, salt = user
    candidate_hash = hash_password(password, salt)

    if hmac.compare_digest(candidate_hash, stored_hash):
        return {
            "id": user_id,
            "username": stored_username
        }

    return None


# =====================================================
# TRIP HISTORY
# =====================================================

def save_trip(user_id, data):
    overview = data.get("trip_overview", {})
    budget = data.get("budget", {})

    source = str(overview.get("source") or "Unknown")
    destination = str(overview.get("destination") or "Unknown")
    days = int(overview.get("travel_days") or 0)

    try:
        total_cost = float(budget.get("total_cost") or 0)
    except (ValueError, TypeError):
        total_cost = 0

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO trips (
                user_id, source, destination,
                travel_days, total_cost, trip_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                source,
                destination,
                days,
                total_cost,
                json.dumps(data, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds")
            )
        )


def get_user_trips(user_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, source, destination, travel_days,
                   total_cost, created_at
            FROM trips
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()


def get_trip_details(trip_id, user_id):
    with get_connection() as conn:
        result = conn.execute(
            """
            SELECT trip_json
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id)
        ).fetchone()

    if result:
        return json.loads(result[0])

    return None


# =====================================================
# SESSION STATE
# =====================================================

defaults = {
    "authenticated": False,
    "user": None,
    "page": "Dashboard",
    "messages": [],
    "plan_text": "",
    "trip_data": None,
    "selected_trip": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


def navigate(page):
    st.session_state.page = page


def reset_trip():
    st.session_state.messages = []
    st.session_state.plan_text = ""
    st.session_state.trip_data = None
    st.session_state.page = "Dashboard"


# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

/* =========================================
   GLOBAL DARK THEME
========================================= */

:root {
    color-scheme: dark;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stHeader"] {
    background-color: #0B1120 !important;
    color: #F1F5F9 !important;
    font-family: 'DM Sans', sans-serif !important;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* =========================================
   SIDEBAR
========================================= */

[data-testid="stSidebar"] {
    background-color: #111C2F !important;
    border-right: 1px solid #26364D !important;
}

[data-testid="stSidebar"] * {
    color: #E2E8F0;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}

/* Sidebar buttons */

[data-testid="stSidebar"] .stButton > button {
    background-color: #1E2D43 !important;
    color: #F8FAFC !important;
    border: 1px solid #354963 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 45px;
    transition: all .25s ease;
}

[data-testid="stSidebar"] .stButton > button p {
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #0D9488 !important;
    border-color: #2DD4BF !important;
    transform: translateY(-2px);
}

[data-testid="stSidebar"] .stButton > button:hover p {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
}

/* =========================================
   HERO SECTION
========================================= */

.hero {
    background: linear-gradient(120deg, #10243F, #173D59);
    padding: 42px;
    border: 1px solid #294765;
    border-radius: 22px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,.25);
}

.hero h1 {
    color: #FFFFFF !important;
    font-size: 38px;
    font-weight: 800;
}

.hero p {
    color: #CBD5E1 !important;
    line-height: 1.7;
}

.hero-tag {
    color: #5EEAD4 !important;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
}

/* =========================================
   ALL TEXT
========================================= */

.stApp p,
.stApp label,
.stApp li,
.stApp span,
.stApp .stMarkdown,
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: #E2E8F0;
}

.section-heading {
    color: #F8FAFC !important;
    font-size: 23px;
    font-weight: 800;
    margin: 25px 0 15px;
}

.section-description {
    color: #A5B4C7 !important;
}

/* =========================================
   INPUT FIELDS
========================================= */

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stTextArea label,
.stDateInput label {
    color: #E2E8F0 !important;
    font-weight: 600 !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stDateInput input {
    background-color: #172338 !important;
    color: #FFFFFF !important;
    border: 1px solid #40536E !important;
    border-radius: 9px !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #A6B5C8 !important;
    opacity: 1 !important;
}

.stNumberInput button {
    background-color: #253750 !important;
    color: #FFFFFF !important;
    border-color: #40536E !important;
}

/* Dropdowns */

[data-baseweb="select"] > div {
    background-color: #172338 !important;
    color: #FFFFFF !important;
    border-color: #40536E !important;
}

[data-baseweb="select"] *,
[role="listbox"] *,
[role="option"] {
    color: #FFFFFF !important;
}

[role="listbox"] {
    background-color: #172338 !important;
}

/* =========================================
   LOGIN / REGISTER TABS
========================================= */

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background-color: #172338 !important;
    border-bottom: 1px solid #40536E !important;
    border-radius: 10px 10px 0 0;
    gap: 8px;
}

/* Both tabs remain visible, selected or not */

[data-testid="stTabs"] button[data-baseweb="tab"] {
    background-color: #1E2D43 !important;
    color: #E2E8F0 !important;
    border-radius: 8px 8px 0 0 !important;
    border: 1px solid #40536E !important;
    opacity: 1 !important;
}

/* Force nested tab text to remain visible */

[data-testid="stTabs"] button[data-baseweb="tab"] *,
[data-testid="stTabs"] button[data-baseweb="tab"] p,
[data-testid="stTabs"] button[data-baseweb="tab"] span {
    color: #E2E8F0 !important;
    opacity: 1 !important;
}

/* Selected tab */

[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #0D9488 !important;
    border-color: #2DD4BF !important;
    color: #FFFFFF !important;
}

[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] * {
    color: #FFFFFF !important;
}

/* Hover */

[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
    background-color: #29415E !important;
}

/* =========================================
   FORMS AND CARDS
========================================= */

[data-testid="stForm"],
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: #142137;
    border-color: #334861 !important;
    border-radius: 14px;
}

.result-card,
.float-card {
    background: #172338 !important;
    border: 1px solid #344861 !important;
    border-radius: 15px;
    padding: 22px;
    box-shadow: 0 5px 18px rgba(0,0,0,.20);
    transition: transform .25s ease, box-shadow .25s ease;
}

.float-card:hover,
.result-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 25px rgba(0,0,0,.35);
    border-color: #0D9488 !important;
}

.float-icon {
    font-size: 25px;
}

.float-title {
    color: #A5B4C7 !important;
    font-size: 13px;
}

.float-value {
    color: #FFFFFF !important;
    font-size: 25px;
    font-weight: 800;
}

.float-note {
    color: #94A3B8 !important;
}

/* =========================================
   BUTTONS
========================================= */

.stButton > button,
.stDownloadButton > button {
    background-color: #1E2D43 !important;
    color: #FFFFFF !important;
    border: 1px solid #40536E !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    min-height: 42px;
}

.stButton > button p,
.stDownloadButton > button p {
    color: #FFFFFF !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #29415E !important;
    border-color: #2DD4BF !important;
}

/* Primary action buttons */

.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background-color: #0D9488 !important;
    color: #FFFFFF !important;
    border: 1px solid #2DD4BF !important;
}

.stButton > button[kind="primary"] *,
.stFormSubmitButton > button * {
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button:hover {
    background-color: #0F766E !important;
}

/* =========================================
   METRICS
========================================= */

[data-testid="stMetric"] {
    background-color: #172338 !important;
    border: 1px solid #344861 !important;
    padding: 15px;
    border-radius: 12px;
}

[data-testid="stMetricLabel"] {
    color: #A5B4C7 !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
}

/* =========================================
   ALERTS AND MESSAGES
========================================= */

[data-testid="stAlert"] {
    border-radius: 10px;
}

[data-testid="stAlert"] p {
    color: #F8FAFC !important;
}

/* =========================================
   TABLES AND DATAFRAMES
========================================= */

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background-color: #172338 !important;
    border: 1px solid #344861;
    border-radius: 10px;
}

/* =========================================
   CHECKBOXES AND RADIO BUTTONS
========================================= */

.stCheckbox label,
.stRadio label {
    color: #E2E8F0 !important;
}

.stCheckbox span,
.stRadio span {
    color: #E2E8F0 !important;
}

/* =========================================
   DIVIDERS AND FOOTER
========================================= */

hr {
    border-color: #334155 !important;
}

.footer {
    text-align: center;
    color: #94A3B8 !important;
    padding: 25px;
    font-size: 12px;
}

.footer strong {
    color: #F8FAFC !important;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# AUTHENTICATION PAGE
# =====================================================

def authentication_page():

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">✦ TRAVELMATE AI</div>
        <h1>Your journey begins here.</h1>
        <p>Sign in or create an account to organize your travel plans.</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown("## Welcome to TravelMate AI")
        st.write(
            "Your personal AI travel assistant for discovering "
            "destinations, planning itineraries and managing budgets."
        )

        st.markdown("### What you can do")
        st.write("✈️ Search sample flight information")
        st.write("🏨 Discover accommodation")
        st.write("🗺️ Generate day-wise itineraries")
        st.write("🌤️ Check destination weather")
        st.write("💰 Estimate travel costs")
        st.write("📚 Save your previous trip plans")

    with right:

        st.markdown("## Account access")

        login_tab, register_tab = st.tabs([
            "Login",
            "Create account"
        ])

        with login_tab:

            with st.form("login_form"):

                username = st.text_input("Username")
                password = st.text_input(
                    "Password",
                    type="password"
                )

                login_submit = st.form_submit_button(
                    "Login",
                    type="primary",
                    use_container_width=True
                )

            if login_submit:

                user = authenticate_user(username, password)

                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with register_tab:

            with st.form("register_form"):

                new_username = st.text_input("Choose a username")
                new_password = st.text_input(
                    "Create a password",
                    type="password"
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password"
                )

                register_submit = st.form_submit_button(
                    "Create account",
                    type="primary",
                    use_container_width=True
                )

            if register_submit:

                if new_password != confirm_password:
                    st.error("Passwords do not match.")

                else:
                    success, message = register_user(
                        new_username,
                        new_password
                    )

                    if success:
                        st.success(message + " Please log in.")
                    else:
                        st.error(message)

    st.divider()

    st.caption(
        "Local academic demonstration. Do not reuse important passwords."
    )


# =====================================================
# DASHBOARD
# =====================================================

def dashboard_page():

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">✦ AI POWERED TRAVEL PLANNING</div>
        <h1>Discover your next adventure.</h1>
        <p>
            Plan smarter, explore destinations and create your
            next journey with your personal AI travel assistant.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-heading">Plan your journey</div>',
        unsafe_allow_html=True
    )

    with st.form("travel_form"):

        col1, col2 = st.columns(2)

        with col1:
            source = st.text_input(
                "Starting city",
                placeholder="e.g. Hyderabad"
            )

        with col2:
            destination = st.text_input(
                "Destination city",
                placeholder="e.g. Delhi"
            )

        col3, col4 = st.columns(2)

        with col3:
            days = st.number_input(
                "Travel days",
                min_value=1,
                max_value=7,
                value=3
            )

        with col4:
            daily_budget = st.number_input(
                "Daily expense budget (₹)",
                min_value=1,
                value=1500,
                step=100
            )

        submitted = st.form_submit_button(
            "✈️ Generate My Travel Plan",
            type="primary",
            use_container_width=True
        )

    if submitted:

        if not source.strip() or not destination.strip():
            st.error("Enter both cities.")

        elif source.strip().lower() == destination.strip().lower():
            st.error("Starting city and destination must be different.")

        else:

            query = f"""
            Plan a {days}-day trip from {source.strip()} to
            {destination.strip()}.

            My daily expense budget is {daily_budget} rupees.

            Find a flight, hotel, tourist attractions and weather
            forecast using the available tools.

            Use itinerary_search to create a day-wise itinerary.

            Include attractions with ratings strictly greater than 4.0.

            Calculate the estimated budget.

            Return both a readable plan and valid JSON using the
            required project structure.

            Clearly distinguish travel days and hotel nights.

            Do not invent unavailable information.

            Mention that flights, hotels and attractions come from
            sample datasets, not live booking services.
            """

            try:

                with st.spinner("TravelMate AI is planning your trip..."):

                    # Remove the previous shared output so an old plan
                    # cannot accidentally be saved as this user's trip.
                    previous_bytes = None

                    if TRIP_FILE.exists():
                        previous_bytes = TRIP_FILE.read_bytes()
                        TRIP_FILE.unlink()

                    try:
                        response = agent.invoke({
                            "messages": st.session_state.messages + [
                                {
                                    "role": "user",
                                    "content": query
                                }
                            ]
                        })

                        st.session_state.messages = response["messages"]

                        final_message = st.session_state.messages[-1]

                        if isinstance(final_message.content, str):
                            response_text = final_message.content
                        else:
                            response_text = "".join(
                                block.get("text", "")
                                for block in final_message.content
                                if isinstance(block, dict)
                                and block.get("type") == "text"
                            )

                        st.session_state.plan_text = response_text
                        st.session_state.trip_data = None

                        if "{" in response_text and "}" in response_text:

                            validate_and_save_json(response_text)

                            if TRIP_FILE.exists():

                                with open(
                                    TRIP_FILE,
                                    "r",
                                    encoding="utf-8"
                                ) as file:
                                    trip_data = json.load(file)

                                st.session_state.trip_data = trip_data

                                save_trip(
                                    st.session_state.user["id"],
                                    trip_data
                                )

                                st.success(
                                    "Trip generated and saved to your history!"
                                )
                            else:
                                st.warning(
                                    "The readable plan was generated, "
                                    "but valid JSON was not saved. "
                                    "This trip was not added to history."
                                )

                        else:
                            st.warning(
                                "The response did not contain a JSON plan. "
                                "It was not added to trip history."
                            )

                    finally:
                        # Restore the previous shared output file.
                        if previous_bytes is not None:
                            TRIP_FILE.write_bytes(previous_bytes)
                        elif TRIP_FILE.exists():
                            TRIP_FILE.unlink()

            except Exception as error:
                st.error(f"Unable to generate trip: {error}")

    # Show generated results
    if st.session_state.plan_text:

        st.divider()

        st.markdown("## Your travel plan")

        st.markdown(st.session_state.plan_text)

        data = st.session_state.trip_data

        if data:

            overview = data.get("trip_overview", {})
            budget = data.get("budget", {})

            st.markdown("## Travel overview")

            a, b, c, d = st.columns(4)

            cards = [
                ("✈️", "Flight", budget.get("flight_cost", 0)),
                ("🏨", "Hotel", budget.get("hotel_cost", 0)),
                ("💳", "Daily expenses", budget.get("daily_expenses", 0)),
                ("💰", "Total cost", budget.get("total_cost", 0))
            ]

            for column, card in zip([a, b, c, d], cards):
                with column:
                    st.markdown(f"""
                    <div class="float-card">
                        <div class="float-icon">{card[0]}</div>
                        <div class="float-title">{html.escape(card[1])}</div>
                        <div class="float-value">₹{float(card[2] or 0):,.0f}</div>
                        <div class="float-note">Estimated value</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.write("")

            tabs = st.tabs([
                "Overview",
                "Itinerary",
                "Weather",
                "Budget",
                "JSON"
            ])

            with tabs[0]:
                st.subheader("Flight")
                st.json(data.get("flight", {}))
                st.subheader("Hotel")
                st.json(data.get("hotel", {}))
                st.subheader("Attractions")
                st.json(data.get("attractions", []))

            with tabs[1]:
                for day in data.get("day_wise_itinerary", []):
                    with st.container(border=True):
                        st.markdown(f"### {day.get('day', 'Travel day')}")
                        for place in day.get("attractions", []):
                            st.write(
                                f"📍 {place.get('name')} "
                                f"— ⭐ {place.get('rating')}"
                            )

            with tabs[2]:
                weather = data.get("weather_forecast", [])
                if weather:
                    st.dataframe(weather, use_container_width=True)
                else:
                    st.info("No forecast available.")

            with tabs[3]:
                st.json(budget)

            with tabs[4]:
                st.json(data)

                st.download_button(
                    "Download trip JSON",
                    data=json.dumps(data, indent=4, ensure_ascii=False),
                    file_name="trip_plan.json",
                    mime="application/json",
                    use_container_width=True
                )


# =====================================================
# HISTORY PAGE
# =====================================================

def history_page():

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">✦ YOUR JOURNEY ARCHIVE</div>
        <h1>My Trip History</h1>
        <p>All your previously generated travel plans, in one place.</p>
    </div>
    """, unsafe_allow_html=True)

    trips = get_user_trips(st.session_state.user["id"])

    if not trips:
        st.info(
            "You haven't saved any trips yet. Generate your first "
            "trip from the Dashboard."
        )
        return

    st.write(f"**{len(trips)} saved trip(s)**")

    for trip in trips:

        trip_id, source, destination, days, total_cost, created_at = trip

        with st.container(border=True):

            col1, col2 = st.columns([3, 1])

            with col1:

                st.markdown(
                    f"### {html.escape(source)} → "
                    f"{html.escape(destination)}"
                )

                st.caption(
                    f"{days} travel days · "
                    f"₹{float(total_cost or 0):,.0f} estimated · "
                    f"{created_at}"
                )

            with col2:

                if st.button(
                    "View trip",
                    key=f"view_{trip_id}",
                    use_container_width=True
                ):
                    st.session_state.selected_trip = trip_id

    if st.session_state.selected_trip:

        selected = get_trip_details(
            st.session_state.selected_trip,
            st.session_state.user["id"]
        )

        if selected:

            st.divider()
            st.subheader("Saved trip details")

            st.json(selected)

            st.download_button(
                "Download saved trip",
                data=json.dumps(
                    selected,
                    indent=4,
                    ensure_ascii=False
                ),
                file_name=f"saved_trip_{st.session_state.selected_trip}.json",
                mime="application/json",
                key=f"download_{st.session_state.selected_trip}"
            )


# =====================================================
# APPLICATION NAVIGATION
# =====================================================

if not st.session_state.authenticated:

    authentication_page()

else:

    with st.sidebar:

        st.markdown("## ✈️ TravelMate AI")

        st.caption(
            f"Signed in as {st.session_state.user['username']}"
        )

        st.divider()

        st.markdown("### Navigation")

        if st.button("🏠 Dashboard", use_container_width=True):
            navigate("Dashboard")

        if st.button("📚 My Trip History", use_container_width=True):
            navigate("History")

        st.divider()

        # Direct callback avoids relying on stale button state.
        st.button(
            "＋ Plan a New Trip",
            use_container_width=True,
            on_click=reset_trip
        )

        st.divider()

        st.button(
            "↪ Logout",
            use_container_width=True,
            on_click=logout
        )

    if st.session_state.page == "Dashboard":
        dashboard_page()

    elif st.session_state.page == "History":
        history_page()


# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<div class="footer">
    <strong>✈️ TravelMate AI</strong><br>
    Intelligent Agentic AI Travel Planning Assistant<br>
    Python · LangChain · Google Gemini · Streamlit · SQLite
</div>
""", unsafe_allow_html=True)
