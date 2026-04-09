"""
Betting Performance Section for Weather Dashboard
Insert this after "Current Forecast" section (around line 155)
"""

# ============================================================================
# BETTING PERFORMANCE SECTION
# ============================================================================

st.header("🎯 Betting Performance")
st.markdown("Optimal timing for Polymarket bets: **18h ahead** (best accuracy + odds)")

# Get recent observations (today + yesterday)
today = datetime.now().date()
yesterday = today - timedelta(days=1)

query_obs = """
SELECT date, temp_max
FROM observations
WHERE location = ?
  AND date IN (?, ?)
ORDER BY date DESC
"""
recent_obs = load_data(query_obs, (location_key, today, yesterday))

if not recent_obs.empty:
    # Process observations
    obs_dict = {row['date']: row['temp_max'] for _, row in recent_obs.iterrows()}
    today_actual = obs_dict.get(str(today))
    yesterday_actual = obs_dict.get(str(yesterday))
    
    # Function to get forecast at specific timeframe
    def get_forecast_at_timeframe(target_date, hours_range):
        """Get ensemble forecast at specific lead time"""
        query = """
        SELECT AVG(temp_max) as avg_temp, COUNT(*) as model_count
        FROM forecasts
        WHERE target_date = ?
          AND location = ?
          AND hours_ahead BETWEEN ? AND ?
          AND model NOT LIKE 'ENSEMBLE%'
        """
        min_hours = hours_range[0]
        max_hours = hours_range[1]
        result = load_data(query, (target_date, location_key, min_hours, max_hours))
        
        if not result.empty and result['model_count'].iloc[0] > 0:
            return result['avg_temp'].iloc[0]
        return None
    
    # Get forecasts at key timeframes
    timeframes = {
        '6h': (5, 7),
        '12h': (11, 13),
        '18h': (17, 19),  # PRIMARY betting window
        '24h': (23, 25),  # SECONDARY
        '48h': (47, 49)
    }
    
    # Display Today + Yesterday metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Today")
        if today_actual is not None:
            st.metric("Actual Temperature", f"{today_actual:.1f}°C")
            
            # Get 18h forecast for today
            today_18h = get_forecast_at_timeframe(today, timeframes['18h'])
            if today_18h is not None:
                error_18h = today_18h - today_actual
                st.caption(f"🎯 18h forecast: {today_18h:.1f}°C (error: {error_18h:+.1f}°C)")
            
            # Get 24h forecast for today
            today_24h = get_forecast_at_timeframe(today, timeframes['24h'])
            if today_24h is not None:
                error_24h = today_24h - today_actual
                st.caption(f"📊 24h forecast: {today_24h:.1f}°C (error: {error_24h:+.1f}°C)")
        else:
            st.info("Today's observation not yet available")
    
    with col2:
        st.subheader("📅 Yesterday")
        if yesterday_actual is not None:
            st.metric("Actual Temperature", f"{yesterday_actual:.1f}°C")
            
            # Get 18h forecast for yesterday
            yesterday_18h = get_forecast_at_timeframe(yesterday, timeframes['18h'])
            if yesterday_18h is not None:
                error_18h = yesterday_18h - yesterday_actual
                st.caption(f"🎯 18h forecast: {yesterday_18h:.1f}°C (error: {error_18h:+.1f}°C)")
            
            # Get 24h forecast for yesterday
            yesterday_24h = get_forecast_at_timeframe(yesterday, timeframes['24h'])
            if yesterday_24h is not None:
                error_24h = yesterday_24h - yesterday_actual
                st.caption(f"📊 24h forecast: {yesterday_24h:.1f}°C (error: {error_24h:+.1f}°C)")
        else:
            st.info("Yesterday's observation not available")
    
    st.markdown("---")
    
    # Forecast Timeline Table (for today or yesterday)
    st.subheader("📊 Forecast Evolution")
    
    # Choose which date to show timeline for
    timeline_date = today if today_actual is not None else yesterday
    timeline_actual = today_actual if today_actual is not None else yesterday_actual
    
    if timeline_actual is not None:
        st.markdown(f"**Date:** {timeline_date} | **Actual:** {timeline_actual:.1f}°C")
        
        # Get forecasts for all models at different timeframes
        query_timeline = """
        SELECT 
            model,
            hours_ahead,
            temp_max
        FROM forecasts
        WHERE target_date = ?
          AND location = ?
          AND model NOT LIKE 'ENSEMBLE%'
        ORDER BY model, hours_ahead
        """
        timeline_data = load_data(query_timeline, (timeline_date, location_key))
        
        if not timeline_data.empty:
            # Pivot table: models as rows, timeframes as columns
            pivot_data = []
            models = timeline_data['model'].unique()
            
            for model in models:
                model_data = timeline_data[timeline_data['model'] == model]
                row = {'Model': model}
                
                for tf_name, (min_h, max_h) in timeframes.items():
                    # Find forecast closest to this timeframe
                    tf_forecasts = model_data[
                        (model_data['hours_ahead'] >= min_h) & 
                        (model_data['hours_ahead'] <= max_h)
                    ]
                    if not tf_forecasts.empty:
                        # Take average if multiple forecasts in range
                        avg_temp = tf_forecasts['temp_max'].mean()
                        error = avg_temp - timeline_actual
                        row[tf_name] = f"{avg_temp:.1f} ({error:+.1f})"
                    else:
                        row[tf_name] = "-"
                
                pivot_data.append(row)
            
            if pivot_data:
                df_timeline = pd.DataFrame(pivot_data)
                
                # Reorder columns for display
                column_order = ['Model', '48h', '24h', '18h', '12h', '6h']
                df_timeline = df_timeline[[col for col in column_order if col in df_timeline.columns]]
                
                st.dataframe(
                    df_timeline,
                    use_container_width=True,
                    height=400
                )
                
                st.caption("Format: Temperature (Error). 🎯 18h is PRIMARY betting window, 📊 24h is SECONDARY")
    
    st.markdown("---")
    
    # Timeframe Accuracy Chart (aggregate over last N days)
    st.subheader("📈 Accuracy by Lead Time")
    st.markdown(f"Average performance over last {days_back} days")
    
    # Query to get MAE by timeframe bucket
    query_timeframe_acc = """
    SELECT 
        CASE 
            WHEN hours_ahead BETWEEN 5 AND 7 THEN '6h'
            WHEN hours_ahead BETWEEN 11 AND 13 THEN '12h'
            WHEN hours_ahead BETWEEN 17 AND 19 THEN '18h'
            WHEN hours_ahead BETWEEN 23 AND 25 THEN '24h'
            WHEN hours_ahead BETWEEN 35 AND 37 THEN '36h'
            WHEN hours_ahead BETWEEN 47 AND 49 THEN '48h'
        END as timeframe,
        AVG(ABS(bias)) as mae,
        COUNT(*) as count
    FROM model_bias
    WHERE location = ?
      AND date >= date('now', '-' || ? || ' days')
      AND hours_ahead IN (6, 12, 18, 24, 36, 48)
    GROUP BY timeframe
    ORDER BY 
        CASE timeframe
            WHEN '6h' THEN 1
            WHEN '12h' THEN 2
            WHEN '18h' THEN 3
            WHEN '24h' THEN 4
            WHEN '36h' THEN 5
            WHEN '48h' THEN 6
        END
    """
    timeframe_acc = load_data(query_timeframe_acc, (location_key, days_back))
    
    if not timeframe_acc.empty:
        # Create bar chart
        fig = go.Figure()
        
        # Color code: green for 18h (sweet spot), yellow for others
        colors = ['lightcoral' if tf == '6h' or tf == '12h' 
                 else 'lightgreen' if tf == '18h' 
                 else 'lightyellow' if tf == '24h'
                 else 'lightgray'
                 for tf in timeframe_acc['timeframe']]
        
        fig.add_trace(go.Bar(
            x=timeframe_acc['timeframe'],
            y=timeframe_acc['mae'],
            marker_color=colors,
            text=timeframe_acc['mae'].apply(lambda x: f"{x:.2f}°C"),
            textposition='outside',
            name='MAE'
        ))
        
        fig.update_layout(
            title="Mean Absolute Error by Lead Time",
            xaxis_title="Lead Time (hours before target)",
            yaxis_title="MAE (°C)",
            height=400,
            annotations=[
                dict(
                    x='18h',
                    y=timeframe_acc[timeframe_acc['timeframe'] == '18h']['mae'].iloc[0] if '18h' in timeframe_acc['timeframe'].values else 0,
                    text="🎯 PRIMARY",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="green",
                    ax=0,
                    ay=-40
                )
            ] if '18h' in timeframe_acc['timeframe'].values else []
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary table
        st.caption("**Recommended betting windows:**")
        st.caption("🎯 **18h ahead** - PRIMARY (best accuracy + odds balance)")
        st.caption("📊 **24h ahead** - SECONDARY (standard benchmark)")
        st.caption("💎 **48h ahead** - EARLY (contrarian plays, higher risk)")
    else:
        st.info(f"Not enough data yet. Need at least {days_back} days of history.")
else:
    st.info("No recent observations available. Run `./weather_tracker.py observe-all` first.")

# End of Betting Performance section
