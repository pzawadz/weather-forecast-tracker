# Weather Forecast Tracker

System do zbierania i weryfikacji prognoz pogodowych dla Warszawy.

## Funkcje

- ✅ **Multi-model**: ECMWF IFS, GFS, ICON, Meteo France, GEM
- ✅ **Ensemble**: mediana i średnia prognoz
- ✅ **Zbieranie co 4h**: prognozy na jutro z różnych horyzontów czasowych
- ✅ **Weryfikacja**: porównanie z rzeczywistymi pomiarami
- ✅ **Tracking biasu**: błędy każdego modelu w czasie
- ✅ **Statystyki**: MAE, RMSE, mean error dla każdego modelu

## Instalacja

```bash
cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker
pip3 install requests
chmod +x weather_tracker.py
```

## Użycie

### Zbierz prognozy na jutro
```bash
./weather_tracker.py forecast
```

### Zbierz rzeczywiste dane z wczoraj
```bash
./weather_tracker.py observe
```

### Zbierz dane + prognozy (daily run)
```bash
./weather_tracker.py both
```

### Pokaż statystyki
```bash
./weather_tracker.py stats           # ostatnie 7 dni
./weather_tracker.py stats 14        # ostatnie 14 dni
```

## Automatyzacja (cron)

Dodaj do crontaba (`crontab -e`):

```bash
# Zbierz prognozy co 4h (6:00, 10:00, 14:00, 18:00, 22:00)
0 6,10,14,18,22 * * * cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker && ./weather_tracker.py forecast >> logs/forecast.log 2>&1

# Zbierz rzeczywiste dane rano (8:00)
0 8 * * * cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker && ./weather_tracker.py observe >> logs/observe.log 2>&1

# Weekly stats report (poniedziałek 9:00)
0 9 * * 1 cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker && ./weather_tracker.py stats 7 >> logs/stats.log 2>&1
```

## Struktura bazy danych

### `forecasts` table
- `model`: nazwa modelu (ecmwf_ifs025, gfs_global, ENSEMBLE_MEDIAN, etc.)
- `forecast_time`: kiedy pobrano prognozę
- `target_date`: na który dzień prognoza
- `hours_ahead`: ile godzin przed target_date
- `temp_max`: prognozowana max temperatura

### `observations` table
- `date`: dzień pomiaru
- `temp_max`: rzeczywista max temperatura

### `model_bias` table
- `model`: nazwa modelu
- `date`: dzień którego dotyczy błąd
- `bias`: błąd prognozy (forecast - actual)
- `hours_ahead`: horyzont prognozy

## Przykładowe zapytania SQL

### Porównaj prognozy 24h przed vs actual
```sql
SELECT 
  f.model,
  f.target_date,
  f.temp_max as forecast,
  o.temp_max as actual,
  (f.temp_max - o.temp_max) as error
FROM forecasts f
JOIN observations o ON f.target_date = o.date
WHERE f.hours_ahead BETWEEN 20 AND 28
  AND f.target_date >= date('now', '-7 days')
ORDER BY f.target_date DESC, f.model;
```

### Najlepszy model ostatnie 30 dni
```sql
SELECT 
  model,
  COUNT(*) as days,
  AVG(ABS(bias)) as mae,
  SQRT(AVG(bias * bias)) as rmse
FROM model_bias
WHERE date >= date('now', '-30 days')
  AND hours_ahead BETWEEN 20 AND 28
GROUP BY model
ORDER BY mae ASC;
```

### Ewolucja prognozy dla konkretnego dnia
```sql
SELECT 
  forecast_time,
  hours_ahead,
  model,
  temp_max
FROM forecasts
WHERE target_date = '2026-04-07'
ORDER BY hours_ahead DESC, model;
```

## API Sources

- **Open-Meteo Forecast API**: https://api.open-meteo.com/v1/forecast
  - ECMWF IFS 0.25°
  - GFS Global
  - ICON Global
  - Meteo France Seamless
  - GEM Global

- **Open-Meteo Historical API**: https://archive-api.open-meteo.com/v1/archive
  - Rzeczywiste pomiary z stacji meteorologicznych

## Rozszerzenia (TODO)

- [ ] Dodaj polskie modele (UM, AROME z IMGW)
- [ ] Korekcja biasu w czasie rzeczywistym
- [ ] Wykresy porównawcze (matplotlib)
- [ ] Email/Telegram alert z raportami
- [ ] Web dashboard (Streamlit/Dash)
- [ ] Tracking innych parametrów (opady, wiatr)
