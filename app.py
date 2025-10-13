from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import requests
from flask import Flask, redirect, request, url_for, flash, get_flashed_messages, render_template
from markupsafe import escape
import os
from dotenv import load_dotenv

load_dotenv()  



app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_local_hour(lat, lon):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat)
    if tz_name:
        tz = pytz.timezone(tz_name)
        return datetime.now(tz).strftime('%H:%M')
    else:
        return None

def get_snarky_weather_remark(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        try:
            choices = response.json().get('choices')
            if choices and len(choices) > 0:
                return choices[0].get('message', {}).get('content', '').strip() or "[AI had nothing snarky to say—try again!]"
            return "[No response from LLM]"
        except Exception:
            return "[Invalid JSON from OpenRouter]"
    else:
        return f"OpenRouter API Error: {response.status_code}"
@app.route('/', methods=["GET", "POST"])
@app.route("/weather", methods=["GET", "POST"])
def weather():
    if request.method == "POST":
        city = request.form.get("city")
        if city:
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_KEY}"
            response = requests.get(weather_url)
            if response.status_code == 200:
                weather_data = response.json()
                description = weather_data['weather'][0]['description']
                temp_k = weather_data['main']['temp']
                temp_f = (temp_k - 273.15) * 9/5 + 32
                lat, lon = weather_data['coord']['lat'], weather_data['coord']['lon']
                local_time = get_local_hour(lat, lon)
                prompt = (
                    f"You are a snarky, dry, rude Gen Z weather forecaster. NO HASHTAGS. "
                    f"Today's weather in {city}: '{description}'. Local time is {local_time}. Weather is {int(temp_f)}. "
                    "Give a funny, short, snarky remark."
                )
                snark = get_snarky_weather_remark(prompt)
                flash(snark)
            else:
                flash("City not found.")
        else:
            flash("City not found.")
        return redirect(url_for('weather'))

    messages = get_flashed_messages()
    weather_message = messages[0] if messages else ""
    return render_template('index.html', weather_message=escape(weather_message))

if __name__ == '__main__':
    app.run(debug=True)
