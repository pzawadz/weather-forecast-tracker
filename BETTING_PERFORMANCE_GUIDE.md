# Betting Performance Dashboard - User Guide

**Dashboard URL:** https://d2175rmfwid55c.cloudfront.net

---

## 🎯 Overview

The **Betting Performance** section helps you make better Polymarket bets by showing:
1. **Today + Yesterday** actual temperatures vs forecasts
2. **Forecast Evolution** - how accurate each model was at different timeframes
3. **Timeframe Accuracy** - which lead time performs best

---

## 📊 Dashboard Sections

### 1. Today + Yesterday Quick View

```
📅 Today                          📅 Yesterday
Actual Temperature: 9.3°C         Actual Temperature: 10.2°C
🎯 18h forecast: 9.0°C (-0.3°C)   🎯 18h forecast: 10.1°C (-0.1°C)
📊 24h forecast: 8.9°C (-0.4°C)   📊 24h forecast: 10.0°C (-0.2°C)
```

**What it shows:**
- Actual measured temperature (from observations)
- **18h ahead forecast** - your PRIMARY betting window 🎯
- **24h ahead forecast** - your SECONDARY reference 📊
- Error in parentheses (forecast - actual)

**How to read errors:**
- **Negative (-0.3°C):** Forecast was too cold
- **Positive (+0.5°C):** Forecast was too hot
- **Close to 0:** Very accurate! ✅

---

### 2. Forecast Evolution Table

```
Date: 2026-04-08 | Actual: 9.3°C

Model              | 48h         | 24h         | 18h         | 12h         | 6h
-------------------|-------------|-------------|-------------|-------------|-------------
ICON Global        | 8.8 (-0.5)  | 9.2 (-0.1)  | 9.3 (0.0)✅  | 9.3 (0.0)   | 9.3 (0.0)
ENSEMBLE           | 8.5 (-0.8)  | 8.9 (-0.4)  | 9.0 (-0.3)  | 9.1 (-0.2)  | 9.1 (-0.2)
ICON-EU            | 8.3 (-1.0)  | 8.8 (-0.5)  | 8.9 (-0.4)  | 8.9 (-0.4)  | 8.9 (-0.4)
ECMWF              | 9.9 (+0.6)  | 10.3 (+1.0) | 10.4 (+1.1) | 10.4 (+1.1) | 10.4 (+1.1)
```

**What it shows:**
- How each model's forecast evolved over time
- Format: `Temperature (Error)`
- **18h column is highlighted** - this is your sweet spot!

**How to use:**
1. Look at the **18h column** - these forecasts had 18 hours to reach the target
2. Find models with **smallest errors** at 18h
3. Check if they're **consistently good** across multiple days
4. **Bet accordingly** when those models agree

**Key insights:**
- Models **converge** closer to target time (6h column most accurate)
- But by then **market is closed**! ⏰
- **18h ahead** gives you time to bet before closure
- Some models (ECMWF in example) have **persistent bias** → avoid!

---

### 3. Timeframe Accuracy Chart

```
Mean Absolute Error by Lead Time

MAE (°C)
   1.2 ├─────────────────────────────── 48h
       │
   0.9 ├────────────────────── 36h
       │
   0.6 ├──────────────── 24h (📊 SECONDARY)
       │
   0.4 ├───────── 18h (🎯 PRIMARY) ← Best balance!
       │
   0.3 ├──── 12h
       │
   0.2 ├── 6h
       └────────────────────────────────
```

**What it shows:**
- Average accuracy (MAE) at each lead time
- Based on last 7 days (configurable in sidebar)
- Color-coded: 🟢 Green = 18h (optimal)

**How to interpret:**
- **Lower MAE = Better accuracy**
- **18h ahead:** Best balance of accuracy + betting opportunity
- **6-12h ahead:** Most accurate, but market closed
- **48h ahead:** Least accurate, but early odds

---

## 🎯 How to Use for Polymarket Betting

### Step 1: Check Yesterday's Performance
**Goal:** See which models were accurate recently

```
Yesterday: Actual 10.2°C
🎯 18h forecast: 10.1°C (-0.1°C) ✅ Excellent!
```

✅ **If error < 0.5°C:** Models are performing well  
⚠️ **If error > 1.0°C:** Models might be off, bet cautiously

---

### Step 2: Review Forecast Evolution
**Goal:** Identify best-performing models

Look at the **18h column** in the table:
- Which models had **smallest errors**?
- Are they **consistently good** across days?

**Example:**
```
ICON Global at 18h: 0.0°C error ✅ Trust this model!
ECMWF at 18h: +1.1°C error ❌ Avoid this model
```

---

### Step 3: Check Current Forecast
**Goal:** See tomorrow's predictions

Scroll up to "📊 Current Forecast" section:
- **Ensemble Median:** Consensus prediction
- **Model Breakdown:** Individual model predictions

**If models agree (range < 2°C):** High confidence ✅  
**If models disagree (range > 3°C):** Uncertain, risky ⚠️

---

### Step 4: Place Your Bet

**Timing:**
- **18:00 UTC** (evening before) - PRIMARY window 🎯
  - Example: Tuesday 18:00 → Bet on Wednesday temp
  - Market closes: Wednesday 00:00
  
- **00:00-08:00 UTC** (morning of D-1) - SECONDARY window 📊
  - Example: Wednesday morning → Bet on Thursday temp
  - Market closes: Thursday 00:00

