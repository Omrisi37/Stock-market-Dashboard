# Real-Time Economic Dashboard
# Save this as: economic_dashboard.py

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests

# Page configuration
st.set_page_config(
    page_title="Economic Dashboard", 
    page_icon="📈", 
    layout="wide"
)

# Dashboard title
st.title("📈 Real-Time Economic Dashboard")
st.markdown("---")

# Sidebar for user inputs
st.sidebar.header("Dashboard Controls")

# Stock symbols to track
default_stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
selected_stocks = st.sidebar.multiselect(
    "Select Stocks to Track:",
    ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX"],
    default=default_stocks
)

# Time period selector
time_period = st.sidebar.selectbox(
    "Time Period:",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=2
)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.experimental_rerun()

# Function to get stock data
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_stock_data(symbols, period="1mo"):
    """
    Fetch stock data for given symbols
    """
    data = {}
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            info = stock.info
            
            data[symbol] = {
                'history': hist,
                'info': info,
                'current_price': hist['Close'].iloc[-1] if not hist.empty else 0,
                'change': hist['Close'].iloc[-1] - hist['Close'].iloc[-2] if len(hist) > 1 else 0
            }
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {e}")
            
    return data

# Function to get economic indicators
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_economic_indicators():
    """
    Get basic economic indicators
    """
    indicators = {}
    
    try:
        # Get major indices
        indices = {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI", 
            "NASDAQ": "^IXIC"
        }
        
        for name, symbol in indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = current - previous
                change_pct = (change / previous) * 100
                
                indicators[name] = {
                    'value': current,
                    'change': change,
                    'change_pct': change_pct
                }
    except Exception as e:
        st.error(f"Error fetching economic indicators: {e}")
    
    return indicators

# Main dashboard layout
if selected_stocks:
    
    # Get data
    with st.spinner("Loading stock data..."):
        stock_data = get_stock_data(selected_stocks, time_period)
    
    with st.spinner("Loading economic indicators..."):
        economic_data = get_economic_indicators()
    
    # Top section: Economic indicators
    st.header("📊 Market Overview")
    
    if economic_data:
        cols = st.columns(len(economic_data))
        for i, (name, data) in enumerate(economic_data.items()):
            with cols[i]:
                change_color = "🟢" if data['change'] >= 0 else "🔴"
                st.metric(
                    label=name,
                    value=f"{data['value']:,.2f}",
                    delta=f"{data['change_pct']:+.2f}%"
                )
    
    # Stock prices section
    st.header("💰 Stock Prices")
    
    # Current prices display
    price_cols = st.columns(len(selected_stocks))
    for i, symbol in enumerate(selected_stocks):
        if symbol in stock_data:
            data = stock_data[symbol]
            with price_cols[i]:
                change_pct = (data['change'] / (data['current_price'] - data['change'])) * 100
                st.metric(
                    label=symbol,
                    value=f"${data['current_price']:.2f}",
                    delta=f"{change_pct:+.2f}%"
                )
    
    # Stock price charts
    st.header("📈 Price Charts")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Individual Charts", "Comparison Chart"])
    
    with tab1:
        for symbol in selected_stocks:
            if symbol in stock_data and not stock_data[symbol]['history'].empty:
                hist = stock_data[symbol]['history']
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist.index,
                    y=hist['Close'],
                    mode='lines',
                    name=f'{symbol} Close Price',
                    line=dict(width=3)
                ))
                
                fig.update_layout(
                    title=f"{symbol} Stock Price ({time_period})",
                    xaxis_title="Date",
                    yaxis_title="Price ($)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Comparison chart (normalized)
        fig = go.Figure()
        
        for symbol in selected_stocks:
            if symbol in stock_data and not stock_data[symbol]['history'].empty:
                hist = stock_data[symbol]['history']
                # Normalize to percentage change from first day
                normalized = (hist['Close'] / hist['Close'].iloc[0] - 1) * 100
                
                fig.add_trace(go.Scatter(
                    x=hist.index,
                    y=normalized,
                    mode='lines',
                    name=symbol,
                    line=dict(width=2)
                ))
        
        fig.update_layout(
            title="Stock Performance Comparison (% Change)",
            xaxis_title="Date",
            yaxis_title="Percentage Change (%)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Volume analysis
    st.header("📊 Trading Volume")
    
    volume_data = []
    for symbol in selected_stocks:
        if symbol in stock_data and not stock_data[symbol]['history'].empty:
            hist = stock_data[symbol]['history']
            avg_volume = hist['Volume'].tail(30).mean()  # 30-day average
            recent_volume = hist['Volume'].iloc[-1]
            
            volume_data.append({
                'Stock': symbol,
                'Recent Volume': recent_volume,
                '30-Day Avg Volume': avg_volume,
                'Volume Ratio': recent_volume / avg_volume if avg_volume > 0 else 0
            })
    
    if volume_data:
        volume_df = pd.DataFrame(volume_data)
        
        fig = px.bar(
            volume_df, 
            x='Stock', 
            y='Volume Ratio',
            title="Recent Volume vs 30-Day Average (Ratio)",
            color='Volume Ratio',
            color_continuous_scale='RdYlGn'
        )
        fig.add_hline(y=1, line_dash="dash", line_color="black", 
                     annotation_text="Average Volume")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    st.header("📋 Summary Statistics")
    
    summary_data = []
    for symbol in selected_stocks:
        if symbol in stock_data and not stock_data[symbol]['history'].empty:
            hist = stock_data[symbol]['history']
            
            summary_data.append({
                'Stock': symbol,
                'Current Price': f"${stock_data[symbol]['current_price']:.2f}",
                'High': f"${hist['High'].max():.2f}",
                'Low': f"${hist['Low'].min():.2f}",
                'Avg Volume': f"{hist['Volume'].mean():,.0f}",
                'Volatility': f"{hist['Close'].pct_change().std():.4f}"
            })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

else:
    st.warning("Please select at least one stock symbol from the sidebar.")

# Footer
st.markdown("---")
st.markdown("""
**Data Sources:** Yahoo Finance  
**Update Frequency:** Real-time (cached for 1 minute)  
**Last Updated:** """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Instructions for running
st.sidebar.markdown("---")
st.sidebar.markdown("""
### How to Run:
1. Save this code as `economic_dashboard.py`
2. Install requirements: `pip install streamlit yfinance plotly`
3. Run: `streamlit run economic_dashboard.py`
4. Open browser to view dashboard
""")
