from freqtrade import __version__
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="FreqTrade Bot")

@app.get("/")
def read_root():
    return {
        "message": "FreqTrade Bot is running!",
        "version": __version__,
        "status": "active"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print(f"FreqTrade version: {__version__}")
    print("FreqTrade bot is deployed successfully!")
    # Запускаем веб-сервер
    uvicorn.run(app, host="0.0.0.0", port=8000)