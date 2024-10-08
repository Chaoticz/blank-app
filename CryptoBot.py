import streamlit as st
import requests
import time
import numpy as np
import pandas as pd

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
            'priceChange': float(data.get('priceChange', 0)),  # Standaardwaarde 0 als het niet bestaat
            'open': float(data.get('open', 0)),  # Standaardwaarde 0 als het niet bestaat
            'high': float(data.get('high', 0)),  # Standaardwaarde 0 als het niet bestaat
            'low': float(data.get('low', 0)),  # Standaardwaarde 0 als het niet bestaat
            'volume': float(data.get('volume', 0)),  # Standaardwaarde 0 als het niet bestaat
            'last': float(data.get('last', 0))  # Standaardwaarde 0 als het niet bestaat
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

# Functie voor de beslissingslogica
def decision_strategy(historical_data):
    price_change = historical_data['priceChange']
    ma_short = historical_data['last']  # Voorbeeld, hier zou je het 50-daags gemiddelde berekenen
    ma_long = historical_data['open']  # Voorbeeld, hier zou je het 200-daags gemiddelde berekenen
    rsi = calculate_rsi([historical_data['open'], historical_data['high'], historical_data['low'], historical_data['last']])

    # Beslissingslogica gebaseerd op RSI, MA, en prijsverandering
    if rsi is not None:
        if rsi < 30:
            return "Kopen"  # Oververkocht
        elif rsi > 70:
            return "Verkopen"  # Overgekocht
    if ma_short > ma_long:
        return "Kopen"  # Korte termijn MA is boven lange termijn MA
    elif ma_short < ma_long:
        return "Verkopen"  # Korte termijn MA is onder lange termijn MA
    else:
        return "Houden"  # Geen duidelijke signalen

# Streamlit app
st.title("Crypto Beslissings Tool met Pushmeldingen")

selected_crypto = st.selectbox("Kies een cryptocurrency:", ['WIF', 'SOL'])
if selected_crypto:
    # Element voor de dynamische tabel
    table_placeholder = st.empty()

    previous_advice = None  # Voor het opslaan van het vorige advies

    # Loop om de prijs elke 10 seconden te verversen
    while True:
        # Verkrijg huidige prijs en historische gegevens
        current_price = get_crypto_price(API_KEY, selected_crypto)
        historical_data = get_historical_data(API_KEY, selected_crypto)

        if current_price is not None and historical_data is not None:
            # Bereken advies
            current_advice = decision_strategy(historical_data)

            # Maak een tabel om de gegevens overzichtelijk te tonen
            table_data = {
                'Kenmerk': ['Huidige Prijs (EUR)', 'Prijsverandering (24h)', 'Volume', 'Laatste Prijs', 'Advies'],
                'Waarde': [
                    f"{current_price:.2f}",
                    f"{historical_data['priceChange']:.2f}",
                    f"{historical_data['volume']:.2f}",
                    f"{historical_data['last']:.2f}",
                    current_advice
                ]
            }
            df = pd.DataFrame(table_data)

            # Vernieuw de tabel binnen hetzelfde element
            table_placeholder.table(df)

            # Controleer of het advies is veranderd
            if previous_advice != current_advice:
                title = f"Advies verandering voor {selected_crypto}"
                message = f"Nieuw advies: {current_advice}"
                send_push_notification(title, message)
                previous_advice = current_advice

        time.sleep(10)  # Wacht 10 seconden voordat je opnieuw ophaalt
