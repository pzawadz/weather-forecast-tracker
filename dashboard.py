#!/usr/bin/env python3
"""
Weather Forecast Tracker - Web Dashboard
Real-time forecasts, historical data, model performance
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Weather Forecast Tracker",
    page_icon="🌤️",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect('weather_forecasts.db', check_same_thread=False)

def load_data(query, params=()):
    """Load data from database"""
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    return df

# Header
st.title("🌤️ Weather Forecast Tracker")
st.markdown("Multi-model ensemble forecasting for Warsaw")

# Sidebar
st.sidebar.header("Settings")
days_back = st.sidebar.slider("History (days)", 1, 30, 7)
show_raw = st.sidebar.checkbox("Show individual models", value=True)

# Main metrics (current forecast)
st.header("📊 Current Forecast")

tomorrow = (datetime.now() + timedelta(days=1)).date()

# Get latest forecast
query = """
SELECT model, temp_max, forecast_time, hours_ahead
FROM forecasts
WHERE target_date = ?
  AND forecast_time = (SELECT MAX(forecast_time) FROM forecasts WHERE target_date = ?)
ORDER BY model
"""
current_forecast = load_data(query, (tomorrow, tomorrow))

if not current_forecast.empty:
    # Calculate ensemble
    models = current_forecast[~current_forecast['model'].str.contains('ENSEMBLE')]
    if not models.empty:
        median_temp = models['temp_max'].median()
        std_dev = models['temp_max'].std()
        min_temp = models['temp_max'].min()
        max_temp = models['temp_max'].max()
        
        forecast_time = pd.to_datetime(current_forecast['forecast_time'].iloc[0])
        hours_ahead = current_forecast['hours_ahead'].iloc[0]
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric(
            label="Target Date",
            value=tomorrow.strftime('%Y-%m-%d')
        )
        
        col2.metric(
            label="Ensemble Median",
            value=f"{median_temp:.1f}°C"
        )
        
        col3.metric(
            label="Uncertainty",
            value=f"±{std_dev:.1f}°C",
            delta=f"Range: {max_temp-min_temp:.1f}°C"
        )
        
        col4.metric(
            label="Models",
            value=len(models)
        )
        
        col5.metric(
            label="Updated",
            value=f"{hours_ahead:.0f}h ago",
            delta=forecast_time.strftime('%H:%M')
        )
        
        # Model breakdown
        if show_raw:
            st.subheader("Model Breakdown")
            
            # Create bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=models['model'],
                y=models['temp_max'],
                marker_color='lightblue',
                text=models['temp_max'].apply(lambda x: f"{x:.1f}°C"),
                textposition='auto',
            ))
            
            fig.add_hline(y=median_temp, line_dash="dash", line_color="red",
                         annotation_text=f"Median: {median_temp:.1f}°C")
            
            fig.update_layout(
                title="Current Model Predictions",
                xaxis_title="Model",
                yaxis_title="Temperature (°C)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No forecast data available. Run `./weather_tracker.py forecast` first.")

# Historical Performance
st.header("📈 Model Performance")

# Get model stats
query = """
SELECT 
    model,
    COUNT(*) as forecasts,
    AVG(ABS(bias)) as mae,
    SQRT(AVG(bias * bias)) as rmse,
    AVG(bias) as mean_error
FROM model_bias
WHERE date >= date('now', '-' || ? || ' days')
  AND hours_ahead BETWEEN 20 AND 28
