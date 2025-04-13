import streamlit as st
from streamlit_javascript import st_javascript


# Automatically run JS to get location
location = st_javascript("""
    navigator.geolocation.getCurrentPosition(
        (loc) => {
            const coords = {
                latitude: loc.coords.latitude,
                longitude: loc.coords.longitude
            };
            window.parent.postMessage({ type: 'streamlit:setComponentValue', value: coords }, '*');
        },
        (err) => {
            window.parent.postMessage({ type: 'streamlit:setComponentValue', value: null }, '*');
        }
    );
""")

if location:
    st.success(f"Your location: {location['latitude']}, {location['longitude']}")
else:
    st.warning("Location not fetched yet or denied.")