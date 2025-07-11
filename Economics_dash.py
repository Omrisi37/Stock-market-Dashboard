# Real-Time Economic Dashboard - Enhanced Version
# Save this as: economic_dashboard.py

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import time

# Page configuration
st.set_page_config(
    page_title="Economic Dashboard", 
    page_icon="📈", 
    layout="wide"
)

# Dashboard title
st.title("📈 Real-Time Economic Dashboard")
st.markdown("---")

# Stock exchanges and their indices
EXCHANGES = {
    "🇺🇸 US Markets": {
        "indices": {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI", 
            "NASDAQ": "^IXIC",
            "Russell 2000": "^RUT"
        },
        "popular_stocks": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX", "AMD", "ORCL"]
    },
    "🇮🇱 Israel (TASE)": {
        "indices": {
            "TA-125": "^TA125.TA",
            "TA-35": "^TA35.TA",
            "TA-90": "^TA90.TA"
        },
        "popular_stocks": ["TEVA.TA", "ICL.TA", "CHKP.TA", "NICE.TA", "ELCO.TA", "POLI.TA", "MZTF.TA", "ESLT.TA"]
    },
    "🇪🇺 Europe": {
        "indices": {
            "FTSE 100": "^FTSE",
            "DAX": "^GDAXI",
            "CAC 40": "^FCHI"
        },
        "popular_stocks": ["ASML.AS", "SAP.DE", "NESN.SW", "NOVN.SW", "MC.PA", "OR.PA"]
    },
    "🇯🇵 Japan": {
        "indices": {
            "Nikkei 225": "^N225",
            "TOPIX": "^TPX"
        },
        "popular_stocks": ["7203.T", "6758.T", "9984.T", "9983.T", "6861.T"]
    }
}

# Sidebar for user inputs
st.sidebar.header("Dashboard Controls")

# Exchange selector
selected_exchange = st.sidebar.selectbox(
    "Select Stock Exchange:",
    list(EXCHANGES.keys()),
    index=0
)

# Get data for selected exchange
exchange_data = EXCHANGES[selected_exchange]

# Stock search functionality
st.sidebar.subheader("🔍 Search Stocks")
search_term = st.sidebar.text_input(
    "Search by company name or symbol:",
    placeholder="e.g., Apple, AAPL, Microsoft"
)

# Function to search stocks with better error handling
@st.cache_data(ttl=3600)  # Cache for 1 hour
def search_stocks(query, current_exchange):
    """
    Search for stocks based on company name or symbol
    """
    if not query or len(query) < 2:
        return []
    
    try:
        search_results = []
        query_upper = query.upper().strip()
        
        # Handle different exchanges
        if current_exchange == "🇮🇱 Israel (TASE)":
            # Try with .TA suffix for Israeli stocks
            test_symbols = [query_upper, f"{query_upper}.TA"]
        elif current_exchange == "🇪🇺 Europe":
            # Try common European suffixes
            test_symbols = [query_upper, f"{query_upper}.AS", f"{query_upper}.DE", f"{query_upper}.PA"]
        elif current_exchange == "🇯🇵 Japan":
            # Try with .T suffix for Japanese stocks
            test_symbols = [query_upper, f"{query_upper}.T"]
        else:
            # US markets - try as is
            test_symbols = [query_upper]
        
        for symbol in test_symbols:
            try:
                ticker = yf.Ticker(symbol)
                # Try to get basic info with timeout
                info = ticker.info
                
                # Check if we got valid data
                if info and len(info) > 3:  # Basic check for valid response
                    long_name = info.get('longName', info.get('shortName', symbol))
                    if long_name and long_name != symbol:
                        search_results.append({
                            'symbol': symbol,
                            'name': long_name,
                            'sector': info.get('sector', 'N/A'),
                            'currency': info.get('currency', 'N/A')
                        })
                        break  # Found valid result, no need to try other variations
                        
            except Exception:
                continue  # Try next symbol variation
        
        return search_results[:5]  # Limit to 5 results
        
    except Exception as e:
        return []

# Initialize session state for selected exchange
if 'current_exchange' not in st.session_state:
    st.session_state.current_exchange = selected_exchange

