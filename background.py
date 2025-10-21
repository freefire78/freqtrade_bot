from flask import Flask
from threading import Thread
import time
import requests

app = Flask('')

@app.route('/')
def home():
    return "🤖 FreqTrade Bot is alive and running!"

@app.route('/health')
def health():
    return "✅ Healthy"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Запускает Flask сервер в отдельном потоке"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("🔄 Background keep-alive server started on port 8080")