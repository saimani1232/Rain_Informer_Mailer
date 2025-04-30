from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import smtplib
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'my-key')

# Email configuration
MY_EMAIL = os.getenv('MY_EMAIL')
MY_PASSWORD = os.getenv('MY_PASSWORD')

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GEO_API_URL = "https://api.api-ninjas.com/v1/geocoding"
LOC_API_URL = "https://us1.locationiq.com/v1/reverse"
GEO_API_KEY = os.getenv('GEO_API_KEY')
LOC_API_KEY = os.getenv('LOC_API_KEY')

def send_email(recipient, location, weather_data):
    """Send an email alert with detailed weather information"""
    # Format the weather summary for email
    weather_summary = format_weather_summary(weather_data)
    
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=recipient,
            msg=(
                "Subject: 🌧️ Weather Alert: Updated Forecast for Your Location!\n"
                "Content-Type: text/plain; charset=utf-8\n\n"
                f"Hello, weather warrior!,\n\n"
                "We hope you're having a great day! Here's your detailed weather forecast from WeatherWatch:\n\n"
                f"Location: {location}\n\n"
                f"{weather_summary}\n\n"
                "Stay prepared and plan your day accordingly!\n\n"
                "Best regards,\nWeatherWatch Team\n"
                "\"Helping you stay one step ahead of the weather!\""
            ).encode("utf-8")
        )

def format_weather_summary(weather_data):
    """Format weather data into a readable summary for email"""
    if not weather_data or 'hourly' not in weather_data:
        return "Weather data unavailable at this time."
    
    # Determine overall weather condition
    condition = "Rainy" if any(r > 0.5 for r in weather_data['hourly']['rain'][:24]) else "Clear"
    emoji = "🌧️" if condition == "Rainy" else "☀️"
    
    # Get temperature range if available
    temp_range = ""
    if 'temperature_2m' in weather_data['hourly']:
        temps = weather_data['hourly']['temperature_2m'][:24]
        min_temp = min(temps)
        max_temp = max(temps)
        temp_unit = weather_data['hourly_units'].get('temperature_2m', '°C')
        temp_range = f"Temperature Range: {min_temp}{temp_unit} to {max_temp}{temp_unit}\n"

    # Format precipitation info
    rain_data = weather_data['hourly']['rain'][:24]
    max_rain = max(rain_data)
    rain_hours = sum(1 for r in rain_data if r > 0.1)
    rain_unit = weather_data['hourly_units'].get('rain', 'mm')
    
    rain_summary = f"Weather Condition: {condition} {emoji}\n"
    rain_summary += f"Maximum Precipitation: {max_rain}{rain_unit}\n"
    
    if rain_hours > 0:
        rain_summary += f"Expected Rain: {rain_hours} hours throughout the day\n"
        rain_time = "morning" if rain_data[:8].count(max_rain) > 0 else "afternoon" if rain_data[8:16].count(max_rain) > 0 else "evening"
        rain_summary += f"Heaviest Rain: Expected in the {rain_time}\n"
        rain_summary += "\nPlease remember to carry an umbrella or raincoat to stay dry. Drive safe if you're heading out!"
    else:
        rain_summary += "No significant precipitation expected today."
    
    return f"{temp_range}{rain_summary}"

def get_weather(latitude, longitude):
    """Get comprehensive weather data from Open Meteo API"""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,rain,showers,weathercode,cloudcover,windspeed_10m",
        "forecast_days": "1",
        "timezone": "auto",
    }
    response = requests.get(OPEN_METEO_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_weather_icon(weathercode):
    """Map Open Meteo weather codes to appropriate emoji icons"""
    weather_icons = {
        0: "☀️",  # Clear sky
        1: "🌤️",  # Mainly clear
        2: "⛅",  # Partly cloudy
        3: "☁️",  # Overcast
        45: "🌫️",  # Fog
        48: "🌫️",  # Depositing rime fog
        51: "🌦️",  # Light drizzle
        53: "🌦️",  # Moderate drizzle
        55: "🌧️",  # Dense drizzle
        56: "🌨️",  # Light freezing drizzle
        57: "🌨️",  # Dense freezing drizzle
        61: "🌦️",  # Slight rain
        63: "🌧️",  # Moderate rain
        65: "🌧️",  # Heavy rain
        66: "🌨️",  # Light freezing rain
        67: "🌨️",  # Heavy freezing rain
        71: "❄️",  # Slight snow fall
        73: "❄️",  # Moderate snow fall
        75: "❄️",  # Heavy snow fall
        77: "❄️",  # Snow grains
        80: "🌦️",  # Slight rain showers
        81: "🌧️",  # Moderate rain showers
        82: "🌧️",  # Violent rain showers
        85: "🌨️",  # Slight snow showers
        86: "🌨️",  # Heavy snow showers
        95: "⛈️",  # Thunderstorm
        96: "⛈️",  # Thunderstorm with slight hail
        99: "⛈️",  # Thunderstorm with heavy hail
    }
    return weather_icons.get(weathercode, "🌡️")

def get_location(city_name):
    """Get latitude and longitude data for a city name"""
    headers = {"X-Api-Key": GEO_API_KEY}
    response = requests.get(f"{GEO_API_URL}?city={city_name}", headers=headers)
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return None

def get_name(lati, longi):
    """Get location name from latitude and longitude"""
    params = {
        "lat": lati,
        "lon": longi,
        "key": LOC_API_KEY,
        "format": "json"
    }
    try:
        response = requests.get(LOC_API_URL, params=params)
        if response.status_code != 200:
            print(f"API request failed with status code {response.status_code}: {response.text}")
            return "Unknown Location"
        data = response.json()
        if 'display_name' not in data:
            print("The response did not contain 'display_name'.")
            return "Unknown Location"
        return data['display_name']
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return "Unknown Location"
    except ValueError as e:
        print(f"Error in JSON decoding: {e}")
        return "Unknown Location"

def prepare_hourly_forecast(weather_data):
    """Prepare hourly forecast data for display"""
    if not weather_data or 'hourly' not in weather_data:
        return []
    
    # Get hourly timestamps and convert to readable time
    timestamps = weather_data['hourly']['time'][:24]
    temps = weather_data['hourly'].get('temperature_2m', [0] * 24)[:24]
    rain = weather_data['hourly'].get('rain', [0] * 24)[:24]
    weathercodes = weather_data['hourly'].get('weathercode', [0] * 24)[:24]
    cloudcover = weather_data['hourly'].get('cloudcover', [0] * 24)[:24]
    windspeed = weather_data['hourly'].get('windspeed_10m', [0] * 24)[:24]
    
    forecast = []
    for i in range(24):
        # Extract hour from ISO timestamp
        dt = datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))
        hour = dt.strftime("%H:%M")
        
        # Get weather icon
        icon = get_weather_icon(weathercodes[i]) if i < len(weathercodes) else "🌡️"
        
        forecast.append({
            'hour': hour,
            'temp': temps[i] if i < len(temps) else 0,
            'rain': rain[i] if i < len(rain) else 0,
            'icon': icon,
            'clouds': cloudcover[i] if i < len(cloudcover) else 0,
            'wind': windspeed[i] if i < len(windspeed) else 0
        })
    
    return forecast

