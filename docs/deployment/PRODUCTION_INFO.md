# Weather Forecast Tracker - Production Info

## 🌐 Dashboard URL
**Production:** https://d2175rmfwid55c.cloudfront.net/

## 📊 System Status

**Region:** EU-WEST-1 (Ireland)
**Server:** ubuntu@172.31.13.147 (EC2 t4g.small)
**Database:** SQLite at `/home/ubuntu/weather-forecast-tracker/weather_forecasts.db`

## 🔗 Links
- **Dashboard:** https://d2175rmfwid55c.cloudfront.net/
- **GitHub:** https://github.com/pzawadz/weather-forecast-tracker
- **Location:** Warsaw (52.2297°N, 21.0122°E)

## 📈 Current Setup
- **Models:** 6 (ECMWF, ICON-EU, GFS, ICON Global, Meteo France, GEM)
- **Collection:** Every 4 hours (parallel, ~0.5s)
- **Observations:** Daily 8:00 AM UTC
- **Accuracy:** MAE: 0.00°C (1 day sample)

## 🎯 Performance
- **Forecasts collected:** 54
- **Observations:** 1
- **Success rate:** 100% (6/6 models)
- **Best model (Poland):** ICON-EU (7km, German regional)

---

**Last Updated:** 2026-04-08 08:55 UTC
