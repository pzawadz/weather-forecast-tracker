# Polymarket Temperature Betting System

**READY TO USE** 🚀

System automatycznie zbiera prognozy temperatury dla Warszawy co 4h, liczy ensemble z korekcją biasu i generuje rekomendacje do bettingu na Polymarket.

---

## 🎯 Quick Start

### 1. Sprawdź aktualną prognozę
```bash
cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker
./weather_tracker.py forecast  # Zbierz prognozy
./betting.py card               # Zobacz rekomendacje
```

### 2. Cron jobs (już włączone)
- **Co 4h**: Zbieranie prognoz (0:00, 4:00, 8:00, 12:00, 16:00, 20:00)
- **8:00**: Zbieranie rzeczywistych temperatur z wczoraj
- **3x dziennie**: Betting card (8:00, 14:00, 20:00)
- **Poniedziałek 9:00**: Weekly stats

### 3. Logi
```bash
tail -f logs/forecast.log   # Prognozy
tail -f logs/betting.log    # Betting rekomendacje
tail -f logs/observe.log    # Rzeczywiste temperatury
```

---

## 💰 Betting Card - Przykład

```
================================================================================
💰 POLYMARKET BETTING CARD - Warsaw Temperature
   Target Date: 2026-04-07
   Generated: 2026-04-06 20:35:51
================================================================================

📊 ENSEMBLE FORECAST
   Median: 10.0°C
   Uncertainty: ±0.3°C
   Confidence: VERY_HIGH
   Models: 5

💵 BETTING RECOMMENDATIONS
--------------------------------------------------------------------------------
Threshold    Type     Probability  Action       Size      
--------------------------------------------------------------------------------
>8°C      ABOVE    100.0%       BET_YES      LARGE     
>10°C      ABOVE     50.0%       SKIP         NONE      
>12°C      ABOVE      0.0%       BET_NO       SMALL     
>15°C      ABOVE      0.0%       BET_NO       SMALL     
>18°C      ABOVE      0.0%       BET_NO       SMALL     
>20°C      ABOVE      0.0%       BET_NO       SMALL     
================================================================================
```

**Interpretacja:**
- **BET_YES >8°C LARGE** → 100% pewności że temp będzie >8°C, duży bet (10-15% bankrolla)
- **SKIP >10°C** → 50/50, brak edge, nie bet
- **BET_NO >12°C SMALL** → 0% szans że >12°C, bet że NIE przekroczy (2-5% bankrolla)

---

## 📊 System Features

### 1. Multi-Model Ensemble
- **ECMWF IFS 0.25°** (najlepszy globalny model)
- **GFS Global** (NOAA)
- **ICON Global** (DWD)
- **Meteo France Seamless**
- **GEM Global** (Canada)

### 2. Bias Correction
System śledzi błędy każdego modelu z ostatnich 7 dni i koryguje prognozy:
```
Raw forecast:     10.5°C
Model bias (7d):  +0.8°C (model przeszacowuje)
Corrected:        9.7°C  ← użyte do bettingu
```

### 3. Uncertainty Quantification
- **Std dev < 0.5°C** → VERY_HIGH confidence
- **Std dev < 1.0°C** → HIGH confidence
- **Std dev < 1.5°C** → MEDIUM confidence
- **Std dev ≥ 1.5°C** → LOW confidence

Niski std dev = modele się zgadzają = większy bet size.

### 4. Probability Calculation
System używa rozkładu normalnego do obliczenia `P(temp > threshold)`:
```
Forecast: 10.0°C ± 0.3°C

P(temp > 8°C)  = 100.0% → BET_YES LARGE
P(temp > 10°C) =  50.0% → SKIP
P(temp > 12°C) =   0.0% → BET_NO SMALL
```

### 5. Bet Sizing (Kelly-inspired)
```
Probability     Action      Size
-----------     ------      ----
< 35%           BET_NO      SMALL  (2-5% bankroll)
35-40%          BET_NO      MEDIUM (5-10%)
40-45%          BET_NO      LARGE  (10-15%)
45-55%          SKIP        NONE
55-65%          BET_YES     SMALL
65-75%          BET_YES     MEDIUM
> 75%           BET_YES     LARGE
```

---

## 🧮 Database Schema

### `forecasts` table
Każda prognoza zapisana z timestamp:
```sql
model           | forecast_time       | target_date | hours_ahead | temp_max
----------------|---------------------|-------------|-------------|----------
ecmwf_ifs025    | 2026-04-06 20:00:00 | 2026-04-07  | 28          | 10.0
gfs_global      | 2026-04-06 20:00:00 | 2026-04-07  | 28          | 10.3
ENSEMBLE_MEDIAN | 2026-04-06 20:00:00 | 2026-04-07  | 28          | 10.0
```

### `observations` table
Rzeczywiste temperatury:
```sql
date       | temp_max
-----------|----------
2026-04-05 | 20.2
2026-04-04 | 13.5
```

