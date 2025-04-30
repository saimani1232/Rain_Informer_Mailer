from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import smtplib
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

def send_email(recipient, location):
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=recipient,
            msg=(
                "Subject: 🌧️ Rain Alert: Weather Update for Your Location!\n"
                "Content-Type: text/plain; charset=utf-8\n\n"
                f"Hello, weather warrior!,\n\n"
                "We hope you're having a great day! 🌦️ This is a friendly reminder from WeatherWatch "
                "that rain is expected in your area. Here are the details:\n\n"
                f"Location: {location}\n\n"
                "Weather Condition: Rainy 🌧️\n\n"
                "Please remember to carry an umbrella or raincoat to stay dry. Drive safe if you’re heading out!\n\n"
                "Stay prepared,\nWeatherWatch Team\n"
                "\"Helping you stay one step ahead of the weather!\""
            ).encode("utf-8")
        )

def get_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "rain",
        "forecast_days": "1",
        "timezone": "auto",
    }
    response = requests.get(OPEN_METEO_URL, params=params)
    return response.json()["hourly"]["rain"]

def get_location(city_name):
    headers = {"X-Api-Key": GEO_API_KEY}
    response = requests.get(f"{GEO_API_URL}?city={city_name}", headers=headers)
    return response.json()[0]

def get_name(lati, longi):
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

@app.route("/", methods=["GET", "POST"])
def index():
    emoji, location = "☀️", "No data yet"
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
            latitude, longitude = location_data["latitude"], location_data["longitude"]
            location = location_data["name"]
        rain_data = get_weather(latitude, longitude)
        is_rainy = any(r > 0.6 for r in rain_data[:24])
        if is_rainy:
            flash(f"It's going to rain! in {location} Sending an email...")
            send_email(recipient, location)
            emoji = "🌧️"
        else:
            flash(f"No rain today in {location}.")
            emoji = "☀️"
        return render_template("index.html", emoji=emoji, location=location)
    return render_template("index.html", emoji=False, location=location)

if __name__ == "__main__":
    app.run(debug=True)
