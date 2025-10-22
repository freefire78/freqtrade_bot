import subprocess
import os
import time
import threading
from flask import Flask

keep_alive_app = Flask(__name__)

@keep_alive_app.route('/')
def home():
    return '''
    <h1>🤖 FreqTrade Bot</h1>
    <p>FreqTrade is running...</p>
    <p><a href="/">Access FreqTrade UI</a></p>
    <p>If you see "UI not installed", wait a moment and refresh - UI is installing during build.</p>
    '''

def run_keep_alive():
    keep_alive_app.run(host='0.0.0.0', port=8081)

def start_keep_alive():
    t = threading.Thread(target=run_keep_alive)
    t.daemon = True
    t.start()
    print("🔄 Keep-alive server started on port 8081")

def check_ui():
    """Проверяет установлен ли UI"""
    ui_path = os.path.join('user_data', 'ui')
    if os.path.exists(ui_path):
        print("✅ FreqTrade UI is installed")
        # Покажем что в папке ui
        try:
            ui_files = os.listdir(ui_path)
            print(f"   UI files: {len(ui_files)} items")
            return True
        except:
            print("   Could not list UI files")
            return True
    else:
        print("❌ FreqTrade UI is NOT installed")
        return False

def install_ui_if_needed():
    """Устанавливает UI если он не установлен"""
    if not check_ui():
        print("📦 Installing FreqTrade UI...")
        try:
            result = subprocess.run([
                'freqtrade', 'install-ui',
                '--userdir', 'user_data'
            ], capture_output=True, text=True, timeout=120)
            
            print(f"UI installation completed with code: {result.returncode}")
            if result.returncode == 0:
                print("✅ UI installed successfully")
            else:
                print(f"⚠️ UI installation issues: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ UI installation timed out")
        except Exception as e:
            print(f"❌ UI installation error: {e}")

def run_freqtrade():
    print("🚀 Starting FreqTrade...")
    
    # Проверяем и при необходимости устанавливаем UI
    install_ui_if_needed()
    
    # Финальная проверка
    check_ui()
    
    try:
        # Запускаем FreqTrade веб-сервер
        print("🌐 Starting FreqTrade webserver...")
        subprocess.run([
            'freqtrade', 'webserver',
            '--userdir', 'user_data',
            '--config', 'user_data/config.json'
        ])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("🤖 FreqTrade Bot - With UI Support")
    print("==========================================")
    
    start_keep_alive()
    time.sleep(2)
    run_freqtrade()