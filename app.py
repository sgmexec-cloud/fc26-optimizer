import streamlit as st
import pandas as pd

# Set up the look of the web page
st.set_page_config(page_title="FC 26 Build Engine", page_icon="⚽", layout="centered")

st.title("⚽ FC 26 Attribute Optimizer")
st.write("Welcome to the ultimate FC 26 Scout and Math Engine. Enter your player vision and AP budget to generate the mathematically perfect build.")

st.divider()

# Create the Input Boxes for the User
col1, col2 = st.columns(2)

with col1:
    player_request = st.text_input("Player Identity & Position", placeholder="e.g., Micky van de Ven CB")

with col2:
    ap_budget = st.number_input("Attribute Points (AP) Budget", min_value=1000, max_value=3500, value=2630, step=10)

st.divider()

# The Magic Button
if st.button("Generate Perfect Build", type="primary"):
    if player_request:
        st.info(f"Scouting {player_request} with {ap_budget} AP... (AI Engine will be connected here!)")
    else:
        st.warning("Please enter a player identity before generating a build.")
