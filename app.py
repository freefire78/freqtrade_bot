import subprocess
import os
import time
import threading
from flask import Flask

# Keep-alive сервер
keep_alive_app = Flask(__name__)

@keep_alive_app.route('/')
def home():
    return "🤖 FreqTrade Bot is alive!"

@keep_alive_app.route('/health')
def health():
    return "✅ Healthy"

def run_keep_alive():
    keep_alive_app.run(host='0.0.0.0', port=8080)

def start_keep_alive():
    t = threading.Thread(target=run_keep_alive)
    t.daemon = True
    t.start()
    print("🔄 Keep-alive server started")

def run_freqtrade():
    """Запуск FreqTrade без аргумента --port"""
    print("🚀 Starting FreqTrade...")
    
    try:
        # Только необходимые аргументы
        subprocess.run([
            'freqtrade', 'webserver',
            '--config', 'config.json',
            '--userdir', 'user_data'
        ])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("🤖 FreqTrade Bot - Simplified Version")
    print("==========================================")
    
    start_keep_alive()
    time.sleep(2)
    run_freqtrade()