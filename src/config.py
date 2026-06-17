import pandas as pd

# Global Configuration
AS_OF_DATE  = pd.Timestamp('2026-06-13')
TRAIN_START = pd.Timestamp('2000-01-01')
K = 32
MODEL_DIR = "models"
DATA_DIR = "data"

EV_THRESHOLD   = 0.04
KELLY_FRACTION = 0.25

world_avg_gdp  = 13000
world_population = 8000
world_avg_squad = 200
host_teams = ['United States', 'Mexico', 'Canada']

team_mapping = {
    'West Germany': 'Germany', 'East Germany': 'Germany',
    'Soviet Union': 'Russia', 'Serbia and Montenegro': 'Serbia',
    'Zaire': 'DR Congo', 'China': 'China PR',
    'Türkiye': 'Turkey', 'Ivory Coast': 'Ivory Coast',
    "Côte d'Ivoire": 'Ivory Coast',
}

tournament_weights = {
    'FIFA World Cup': 3.0, 'Copa América': 2.5, 'UEFA Euro': 2.5,
    'African Cup of Nations': 2.5, 'AFC Asian Cup': 2.5, 'Gold Cup': 2.5,
    'UEFA Nations League': 2.0, 'FIFA World Cup qualification': 2.0,
    'UEFA Euro qualification': 1.5, 'African Cup of Nations qualification': 1.5,
    'AFC Asian Cup qualification': 1.5, 'Friendly': 1.0
}

confederation_map = {
    'Brazil': 'CONMEBOL', 'Argentina': 'CONMEBOL', 'Uruguay': 'CONMEBOL', 'Colombia': 'CONMEBOL', 'Chile': 'CONMEBOL', 'Paraguay': 'CONMEBOL', 'Peru': 'CONMEBOL', 'Ecuador': 'CONMEBOL', 'Bolivia': 'CONMEBOL', 'Venezuela': 'CONMEBOL',
    'Germany': 'UEFA', 'France': 'UEFA', 'Spain': 'UEFA', 'Italy': 'UEFA', 'England': 'UEFA', 'Netherlands': 'UEFA', 'Portugal': 'UEFA', 'Belgium': 'UEFA', 'Croatia': 'UEFA', 'Russia': 'UEFA', 'Sweden': 'UEFA', 'Poland': 'UEFA', 'Denmark': 'UEFA', 'Switzerland': 'UEFA', 'Czech Republic': 'UEFA', 'Serbia': 'UEFA', 'Austria': 'UEFA', 'Hungary': 'UEFA', 'Romania': 'UEFA', 'Bulgaria': 'UEFA', 'Scotland': 'UEFA', 'Turkey': 'UEFA', 'Ukraine': 'UEFA', 'Slovakia': 'UEFA', 'Slovenia': 'UEFA', 'Greece': 'UEFA', 'Norway': 'UEFA', 'Bosnia and Herzegovina': 'UEFA',
    'United States': 'CONCACAF', 'Mexico': 'CONCACAF', 'Canada': 'CONCACAF', 'Costa Rica': 'CONCACAF', 'Honduras': 'CONCACAF', 'Jamaica': 'CONCACAF', 'El Salvador': 'CONCACAF', 'Haiti': 'CONCACAF', 'Panama': 'CONCACAF', 'Curaçao': 'CONCACAF',
    'Nigeria': 'CAF', 'Cameroon': 'CAF', 'Senegal': 'CAF', 'Ghana': 'CAF', 'Morocco': 'CAF', 'Tunisia': 'CAF', 'Egypt': 'CAF', 'Algeria': 'CAF', 'Ivory Coast': 'CAF', 'DR Congo': 'CAF', 'South Africa': 'CAF', 'Angola': 'CAF', 'Togo': 'CAF', 'Cape Verde': 'CAF',
    'Japan': 'AFC', 'South Korea': 'AFC', 'Iran': 'AFC', 'Australia': 'AFC', 'Saudi Arabia': 'AFC', 'China PR': 'AFC', 'Iraq': 'AFC', 'Indonesia': 'AFC', 'Qatar': 'AFC', 'Uzbekistan': 'AFC', 'Jordan': 'AFC',
    'New Zealand': 'OFC',
}

