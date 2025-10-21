import subprocess
import os
import time
import threading
import json
from flask import Flask

keep_alive_app = Flask(__name__)

@keep_alive_app.route('/')
def home():
    return "🤖 FreqTrade Bot is alive!"

def run_keep_alive():
    keep_alive_app.run(host='0.0.0.0', port=8080)

def start_keep_alive():
    t = threading.Thread(target=run_keep_alive)
    t.daemon = True
    t.start()
    print("🔄 Keep-alive server started")

def run_freqtrade():
    print("🚀 Starting FreqTrade with detailed logging...")
    
    try:
        # Запускаем с максимальным verbose и логированием в файл
        process = subprocess.Popen([
            'freqtrade', 'webserver',
            '--config', 'user_data/config.json',
            '--userdir', 'user_data',
            '-vvv',  # Максимальная детализация логов
            '--logfile', 'freqtrade_debug.log'  # Логи в файл
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("⏳ FreqTrade process started...")
        print("📝 Detailed logs in freqtrade_debug.log")
        
        # Читаем вывод в реальном времени
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"FreqTrade: {output.strip()}")
        
        # После завершения получаем stderr
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"❌ FreqTrade STDERR: {stderr_output}")
            
        returncode = process.poll()
        print(f"🔄 FreqTrade exited with code: {returncode}")
        
    except Exception as e:
        print(f"❌ Process Error: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("🤖 FreqTrade Bot - Debug Mode")
    print("==========================================")
    
    # Проверка конфига
    config_path = 'user_data/config.json'
    if os.path.exists(config_path):
        file_size = os.path.getsize(config_path)
        print(f"📄 Config file exists, size: {file_size} bytes")
        
        # Попробуем прочитать и распарсить конфиг
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
                config = json.loads(config_content)
                print("✅ Config JSON syntax is valid!")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
        except Exception as e:
            print(f"❌ File Error: {e}")
    else:
        print("❌ Config file not found!")
    
    start_keep_alive()
    time.sleep(2)
    run_freqtrade()