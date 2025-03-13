import argparse
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import math

import numpy as np
import pandas as pd
import yfinance as yf

# Konfiguracja logowania – ustawione na tryb wysokiej ostrożności
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def validate_result(result: dict) -> dict:
    """
    Walidacja wyników obliczeń. Jeśli którąś z wartości jest nieprawidłowa,
    ustawiamy ją na bezpieczną wartość i logujemy błąd.
    """
    ticker = result.get("Ticker", "UNKNOWN")
    cp = result.get("CurrentPrice")
    ma50 = result.get("MA50")
    if cp is None or ma50 is None or cp <= 0 or ma50 <= 0:
        logging.error(
            "Niepoprawne ceny dla %s: CurrentPrice=%s, MA50=%s", ticker, cp, ma50)
        result["Score"] = 0.0

    # Flatness powinna być w przedziale [0, 1]
    flatness = result.get("Flatness", 0.0)
    if flatness < 0 or flatness > 1:
        logging.error("Flatness poza zakresem dla %s: %f", ticker, flatness)
        result["Flatness"] = max(0, min(flatness, 1))

    # Proximity również powinno być w [0, 1]
    proximity = result.get("Proximity", 0.0)
    if proximity < 0 or proximity > 1:
        logging.error("Proximity poza zakresem dla %s: %f", ticker, proximity)
        result["Proximity"] = max(0, min(proximity, 1))

    # Bonus nie powinien być mniejszy niż 1
    bonus = result.get("Bonus", 1)
    if bonus < 1:
        logging.error("Bonus mniejszy niż 1 dla %s: %f", ticker, bonus)
        result["Bonus"] = 1.0

    # Score – sprawdzamy, czy nie jest NaN lub nieskończony
    score = result.get("Score", 0.0)
    if math.isnan(score) or math.isinf(score):
        logging.error("Score nieprawidłowy dla %s: %f", ticker, score)
        result["Score"] = 0.0

    return result


