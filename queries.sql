-- Weather Forecast Tracker - Useful SQL Queries

-- 1. Show all forecasts for tomorrow with ensemble
SELECT 
    model,
    temp_max,
    hours_ahead,
    forecast_time
FROM forecasts
WHERE target_date = date('now', '+1 day')
ORDER BY hours_ahead DESC, model;

-- 2. Compare 24h forecasts with actuals (last 7 days)
SELECT 
    f.target_date,
    f.model,
    f.temp_max as forecast,
    o.temp_max as actual,
    ROUND(f.temp_max - o.temp_max, 2) as error,
    ABS(ROUND(f.temp_max - o.temp_max, 2)) as abs_error
FROM forecasts f
JOIN observations o ON f.target_date = o.date
WHERE f.hours_ahead BETWEEN 20 AND 28
  AND f.target_date >= date('now', '-7 days')
ORDER BY f.target_date DESC, abs_error ASC;

-- 3. Model ranking by MAE (last 30 days)
SELECT 
    model,
    COUNT(*) as forecasts,
    ROUND(AVG(ABS(bias)), 2) as mae,
    ROUND(AVG(bias), 2) as mean_error,
    ROUND(SQRT(AVG(bias * bias)), 2) as rmse,
    ROUND(MIN(bias), 2) as min_error,
    ROUND(MAX(bias), 2) as max_error
FROM model_bias
WHERE date >= date('now', '-30 days')
  AND hours_ahead BETWEEN 20 AND 28
GROUP BY model
ORDER BY mae ASC;

-- 4. Forecast evolution for specific date
SELECT 
    forecast_time,
    hours_ahead,
    model,
    temp_max,
    CASE 
        WHEN hours_ahead >= 48 THEN '48h+'
        WHEN hours_ahead >= 24 THEN '24-48h'
        WHEN hours_ahead >= 12 THEN '12-24h'
        ELSE '<12h'
    END as horizon_bucket
FROM forecasts
WHERE target_date = '2026-04-07'
ORDER BY hours_ahead DESC, forecast_time, model;

-- 5. Best model by forecast horizon
SELECT 
    CASE 
        WHEN hours_ahead >= 40 THEN '48h'
        WHEN hours_ahead >= 20 THEN '24h'
        WHEN hours_ahead >= 12 THEN '12h'
        ELSE '6h'
    END as horizon,
    model,
    COUNT(*) as days,
    ROUND(AVG(ABS(bias)), 2) as mae
FROM model_bias
WHERE date >= date('now', '-30 days')
GROUP BY horizon, model
ORDER BY horizon DESC, mae ASC;

-- 6. Daily forecast accuracy trend
SELECT 
    date,
    COUNT(DISTINCT model) as models,
    ROUND(AVG(ABS(bias)), 2) as avg_mae,
    ROUND(MIN(ABS(bias)), 2) as best_model_error,
    ROUND(MAX(ABS(bias)), 2) as worst_model_error
FROM model_bias
WHERE hours_ahead BETWEEN 20 AND 28
  AND date >= date('now', '-14 days')
GROUP BY date
ORDER BY date DESC;

-- 7. Ensemble vs individual models
WITH ensemble_errors AS (
    SELECT 
        date,
        ABS(bias) as error
    FROM model_bias
    WHERE model IN ('ENSEMBLE_MEDIAN', 'ENSEMBLE_MEAN')
      AND hours_ahead BETWEEN 20 AND 28
),
model_errors AS (
    SELECT 
        date,
        MIN(ABS(bias)) as best_single_model_error
    FROM model_bias
    WHERE model NOT LIKE 'ENSEMBLE%'
      AND hours_ahead BETWEEN 20 AND 28
    GROUP BY date
)
SELECT 
    e.date,
    ROUND(e.error, 2) as ensemble_error,
    ROUND(m.best_single_model_error, 2) as best_model_error,
    CASE 
        WHEN e.error < m.best_single_model_error THEN 'Ensemble better'
        ELSE 'Single model better'
    END as winner
FROM ensemble_errors e
JOIN model_errors m ON e.date = m.date
ORDER BY e.date DESC;

-- 8. Model consistency (std deviation of errors)
SELECT 
    model,
    COUNT(*) as days,
    ROUND(AVG(bias), 2) as mean_bias,
    ROUND(AVG(ABS(bias)), 2) as mae,
    ROUND(SQRT(AVG(bias * bias) - AVG(bias) * AVG(bias)), 2) as std_dev
FROM model_bias
WHERE hours_ahead BETWEEN 20 AND 28
  AND date >= date('now', '-30 days')
GROUP BY model
ORDER BY std_dev ASC;

-- 9. Recent observations
SELECT 
    date,
    temp_max,
    created_at
FROM observations
ORDER BY date DESC
LIMIT 14;

-- 10. Coverage check (do we have forecasts for all days?)
SELECT 
    o.date,
    o.temp_max as actual,
    COUNT(DISTINCT f.model) as models_count,
    GROUP_CONCAT(DISTINCT f.model) as models
FROM observations o
LEFT JOIN forecasts f ON f.target_date = o.date
GROUP BY o.date
ORDER BY o.date DESC;

-- 11. Hourly forecast progression for today
SELECT 
    strftime('%H:%M', forecast_time) as time,
    model,
    temp_max,
    hours_ahead
FROM forecasts
WHERE target_date = date('now')
  AND date(forecast_time) = date('now', '-1 day')
ORDER BY forecast_time, model;

-- 12. Export for CSV/plotting
SELECT 
    f.target_date as date,
    f.hours_ahead,
    f.model,
    f.temp_max as forecast,
    o.temp_max as actual,
    (f.temp_max - o.temp_max) as error
FROM forecasts f
LEFT JOIN observations o ON f.target_date = o.date
WHERE f.target_date >= date('now', '-30 days')
ORDER BY f.target_date DESC, f.hours_ahead DESC, f.model;
