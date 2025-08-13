import json
from typing import Optional, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    location: str = Field(description="The city or location to get weather for")
    days: Optional[int] = Field(default=1, description="Number of forecast days (1-10)")


class WeatherMCPTool(BaseTool):
    name: str = "weather_tool"
    description: str = (
        """
    Get current weather and forecast data for any location.
    This tool provides detailed weather information including temperature, 
    conditions, humidity, wind speed, and multi-day forecasts.
    """
    )
    args_schema: Type[BaseModel] = WeatherInput
    api_key: str = Field(description="WeatherAPI key")
    base_url: str = Field(default="http://api.weatherapi.com/v1", description="WeatherAPI base URL")

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key=api_key, **kwargs)

    def _run(self, location: str, days: int = 1) -> str:
        """Get weather data for a location"""
        try:
            # Use forecast API which includes both current and forecast data
            forecast_url = f"{self.base_url}/forecast.json"
            forecast_params = {
                "key": self.api_key,
                "q": location,
                "days": min(max(days, 1), 10),  # Ensure days is between 1-10
                "aqi": "yes",
                "alerts": "yes",
            }

            print(f"Making request to: {forecast_url}")
            print(f"Parameters: {forecast_params}")

            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)

            # Check for API errors
            if forecast_response.status_code == 400:
                error_data = forecast_response.json()
                return f"API Error: {error_data.get('error', {}).get('message', 'Bad request')}"
            elif forecast_response.status_code == 401:
                return "API Error: Invalid API key. Please check your WeatherAPI key."
            elif forecast_response.status_code == 403:
                return "API Error: API key has exceeded quota or doesn't have access to this resource."

            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Debug: Print raw response structure
            print("Raw API Response Keys:", list(forecast_data.keys()))

            # Validate response structure
            if "location" not in forecast_data or "current" not in forecast_data:
                return f"Invalid API response structure: {list(forecast_data.keys())}"

            # Format the response with safe data extraction
            location_data = forecast_data.get("location", {})
            current_data = forecast_data.get("current", {})
            forecast_days = forecast_data.get("forecast", {}).get("forecastday", [])

            weather_info = {
                "location": {
                    "name": location_data.get("name", "Unknown"),
                    "region": location_data.get("region", ""),
                    "country": location_data.get("country", ""),
                    "local_time": location_data.get("localtime", ""),
                    "latitude": location_data.get("lat", 0),
                    "longitude": location_data.get("lon", 0),
                },
                "current": {
                    "last_updated": current_data.get("last_updated", ""),
                    "temperature_c": current_data.get("temp_c", 0),
                    "temperature_f": current_data.get("temp_f", 0),
                    "condition": current_data.get("condition", {}).get("text", "Unknown"),
                    "condition_icon": current_data.get("condition", {}).get("icon", ""),
                    "wind_kph": current_data.get("wind_kph", 0),
                    "wind_mph": current_data.get("wind_mph", 0),
                    "wind_dir": current_data.get("wind_dir", ""),
                    "humidity": current_data.get("humidity", 0),
                    "feels_like_c": current_data.get("feelslike_c", 0),
                    "feels_like_f": current_data.get("feelslike_f", 0),
                    "uv_index": current_data.get("uv", 0),
                    "visibility_km": current_data.get("vis_km", 0),
                    "pressure_mb": current_data.get("pressure_mb", 0),
                    "is_day": current_data.get("is_day", 1),
                },
                "forecast": [],
            }

            # Add air quality if available
            if "air_quality" in current_data:
                weather_info["current"]["air_quality"] = current_data["air_quality"]

            # Process forecast data
            for day_data in forecast_days:
                day_weather = day_data.get("day", {})
                astro_data = day_data.get("astro", {})

                day_info = {
                    "date": day_data.get("date", ""),
                    "max_temp_c": day_weather.get("maxtemp_c", 0),
                    "min_temp_c": day_weather.get("mintemp_c", 0),
                    "max_temp_f": day_weather.get("maxtemp_f", 0),
                    "min_temp_f": day_weather.get("mintemp_f", 0),
                    "avg_temp_c": day_weather.get("avgtemp_c", 0),
                    "condition": day_weather.get("condition", {}).get("text", "Unknown"),
                    "condition_icon": day_weather.get("condition", {}).get("icon", ""),
                    "chance_of_rain": day_weather.get("daily_chance_of_rain", 0),
                    "chance_of_snow": day_weather.get("daily_chance_of_snow", 0),
                    "max_wind_kph": day_weather.get("maxwind_kph", 0),
                    "avg_humidity": day_weather.get("avghumidity", 0),
                    "uv_index": day_weather.get("uv", 0),
                    "sunrise": astro_data.get("sunrise", ""),
                    "sunset": astro_data.get("sunset", ""),
                    "moon_phase": astro_data.get("moon_phase", ""),
                }
                weather_info["forecast"].append(day_info)

            # Add alerts if available
            if "alerts" in forecast_data and forecast_data["alerts"].get("alert"):
                weather_info["alerts"] = forecast_data["alerts"]["alert"]

            return json.dumps(weather_info, indent=2)

        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to weather service. Check your internet connection."
        except requests.exceptions.HTTPError as e:
            return f"HTTP Error: {e.response.status_code} - {e.response.reason}"
        except json.JSONDecodeError:
            return "Error: Invalid response format from weather service."
        except KeyError as e:
            return f"Error: Missing expected data field: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)} (Type: {type(e).__name__})"


__all__ = ["WeatherInput", "WeatherMCPTool"]