gdp_per_capita = {
    'Brazil': 10800, 'Argentina': 13700, 'Uruguay': 17900, 'Colombia': 7000, 'Chile': 16000, 'Paraguay': 6000, 'Peru': 7200, 'Ecuador': 6300, 'Bolivia': 3600, 'Venezuela': 3500, 'Germany': 54300, 'France': 46000, 'Spain': 33000, 'Italy': 37700, 'England': 49000, 'Netherlands': 61000, 'Portugal': 25000, 'Belgium': 51000, 'Croatia': 20000, 'Russia': 12000, 'Sweden': 56000, 'Poland': 18000, 'Denmark': 67000, 'Switzerland': 92000, 'Czech Republic': 27000, 'Serbia': 10000, 'Austria': 56000, 'Hungary': 18000, 'Romania': 15000, 'Bulgaria': 13000, 'Scotland': 46000, 'Turkey': 12000, 'Ukraine': 4500, 'Slovakia': 22000, 'Slovenia': 28000, 'Greece': 21000, 'Norway': 106000, 'United States': 80000, 'Mexico': 11000, 'Canada': 55000, 'Costa Rica': 13000, 'Honduras': 2900, 'Jamaica': 6000, 'El Salvador': 4500, 'Haiti': 1700, 'Panama': 16000, 'Curaçao': 20000,
    'Nigeria': 2200, 'Cameroon': 1700, 'Senegal': 1700, 'Ghana': 2400, 'Morocco': 4000, 'Tunisia': 3800, 'Egypt': 3800, 'Algeria': 4000, 'Ivory Coast': 2700, 'DR Congo': 600, 'South Africa': 6800, 'Cape Verde': 4000,
    'Japan': 34000, 'South Korea': 35000, 'Iran': 4000, 'Australia': 64000, 'Saudi Arabia': 30000, 'China PR': 13000, 'Iraq': 5000, 'Qatar': 83000, 'New Zealand': 48000, 'Uzbekistan': 2400, 'Jordan': 4500, 'Bosnia and Herzegovina': 8000,
}

population = {
    'Brazil': 215, 'Argentina': 46, 'Uruguay': 3.5, 'Colombia': 52, 'Chile': 19, 'Paraguay': 7.4, 'Peru': 33, 'Ecuador': 18, 'Bolivia': 12, 'Venezuela': 29, 'Germany': 84, 'France': 68, 'Spain': 48, 'Italy': 59, 'England': 56, 'Netherlands': 18, 'Portugal': 10, 'Belgium': 12, 'Croatia': 3.9, 'Russia': 144, 'Sweden': 10, 'Poland': 38, 'Denmark': 6, 'Switzerland': 9, 'Czech Republic': 11, 'Serbia': 6.8, 'Austria': 9, 'Hungary': 9.7, 'Romania': 19, 'Bulgaria': 6.5, 'Scotland': 5.5, 'Turkey': 85, 'Ukraine': 44, 'Slovakia': 5.5, 'Slovenia': 2.1, 'Greece': 10.5, 'Norway': 5.4, 'United States': 335, 'Mexico': 130, 'Canada': 38, 'Costa Rica': 5.2, 'Honduras': 10, 'Jamaica': 3, 'El Salvador': 6.5, 'Haiti': 12, 'Panama': 4.4, 'Curaçao': 0.19,
    'Nigeria': 220, 'Cameroon': 28, 'Senegal': 17, 'Ghana': 33, 'Morocco': 38, 'Tunisia': 12, 'Egypt': 105, 'Algeria': 46, 'Ivory Coast': 27, 'DR Congo': 100, 'South Africa': 60, 'Cape Verde': 0.6,
    'Japan': 125, 'South Korea': 52, 'Iran': 88, 'Australia': 26, 'Saudi Arabia': 35, 'China PR': 1400, 'Iraq': 42, 'Qatar': 2.9, 'New Zealand': 5, 'Uzbekistan': 36, 'Jordan': 10.8, 'Bosnia and Herzegovina': 3.2,
}

