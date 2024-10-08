import streamlit as st
import requests
import numpy as np
import pandas as pd
import time

# Voer hier je Bitvavo API-sleutel in
API_KEY = '275ef1c47fe97b28e0a31d998ec4ec380bca4c1c2b0c3549a72cacaf98a02bc6'  # Vervang dit door je echte API-sleutel
PUSHOVER_USER_KEY = 'ucag73yvz83gz9b6fz31jqux4u7i7p'  # Vervang dit door je Pushover User Key
PUSHOVER_API_TOKEN = 'athjqvpye1dtgo4326xqg4vmu1n153'  # Vervang dit door je Pushover API Token

# Functie om Pushover notificatie te sturen
def send_push_notification(title, message):
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": title,
        "message": message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Melding succesvol verzonden!")
    else:
        print(f"Fout bij het verzenden van de melding. Status: {response.status_code}")

# Functie om de huidige prijs van een cryptocurrency op te halen
def get_crypto_price(api_key, symbol, market='EUR'):
    url = f"https://api.bitvavo.com/v2/ticker/price?market={symbol}-{market}"
    headers = {"X-Bitvavo-Access-Key": api_key}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return float(response.json()['price'])
    else:
        st.error(f"Fout bij het ophalen van de prijs voor {symbol}.")
        return None

# Functie om historische gegevens op te halen
def get_historical_data(api_key, symbol, market='EUR'):
    url = f"https://api.bitvavo.com/v2/ticker/24h?market={symbol}-{market}"
    headers = {"X-Bitvavo-Access-Key": api_key}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return {
            'priceChange': float(data.get('priceChange', 0)),
            'open': float(data.get('open', 0)),
            'high': float(data.get('high', 0)),
            'low': float(data.get('low', 0)),
            'volume': float(data.get('volume', 0)),
            'last': float(data.get('last', 0))
        }
    else:
        st.error(f"Fout bij het ophalen van historische gegevens voor {symbol}.")
        return None

# Functie om de RSI te berekenen
def calculate_rsi(prices, window=14):
    if len(prices) < window:
        return None
    delta = np.diff(prices)
    gain = (delta[delta > 0]).sum() / window
    loss = (-delta[delta < 0]).sum() / window
    
    rs = gain / loss if loss > 0 else 0
    return 100 - (100 / (1 + rs))

# Functie om de Moving Average te berekenen
def calculate_moving_average(prices, window=14):
    if len(prices) < window:
        return None
    return np.mean(prices[-window:])

# Functie om de MACD te berekenen
def calculate_macd(prices, short_window=12, long_window=26, signal_window=9):
    if len(prices) < long_window:
        return None, None
    short_ema = np.mean(prices[-short_window:])
    long_ema = np.mean(prices[-long_window:])
    macd_line = short_ema - long_ema
    signal_line = np.mean(prices[-signal_window:])
    return macd_line, signal_line

# Functie voor de beslissingslogica
def decision_strategy(historical_data, prices):
    # Initialiseer adviezen
    advice = {
        'RSI': "Houden",
        'MA': "Houden",
        'MACD': "Houden"
    }

    # Bereken indicatoren
    rsi = calculate_rsi(prices)
    ma_short = calculate_moving_average(prices, window=50)  # Korte termijn MA
    ma_long = calculate_moving_average(prices, window=200)  # Lange termijn MA
    macd, signal = calculate_macd(prices)

    # RSI logica
    if rsi is not None:
        if rsi < 30:
            advice['RSI'] = "Kopen"
        elif rsi > 70:
            advice['RSI'] = "Verkopen"

    # MA logica
    if ma_short is not None and ma_long is not None:
        if ma_short > ma_long:
            advice['MA'] = "Kopen"
        elif ma_short < ma_long:
            advice['MA'] = "Verkopen"

    # MACD logica
    if macd is not None and signal is not None:
        if macd > signal:
            advice['MACD'] = "Kopen"
        elif macd < signal:
            advice['MACD'] = "Verkopen"

    return advice

# Streamlit app setup
st.title("Crypto Overzicht: WIF en SOL")

# Stuur startmelding
send_push_notification("Crypto Bot Actief", "De Crypto beslissingsbot is nu actief.")

# Verkrijg huidige prijzen en historische gegevens voor WIF en SOL
current_price_wif = get_crypto_price(API_KEY, 'WIF')
current_price_sol = get_crypto_price(API_KEY, 'SOL')
historical_data_wif = get_historical_data(API_KEY, 'WIF')
historical_data_sol = get_historical_data(API_KEY, 'SOL')

# Voor de prijsdata (bijv. laatste 200 prijzen voor MA en MACD)
price_history_wif = []
price_history_sol = []

# Check of prijzen en historische gegevens succesvol zijn opgehaald
if current_price_wif is not None and historical_data_wif is not None:
    price_history_wif.append(current_price_wif)

if current_price_sol is not None and historical_data_sol is not None:
    price_history_sol.append(current_price_sol)

# Zorg ervoor dat de prijs geschiedenis de nodige lengte heeft voor berekeningen
if len(price_history_wif) >= 200 and len(price_history_sol) >= 200:
    # Bereken advies voor WIF en SOL
    advice_wif = decision_strategy(historical_data_wif, price_history_wif)
    advice_sol = decision_strategy(historical_data_sol, price_history_sol)

    # Maak een tabel met de gegevens van zowel WIF als SOL
    table_data = {
        'Kenmerk': ['Huidige Prijs (EUR)', 'Prijsverandering (24h)', 'Volume', 'Laatste Prijs', 'RSI', 'MA', 'MACD'],
        'WIF': [
            f"{current_price_wif:.2f}",
            f"{historical_data_wif['priceChange']:.2f}",
            f"{historical_data_wif['volume']:.2f}",
            f"{historical_data_wif['last']:.2f}",
            advice_wif['RSI'],
            advice_wif['MA'],
            advice_wif['MACD'],
        ],
        'SOL': [
            f"{current_price_sol:.2f}",
            f"{historical_data_sol['priceChange']:.2f}",
            f"{historical_data_sol['volume']:.2f}",
            f"{historical_data_sol['last']:.2f}",
            advice_sol['RSI'],
            advice_sol['MA'],
            advice_sol['MACD'],
        ],
    }

    # Controleer of de lengte van de arrays gelijk is
    if all(len(arr) == len(table_data['Kenmerk']) for arr in table_data.values()):
        # Maak DataFrame voor de tabel
        df = pd.DataFrame(table_data)
        st.table(df)
    else:
        st.error("Fout bij het maken van de tabel: arrays zijn niet van dezelfde lengte.")
else:
    st.error("Niet genoeg gegevens om berekeningen uit te voeren.")
