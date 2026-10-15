from math import atan2, cos, radians, sin, sqrt

from app.models.poi import POI


def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate straight-line distance between two coordinates.
    """

    earth_radius_km = 6371.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a),
    )

    return earth_radius_km * c


def estimate_road_distance(straight_distance_km: float) -> float:
    """
    Demo road-distance approximation.

    Road networks are longer than straight-line distance,
    so we apply a controlled detour factor.
    """

    return straight_distance_km * 1.25


def calculate_walk_option(
    distance_km: float,
):
    duration = max(
        5,
        round((distance_km / 4.5) * 60),
    )

    return {
        "mode": "Walk",
        "option_type": "Fastest",
        "duration_minutes": duration,
        "walking_minutes": duration,
        "distance_km": round(distance_km, 2),
        "fare": 0.0,
        "boarding_stop": None,
        "alighting_stop": None,
        "intermediate_stops": [],
        "reliability_score": 0.98,
        "last_mile_distance_km": 0.0,
        "last_mile_minutes": 0,
    }


def calculate_auto_option(
    distance_km: float,
):
    duration = max(
        8,
        round((distance_km / 22) * 60),
    )
    base_fare = 30.0
    per_km = 18.0

    fare = base_fare + (
        max(0.0, distance_km - 1.5)
        * per_km
    )

    return {
        "mode": "Auto",
        "option_type": "Balanced",
        "duration_minutes": duration,
        "walking_minutes": 2,
        "distance_km": round(distance_km, 2),
        "fare": round(fare, 2),
        "boarding_stop": "Nearest pickup point",
        "alighting_stop": "Nearest destination point",
        "intermediate_stops": [],
        "reliability_score": 0.85,
        "last_mile_distance_km": 0.1,
        "last_mile_minutes": 2,
    }


def calculate_bus_option(
    distance_km: float,
):
    duration = max(
        15,
        round((distance_km / 15) * 60) + 10,
    )

    walking = min(
        15,
        max(5, round(distance_km * 3)),
    )

    fare = max(
        10.0,
        min(40.0, 10.0 + distance_km * 4.0),
    )

    return {
        "mode": "Bus",
        "option_type": "Cheapest",
        "duration_minutes": duration,
        "walking_minutes": walking,
        "distance_km": round(distance_km, 2),
        "fare": round(fare),
        "boarding_stop": "Nearest PMPML stop",
        "alighting_stop": "Nearest PMPML stop",
        "intermediate_stops": [
            "Pune Central",
            "City Route",
        ],
        "reliability_score": 0.78,
        "last_mile_distance_km": 0.4,
        "last_mile_minutes": 5,
    }


def calculate_metro_option(
    distance_km: float,
):
    duration = max(
        15,
        round((distance_km / 28) * 60) + 8,
    )

    walking = min(
        18,
        max(5, round(distance_km * 2)),
    )

    fare = max(
        10.0,
        min(50.0, 10.0 + distance_km * 5.0),
    )

    return {
        "mode": "Metro",
        "option_type": "Fastest",
        "duration_minutes": duration,
        "walking_minutes": walking,
        "distance_km": round(distance_km, 2),
        "fare": round(fare),
        "boarding_stop": "Nearest Pune Metro station",
        "alighting_stop": "Nearest Pune Metro station",
        "intermediate_stops": [
            "Metro corridor",
        ],
        "reliability_score": 0.90,
        "last_mile_distance_km": 0.6,
        "last_mile_minutes": 7,
    }


def calculate_bus_metro_option(
    distance_km: float,
):
    duration = max(
        20,
        round((distance_km / 24) * 60) + 15,
    )

    walking = min(
        20,
        max(7, round(distance_km * 2.5)),
    )

    fare = max(
        15.0,
        min(
            65.0,
            15.0 + distance_km * 5.5,
        ),
    )

    return {
        "mode": "Bus + Metro",
        "option_type": "Balanced",
        "duration_minutes": duration,
        "walking_minutes": walking,
        "distance_km": round(distance_km, 2),
        "fare": round(fare),
        "boarding_stop": "Nearest PMPML stop",
        "alighting_stop": "Nearest Metro station",
        "intermediate_stops": [
            "PMPML feeder",
            "Metro interchange",
        ],
        "reliability_score": 0.84,
        "last_mile_distance_km": 0.5,
        "last_mile_minutes": 6,
    }


def generate_transport_options(
    origin: POI,
    destination: POI,
):
    straight_distance = haversine_distance_km(
        origin.latitude,
        origin.longitude,
        destination.latitude,
        destination.longitude,
    )

    road_distance = estimate_road_distance(
        straight_distance
    )

    options = [
        calculate_walk_option(road_distance),
        calculate_bus_option(road_distance),
        calculate_metro_option(road_distance),
        calculate_bus_metro_option(road_distance),
        calculate_auto_option(road_distance),
    ]

    cheapest = min(
        options,
        key=lambda option: option["fare"],
    )

    fastest = min(
        options,
        key=lambda option: option["duration_minutes"],
    )

    def balanced_score(option):
        max_fare = max(
            item["fare"]
            for item in options
        )

        max_duration = max(
            item["duration_minutes"]
            for item in options
        )

        fare_score = (
            option["fare"] / max_fare
            if max_fare
            else 0
        )

        time_score = (
            option["duration_minutes"]
            / max_duration
            if max_duration
            else 0
        )

        reliability_penalty = (
            1.0 - option["reliability_score"]
        )

        return (
            0.40 * time_score
            + 0.30 * fare_score
            + 0.20 * reliability_penalty
            + 0.10 * (
                option["walking_minutes"] / 20
            )
        )

    balanced = min(
        options,
        key=balanced_score,
    )

    for option in options:
        option["option_type"] = "Alternative"

    cheapest["option_type"] = "Cheapest"
    fastest["option_type"] = "Fastest"
    balanced["option_type"] = "Balanced"

    return options