import httpx


PUNE_LATITUDE = 18.5204
PUNE_LONGITUDE = 73.8567


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


def get_weather_assessment():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": PUNE_LATITUDE,
        "longitude": PUNE_LONGITUDE,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "hourly": (
            "precipitation_probability,"
            "precipitation,"
            "weather_code"
        ),
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }

    try:
        response = httpx.get(
            url,
            params=params,
            timeout=10.0,
        )

        response.raise_for_status()

        data = response.json()

    except httpx.HTTPError as exc:
        return {
            "available": False,
            "error": f"Weather service unavailable: {exc}",
        }

    current = data.get("current", {})

    weather_code = current.get("weather_code")
    precipitation = current.get("precipitation", 0.0)

    weather_description = WEATHER_CODES.get(
        weather_code,
        "Unknown conditions",
    )

    if precipitation > 0:
        weather_risk = "rain"
        walking_warning = True
        recommendation = (
            "Rain is currently present. Prefer metro, bus, or auto "
            "over long walking segments."
        )
    elif weather_code in {61, 63, 65, 80, 81, 82}:
        weather_risk = "rain"
        walking_warning = True
        recommendation = (
            "Rain may affect the trip. Consider reducing long "
            "walking segments."
        )
    elif weather_code in {95, 96, 99}:
        weather_risk = "storm"
        walking_warning = True
        recommendation = (
            "Thunderstorm conditions may affect the trip. "
            "Avoid unnecessary outdoor walking."
        )
    elif weather_code in {45, 48}:
        weather_risk = "fog"
        walking_warning = False
        recommendation = (
            "Reduced visibility is possible. Allow extra travel time."
        )
    else:
        weather_risk = "low"
        walking_warning = False
        recommendation = (
            "Weather conditions are currently suitable for the trip."
        )

    return {
        "available": True,
        "city": "Pune",
        "temperature_c": current.get("temperature_2m"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "precipitation_mm": precipitation,
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "weather_code": weather_code,
        "description": weather_description,
        "weather_risk": weather_risk,
        "walking_warning": walking_warning,
        "recommendation": recommendation,
        "source": "Open-Meteo",
    }