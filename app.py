import subprocess
import sys
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="FreqTrade Trading Bot")

@app.get("/")
def read_root():
    return {"message": "FreqTrade Trading Bot is running!"}

@app.get("/logs")
def get_logs():
    try:
        with open('freqtrade_logs.txt', 'r') as f:
            logs = f.read()
        return {"logs": logs}
    except FileNotFoundError:
        return {"logs": "No logs yet"}

def run_bot():
    print("Starting FreqTrade bot with logging...")
    try:
        # Запускаем freqtrade с логированием в файл
        with open('freqtrade_logs.txt', 'w') as log_file:
            process = subprocess.Popen([
                'freqtrade', 'trade',
                '--config', 'config.json',
                '--strategy-path', 'strategies',
                '--verbosity', 'INFO'
            ], stdout=log_file, stderr=subprocess.STDOUT, text=True)
            
            # Также выводим логи в консоль Render
            with open('freqtrade_logs.txt', 'r') as f:
                while True:
                    line = f.readline()
                    if line:
                        print(line.strip())
                    # Можно добавить небольшую задержку
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Запускаем бот в фоновом режиме
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем веб-сервер
    uvicorn.run(app, host="0.0.0.0", port=8000)