def fetch_stock_data(ticker: str) -> dict:
    """
    Pobiera dane historyczne (ostatnie 70 dni) i oblicza:
      - MA50: 50-dniowa średnia zamknięć.
      - d: względna różnica (CurrentPrice - MA50) / MA50.
      - proximity: funkcja gaussowska, która maleje wraz z |d| (maksimum przy d = 0).
      - bonus: premiuje, gdy cena jest poniżej MA50 (dla d < 0).
      - flatness: miara prostoty MA50, liczona na podstawie nachylenia MA50 między ostatnim dniem a wartością sprzed 5 dni.
      - score: ostateczny wskaźnik = flatness * proximity * bonus.
    Dodatkowo pobierana jest nazwa firmy (Company) na podstawie danych z yfinance.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        # Pobranie informacji o spółce – próbujemy pobrać longName, potem shortName, w przeciwnym razie ticker
        info = ticker_obj.info
        company_name = info.get("longName") or info.get("shortName") or ticker

        # Pobieramy dane z ostatnich 70 dni – wystarczające do obliczenia MA50
        data = ticker_obj.history(period="70d")
        if data.empty or len(data) < 50:
            raise ValueError(f"Za mało danych dla {ticker}")

        data = data.sort_index()  # Uporządkowanie chronologiczne

        # Obliczamy 50-dniową średnią zamknięć
        data['MA50'] = data['Close'].rolling(window=50).mean()
        ma50_series = data['MA50'].dropna()
        if ma50_series.empty:
            raise ValueError(f"Brak obliczonej MA50 dla {ticker}")

        # Bieżące wartości
        current_price = data['Close'].iloc[-1]
        ma50_latest = ma50_series.iloc[-1]

        # Obliczamy flatness – mierzymy nachylenie MA50 między ostatnim dniem a wartością sprzed 5 dni
        if len(ma50_series) >= 5:
            ma50_5days_ago = ma50_series.iloc[-5]
            slope = (ma50_latest - ma50_5days_ago) / \
                ma50_5days_ago  # procentowa zmiana
        else:
            slope = 0.0
        threshold = 0.05  # 5% – jeśli zmiana przekracza 5%, flatness = 0
        flatness = max(0, 1 - (abs(slope) / threshold))

        # Obliczamy względną różnicę d między bieżącą ceną a MA50
        d = (current_price - ma50_latest) / ma50_latest

        # Proximity – funkcja gaussowska; maksimum przy d = 0.
        sigma = 0.03  # Parametr definiujący czułość
        proximity = math.exp(- (d ** 2) / (2 * sigma ** 2))

        # Bonus – premiujemy, gdy cena jest poniżej MA50 (d < 0)
        gamma = 1.0
        bonus = 1 + gamma * (-d) if d < 0 else 1

        # Ostateczny score
        score = flatness * proximity * bonus

        result = {
            "Ticker": ticker,
            "Company": company_name,
            "CurrentPrice": current_price,
            "MA50": ma50_latest,
            "DistancePct": d,         # dodatnie, gdy cena powyżej MA50; ujemne, gdy poniżej
            "Flatness": flatness,       # 1 = idealnie pozioma MA50, 0 = zbyt stroma
            "Proximity": proximity,     # maksymalnie 1, maleje przy większym |d|
            "Bonus": bonus,             # > 1, gdy cena poniżej MA50
            "Score": score
        }
        return validate_result(result)
    except Exception as e:
        logging.error("Błąd dla %s: %s", ticker, str(e))
        return {
            "Ticker": ticker,
            "Company": ticker,  # w razie błędu używamy tickera jako nazwy
            "CurrentPrice": None,
            "MA50": None,
            "DistancePct": 0.0,
            "Flatness": 0.0,
            "Proximity": 0.0,
            "Bonus": 0.0,
            "Score": 0.0
        }


def fetch_all_data(tickers: list) -> list:
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for res in executor.map(fetch_stock_data, tickers):
            results.append(res)
    return results


def allocate_investment(data: list, monthly_capital: float) -> list:
    """
    Alokuje miesięczny kapitał proporcjonalnie do wyliczonego wskaźnika score
    (tylko dla spółek, dla których score > 0).
    """
    df = pd.DataFrame(data)
    df = df[df['Score'] > 0].copy()
    if df.empty:
        return []
    total_score = df['Score'].sum()
    if total_score <= 0:
        logging.error("Suma score jest niepoprawna: %f", total_score)
        return []
    df['AllocationPct'] = df['Score'] / total_score
    df['AllocationPLN'] = (df['AllocationPct'] * monthly_capital).round(2)
    return df.to_dict(orient="records")


def main():
    parser = argparse.ArgumentParser(
        description="Program inwestycyjny: Im bliżej ceny do MA50 (nawet poniżej), tym większa alokacja kapitału."
    )
    parser.add_argument("--capital", type=float,
                        help="Miesięczna kwota inwestycji (np. 1072.32)")
    args = parser.parse_args()

    try:
        monthly_capital = args.capital if args.capital is not None else float(
            input("Podaj miesięczną kwotę inwestycji (np. 1072.32): "))
        if monthly_capital <= 0:
            raise ValueError("Kwota inwestycji musi być dodatnia.")
    except Exception as e:
        logging.error("Błąd przy pobieraniu kapitału: %s", str(e))
        monthly_capital = 3000.0

    # Lista spółek, które uważasz za najlepsze (ticker jest wykorzystywany do pobierania danych, ale wyświetlimy nazwę firmy)
    tickers = ["GRG.L", "LEG", "MAN", "LDOS", "LKQ", "KDP", "UPS", "GPC"]

    print("Pobieranie danych dla spółek...")
    data = fetch_all_data(tickers)

    # Walidacja – upewnij się, że mamy przynajmniej jakieś dane
    if not data or all(item.get("Score", 0) == 0 for item in data):
        print("Brak poprawnych danych lub sygnałów kupna. Sprawdź logi błędów.")
        return

    # Wyświetlamy wyniki oceny
    df = pd.DataFrame(data)
    print("\nWyniki oceny (spółki, im bliżej ceny do MA50, tym lepszy score):")
    df_buy = df[df['Score'] > 0].copy()
    if df_buy.empty:
        print("Brak spółek spełniających kryterium.")
    else:
        df_buy = df_buy.sort_values(by='Score', ascending=False)
        print(df_buy[['Company', 'CurrentPrice', 'MA50', 'DistancePct',
              'Flatness', 'Proximity', 'Bonus', 'Score']].to_string(index=False))

        allocation = allocate_investment(data, monthly_capital)
        if allocation:
            print("\nProponowana alokacja kapitału:")
            df_alloc = pd.DataFrame(allocation)
            print(df_alloc[['Company', 'AllocationPct',
                  'AllocationPLN']].to_string(index=False))
        else:
            print("Brak spółek z dodatnim score do alokacji kapitału.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nAnaliza przeprowadzona: {now}")


if __name__ == '__main__':
    main()
