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

# Functie voor de beslissingslogica
def decision_strategy(historical_data):
    price_change = historical_data['priceChange']
    ma_short = historical_data['last']  # Voorbeeld voor een kort MA
    ma_long = historical_data['open']  # Voorbeeld voor een lang MA

    # Eenvoudige beslissingslogica
    if price_change > 0:
        return "Kopen"
    elif price_change < 0:
        return "Verkopen"
    else:
        return "Houden/Wachten"

# Streamlit app setup
st.title("Crypto Overzicht: WIF en SOL")

# Maak een lege placeholder voor de dynamische tabel
table_placeholder = st.empty()

previous_advice_wif = None
previous_advice_sol = None

# Loop om de prijs elke 10 seconden te verversen
while True:
    # Verkrijg huidige prijzen en historische gegevens
    current_price_wif = get_crypto_price(API_KEY, 'WIF')
    current_price_sol = get_crypto_price(API_KEY, 'SOL')
    
    historical_data_wif = get_historical_data(API_KEY, 'WIF')
    historical_data_sol = get_historical_data(API_KEY, 'SOL')

    if current_price_wif is not None and historical_data_wif is not None and \
       current_price_sol is not None and historical_data_sol is not None:
        
        # Bereken advies voor WIF en SOL
        current_advice_wif = decision_strategy(historical_data_wif)
        current_advice_sol = decision_strategy(historical_data_sol)

        # Maak een tabel met de gegevens van zowel WIF als SOL
        table_data = {
            'Kenmerk': ['Huidige Prijs (EUR)', 'Prijsverandering (24h)', 'Volume', 'Laatste Prijs', 'Advies'],
            'WIF': [
                f"{current_price_wif:.2f}",
                f"{historical_data_wif['priceChange']:.2f}",
                f"{historical_data_wif['volume']:.2f}",
                f"{historical_data_wif['last']:.2f}",
                current_advice_wif
            ],
            'SOL': [
                f"{current_price_sol:.2f}",
                f"{historical_data_sol['priceChange']:.2f}",
                f"{historical_data_sol['volume']:.2f}",
                f"{historical_data_sol['last']:.2f}",
                current_advice_sol
            ]
        }
        
        df = pd.DataFrame(table_data)

        # Vernieuw de tabel binnen hetzelfde element
        table_placeholder.table(df)

        # Controleer of het advies is veranderd voor WIF
        if previous_advice_wif != current_advice_wif:
            title = "Advies verandering voor WIF"
            message = f"Nieuw advies: {current_advice_wif}"
            send_push_notification(title, message)
            previous_advice_wif = current_advice_wif

        # Controleer of het advies is veranderd voor SOL
        if previous_advice_sol != current_advice_sol:
            title = "Advies verandering voor SOL"
            message = f"Nieuw advies: {current_advice_sol}"
            send_push_notification(title, message)
            previous_advice_sol = current_advice_sol

    time.sleep(10)  # Wacht 10 seconden voordat de gegevens opnieuw worden opgehaald
