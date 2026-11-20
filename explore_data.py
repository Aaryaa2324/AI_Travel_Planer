import json
from pathlib import Path

# Get the data folder location
DATA_FOLDER = Path("data")


def explore_json(filename):

    file_path = DATA_FOLDER / filename

    print("\n" + "=" * 60)
    print(f"EXPLORING: {filename}")
    print("=" * 60)

    # Load JSON file
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Check data type
    print("\nData Type:", type(data).__name__)

    # Check total records
    if isinstance(data, list):
        print("Total Records:", len(data))
        print("\nFirst Record:")
        print(json.dumps(data[0], indent=4, ensure_ascii=False))

        if isinstance(data[0], dict):
            print("\nAvailable Columns:")
            print(list(data[0].keys()))

    elif isinstance(data, dict):
        print("\nAvailable Keys:")
        print(list(data.keys()))

        print("\nSample Data:")
        print(json.dumps(data, indent=4, ensure_ascii=False)[:2000])


# Explore all three datasets
explore_json("flights.json")
explore_json("hotels.json")
explore_json("places.json")