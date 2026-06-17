import pandas as pd
import requests
from src.config import AS_OF_DATE, team_mapping, tournament_weights, venue_coords

def load_international_results():
    df_intl = pd.read_csv("https://raw.githubusercontent.com/martj42/international_results/master/results.csv")
    df_intl['date'] = pd.to_datetime(df_intl['date'])
    df_intl = df_intl[df_intl['date'] < AS_OF_DATE].copy()
    df_intl = df_intl.sort_values('date').reset_index(drop=True)

    df_intl['home_team'] = df_intl['home_team'].replace(team_mapping)
    df_intl['away_team'] = df_intl['away_team'].replace(team_mapping)
    df_intl['weight'] = df_intl['tournament'].map(tournament_weights).fillna(1.0)
    
    return df_intl

def fetch_venue_weather(venue_city, match_date_str):
    coords = venue_coords.get(venue_city)
    if not coords:
        return {'temp_c': 22, 'humidity': 60, 'wind_kmh': 15, 'precip_mm': 0}
    
    lat, lon = coords
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,precipitation_sum,windspeed_10m_max,relative_humidity_2m_max"
        f"&start_date={match_date_str}&end_date={match_date_str}"
        f"&timezone=auto"
    )
    
    try:
        r = requests.get(url, timeout=5)
        d = r.json().get('daily', {})
        return {
            'temp_c':     d.get('temperature_2m_max',   [22])[0] or 22,
            'humidity':   d.get('relative_humidity_2m_max', [60])[0] or 60,
            'wind_kmh':   d.get('windspeed_10m_max',    [15])[0] or 15,
            'precip_mm':  d.get('precipitation_sum',    [0])[0]  or 0,
        }
    except Exception:
        return {'temp_c': 22, 'humidity': 60, 'wind_kmh': 15, 'precip_mm': 0}