# Reset stocks if exchange changed
if st.session_state.current_exchange != selected_exchange:
    st.session_state.current_exchange = selected_exchange
    st.session_state.selected_stocks = exchange_data['popular_stocks'][:5]

# Initialize selected stocks for current exchange
if 'selected_stocks' not in st.session_state:
    st.session_state.selected_stocks = exchange_data['popular_stocks'][:5]

# Create extended options list (popular stocks + custom stocks)
available_stocks = list(exchange_data['popular_stocks'])
custom_stocks = getattr(st.session_state, 'custom_stocks', [])

# Add custom stocks to available options if they're not already there
for stock in custom_stocks:
    if stock not in available_stocks:
        available_stocks.append(stock)

# Ensure selected stocks are in available options
valid_selected_stocks = []
for stock in st.session_state.selected_stocks:
    if stock in available_stocks:
        valid_selected_stocks.append(stock)
    elif stock in exchange_data['popular_stocks']:
        valid_selected_stocks.append(stock)

# Update session state with valid stocks only
st.session_state.selected_stocks = valid_selected_stocks

# Show search results
if search_term:
    with st.sidebar:
        with st.spinner("Searching..."):
            search_results = search_stocks(search_term, selected_exchange)
        
        if search_results:
            st.sidebar.write("**Search Results:**")
            for i, result in enumerate(search_results):
                button_key = f"search_{result['symbol']}_{i}_{hash(search_term)}"
                if st.sidebar.button(
                    f"{result['symbol']} - {result['name'][:25]}...", 
                    key=button_key,
                    help=f"Sector: {result['sector']}, Currency: {result['currency']}"
                ):
                    # Add to custom stocks list
                    if 'custom_stocks' not in st.session_state:
                        st.session_state.custom_stocks = []
                    
                    # Add to available stocks if not already there
                    if result['symbol'] not in available_stocks:
                        available_stocks.append(result['symbol'])
                        st.session_state.custom_stocks.append(result['symbol'])
                    
                    # Add to selected stocks if not already selected
                    if result['symbol'] not in st.session_state.selected_stocks:
                        st.session_state.selected_stocks.append(result['symbol'])
                    
                    # Rerun to update the multiselect
                    st.rerun()
        else:
            st.sidebar.write("No results found")

# Stock symbols to track
selected_stocks = st.sidebar.multiselect(
    "Selected Stocks:",
    available_stocks,
    default=st.session_state.selected_stocks,
    key="stock_multiselect",
    help="Select stocks to track. Use search above to add more stocks."
)

# Update session state
st.session_state.selected_stocks = selected_stocks

# Time period selector
time_period = st.sidebar.selectbox(
    "Time Period:",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=2
)

# Market status indicator
def get_market_status():
    """
    Check if market is currently open
    """
    try:
        # Use a major index to check market status
        if selected_exchange == "🇺🇸 US Markets":
            test_ticker = yf.Ticker("^GSPC")
        elif selected_exchange == "🇮🇱 Israel (TASE)":
            test_ticker = yf.Ticker("^TA125.TA")
        else:
            test_ticker = yf.Ticker("^GSPC")  # Default to S&P 500
        
        # Get recent data
        hist = test_ticker.history(period="2d", interval="1d")
        
        if len(hist) >= 2:
            last_date = hist.index[-1].date()
            today = datetime.now().date()
            
            # Check if last data is from today
            if last_date == today:
                return "🟢 Market Open"
            elif (today - last_date).days <= 3:  # Weekend or recent holiday
                return "🟡 Market Closed (Recent Data Available)"
            else:
                return "🔴 Market Closed (Stale Data)"
        else:
            return "🔴 No Market Data"
    except:
        return "❓ Market Status Unknown"

# Display market status
market_status = get_market_status()
st.sidebar.markdown(f"**Market Status:** {market_status}")

# Refresh controls with better error handling
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Refresh", key="refresh_button"):
        # Clear all cached data
        st.cache_data.clear()
        # Reset search term
        if 'search_term' in st.session_state:
            del st.session_state['search_term']
        st.success("Data refreshed!")
        time.sleep(1)
        st.rerun()