@app.route("/", methods=["GET", "POST"])
def index():
    emoji, location = "☀️", "No data yet"
    forecast_data = []

    if request.method == "POST":
        input_type = request.form["input_type"]
        recipient = None
        latitude, longitude = None, None
        location = None

        if input_type == "latlong":
            latitude = request.form["latitude"]
            longitude = request.form["longitude"]
            recipient = request.form["recipient_email_latlong"]
            location = get_name(latitude, longitude)

        elif input_type == "city":
            city_name = request.form["city_name"]
            recipient = request.form["recipient_email_city"]
            location_data = get_location(city_name)
            if location_data:
                latitude, longitude = location_data["latitude"], location_data["longitude"]
                location = location_data["name"]
            else:
                flash(f"Could not find location data for {city_name}.")
                return render_template("index.html", emoji=False, location="No data yet")

        # Get comprehensive weather data
        weather_data = get_weather(latitude, longitude)
        
        if weather_data:
            # Check for rain
            is_rainy = any(r > 0.5 for r in weather_data['hourly']['rain'][:24])
            
            # Get weather code for the current hour
            current_hour = datetime.now().hour
            if 'weathercode' in weather_data['hourly'] and len(weather_data['hourly']['weathercode']) > current_hour:
                current_weather_code = weather_data['hourly']['weathercode'][current_hour]
                emoji = get_weather_icon(current_weather_code)
            else:
                emoji = "🌧️" if is_rainy else "☀️"
            
            # Prepare hourly forecast data
            forecast_data = prepare_hourly_forecast(weather_data)
            
            # Send email if rain is expected
            if is_rainy:
                flash(f"Rain expected in {location}! Sending detailed weather email...")
                send_email(recipient, location, weather_data)
            else:
                flash(f"No significant rain expected today in {location}.")
            
            # Pass forecast_data to the template
            return render_template(
                "index.html", 
                emoji=emoji, 
                location=location, 
                forecast_data=json.dumps(forecast_data),
                weather_units=weather_data.get('hourly_units', {})
            )
        else:
            flash("Error fetching weather data. Please try again.")
    
    return render_template("index.html", emoji=False, location=location)

@app.route("/map-weather", methods=["POST"])
def map_weather():
    """API endpoint for fetching weather data for map locations"""
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not latitude or not longitude:
        return jsonify({"error": "Missing coordinates"}), 400
    
    weather_data = get_weather(latitude, longitude)
    location = get_name(latitude, longitude)
    
    if not weather_data:
        return jsonify({"error": "Could not fetch weather data"}), 500
    
    # Prepare simplified response
    current_hour = datetime.now().hour
    if 'weathercode' in weather_data['hourly'] and len(weather_data['hourly']['weathercode']) > current_hour:
        current_weather_code = weather_data['hourly']['weathercode'][current_hour]
        emoji = get_weather_icon(current_weather_code)
    else:
        is_rainy = any(r > 0.5 for r in weather_data['hourly']['rain'][:24])
        emoji = "🌧️" if is_rainy else "☀️"
    
    # Get current temperature if available
    current_temp = None
    if 'temperature_2m' in weather_data['hourly'] and len(weather_data['hourly']['temperature_2m']) > current_hour:
        current_temp = f"{weather_data['hourly']['temperature_2m'][current_hour]}{weather_data['hourly_units'].get('temperature_2m', '°C')}"
    
    return jsonify({
        "location": location,
        "emoji": emoji,
        "temperature": current_temp,
        "will_rain": any(r > 0.5 for r in weather_data['hourly']['rain'][:24])
    })

if __name__ == "__main__":
    app.run(debug=True)
