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
    """Запуск FreqTrade с конфигом из user_data"""
    print("🚀 Starting FreqTrade...")
    
    try:
        # Указываем путь к конфигу в user_data
        config_path = os.path.join('user_data', 'config.json')
        print(f"📁 Config path: {config_path}")
        
        # Проверяем существует ли файл
        if not os.path.exists(config_path):
            print(f"❌ Config file not found at: {config_path}")
            print("📂 Files in user_data:")
            for file in os.listdir('user_data'):
                print(f"   - {file}")
            return
        
        # Запускаем FreqTrade
        subprocess.run([
            'freqtrade', 'webserver',
            '--config', config_path,
            '--userdir', 'user_data'
        ])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("🤖 FreqTrade Bot - Config in user_data")
    print("==========================================")
    
    # Покажем что в user_data
    print("📂 Contents of user_data:")
    try:
        for item in os.listdir('user_data'):
            print(f"   - {item}")
    except Exception as e:
        print(f"   Error listing user_data: {e}")
    
    start_keep_alive()
    time.sleep(2)
    run_freqtrade()