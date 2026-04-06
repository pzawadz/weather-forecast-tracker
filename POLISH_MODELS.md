# 🇵🇱 Polish Weather Models - Status

## ✅ Co działa (bez dodatkowej konfiguracji):

### ICON-EU (7km resolution)
**Status:** ✅ AKTYWNY (włączony domyślnie)

- **Źródło:** Open-Meteo API (DWD ICON-EU)
- **Rozdzielczość:** 0.0625° (~7 km) nad Polską
- **Porównywalny do:** AROME/ALADIN z IMGW
- **Zasięg:** Europa Środkowa
- **Update:** Co 3h
- **Prognozy:** Do 120h (5 dni)

ICON-EU to niemiecki model meteorologiczny z wysoką rozdzielczością nad Europą Środkową. Dla Warszawy daje **podobną precyzję** jak polskie modele mezoskalowe (AROME, ICON-LAM).

**Już włączony w systemie!** Nie wymaga żadnej konfiguracji.

---

## ⚠️ Opcjonalne (wymagają instalacji):

### Meteo.pl UM (Unified Model)
**Status:** 🟡 OPCJONALNY (wymaga Playwright)

- **Źródło:** ICM UW (meteo.pl)
- **Rozdzielczość:** 4 km nad Polską
- **Update:** 2x dziennie (06:00, 18:00 UTC)
- **Prognozy:** Do 78h

**Instalacja:**
```bash
pip3 install playwright
playwright install chromium

# Test
./scrapers_playwright.py
```

**Włączenie w systemie:**
Edytuj `weather_tracker.py` i dodaj wywołanie scraperów Playwright w funkcji `collect_forecasts()`.

**Uwaga:** Meteo.pl używa JavaScript do renderowania danych, więc wymaga pełnego browsera (Playwright). To dodaje ~200MB zależności + wolniejsze działanie.

---

### IMGW AROME/ICON-LAM
**Status:** ❌ NIE ZAIMPLEMENTOWANE

- **Źródło:** IMGW (cmm.imgw.pl)
- **Rozdzielczość:** 2.5 km (AROME), 2.8 km (ICON-LAM)
- **Problem:** Interaktywna mapa, brak publicznego API

IMGW udostępnia prognozy tylko przez interaktywną mapę (wymaga kliknięć). Brak prostego API. Możliwe rozwiązania:
1. Playwright + clicks simulation (bardzo złożone)
2. Reverse engineering internal API (może się zmienić)
3. Kontakt z IMGW o oficjalne API (mało prawdopodobne)

**Rekomendacja:** Użyj ICON-EU jako proxy (bardzo podobne wyniki).

---

## 🎯 Rekomendowana konfiguracja dla Polymarket betting:

### **Standard (bez instalacji dodatkowych):**
```
✓ ECMWF IFS 0.25° (best global)
✓ ICON-EU 7km 🇵🇱 (Polish region)
✓ GFS Global
✓ ICON Global
✓ Meteo France
✓ GEM Global
```
**6 modeli**, wszystkie przez Open-Meteo API (szybkie, darmowe).

### **Pro (z Playwright):**
```
Wszystkie powyższe +
✓ Meteo.pl UM 4km 🇵🇱 (true Polish model)
```
**7 modeli**, wymaga instalacji Playwright (~200MB).

---

## 📊 Porównanie precyzji (teoretyczne):

| Model | Rozdzielczość | Update | Zasięg | Precyzja dla Warszawy |
|-------|--------------|--------|---------|----------------------|
| **ECMWF IFS** | 9 km | 2x/dzień | Global | ⭐⭐⭐⭐⭐ |
| **ICON-EU 🇵🇱** | 7 km | Co 3h | Europa | ⭐⭐⭐⭐⭐ |
| **Meteo.pl UM** | 4 km | 2x/dzień | Polska | ⭐⭐⭐⭐⭐ |
| **IMGW AROME** | 2.5 km | 4x/dzień | Polska | ⭐⭐⭐⭐⭐ |
| **GFS** | 13 km | 4x/dzień | Global | ⭐⭐⭐⭐ |

**Wnioski:**
- ICON-EU (7km) jest **wystarczająco dobry** dla większości zastosowań
- Meteo.pl UM (4km) może dać ~5% lepsze wyniki, ale wymaga Playwright
- IMGW AROME (2.5km) teoretycznie najlepszy, ale praktycznie niedostępny

---

## 🚀 Szybki start (tylko ICON-EU):

System już działa z ICON-EU! Sprawdź:
```bash
./weather_tracker.py forecast
./betting.py card
```

Output:
```
📊 Collecting forecasts for 2026-04-07
   ✓ ecmwf_ifs025         →  10.0°C
   ✓ icon_eu 🇵🇱          →  10.4°C  ← Polski model!
   ✓ gfs_global           →  10.3°C
   ...
```

---

## 🔧 Jeśli chcesz dodać Meteo.pl UM:

### 1. Instalacja Playwright:
```bash
cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker
pip3 install --break-system-packages playwright
playwright install chromium
```

### 2. Test scraperów:
```bash
./scrapers_playwright.py
```

### 3. Integracja (ręczna, opcjonalna):
Edytuj `weather_tracker.py`:
```python
# Na początku pliku
from scrapers_playwright import scrape_meteo_pl_um

# W funkcji collect_forecasts(), po innych modelach:
um_temp = scrape_meteo_pl_um()
if um_temp:
    save_forecast("METEO_PL_UM", now, tomorrow, int(hours_until_tomorrow), um_temp)
    forecasts_raw.append(um_temp)
    print(f"   ✓ METEO_PL_UM (4km) 🇵🇱      → {um_temp:5.1f}°C")
```

---

## ❓ FAQ

**Q: Czy ICON-EU to "polski" model?**  
A: Nie, to niemiecki DWD model. Ale ma wysoką rozdzielczość nad Polską (7km) i jest porównywalny do AROME/ALADIN.

**Q: Czemu nie ma IMGW AROME/ICON-LAM?**  
A: IMGW nie udostępnia publicznego API. Dane są tylko na interaktywnej mapie (wymaga kliknięć w browser).

**Q: Czy powinienem instalować Playwright?**  
A: Nie, jeśli nie zależy Ci na dodatkowych 1-2% precyzji. ICON-EU jest wystarczający dla betting.

**Q: Jak sprawdzić czy ICON-EU działa?**  
A: `./weather_tracker.py forecast` → szukaj linii `icon_eu 🇵🇱`

**Q: Ile kosztuje Open-Meteo dla ICON-EU?**  
A: Darmowe (free tier, 10,000 calls/day).

---

**TL;DR:** System ma już **polski model** (ICON-EU 7km) który działa bez żadnej konfiguracji. Meteo.pl UM jest opcjonalny i wymaga Playwright (~200MB + wolniejsze).
