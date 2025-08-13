import json

import pandas as pd
import streamlit as st

from agents import TravelAgent
from tools import WeatherMCPTool


# Configuration
st.set_page_config(page_title="AI Travel Assistant", page_icon="🌍", layout="wide")

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .suggestion-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Streamlit App

def main():
    st.markdown('<h1 class="main-header">🌍 AI Travel Assistant</h1>', unsafe_allow_html=True)
    st.markdown("Get weather-based travel suggestions powered by AI")

    # Sidebar for API keys
    st.sidebar.header("🔑 API Configuration")

    groq_api_key = st.sidebar.text_input(
        "Groq API Key", type="password", help="Get your API key from https://console.groq.com/"
    )

    weather_api_key = st.sidebar.text_input(
        "WeatherAPI Key", type="password", help="Get your API key from https://www.weatherapi.com/"
    )

    if not groq_api_key or not weather_api_key:
        st.warning("⚠️ Please enter both API keys in the sidebar to continue.")
        st.info(
            """
        **To get started:**
        1. Get a Groq API key from: https://console.groq.com/
        2. Get a WeatherAPI key from: https://www.weatherapi.com/
        3. Enter both keys in the sidebar
        """
        )
        return

    # Initialize the travel agent
    if "travel_agent" not in st.session_state:
        st.session_state.travel_agent = TravelAgent(groq_api_key, weather_api_key)

    # Main interface
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🗺️ Plan Your Trip")

        location = st.text_input(
            "Enter destination:",
            placeholder="e.g., Paris, France or New York, NY",
            help="Enter any city, region, or country",
        )

        travel_type = st.selectbox(
            "Type of trip:",
            [
                "general",
                "adventure",
                "cultural",
                "business",
                "family",
                "romantic",
                "food & wine",
            ],
            help="This helps customize the suggestions to your travel style",
        )

        if st.button("🔍 Get Travel Suggestions", type="primary"):
            if location:
                with st.spinner(f"Analyzing weather and generating suggestions for {location}..."):
                    suggestions = st.session_state.travel_agent.get_travel_suggestions(
                        location, travel_type
                    )

                    st.markdown('<div class="suggestion-card">', unsafe_allow_html=True)
                    st.markdown("### 🎯 AI Travel Suggestions")
                    st.markdown(suggestions)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.error("Please enter a destination!")

    with col2:
        st.header("🌤️ Quick Weather Check")

        quick_location = st.text_input("Quick weather lookup:", placeholder="City name")

        if st.button("Get Weather", type="secondary"):
            if quick_location:
                with st.spinner("Fetching weather..."):
                    weather_tool = WeatherMCPTool(api_key=weather_api_key)
                    weather_data = weather_tool._run(quick_location, days=3)

                    try:
                        weather_info = json.loads(weather_data)

                        # Check if it's an error message
                        if isinstance(weather_info, dict) and "Error" in str(weather_info):
                            st.error(weather_data)
                            return

                        st.markdown('<div class="weather-card">', unsafe_allow_html=True)

                        # Location info
                        location_info = weather_info.get("location", {})
                        current_info = weather_info.get("current", {})

                        st.markdown(
                            f"### 📍 {location_info.get('name', 'Unknown Location')}"
                        )
                        if location_info.get("region"):
                            st.markdown(
                                f"*{location_info.get('region')}, {location_info.get('country', '')}*"
                            )

                        # Current weather
                        col_temp, col_condition = st.columns(2)
                        with col_temp:
                            temp_c = current_info.get("temperature_c", 0)
                            temp_f = current_info.get("temperature_f", 0)
                            st.markdown(f"**🌡️ Temperature:** {temp_c}°C ({temp_f}°F)")

                            feels_like_c = current_info.get("feels_like_c", 0)
                            feels_like_f = current_info.get("feels_like_f", 0)
                            st.markdown(
                                f"**🤔 Feels like:** {feels_like_c}°C ({feels_like_f}°F)"
                            )

                        with col_condition:
                            condition = current_info.get("condition", "Unknown")
                            st.markdown(f"**☁️ Condition:** {condition}")

                            humidity = current_info.get("humidity", 0)
                            st.markdown(f"**💧 Humidity:** {humidity}%")

                        # Additional details
                        col_wind, col_other = st.columns(2)
                        with col_wind:
                            wind_kph = current_info.get("wind_kph", 0)
                            wind_dir = current_info.get("wind_dir", "")
                            st.markdown(f"**💨 Wind:** {wind_kph} km/h {wind_dir}")

                        with col_other:
                            uv_index = current_info.get("uv_index", 0)
                            visibility = current_info.get("visibility_km", 0)
                            st.markdown(f"**☀️ UV Index:** {uv_index}")
                            st.markdown(f"**👁️ Visibility:** {visibility} km")

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Forecast table
                        forecast = weather_info.get("forecast", [])
                        if forecast:
                            st.markdown("**📅 Forecast:**")
                            forecast_df = pd.DataFrame(
                                [
                                    {
                                        "Date": day["date"],
                                        "High (°C)": day["max_temp_c"],
                                        "Low (°C)": day["min_temp_c"],
                                        "Condition": day["condition"],
                                        "Rain %": f"{day['chance_of_rain']}%",
                                        "UV": day.get("uv_index", 0),
                                    }
                                    for day in forecast
                                ]
                            )
                            st.dataframe(
                                forecast_df, use_container_width=True, hide_index=True
                            )

                        # Show alerts if any
                        alerts = weather_info.get("alerts", [])
                        if alerts:
                            st.warning(
                                f"⚠️ {len(alerts)} weather alert(s) active for this location"
                            )
                            for alert in alerts[:2]:  # Show first 2 alerts
                                st.info(f"**{alert.get('headline', 'Weather Alert')}**")

                    except json.JSONDecodeError:
                        st.error("Error: Could not parse weather data")
                        st.text("Raw response:")
                        st.code(weather_data)
                    except Exception as e:
                        st.error(f"Error displaying weather data: {str(e)}")
                        st.text("Raw response:")
                        st.code(weather_data)
            else:
                st.error("Please enter a location!")

    # Chat History (optional feature)
    st.header("💬 Chat with Travel Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything about travel and weather..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.travel_agent.get_travel_suggestions(
                    prompt, "general"
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style="text-align: center; color: #666;">
        Powered by Groq LLama3, WeatherAPI, and LangChain MCP Tools
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()