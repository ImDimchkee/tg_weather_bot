import openmeteo_requests
import requests_cache
from retry_requests import retry
import httpx as req

# ref: https://open-meteo.com/en/docs

# Lookup city coordinates using geocoding api by open-meteo
def geocoding_search_city(city: str) -> dict:
    response = req.get(url="https://geocoding-api.open-meteo.com/v1/search" + f"?name={city}&count=1&format=json")
    return response.json().get('results')[0]


def scrape_weather_data(latitude: float, longitude: float) -> dict:
	
	weather_conditions = {}

	# Setup the Open-Meteo API client with cache and retry on error
	url = "https://air-quality-api.open-meteo.com/v1/air-quality"
	cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
	retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
	openmeteo = openmeteo_requests.Client(session = retry_session)

	
    # Query params to scrape weather data
	params = {
		"latitude": latitude,
		"longitude": longitude,
		"current": ["european_aqi", "pm10", "pm2_5", "carbon_monoxide"],
		"timezone": "auto",
	}
	responses = openmeteo.weather_api(url, params=params)

	# Process location.
	response = responses[0]
	current = response.Current()
	
	weather_conditions["latitude"] = response.Latitude()
	weather_conditions["longitude"] = response.Longitude()
	
	weather_conditions["current_european_aqi"] = current.Variables(0).Values(0)
	weather_conditions["current_pm10"] = current.Variables(1).Value()
	weather_conditions["current_pm2_5"] = current.Variables(2).Value()
	weather_conditions["current_carbon_monoxide"] = current.Variables(3).Value()

	return weather_conditions


def main() -> None:
	"""This function implemented to debug this module separately from the TG bot

	It does not take any input and does not return any values, just checks basic functionality
	"""
	city_name = input("Please enter city name:")
	city_data = geocoding_search_city(city_name)
	weather_conditions = scrape_weather_data(city_data.get("latitude"), city_data.get("longitude"))
	print(city_name, city_data, weather_conditions)

if __name__ == "__main__":
	main()
