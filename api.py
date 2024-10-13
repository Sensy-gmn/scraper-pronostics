from flask import Flask, jsonify
import json
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Définir le fuseau horaire de Paris
paris_tz = pytz.timezone('Europe/Paris')

@app.route('/pronostics', methods=['GET'])
def get_pronostics():
    # Obtenir la date actuelle dans le fuseau horaire de Paris
    current_date = datetime.now(paris_tz).strftime("%Y-%m-%d")
    filename = f"pronostics_{current_date}.json"
    
    if not os.path.exists(filename):
        return jsonify({"error": "Pas de pronostics disponibles pour aujourd'hui"}), 404
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            pronostics = json.load(f)
        return jsonify(pronostics)
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la lecture des pronostics: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
