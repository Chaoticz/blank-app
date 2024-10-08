import os
import requests
import pandas as pd
import numpy as np
import streamlit as st
import time

# Bitvavo API settings
BITVAVO_API_KEY = os.getenv('BITVAVO_API_KEY')
BITVAVO_API_SECRET = os.getenv('BITVAVO_API_SECRET')
PUSHOVER_USER_KEY = os.getenv('PUSHOVER_USER_KEY')
PUSHOVER_API_TOKEN = os.getenv('PUSHOVER_API_TOKEN')

BASE_URL = 'https://api.bitvavo.com/v2/'

def get_current_prices(crypto_pairs):
    prices = {}
    for pair in crypto_pairs:
        response = requests.get(f"{BASE_URL}{pair}/ticker")
        prices[pair] = float(response.json()['last'])
    return prices

def get_historical_data(pair, days=14):
    response = requests.get(f"{BASE_URL}{pair}/candles?interval=1day&start=now-{days}d&end=now")
    data = response.json()
    return pd.DataFrame(data)

def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_sma(data, period):
    return data['close'].rolling(window=period).mean()

def calculate_ema(data, period):
    return data['close'].ewm(span=period, adjust=False).mean()

def send_notification(message):
    requests.post("https://api.pushover.net/1/messages.json", data={
        'token': PUSHOVER_API_TOKEN,
        'user': PUSHOVER_USER_KEY,
        'message': message
    })

def generate_signal(rsi, sma_short, sma_long):
    if rsi < 30 and sma_short > sma_long:
        return "Kopen"
    elif rsi > 70 and sma_short < sma_long:
        return "Verkopen"
    else:
        return "Houden"

def main():
    st.title("Crypto Monitoring App")
    crypto_pairs = ['BTC-EUR', 'ETH-EUR']
    previous_signal = {}

    while True:
        prices = get_current_prices(crypto_pairs)
        for pair in crypto_pairs:
            historical_data = get_historical_data(pair)
            rsi = calculate_rsi(historical_data)
            sma_short = calculate_sma(historical_data, 5)
            sma_long = calculate_sma(historical_data, 20)

            current_rsi = rsi.iloc[-1]
            current_sma_short = sma_short.iloc[-1]
            current_sma_long = sma_long.iloc[-1]
            signal = generate_signal(current_rsi, current_sma_short, current_sma_long)

            if pair not in previous_signal or previous_signal[pair] != signal:
                send_notification(f"{pair}: {signal}")
                previous_signal[pair] = signal

        st.write(prices)
        time.sleep(10)

if __name__ == "__main__":
    main()
