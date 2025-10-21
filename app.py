import subprocess
import os
import time
import threading
import select
from flask import Flask

keep_alive_app = Flask(__name__)

@keep_alive_app.route('/')
def home():
    return "🤖 FreqTrade Bot is alive!"

def run_keep_alive():
    keep_alive_app.run(host='0.0.0.0', port=8081)

def start_keep_alive():
    t = threading.Thread(target=run_keep_alive)
    t.daemon = True
    t.start()
    print("🔄 Keep-alive server started on port 8081")

def run_freqtrade():
    print("🚀 Starting FreqTrade with DEBUG logging...")
    
    try:
        # Запускаем с максимальным уровнем логирования
        process = subprocess.Popen([
            'freqtrade', 'webserver',
            '--userdir', 'user_data',
            '-vvv',  # MAXIMUM VERBOSITY - все сообщения включая DEBUG
            '--logfile', 'freqtrade_debug.log'  # Дублируем логи в файл
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        print("⏳ FreqTrade process started, reading DEBUG logs...")
        print("📝 Full logs also saved to freqtrade_debug.log")
        
        # Читаем и stdout и stderr одновременно
        while True:
            reads = [process.stdout.fileno(), process.stderr.fileno()]
            ret = select.select(reads, [], [], 1)
            
            for fd in ret[0]:
                if fd == process.stdout.fileno():
                    line = process.stdout.readline()
                    if line:
                        print(f"📢 FREQTRADE: {line.strip()}")
                if fd == process.stderr.fileno():
                    line = process.stderr.readline()
                    if line:
                        print(f"🔴 FREQTRADE ERROR: {line.strip()}")
            
            # Проверяем завершился ли процесс
            if process.poll() is not None:
                # Читаем оставшиеся данные
                print("🔄 Process finished, reading remaining output...")
                for line in process.stdout:
                    print(f"📢 FREQTRADE (final): {line.strip()}")
                for line in process.stderr:
                    print(f"🔴 FREQTRADE ERROR (final): {line.strip()}")
                break
                
        returncode = process.poll()
        print(f"🔄 FreqTrade exited with code: {returncode}")
        
        # Покажем последние строки из файла логов
        if os.path.exists('freqtrade_debug.log'):
            print("=" * 60)
            print("📄 LAST LINES FROM LOG FILE:")
            print("=" * 60)
            with open('freqtrade_debug.log', 'r') as f:
                lines = f.readlines()[-50:]  # Последние 50 строк
                for line in lines:
                    print(f"LOG: {line.strip()}")
        
    except Exception as e:
        print(f"❌ Process Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("==========================================")
    print("🤖 FreqTrade Bot - DEBUG MODE")
    print("==========================================")
    
    # Детальная проверка окружения
    print("🔍 DEBUG - Environment inspection:")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Files in current dir: {os.listdir('.')}")
    print(f"   user_data/ exists: {os.path.exists('user_data')}")
    
    if os.path.exists('user_data'):
        print(f"   Files in user_data: {os.listdir('user_data')}")
        if os.path.exists('user_data/config.json'):
            file_size = os.path.getsize('user_data/config.json')
            print(f"   config.json size: {file_size} bytes")
            
            # Проверим первые 500 символов конфига
            try:
                with open('user_data/config.json', 'r', encoding='utf-8') as f:
                    preview = f.read(500)
                    print(f"   Config preview: {preview[:100]}...")
            except Exception as e:
                print(f"   Error reading config: {e}")
    
    if os.path.exists('user_data/strategies'):
        strategies = os.listdir('user_data/strategies')
        print(f"   Strategies found: {strategies}")
        for strategy in strategies:
            strategy_path = os.path.join('user_data/strategies', strategy)
            if os.path.exists(strategy_path):
                size = os.path.getsize(strategy_path)
                print(f"     {strategy}: {size} bytes")
    
    print("==========================================")
    
    start_keep_alive()
    time.sleep(2)
    run_freqtrade()