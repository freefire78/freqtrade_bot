import subprocess
import os
import sys
import signal
import time
import threading
import requests
from background import keep_alive

# Глобальные переменные
bot_status = "stopped"
bot_process = None
freqtrade_port = 8000
keep_alive_port = 8080

def run_freqtrade():
    """Запуск FreqTrade веб-сервера"""
    global bot_status, bot_process
    
    try:
        print("🚀 Starting FreqTrade Web Interface...")
        bot_status = "starting"
        
        print(f"🌐 FreqTrade UI will be on port {freqtrade_port}")
        print(f"🔗 Keep-alive server on port {keep_alive_port}")
        print("📝 All logs visible in Render dashboard")
        
        # Запускаем FreqTrade веб-сервер
        bot_process = subprocess.Popen([
            'freqtrade', 'webserver',
            '--config', 'config.json',
            '--strategy-path', 'strategies', 
            '--port', str(freqtrade_port),
            '--verbose'
        ])
        
        bot_status = "running"
        print("✅ FreqTrade is now RUNNING")
        
        # Ждем завершения процесса
        bot_process.wait()
        
    except Exception as e:
        bot_status = "error"
        print(f"❌ Error starting FreqTrade: {e}")
    finally:
        bot_status = "stopped"
        print("🛑 FreqTrade stopped")

def start_keep_alive_ping():
    """Пинг самого себя чтобы предотвратить сон"""
    def ping_loop():
        time.sleep(10)  # Ждем запуска сервера
        
        # Получаем URL нашего приложения (будет известен после деплоя)
        render_url = os.environ.get('RENDER_URL', '')
        
        while True:
            try:
                # Пинг основного порта FreqTrade
                response1 = requests.get(f'http://0.0.0.0:{freqtrade_port}/', timeout=10)
                print(f"🔄 FreqTrade ping: {response1.status_code}")
                
                # Пинг keep-alive порта
                response2 = requests.get(f'http://0.0.0.0:{keep_alive_port}/', timeout=10)
                print(f"🔄 Keep-alive ping: {response2.status_code}")
                
            except Exception as e:
                print(f"⚠️ Ping error: {e}")
            
            # Пинг каждые 5 минут (300 секунд)
            time.sleep(300)
    
    ping_thread = threading.Thread(target=ping_loop, daemon=True)
    ping_thread.start()
    print("🔄 Auto-ping service started")

def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown"""
    global bot_process, bot_status
    
    print("🛑 Received shutdown signal...")
    bot_status = "stopping"
    
    if bot_process:
        print("Terminating FreqTrade process...")
        bot_process.terminate()
        bot_process.wait()
    
    print("👋 Shutdown complete")
    sys.exit(0)

if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🤖 FreqTrade Bot with 24/7 Keep-Alive System")
    print("🔄 Background server will prevent auto-sleep")
    print("✅ Suitable for continuous operation")
    print("=" * 60)
    
    # Запускаем keep-alive Flask сервер
    keep_alive()
    
    # Запускаем само-пинг сервис
    start_keep_alive_ping()
    
    # Запускаем FreqTrade
    run_freqtrade()