**Strategy:**
1. Check dashboard at **18:00 UTC**
2. If models agree within 1-2°C → **High confidence bet** ✅
3. If yesterday's error was <0.5°C → **Trust the forecast** ✅
4. If models disagree or yesterday error >1°C → **Pass** or **small bet** ⚠️

---

## 📈 Timeframe Recommendations

| Lead Time | Accuracy | Market Status | Recommendation |
|-----------|----------|---------------|----------------|
| **6h ahead** | ~95% | Closed ⏰ | Too late |
| **12h ahead** | ~90% | Closed ⏰ | Too late |
| **18h ahead** | ~85% | Open ✅ | 🎯 **PRIMARY** |
| **24h ahead** | ~80% | Open ✅ | 📊 **SECONDARY** |
| **36h ahead** | ~75% | Open ✅ | 💎 Early |
| **48h ahead** | ~70% | Open ✅ | ⚠️ Risky |

---

## 🏆 Success Criteria

### High-Confidence Bet ✅
- ✅ Models agree (range < 2°C)
- ✅ Yesterday's 18h error < 0.5°C
- ✅ Ensemble median clear (not on boundary)
- ✅ Top models (ICON-EU, ECMWF, IMGW) align

**Action:** Bet confidently!

### Medium-Confidence Bet ⚠️
- ⚠️ Models somewhat disagree (range 2-3°C)
- ⚠️ Yesterday's error 0.5-1.0°C
- ⚠️ Some models off, but ensemble stable

**Action:** Smaller bet or wait

### Low-Confidence / Pass ❌
- ❌ Models disagree heavily (range > 3°C)
- ❌ Yesterday's error > 1.5°C
- ❌ Weather pattern change (front moving in)

**Action:** Skip or very small bet

---

## 💡 Pro Tips

### 1. Track Model Performance
**Goal:** Know which models work best for your city

Check "Forecast Evolution" daily:
- Which models have **lowest errors** at 18h?
- Which have **persistent bias** (always too hot/cold)?
- Trust the **consistent winners**

### 2. Use Yesterday as Guide
**Goal:** Recent accuracy predicts today's accuracy

If yesterday's 18h forecast was accurate → Today likely similar  
If yesterday was off → Be more cautious today

### 3. Weather Pattern Changes
**Goal:** Detect when forecasts become uncertain

**Stable pattern:** Models agree, errors small → Bet confidently ✅  
**Changing pattern:** Models disagree, errors large → Reduce risk ⚠️

Check "Current Forecast" uncertainty (±X°C):
- **Low (<1°C):** Stable ✅
- **High (>2°C):** Uncertain ⚠️

### 4. Multi-City Strategy
**Goal:** Diversify across multiple cities

- Warsaw 🇵🇱: ICON-EU strong (7km resolution)
- Paris 🇫🇷: Meteo France best (native model)
- Munich 🇩🇪: ICON-EU excellent (German model)
- London 🇬🇧: ECMWF reliable (UK-based)

Use **location selector** in sidebar to switch cities!

---

## 🔧 Dashboard Settings

**Sidebar → Settings:**
- **📍 Location:** Choose city (Warsaw/Paris/Munich/London)
- **History (days):** 1-30 days (affects timeframe accuracy chart)
- **Show individual models:** Toggle model breakdown on/off

**Recommended:**
- **History: 7 days** (good balance, recent data)
- **Models: ON** (see individual performance)

---

## 📅 Daily Routine

### Morning Check (08:00-10:00 local)
1. Open dashboard
2. Check **Yesterday** section
   - Was 18h forecast accurate?
   - Note which models performed well
3. Scroll to **Current Forecast**
   - See tomorrow's prediction
   - Check model agreement

### Evening Bet (18:00-20:00 local / ~17:00-19:00 UTC)
1. Re-check dashboard (fresh data!)
2. Review **Betting Performance**
   - Today + Yesterday accuracy
   - Forecast Evolution (18h column)
3. **Place bet** if confident
4. Set reminder for tomorrow morning

### Next Morning (Review)
1. Check actual temperature
2. Compare with your bet
3. Update mental notes on model performance

---

## 🚀 Expected ROI

**With good strategy (following 18h window):**
- **Conservative:** 10-15% monthly
- **Moderate:** 15-20% monthly
- **Aggressive:** 20-30% monthly (higher risk)

**Key to success:**
- ✅ Follow 18h PRIMARY window
- ✅ Only bet when models agree
- ✅ Track model performance per city
- ✅ Skip uncertain days (preserve capital)

---

## ❓ FAQ

**Q: Why 18h ahead, not 6h (most accurate)?**  
A: Market closes at 00:00 UTC. By 6h ahead (18:00 same day), market is already closed!

**Q: Can I bet 48h ahead for better odds?**  
A: Yes, but accuracy drops to ~70%. Higher risk, higher reward.

**Q: Which model is best?**  
A: Depends on city! Check "Forecast Evolution" - varies by location and weather pattern.

**Q: What if models disagree?**  
A: Skip or bet small. Disagreement = uncertainty = higher risk.

**Q: How often should I check dashboard?**  
A: Daily evening (18:00 UTC) for PRIMARY bets. Morning for review.

---

**Dashboard URL:** https://d2175rmfwid55c.cloudfront.net

**Questions?** Check the dashboard daily and track which strategies work best for you!

🎯 **Good luck betting!** 🚀