with col2:
    if st.button("🗑️ Clear", key="clear_button"):
        # Clear cache and reset selections
        st.cache_data.clear()
        if 'selected_stocks' in st.session_state:
            st.session_state.selected_stocks = exchange_data['popular_stocks'][:5]
        if 'custom_stocks' in st.session_state:
            del st.session_state['custom_stocks']
        st.success("Cache cleared!")
        time.sleep(1)
        st.rerun()

# Function to get stock data with error handling
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_stock_data(symbols, period="1mo"):
    """
    Fetch stock data for given symbols with comprehensive error handling
    """
    data = {}
    errors = []
    
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            
            # Get historical data
            hist = stock.history(period=period)
            
            if hist.empty:
                errors.append(f"{symbol}: No historical data available")
                continue
            
            # Get company info (with fallback)
            try:
                info = stock.info
            except:
                info = {'longName': symbol, 'sector': 'Unknown'}
            
            # Calculate current price and change
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                previous_price = hist['Close'].iloc[-2]
                change = current_price - previous_price
                change_pct = (change / previous_price) * 100 if previous_price != 0 else 0
            else:
                current_price = hist['Close'].iloc[-1] if not hist.empty else 0
                change = 0
                change_pct = 0
            
            data[symbol] = {
                'history': hist,
                'info': info,
                'current_price': current_price,
                'change': change,
                'change_pct': change_pct,
                'last_update': hist.index[-1] if not hist.empty else datetime.now()
            }
            
        except Exception as e:
            errors.append(f"{symbol}: {str(e)}")
            continue
    
    return data, errors

# Function to get economic indicators with error handling
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_economic_indicators(exchange_key):
    """
    Get economic indicators for selected exchange
    """
    indicators = {}
    errors = []
    
    try:
        indices = EXCHANGES[exchange_key]['indices']
        
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")  # Get more days to handle weekends
                
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = current - previous
                    change_pct = (change / previous) * 100 if previous != 0 else 0
                    
                    indicators[name] = {
                        'value': current,
                        'change': change,
                        'change_pct': change_pct,
                        'last_update': hist.index[-1]
                    }
                elif len(hist) == 1:
                    # Only one day of data
                    current = hist['Close'].iloc[-1]
                    indicators[name] = {
                        'value': current,
                        'change': 0,
                        'change_pct': 0,
                        'last_update': hist.index[-1]
                    }
                else:
                    errors.append(f"{name}: No data available")
                    
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
                continue
                
    except Exception as e:
        errors.append(f"Error fetching indicators: {str(e)}")
    
    return indicators, errors