temperature = {
    'Brazil': 25, 'Argentina': 18, 'Uruguay': 17, 'Colombia': 24, 'Chile': 14, 'Paraguay': 23, 'Peru': 20, 'Ecuador': 22, 'Bolivia': 15, 'Venezuela': 26, 'Germany': 9, 'France': 12, 'Spain': 15, 'Italy': 14, 'England': 10, 'Netherlands': 10, 'Portugal': 16, 'Belgium': 10, 'Croatia': 13, 'Russia': 5, 'Sweden': 6, 'Poland': 9, 'Denmark': 8, 'Switzerland': 9, 'Czech Republic': 10, 'Serbia': 12, 'Austria': 8, 'Hungary': 11, 'Romania': 10, 'Bulgaria': 11, 'Scotland': 8, 'Turkey': 14, 'Ukraine': 9, 'Slovakia': 10, 'Slovenia': 11, 'Greece': 17, 'Norway': 4, 'United States': 15, 'Mexico': 21, 'Canada': 3, 'Costa Rica': 24, 'Honduras': 25, 'Jamaica': 27, 'El Salvador': 25, 'Haiti': 27, 'Panama': 27, 'Curaçao': 28,
    'Nigeria': 28, 'Cameroon': 26, 'Senegal': 28, 'Ghana': 28, 'Morocco': 18, 'Tunisia': 19, 'Egypt': 22, 'Algeria': 23, 'Ivory Coast': 27, 'DR Congo': 25, 'South Africa': 18, 'Cape Verde': 25,
    'Japan': 15, 'South Korea': 13, 'Iran': 18, 'Australia': 22, 'Saudi Arabia': 30, 'China PR': 13, 'Iraq': 23, 'Qatar': 33, 'New Zealand': 13, 'Uzbekistan': 14, 'Jordan': 18, 'Bosnia and Herzegovina': 11,
}

squad_strength = {
    'Germany': 850, 'France': 1050, 'England': 1100, 'Spain': 900, 'Brazil': 900, 'Portugal': 750, 'Netherlands': 700, 'Belgium': 550, 'Argentina': 750, 'Italy': 500, 'Croatia': 260, 'Denmark': 380, 'Switzerland': 350, 'Austria': 310, 'Norway': 320, 'Sweden': 280, 'Scotland': 280, 'Turkey': 240, 'Serbia': 220, 'Poland': 230, 'Uruguay': 270, 'Colombia': 320, 'Ecuador': 160, 'Chile': 150, 'Paraguay': 110, 'Peru': 80, 'Bolivia': 50, 'Venezuela': 70, 'Mexico': 180, 'United States': 300, 'Canada': 230, 'Costa Rica': 60, 'Panama': 55, 'Honduras': 40, 'El Salvador': 30, 'Haiti': 35, 'Jamaica': 70, 'Curaçao': 20,
    'Morocco': 280, 'Senegal': 200, 'Egypt': 130, 'Algeria': 150, 'Tunisia': 120, 'Ghana': 160, 'Nigeria': 280, 'Cameroon': 150, 'Ivory Coast': 170, 'DR Congo': 60, 'South Africa': 70, 'Cape Verde': 45,
    'Japan': 250, 'South Korea': 200, 'Iran': 90, 'Australia': 130, 'Saudi Arabia': 110, 'Qatar': 60, 'Iraq': 60, 'Jordan': 30, 'Uzbekistan': 50, 'China PR': 70, 'New Zealand': 40, 'Bosnia and Herzegovina': 130,
}

venue_coords = {
    'Houston':        (29.6847, -95.4107), 'Dallas':         (32.7480, -97.0930),
    'Los Angeles':    (33.9534, -118.3392), 'New York':       (40.8135, -74.0745),
    'San Francisco':  (37.4032, -121.9698), 'Seattle':        (47.5952, -122.3316),
    'Boston':         (42.0909, -71.2643), 'Philadelphia':   (39.9007, -75.1675),
    'Kansas City':    (39.0489, -94.4839), 'Atlanta':        (33.7553, -84.4006),
    'Miami':          (25.9580, -80.2388), 'Vancouver':      (49.2769, -123.1128),
    'Toronto':        (43.6336, -79.3893), 'Guadalajara':    (20.6843, -103.3040),
    'Mexico City':    (19.3028, -99.1505), 'Monterrey':      (25.6688, -100.3126),
}