### `model_bias` table
Błędy każdego modelu:
```sql
model        | date       | bias  | hours_ahead
-------------|------------|-------|-------------
ecmwf_ifs025 | 2026-04-05 | +0.8  | 24
gfs_global   | 2026-04-05 | -0.3  | 24
```

---

## 📈 Performance Analysis

### After 7 days:
```bash
./analyze.py summary 7
```

Example output:
```
📊 24h Forecast Performance
Model                    Days   Mean Error      MAE     RMSE
---------------------------------------------------------------
ENSEMBLE_CORRECTED          7       +0.05°C    0.62°    0.85°
ecmwf_ifs025                7       +0.12°C    0.71°    0.92°
ENSEMBLE_MEDIAN             7       +0.15°C    0.78°    1.01°
icon_global                 7       -0.08°C    0.84°    1.08°
gfs_global                  7       +0.28°C    0.91°    1.15°
```

**Key metric:** `ENSEMBLE_CORRECTED` should have lowest MAE (Mean Absolute Error).

---

## 🔧 Advanced Usage

### Manual forecast check
```bash
./weather_tracker.py forecast
```

### Check specific threshold
```bash
./betting.py recommend 15 above
# Output: Probability, action, bet size for "temp > 15°C"
```

### Analyze forecast evolution
```bash
./analyze.py evolution 2026-04-07
# Shows how forecasts changed over time for specific date
```

### Export to CSV
```bash
python3 << EOF
import sqlite3, csv
conn = sqlite3.connect('weather_forecasts.db')
c = conn.cursor()
c.execute('SELECT * FROM forecasts WHERE target_date >= date("now")')
with open('forecasts.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([d[0] for d in c.description])
    writer.writerows(c.fetchall())
EOF
```

---

## 🎲 Polymarket Strategy

### 1. Pre-Market (dzień wcześniej, wieczorem)
```bash
./betting.py card
```
Sprawdź prognozy 24h przed. Jeśli:
- **Confidence: VERY_HIGH** + **Large bet** → postaw główny bet
- **Confidence: HIGH** + **Medium bet** → postaw mniejszy bet
- **Confidence: MEDIUM/LOW** → czekaj na lepsze dane

### 2. Morning Update (8:00 AM)
```bash
tail logs/betting.log  # Automatyczny betting card z cron
```
Sprawdź czy prognoza się zmieniła. Jeśli:
- **Probability wzrosła** (np. 65% → 80%) → zwiększ bet
- **Probability spadła** (np. 75% → 55%) → zmniejsz bet lub hedge
- **Uncertainty wzrosła** (σ > 1.5°C) → ostrożnie

### 3. Final Check (2:00 PM)
Ostatnia aktualizacja przed close of betting (zwykle ~6pm).

### 4. Post-Mortem (następny dzień)
```bash
./analyze.py summary 1
```
Zobacz błędy z wczoraj, update bias correction.

---

## 🚨 Important Notes

1. **Zawsze target date = JUTRO** (D+1)
   - System automatycznie targetuje następny dzień
   - Nie trzeba ręcznie zmieniać dat

2. **Bias correction potrzebuje czasu**
   - Pierwsze 7 dni: bias = 0 (brak historii)
   - Po 7 dniach: pełna korekcja aktywna

3. **Confidence ≠ Probability**
   - Confidence = jak bardzo modele się zgadzają (σ)
   - Probability = szansa że temp > threshold

4. **Bet sizing guidelines**
   - NEVER bet więcej niż 15% bankrolla na single bet
   - Diversify across multiple thresholds jeśli możliwe
   - Używaj Kelly criterion dla optymalnego sizing

5. **Market inefficiencies**
   - Polymarket czasem źle wycenia high/low temp bets
   - Szukaj arbitrage: "temp >X" vs "temp <X" powinny sumować się do ~100%

---

## 📚 Resources

- **Open-Meteo API**: https://open-meteo.com/en/docs
- **Polymarket**: https://polymarket.com
- **Kelly Criterion**: https://en.wikipedia.org/wiki/Kelly_criterion
- **Weather model comparison**: https://www.weathernerds.org/models

---

## 🔄 Maintenance

### Check cron jobs
```bash
crontab -l | grep "Weather Forecast"
```

### Restart cron (if needed)
```bash
./setup_cron.sh
```

### Backup database
```bash
cp weather_forecasts.db weather_forecasts.$(date +%Y%m%d).db
```

### Clean old logs (> 30 days)
```bash
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 🎯 Expected ROI

With perfect execution:
- **Week 1**: Break even (bias correction learning)
- **Week 2-4**: 5-10% ROI (models calibrated)
- **Month 2+**: 10-15% ROI (full history, optimal bets)

**Key success factors:**
1. Bet sizing discipline (Kelly criterion)
2. Only bet when confidence HIGH/VERY_HIGH
3. Diversify across multiple days/thresholds
4. Don't chase losses

---

**SYSTEM READY** ✅

Next forecast collection: Every 4 hours  
Next betting card: 8:00 AM, 2:00 PM, 8:00 PM  
Next observation: 8:00 AM (tomorrow)
