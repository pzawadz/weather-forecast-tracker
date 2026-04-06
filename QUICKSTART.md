# Quick Start Guide

## 1. Instalacja

```bash
cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker
pip3 install requests
chmod +x weather_tracker.py analyze.py setup_cron.sh
```

## 2. Pierwsze uruchomienie

```bash
# Zbierz pierwszą paczkę danych
./weather_tracker.py both

# Zobacz co się zebrało
./analyze.py summary
```

## 3. Automatyzacja

```bash
# Ustaw cron jobs (co 4h prognozy, codziennie obserwacje)
./setup_cron.sh

# Sprawdź logi
tail -f logs/forecast.log
```

## 4. Codzienne użycie

Po kilku dniach zbierania:

```bash
# Statystyki skuteczności modeli
./weather_tracker.py stats 7

# Pełny raport analityczny
./analyze.py summary 14

# Ewolucja prognozy dla konkretnego dnia
./analyze.py evolution 2026-04-07
```

## 5. Przykładowe wyniki (po tygodniu)

```
📊 24h Forecast Performance
Model                          Days   Mean Error      MAE     RMSE
--------------------------------------------------------------------------------
ENSEMBLE_MEDIAN                   7       +0.12°C    0.85°    1.10°
ecmwf_ifs025                      7       +0.15°C    0.92°    1.15°
icon_global                       7       -0.08°C    0.98°    1.22°
gfs_global                        7       +0.21°C    1.05°    1.30°
ENSEMBLE_MEAN                     7       +0.18°C    1.08°    1.35°
gem_global                        7       +0.35°C    1.12°    1.42°
meteofrance_seamless              7       -0.42°C    1.25°    1.58°
```

**Wnioski:**
- ENSEMBLE_MEDIAN zwykle najlepszy (MAE ~0.85°C)
- ECMWF IFS najbardziej precyzyjny pojedynczy model
- Ensemble redukuje błędy o ~10-15% vs najlepszy model

## 6. Rozszerzenia

### Dodaj polskie modele (IMGW)

Będzie wymagało manualnego scrapowania/logowania z:
- https://www.meteo.pl/um/php/meteorogram_list.php (UM/WRF)
- https://cmm.imgw.pl (AROME, COSMO, ICON-LAM)

### Korekcja biasu w czasie rzeczywistym

```python
# W weather_tracker.py, funkcja collect_forecasts()
# Po zebraniu raw forecasts:

corrected_forecasts = []
for model in MODELS:
    raw_temp = fetch_forecast(model, tomorrow)
    bias_7d = get_recent_bias(model, hours_ahead=24, days=7)
    corrected = raw_temp - bias_7d
    corrected_forecasts.append(corrected)

ensemble = statistics.median(corrected_forecasts)
```

### Email/Telegram alert

```bash
# W setup_cron.sh, dodaj:
# Daily forecast summary at 20:00
0 20 * * * cd $PROJECT_DIR && ./analyze.py summary 1 | mail -s "Weather Forecast" your@email.com
```

## 7. Backup danych

```bash
# Backup bazy SQLite
cp weather_forecasts.db weather_forecasts.$(date +%Y%m%d).db

# Export do CSV
python3 << EOF
import sqlite3, csv
conn = sqlite3.connect('weather_forecasts.db')
c = conn.cursor()
c.execute('SELECT * FROM forecasts')
with open('forecasts.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([d[0] for d in c.description])
    writer.writerows(c.fetchall())
EOF
```
