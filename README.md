# ☁️ Rain Informer Mailer 🌧️

A simple web application built with Flask that sends an email notification if it’s going to rain on a given day. The app pulls weather data from an external API and alerts users to stay prepared for rainy conditions.

---

🌐 **Live Demo:** https://rain-informer-mailer.onrender.com/

---

## 🚀 Features
- 🌦️ Fetches real-time weather data using an API.
- 📩 Sends email notifications if rain is expected.
- 🔒 Secure API integration for fetching weather updates.
- 🎨 Simple and user-friendly interface.
- 📡 Lightweight and efficient backend using Flask.

---

## 🛠️ Tech Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JS
- **API:** OpenWeatherMap (or any weather API of your choice)
- **Email Service:** SMTP for sending notifications

---

## 📂 Project Structure

Rain-Informer-Mailer/ ├── static/ # CSS, JS, images and other front-end assets │ ├── css/ │ │ └── styles.css │ ├── js/ │ │ └── main.js │ └── images/ │ └── logo.png ├── templates/ # Jinja2 HTML templates │ ├── index.html │ └── layout.html ├── app.py # Main Flask application ├── requirements.txt # Python dependencies ├── README.md # Project documentation └── .env # Environment variables (API keys, email credentials)

## 1️⃣ Run the Application
1. `python app.py`  
2. Open your browser and navigate to http://127.0.0.1:5000/  
   Or visit the deployed app at https://rain-informer-mailer.onrender.com/

## 🔥 Usage
Enter your city name to check the weather.  
If rain is detected, an email notification will be sent to the configured address.  
Stay prepared for rainy days! ☔

## 📧 Email Notification Preview
**Subject:** 🌧️ Rain Alert for Today!  
**Body:** It looks like it's going to rain today. Don't forget to carry an umbrella! ☔

## 🎯 To-Do / Future Enhancements
✅ Add user authentication for personalized notifications.  
✅ Enable scheduling of daily weather alerts.  
✅ Implement a database to store user preferences.

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

## 📬 Contact
If you have any questions or suggestions, feel free to reach out:

📧 Email: macherlasaimani@gmail.com  
🐙 GitHub: saimani1232

Made with ❤️ using Flask. Stay dry and stay safe! 🌧️☂️
