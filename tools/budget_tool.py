def calculate_budget(
    flight_price,
    hotel_price_per_night,
    number_of_nights,
    daily_expenses,
    number_of_days
):

    flight_cost = flight_price

    hotel_cost = hotel_price_per_night * number_of_nights

    local_cost = daily_expenses * number_of_days

    total_cost = flight_cost + hotel_cost + local_cost

    return {
        "flight_cost": flight_cost,
        "hotel_cost": hotel_cost,
        "local_cost": local_cost,
        "total_cost": total_cost
    }

if __name__ == "__main__":

    budget = calculate_budget(
        flight_price=2907,
        hotel_price_per_night=3650,
        number_of_nights=3,
        daily_expenses=1000
    )

    print("\n========== TRIP BUDGET ==========\n")

    print(f"Flight Cost : ₹{budget['flight_cost']}")
    print(f"Hotel Cost  : ₹{budget['hotel_cost']}")
    print(f"Local Cost  : ₹{budget['local_cost']}")

    print("--------------------------------")

    print(f"Total Budget: ₹{budget['total_cost']}")

    print("\n================================")