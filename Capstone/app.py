from flask import Flask
from routes import init_routes
from dotenv import load_dotenv
import os

from flask import send_from_directory

app = Flask(__name__)
load_dotenv()
app.secret_key = "SECRET"
init_routes(app)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@app.route('/data/fitness_data.json')
def serve_fitness_data():
    return send_from_directory('data', 'fitness_data.json')

@app.context_processor
def inject_google_key():
    return dict(GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)

if __name__ == "__main__":
    app.run(debug=True)
