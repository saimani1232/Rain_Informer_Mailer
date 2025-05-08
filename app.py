from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import smtplib
from datetime import datetime
import json
import matplotlib.pyplot as plt
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
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

def generate_weather_graph(weather_data):
    """Generate a temperature and rain graph for the next 24 hours and return as bytes."""
    hours = [datetime.fromisoformat(t.replace('Z', '+00:00')).strftime('%H:%M') for t in weather_data['hourly']['time'][:24]]
    temps = weather_data['hourly']['temperature_2m'][:24]
    rain = weather_data['hourly']['rain'][:24]
    temp_unit = weather_data['hourly_units'].get('temperature_2m', '°C')
    rain_unit = weather_data['hourly_units'].get('rain', 'mm')

    fig, ax1 = plt.subplots(figsize=(8, 3))
    color = 'tab:red'
    ax1.set_xlabel('Hour')
    ax1.set_ylabel(f'Temperature ({temp_unit})', color=color)
    ax1.plot(hours, temps, color=color, marker='o', label='Temperature')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticks(hours[::2])
    ax1.set_xticklabels(hours[::2], rotation=45, ha='right')

    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel(f'Rain ({rain_unit})', color=color)
    ax2.bar(hours, rain, color=color, alpha=0.3, label='Rain')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def send_email(recipient, location, weather_data):
    """Send an email alert with detailed weather information and a graph attachment"""
    # Format the weather summary for email (HTML)
    weather_summary = format_weather_summary(weather_data)
    forecast_table = generate_forecast_table(weather_data)
    graph_bytes = generate_weather_graph(weather_data)

    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = recipient
    msg['Subject'] = "🌧️ Weather Alert: Updated Forecast for Your Location!"

    html = f"""
    <html>
    <body>
        <h2>WeatherWatch: Detailed Weather Forecast</h2>
        <p><b>Location:</b> {location}</p>
        {weather_summary}
        <h3>24-Hour Forecast</h3>
        {forecast_table}
        <h3>Temperature & Rain Graph</h3>
        <p><img src='cid:weathergraph' style='max-width:100%; height:auto;'/></p>
        <p>Stay prepared and plan your day accordingly!<br>
        <b>Best regards,<br>WeatherWatch Team</b><br>
        <i>Helping you stay one step ahead of the weather!</i></p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    # Attach the graph image
    image = MIMEBase('image', 'png', name='weather_graph.png')
    image.set_payload(graph_bytes)
    encoders.encode_base64(image)
    image.add_header('Content-ID', '<weathergraph>')
    image.add_header('Content-Disposition', 'inline', filename='weather_graph.png')
    msg.attach(image)

    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=recipient,
            msg=msg.as_string().encode('utf-8')
        )


def generate_forecast_table(weather_data):
    """Generate an HTML table for the 24-hour forecast."""
    if not weather_data or 'hourly' not in weather_data:
        return "<p>No forecast data available.</p>"
    hours = [datetime.fromisoformat(t.replace('Z', '+00:00')).strftime('%H:%M') for t in weather_data['hourly']['time'][:24]]
    temps = weather_data['hourly']['temperature_2m'][:24]
    rain = weather_data['hourly']['rain'][:24]
    clouds = weather_data['hourly']['cloudcover'][:24]
    wind = weather_data['hourly']['windspeed_10m'][:24]
    weathercodes = weather_data['hourly']['weathercode'][:24]
    temp_unit = weather_data['hourly_units'].get('temperature_2m', '°C')
    rain_unit = weather_data['hourly_units'].get('rain', 'mm')
    wind_unit = weather_data['hourly_units'].get('windspeed_10m', 'km/h')
    def get_icon(code):
        return get_weather_icon(code)
    table = "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse; font-size:12px;'>"
    table += "<tr><th>Hour</th><th>Icon</th><th>Temp</th><th>Rain</th><th>Clouds</th><th>Wind</th></tr>"
    for i in range(24):
        table += f"<tr><td>{hours[i]}</td><td>{get_icon(weathercodes[i])}</td><td>{temps[i]}{temp_unit}</td><td>{rain[i]}{rain_unit}</td><td>{clouds[i]}%</td><td>{wind[i]}{wind_unit}</td></tr>"
    table += "</table>"
    return table


def format_weather_summary(weather_data):
    """Format weather data into a detailed HTML summary for email"""
    if not weather_data or 'hourly' not in weather_data:
        return "<p>Weather data unavailable at this time.</p>"
    condition = "Rainy" if any(r > 0.5 for r in weather_data['hourly']['rain'][:24]) else "Clear"
    emoji = "🌧️" if condition == "Rainy" else "☀️"
    temps = weather_data['hourly']['temperature_2m'][:24]
    min_temp = min(temps)
    max_temp = max(temps)
    temp_unit = weather_data['hourly_units'].get('temperature_2m', '°C')
    rain_data = weather_data['hourly']['rain'][:24]
    max_rain = max(rain_data)
    rain_hours = sum(1 for r in rain_data if r > 0.1)
    rain_unit = weather_data['hourly_units'].get('rain', 'mm')
    summary = f"""
    <div style='font-size:14px;'>
        <b>Weather Condition:</b> {condition} {emoji}<br>
        <b>Temperature Range:</b> {min_temp}{temp_unit} to {max_temp}{temp_unit}<br>
        <b>Maximum Precipitation:</b> {max_rain}{rain_unit}<br>
        <b>Expected Rain:</b> {rain_hours} hours throughout the day<br>
    """
    if rain_hours > 0:
        rain_time = "morning" if rain_data[:8].count(max_rain) > 0 else "afternoon" if rain_data[8:16].count(max_rain) > 0 else "evening"
        summary += f"<b>Heaviest Rain:</b> Expected in the {rain_time}<br>"
        summary += "<span style='color:#1976d2;'>Please remember to carry an umbrella or raincoat to stay dry. Drive safe if you're heading out!</span>"
    else:
        summary += "<span style='color:#388e3c;'>No significant precipitation expected today.</span>"
    summary += "</div>"
    return summary


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

        # Check if 'display_name' is available
        if 'display_name' not in data:
            print("The response did not contain 'display_name'.")
            return "Unknown Location"

        # Return the 'display_name'
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


#renders the front end form and handles the user input
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
