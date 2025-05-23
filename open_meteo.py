import openmeteo_requests
import requests_cache
from retry_requests import retry
import httpx as requests
import pandas
import matplotlib.pyplot as plt


# ref: https://open-meteo.com/en/docs
# Lookup city coordinates using geocoding api by open-meteo
def geocoding_search_city(city: str) -> dict:
    """
    Retrieve geographic coordinates (latitude, longitude) for a given city name.

    Args:
            city (str): Name of the city to look up.
    """
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&format=json"
    response = requests.get(url=url)
    return response.json().get("results")[0]


def scrape_weather_data(latitude: float, longitude: float) -> dict:
    """
    Fetches air quality weather data for given geographic coordinates using the Open-Meteo Air Quality API.

    Args:
        latitude (float): The latitude of the location to fetch data for.
        longitude (float): The longitude of the location to fetch data for.
    """
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)

    openmeteo = openmeteo_requests.Client(session=retry_session)
    # Query params to scrape weather data
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide"],
    }

    # Process location.
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    current = response.Current()

    weather_conditions = {}
    weather_conditions["latitude"] = response.Latitude()
    weather_conditions["longitude"] = response.Longitude()
    weather_conditions["current_pm10"] = current.Variables(0).Value()
    weather_conditions["current_pm2_5"] = current.Variables(1).Value()
    weather_conditions["current_carbon_monoxide"] = current.Variables(2).Value()
    weather_conditions["current_nitrogen_dioxide"] = current.Variables(3).Value()

    return weather_conditions

def scrape_historic_weather_data(latitude: float, longitude: float) -> str:
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)

    openmeteo = openmeteo_requests.Client(session=retry_session)
    # Query params to scrape weather data
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
	    "hourly": ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide"],
	    "past_days": 7
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()

    weather_hourly = {
        "date": pandas.date_range(
            start=pandas.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pandas.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pandas.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "pm10": hourly.Variables(0).ValuesAsNumpy(),
        "pm2_5": hourly.Variables(1).ValuesAsNumpy(),
        "carbon_monoxide": hourly.Variables(2).ValuesAsNumpy(),
        "nitrogen_dioxide": hourly.Variables(3).ValuesAsNumpy(),
    }

    hourly_dataframe = pandas.DataFrame(weather_hourly)

    plt.figure(figsize=(15,6))
    plt.plot(hourly_dataframe["date"], hourly_dataframe["pm10"],label="PM10")
    plt.plot(hourly_dataframe["date"], hourly_dataframe["pm2_5"],label="PM2.5")
    plt.plot(hourly_dataframe["date"], hourly_dataframe["carbon_monoxide"],label="CO")
    plt.plot(hourly_dataframe["date"], hourly_dataframe["nitrogen_dioxide"],label="NO2")

    plt.xlabel("Date")
    plt.ylabel("Concentration")
    plt.title("Historic Air Quality Data (last 7 days)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    image_path = "historic_weather_plot.png"
    plt.savefig(image_path)
    plt.close()

    return image_path
    

def main() -> None:
    """This function implemented to debug this module separately from the TG bot

    It does not take any input and does not return any values, just checks basic functionality
    """
    city_name = input("Please enter city name:")
    city_data = geocoding_search_city(city_name)

    hourly_dataframe = scrape_historic_weather_data(city_data.get("latitude"), city_data.get("longitude"))
    print(hourly_dataframe)
    
    weather_conditions = scrape_weather_data(
        city_data.get("latitude"), city_data.get("longitude")
    )
    print(city_name, city_data, weather_conditions)


if __name__ == "__main__":
    main()