GROUP BY model
ORDER BY mae ASC
"""
performance = load_data(query, (days_back,))

if not performance.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Mean Absolute Error (MAE)")
        fig = px.bar(
            performance,
            x='model',
            y='mae',
            color='mae',
            color_continuous_scale='RdYlGn_r',
            text='mae'
        )
        fig.update_traces(texttemplate='%{text:.2f}°C', textposition='outside')
        fig.update_layout(height=400, xaxis_title="", yaxis_title="MAE (°C)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Model Bias (systematic error)")
        fig = px.bar(
            performance,
            x='model',
            y='mean_error',
            color='mean_error',
            color_continuous_scale='RdBu_r',
            text='mean_error'
        )
        fig.update_traces(texttemplate='%{text:+.2f}°C', textposition='outside')
        fig.update_layout(height=400, xaxis_title="", yaxis_title="Mean Error (°C)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance table
    st.subheader("Detailed Statistics")
    perf_display = performance.copy()
    perf_display['mae'] = perf_display['mae'].apply(lambda x: f"{x:.2f}°C")
    perf_display['rmse'] = perf_display['rmse'].apply(lambda x: f"{x:.2f}°C")
    perf_display['mean_error'] = perf_display['mean_error'].apply(lambda x: f"{x:+.2f}°C")
    perf_display.columns = ['Model', 'Forecasts', 'MAE', 'RMSE', 'Bias']
    st.dataframe(perf_display, use_container_width=True)
else:
    st.info(f"No performance data for last {days_back} days. System needs at least 1 day of history.")

# Accuracy Over Time
st.header("📉 Accuracy Over Time")

query_accuracy = """
SELECT 
    o.date,
    o.temp_max as actual,
    AVG(CASE WHEN f.model NOT LIKE 'ENSEMBLE%' THEN f.temp_max END) as forecast_avg,
    ABS(AVG(CASE WHEN f.model NOT LIKE 'ENSEMBLE%' THEN f.temp_max END) - o.temp_max) as error,
    COUNT(DISTINCT CASE WHEN f.model NOT LIKE 'ENSEMBLE%' THEN f.model END) as model_count
