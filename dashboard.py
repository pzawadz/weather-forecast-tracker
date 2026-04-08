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

# Location configurations (must match weather_tracker.py)
LOCATIONS = {
    'warsaw': {'name': 'Warsaw', 'country': 'Poland', 'flag': '🇵🇱'},
    'paris': {'name': 'Paris', 'country': 'France', 'flag': '🇫🇷'},
    'munich': {'name': 'Munich', 'country': 'Germany', 'flag': '🇩🇪'},
    'london': {'name': 'London', 'country': 'UK', 'flag': '🇬🇧'}
}

# Header
st.title("🌤️ Weather Forecast Tracker")
st.markdown("Multi-model ensemble forecasting across Europe")

# Sidebar
st.sidebar.header("Settings")

# Location selector
location_key = st.sidebar.selectbox(
    "📍 Location",
    options=list(LOCATIONS.keys()),
    format_func=lambda x: f"{LOCATIONS[x]['flag']} {LOCATIONS[x]['name']}, {LOCATIONS[x]['country']}",
    index=0
)
location_info = LOCATIONS[location_key]

st.sidebar.markdown(f"**Selected:** {location_info['flag']} {location_info['name']}")

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
  AND location = ?
  AND forecast_time = (SELECT MAX(forecast_time) FROM forecasts WHERE target_date = ? AND location = ?)
ORDER BY model
"""
current_forecast = load_data(query, (tomorrow, location_key, tomorrow, location_key))

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
        
        # Calculate time since last update
        now = datetime.now()
        hours_since_update = (now - forecast_time.to_pydatetime()).total_seconds() / 3600
        
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
            label="Last Update",
            value=f"{hours_since_update:.1f}h ago",
            delta=f"{hours_ahead:.0f}h ahead"
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
WHERE location = ?
  AND date >= date('now', '-' || ? || ' days')
  AND hours_ahead BETWEEN 20 AND 28
GROUP BY model
ORDER BY mae ASC
"""
performance = load_data(query, (location_key, days_back))

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
LEFT JOIN forecasts f ON f.target_date = o.date AND f.location = o.location
WHERE o.location = ?
  AND o.date >= date('now', '-' || ? || ' days')
GROUP BY o.date
ORDER BY o.date ASC
"""
accuracy_data = load_data(query_accuracy, (location_key, days_back))

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
    JOIN observations o ON f.target_date = o.date AND f.location = o.location
    WHERE f.location = ?
      AND f.model NOT LIKE 'ENSEMBLE%'
      AND o.date >= date('now', '-' || ? || ' days')
    ORDER BY o.date, f.model
    """
    model_accuracy = load_data(query_models, (location_key, days_back))
    
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
st.markdown("Track how forecasts converge as we approach the target date")

# Select date
available_dates_query = """
SELECT DISTINCT target_date 
FROM forecasts 
WHERE location = ?
  AND target_date >= date('now', '-' || ? || ' days')
ORDER BY target_date DESC
"""
available_dates = load_data(available_dates_query, (location_key, days_back))

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
    WHERE location = ?
      AND target_date = ?
    ORDER BY forecast_time DESC, model
    """
    evolution = load_data(query, (location_key, selected_date))
    
    if not evolution.empty:
        # Get actual observation if available
        obs_query = "SELECT temp_max FROM observations WHERE location = ? AND date = ?"
        obs = load_data(obs_query, (location_key, selected_date))
        actual = obs['temp_max'].iloc[0] if not obs.empty else None
        
        # Calculate convergence metrics
        evolution_models = evolution[~evolution['model'].str.contains('ENSEMBLE')]
        if not evolution_models.empty:
            # Group by forecast_time to calculate spread over time
            convergence = evolution_models.groupby('hours_ahead').agg({
                'temp_max': ['mean', 'std', 'min', 'max', 'count']
            }).reset_index()
            convergence.columns = ['hours_ahead', 'mean', 'std', 'min', 'max', 'count']
            convergence['spread'] = convergence['max'] - convergence['min']
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            latest_spread = convergence.iloc[0]['spread'] if len(convergence) > 0 else 0
            earliest_spread = convergence.iloc[-1]['spread'] if len(convergence) > 0 else 0
            
            col1.metric("Latest Spread", f"{latest_spread:.1f}°C",
                       delta=f"{latest_spread - earliest_spread:+.1f}°C")
            col2.metric("Latest Uncertainty", f"±{convergence.iloc[0]['std']:.1f}°C")
            col3.metric("Forecast Updates", len(convergence))
            if actual is not None:
                final_error = abs(convergence.iloc[0]['mean'] - actual)
                col4.metric("Final Error", f"{final_error:.2f}°C",
                           delta="Excellent" if final_error < 1.0 else "Good" if final_error < 2.0 else "Poor")
            else:
                col4.metric("Actual", "Pending")
        
        # Main evolution chart
        st.subheader("Forecast Convergence")
        
        fig = go.Figure()
        
        # Add individual models as thin lines
        for model in evolution[~evolution['model'].str.contains('ENSEMBLE')]['model'].unique():
            model_data = evolution[evolution['model'] == model]
            fig.add_trace(go.Scatter(
                x=model_data['hours_ahead'],
                y=model_data['temp_max'],
                mode='lines+markers',
                name=model,
                line=dict(width=1),
                opacity=0.6,
                marker=dict(size=4)
            ))
        
        # Add ensemble as thick line
        ensemble_data = evolution[evolution['model'] == 'ENSEMBLE_CORRECTED']
        if not ensemble_data.empty:
            fig.add_trace(go.Scatter(
                x=ensemble_data['hours_ahead'],
                y=ensemble_data['temp_max'],
                mode='lines+markers',
                name='Ensemble (corrected)',
                line=dict(width=3, color='blue'),
                marker=dict(size=8)
            ))
        
        # Add actual temperature if available
        if actual is not None:
            fig.add_hline(y=actual, line_dash="dash", line_color="green", line_width=2,
                         annotation_text=f"Actual: {actual:.1f}°C",
                         annotation_position="right")
            
            # Add shaded area showing final uncertainty
            if not convergence.empty:
                final_std = convergence.iloc[0]['std']
                fig.add_hrect(y0=actual-final_std, y1=actual+final_std,
                             fillcolor="green", opacity=0.1,
                             annotation_text=f"±{final_std:.1f}°C", annotation_position="left")
        
        fig.update_layout(
            xaxis_title="Hours Before Target Date",
            yaxis_title="Temperature (°C)",
            height=500,
            xaxis=dict(autorange="reversed"),  # More recent on right
            hovermode='x unified',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Uncertainty evolution chart
        if not convergence.empty:
            st.subheader("Uncertainty Over Time")
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=convergence['hours_ahead'],
                y=convergence['std'],
                mode='lines+markers',
                name='Standard Deviation',
                line=dict(color='orange', width=2),
                fill='tozeroy',
                fillcolor='rgba(255,165,0,0.2)'
            ))
            
            fig2.add_trace(go.Scatter(
                x=convergence['hours_ahead'],
                y=convergence['spread'],
                mode='lines+markers',
                name='Model Spread (max-min)',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            fig2.update_layout(
                xaxis_title="Hours Before Target Date",
                yaxis_title="Uncertainty (°C)",
                height=300,
                xaxis=dict(autorange="reversed"),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Insights
            if convergence['std'].iloc[0] < convergence['std'].iloc[-1]:
                st.success("✓ Forecast uncertainty decreased over time (models converging)")
            else:
                st.warning("⚠ Forecast uncertainty increased (models diverging)")
        
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
WHERE location = ?
ORDER BY date DESC
LIMIT 14
"""
observations = load_data(query, (location_key,))

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

