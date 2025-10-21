from freqtrade import __version__

def main():
    print(f"FreqTrade version: {__version__}")
    print("FreqTrade bot is deployed successfully!")
    
    # Здесь можно добавить запуск вашего бота
    # или оставить для веб-интерфейса

if __name__ == "__main__":
    main()