FROM observations o
LEFT JOIN forecasts f ON f.target_date = o.date
WHERE o.date >= date('now', '-' || ? || ' days')
GROUP BY o.date
ORDER BY o.date ASC
"""
accuracy_data = load_data(query_accuracy, (days_back,))

if not accuracy_data.empty and len(accuracy_data) > 0:
    # Calculate MAE
    mae = accuracy_data['error'].mean()
    best_day = accuracy_data.loc[accuracy_data['error'].idxmin()]
    worst_day = accuracy_data.loc[accuracy_data['error'].idxmax()]
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean Absolute Error", f"{mae:.2f}°C")
    col2.metric("Best Forecast", f"{best_day['error']:.2f}°C", 
                delta=f"{best_day['date']}", delta_color="off")
    col3.metric("Worst Forecast", f"{worst_day['error']:.2f}°C",
                delta=f"{worst_day['date']}", delta_color="off")
    col4.metric("Days Tracked", len(accuracy_data))
    
    # Time series chart
    st.subheader("Error Over Time")
    
    fig = go.Figure()
    
    # Add error line
    fig.add_trace(go.Scatter(
        x=accuracy_data['date'],
        y=accuracy_data['error'],
        mode='lines+markers',
        name='Forecast Error',
        line=dict(color='red', width=2),
        marker=dict(size=8)
    ))
    
    # Add MAE reference line
    fig.add_trace(go.Scatter(
        x=accuracy_data['date'],
        y=[mae] * len(accuracy_data),
        mode='lines',
        name=f'Mean Error ({mae:.2f}°C)',
        line=dict(color='gray', width=1, dash='dash')
    ))
    
    # Add shaded area for good/bad performance
    fig.add_hrect(y0=0, y1=1.0, fillcolor="green", opacity=0.1, 
                  annotation_text="Excellent (<1°C)", annotation_position="right")
    fig.add_hrect(y0=1.0, y1=2.0, fillcolor="yellow", opacity=0.1,
                  annotation_text="Good (1-2°C)", annotation_position="right")
    fig.add_hrect(y0=2.0, y1=accuracy_data['error'].max() * 1.1, fillcolor="red", opacity=0.1,
                  annotation_text="Poor (>2°C)", annotation_position="right")
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Absolute Error (°C)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Model comparison over time
    st.subheader("Model Accuracy Comparison")
    
    query_models = """
    SELECT 
        f.model,
        o.date,
        ABS(f.temp_max - o.temp_max) as error
    FROM forecasts f
    JOIN observations o ON f.target_date = o.date
    WHERE f.model NOT LIKE 'ENSEMBLE%'
      AND o.date >= date('now', '-' || ? || ' days')
    ORDER BY o.date, f.model
    """
    model_accuracy = load_data(query_models, (days_back,))
    
    if not model_accuracy.empty:
        fig = px.line(
            model_accuracy,
            x='date',
            y='error',
            color='model',
            markers=True,
            title="Individual Model Errors Over Time"
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Absolute Error (°C)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("No accuracy data yet. System needs observations (run daily at 8 AM).")

# Forecast Evolution
st.header("🔄 Forecast Evolution")

# Select date
available_dates_query = """
SELECT DISTINCT target_date 
FROM forecasts 
WHERE target_date >= date('now', '-' || ? || ' days')
ORDER BY target_date DESC
"""
available_dates = load_data(available_dates_query, (days_back,))

if not available_dates.empty:
    selected_date = st.selectbox(
        "Select target date",
        available_dates['target_date'].tolist(),
        index=0
    )
    
    # Get forecast evolution
    query = """
    SELECT 
        forecast_time,
        hours_ahead,
        model,
        temp_max
    FROM forecasts
    WHERE target_date = ?
    ORDER BY forecast_time DESC, model
    """
    evolution = load_data(query, (selected_date,))
    
    if not evolution.empty:
        # Get actual observation if available
        obs_query = "SELECT temp_max FROM observations WHERE date = ?"
        obs = load_data(obs_query, (selected_date,))
        actual = obs['temp_max'].iloc[0] if not obs.empty else None
        
        # Plot evolution
        fig = go.Figure()
        
        for model in evolution['model'].unique():
            model_data = evolution[evolution['model'] == model]
            fig.add_trace(go.Scatter(
                x=model_data['hours_ahead'],
                y=model_data['temp_max'],
                mode='lines+markers',
                name=model,
                line=dict(width=2 if 'ENSEMBLE' in model else 1)
            ))
        
        if actual is not None:
            fig.add_hline(y=actual, line_dash="dash", line_color="green",
                         annotation_text=f"Actual: {actual:.1f}°C")
        
        fig.update_layout(
            title=f"Forecast Evolution for {selected_date}",
            xaxis_title="Hours Before Target Date",
            yaxis_title="Temperature (°C)",
            height=500,
            xaxis=dict(autorange="reversed")  # More recent on right
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show actual error if available
        if actual is not None:
            st.subheader(f"Final Errors (Actual: {actual:.1f}°C)")
            
            final_forecasts = evolution[evolution['hours_ahead'] == evolution['hours_ahead'].min()]
            errors = []
            for _, row in final_forecasts.iterrows():
                errors.append({
                    'Model': row['model'],
                    'Forecast': f"{row['temp_max']:.1f}°C",
                    'Error': f"{row['temp_max'] - actual:+.1f}°C",
                    'Abs Error': f"{abs(row['temp_max'] - actual):.1f}°C"
                })
            
            error_df = pd.DataFrame(errors)
            st.dataframe(error_df, use_container_width=True)

# Recent Observations
st.header("🌡️ Recent Observations")

query = """
SELECT date, temp_max, created_at
FROM observations
ORDER BY date DESC
LIMIT 14
"""
observations = load_data(query)

if not observations.empty:
    # Plot observations
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=observations['date'],
        y=observations['temp_max'],
        mode='lines+markers',
        name='Observed Max Temp',
        line=dict(color='orange', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Recent Maximum Temperatures",
        xaxis_title="Date",
        yaxis_title="Temperature (°C)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Table
    obs_display = observations.copy()
    obs_display['temp_max'] = obs_display['temp_max'].apply(lambda x: f"{x:.1f}°C")
    obs_display.columns = ['Date', 'Max Temp', 'Recorded At']
    st.dataframe(obs_display, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Weather Forecast Tracker | Data: <a href='https://open-meteo.com'>Open-Meteo</a> | 
    Models: ECMWF, ICON-EU, GFS, ICON, Meteo France, GEM</p>
</div>
""", unsafe_allow_html=True)
