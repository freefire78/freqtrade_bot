import subprocess
import os
import sys

def run_freqtrade():
    """Запуск FreqTrade с логированием в консоль"""
    print("🚀 Starting FreqTrade Web Interface...")
    print("📝 All logs will appear here and in Render dashboard")
    
    # Получаем порт от Render
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🌐 Web interface will be available on port {port}")
    print("📊 Access your bot at: https://your-app.onrender.com/")
    
    # Запускаем FreqTrade - все его логи пойдут в консоль
    process = subprocess.run([
        'freqtrade', 'webserver',
        '--config', 'config.json',
        '--strategy-path', 'strategies', 
        '--port', str(port),
        '--verbose'
    ])
    
    return process.returncode

if __name__ == "__main__":
    exit_code = run_freqtrade()
    sys.exit(exit_code)