# Main dashboard layout
if selected_stocks:
    
    # Get data with error handling
    with st.spinner("Loading data..."):
        stock_data, stock_errors = get_stock_data(selected_stocks, time_period)
        economic_data, econ_errors = get_economic_indicators(selected_exchange)
    
    # Display any errors
    if stock_errors:
        with st.expander("⚠️ Data Loading Issues", expanded=False):
            for error in stock_errors:
                st.warning(error)
    
    if econ_errors:
        with st.expander("⚠️ Index Data Issues", expanded=False):
            for error in econ_errors:
                st.warning(error)
    
    # Top section: Economic indicators
    st.header(f"📊 {selected_exchange} Overview")
    
    if economic_data:
        cols = st.columns(len(economic_data))
        for i, (name, data) in enumerate(economic_data.items()):
            with cols[i]:
                st.metric(
                    label=name,
                    value=f"{data['value']:,.2f}",
                    delta=f"{data['change_pct']:+.2f}%",
                    help=f"Last updated: {data['last_update'].strftime('%Y-%m-%d %H:%M')}"
                )
    else:
        st.warning("No index data available for selected exchange")
    
    # Stock prices section
    st.header("💰 Stock Prices")
    
    if stock_data:
        # Current prices display
        num_cols = min(len(stock_data), 5)  # Maximum 5 columns
        price_cols = st.columns(num_cols)
        
        stock_items = list(stock_data.items())
        for i in range(0, len(stock_items), num_cols):
            batch = stock_items[i:i+num_cols]
            for j, (symbol, data) in enumerate(batch):
                col_idx = j % num_cols
                with price_cols[col_idx]:
                    company_name = data['info'].get('longName', symbol)
                    short_name = company_name[:20] + "..." if len(company_name) > 20 else company_name
                    
                    st.metric(
                        label=f"{symbol}",
                        value=f"${data['current_price']:.2f}" if data['current_price'] > 0 else "N/A",
                        delta=f"{data['change_pct']:+.2f}%" if data['change_pct'] != 0 else None,
                        help=short_name
                    )
        
        # Stock price charts
        st.header("📈 Price Charts")
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["Individual Charts", "Comparison Chart"])
        
        with tab1:
            for symbol, data in stock_data.items():
                if not data['history'].empty:
                    hist = data['history']
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=hist['Close'],
                        mode='lines',
                        name=f'{symbol} Close Price',
                        line=dict(width=3),
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                    'Date: %{x}<br>' +
                                    'Price: $%{y:.2f}<extra></extra>'
                    ))
                    
                    company_name = data['info'].get('longName', symbol)
                    fig.update_layout(
                        title=f"{symbol} - {company_name} ({time_period})",
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Comparison chart (normalized)
            if len(stock_data) > 1:
                fig = go.Figure()
                
                for symbol, data in stock_data.items():
                    if not data['history'].empty:
                        hist = data['history']
                        # Normalize to percentage change from first day
                        if hist['Close'].iloc[0] != 0:
                            normalized = (hist['Close'] / hist['Close'].iloc[0] - 1) * 100
                            
                            fig.add_trace(go.Scatter(
                                x=hist.index,
                                y=normalized,
                                mode='lines',
                                name=symbol,
                                line=dict(width=2),
                                hovertemplate='<b>%{fullData.name}</b><br>' +
                                            'Date: %{x}<br>' +
                                            'Change: %{y:.2f}%<extra></extra>'
                            ))
                
                fig.update_layout(
                    title="Stock Performance Comparison (% Change from Start)",
                    xaxis_title="Date",
                    yaxis_title="Percentage Change (%)",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Select multiple stocks to see comparison chart")
        
        # Volume analysis
        st.header("📊 Trading Volume")
        
        volume_data = []
        for symbol, data in stock_data.items():
            if not data['history'].empty:
                hist = data['history']
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
                color_continuous_scale='RdYlGn',
                hover_data=['Recent Volume', '30-Day Avg Volume']
            )
            fig.add_hline(y=1, line_dash="dash", line_color="black", 
                         annotation_text="Average Volume")
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.header("📋 Summary Statistics")
        
        summary_data = []
        for symbol, data in stock_data.items():
            if not data['history'].empty:
                hist = data['history']
                
                summary_data.append({
                    'Stock': symbol,
                    'Company': data['info'].get('longName', symbol)[:30] + '...' if len(data['info'].get('longName', symbol)) > 30 else data['info'].get('longName', symbol),
                    'Current Price': f"${data['current_price']:.2f}",
                    'Daily Change': f"{data['change_pct']:+.2f}%",
                    'High': f"${hist['High'].max():.2f}",
                    'Low': f"${hist['Low'].min():.2f}",
                    'Avg Volume': f"{hist['Volume'].mean():,.0f}",
                    'Volatility': f"{hist['Close'].pct_change().std():.4f}",
                    'Last Update': data['last_update'].strftime('%Y-%m-%d %H:%M')
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
    
    else:
        st.error("No stock data available. Please check your selected stocks or try refreshing.")

else:
    st.warning("Please select at least one stock symbol from the sidebar.")

# Footer with helpful information
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    **Selected Exchange:** {selected_exchange}  
    **Market Status:** {market_status}  
    """)

with col2:
    st.markdown(f"""
    **Data Source:** Yahoo Finance  
    **Update Frequency:** 1 minute cache  
    """)

with col3:
    st.markdown(f"""
    **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
    **Time Period:** {time_period}  
    """)

# Instructions for running
st.sidebar.markdown("---")
st.sidebar.markdown("""
### Instructions:
1. Select exchange from dropdown
2. Search for stocks by name/symbol
3. Choose time period for analysis
4. Click refresh to update data
5. Use clear cache if data seems stuck

### Israeli Stocks Examples:
- TEVA.TA (Teva Pharmaceutical)
- ICL.TA (ICL Group)
- CHKP.TA (Check Point)
- NICE.TA (Nice Systems)
""")