# Temperature Patterns Analysis
st.header("🌡️ Accuracy by Temperature Range")

def classify_temp(temp):
    """Classify temperature into ranges"""
    if temp < 0:
        return "Freezing (<0°C)"
    elif temp < 10:
        return "Cold (0-10°C)"
    elif temp < 20:
        return "Cool (10-20°C)"
    elif temp < 25:
        return "Warm (20-25°C)"
    else:
        return "Hot (>25°C)"

query_temp_patterns = """
SELECT 
    o.date,
    o.temp_max as actual,
    AVG(CASE WHEN f.model NOT LIKE 'ENSEMBLE%' THEN f.temp_max END) as forecast_avg,
    ABS(AVG(CASE WHEN f.model NOT LIKE 'ENSEMBLE%' THEN f.temp_max END) - o.temp_max) as error
FROM observations o
LEFT JOIN forecasts f ON f.target_date = o.date AND f.location = o.location
WHERE o.location = ?
  AND o.date >= date('now', '-' || ? || ' days')
GROUP BY o.date
"""
temp_patterns = load_data(query_temp_patterns, (location_key, days_back))

if not temp_patterns.empty and len(temp_patterns) > 0:
    # Add temperature classification
    temp_patterns['temp_range'] = temp_patterns['actual'].apply(classify_temp)
    
    # Calculate MAE by temperature range
    mae_by_range = temp_patterns.groupby('temp_range').agg({
        'error': ['mean', 'count']
    }).reset_index()
    mae_by_range.columns = ['temp_range', 'mae', 'count']
    mae_by_range = mae_by_range[mae_by_range['count'] > 0]  # Only show ranges with data
    
    if not mae_by_range.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart: MAE by temperature range
            fig = px.bar(
                mae_by_range,
                x='temp_range',
                y='mae',
                color='mae',
                color_continuous_scale='RdYlGn_r',
                text='mae',
                title="Forecast Accuracy by Temperature Range"
            )
            fig.update_traces(texttemplate='%{text:.2f}°C', textposition='outside')
            fig.update_layout(
                xaxis_title="Temperature Range",
                yaxis_title="Mean Absolute Error (°C)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sample count by range
            fig2 = px.bar(
                mae_by_range,
                x='temp_range',
                y='count',
                color='count',
                text='count',
                title="Sample Count by Temperature Range"
            )
            fig2.update_traces(texttemplate='%{text}', textposition='outside')
            fig2.update_layout(
                xaxis_title="Temperature Range",
                yaxis_title="Number of Days",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Insights
        best_range = mae_by_range.loc[mae_by_range['mae'].idxmin()]
        worst_range = mae_by_range.loc[mae_by_range['mae'].idxmax()]
        
        col1, col2 = st.columns(2)
        col1.success(f"✓ Best accuracy: **{best_range['temp_range']}** (MAE: {best_range['mae']:.2f}°C)")
        if best_range['temp_range'] != worst_range['temp_range']:
            col2.warning(f"⚠ Worst accuracy: **{worst_range['temp_range']}** (MAE: {worst_range['mae']:.2f}°C)")
        
        st.info("💡 **Note:** This classification is based on observed temperatures only. "
               "True weather pattern analysis (sunny/rainy/cloudy) requires weather codes from API.")
else:
    st.info("Not enough data for temperature pattern analysis yet.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Weather Forecast Tracker | Data: <a href='https://open-meteo.com'>Open-Meteo</a> | 
    Models: ECMWF, ICON-EU, GFS, ICON, Meteo France, GEM</p>
</div>
""", unsafe_allow_html=True)
