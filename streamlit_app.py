import streamlit as st
import pandas as pd
import google.generativeai as genai

# Set up the look of the web page
st.set_page_config(page_title="FC 26 Build Engine", page_icon="⚽", layout="centered")
st.title("⚽ FC 26 Attribute Optimizer")

# Connect to the Gemini Brain using your Secret Key
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # We add tools='code_execution' so the API can run Python math just like the Gem did!
    model = genai.GenerativeModel('gemini-1.5-pro', tools='code_execution')
except Exception as e:
    st.error("Error connecting to Gemini API. Please check your Secrets.")

# Set up the App's "Memory"
if "scout_report" not in st.session_state:
    st.session_state.scout_report = None
if "player_request" not in st.session_state:
    st.session_state.player_request = ""

st.divider()

# ==========================================
# STEP 1: THE SCOUTING PHASE
# ==========================================
st.header("Step 1: Scout the Blueprint")
player_input = st.text_input("Player Identity & Position", placeholder="e.g., Micky van de Ven CB", value=st.session_state.player_request)

if st.button("Generate Scouting Report"):
    if player_input:
        with st.spinner("🕵️‍♂️ Analyzing databases to find the perfect Archetype & Playstyles..."):
            try:
                # Load only the files needed for Phase 1
                all_arch = pd.read_csv("ALL_ARCHETYPES.csv").to_csv(index=False)
                arch_profile = pd.read_csv("ARCHETYPE_PROFILE.csv").to_csv(index=False)
                ps_info = pd.read_csv("PLAYSTYLE_INFO.csv").to_csv(index=False)
                specs = pd.read_csv("SPECIALISATIONS.csv").to_csv(index=False)
                
                prompt_1 = f"""
                You are the ultimate FC 26 Scout. Create a blueprint for a "{player_input}".
                
                Databases provided below:
                --- ALL_ARCHETYPES ---
                {all_arch}
                --- ARCHETYPE_PROFILE ---
                {arch_profile}
                --- PLAYSTYLE_INFO ---
                {ps_info}
                --- SPECIALISATIONS ---
                {specs}
                
                Instructions:
                1. Pick the best Archetype from ARCHETYPE_PROFILE and recommend Height/Weight.
                2. Equip EXACTLY 3 Playstyle+ (Read Base_Playstyle_Plus).
                3. Pick the 8 best standard Playstyles based on PLAYSTYLE_INFO.
                4. Check SPECIALISATIONS. If it improves realism, swap 1 Base Playstyle+ for the bonus one.
                5. Sort attributes into Core (6-8), Secondary (10-12), and Tertiary (the rest).
                6. Assign target Skill Moves and Weak Foot.
                
                Output a clean, readable Scouting Report. Make sure to bold the **Chosen Archetype**. DO NOT MENTION ATTRIBUTE POINTS.
                """
                response_1 = model.generate_content(prompt_1)
                
                # Save to memory so it stays on screen
                st.session_state.scout_report = response_1.text
                st.session_state.player_request = player_input
                st.rerun() # Refresh the screen
                
            except Exception as e:
                st.error(f"Something went wrong: {e}")
    else:
        st.warning("Please enter a player identity.")

# ==========================================
# STEP 2: THE MATH ENGINE (Only shows if Step 1 is done)
# ==========================================
if st.session_state.scout_report:
    st.success("✅ Scouting Complete!")
    st.markdown(st.session_state.scout_report)
    
    st.divider()
    st.header("Step 2: The Math Engine")
    st.info("Check your game to see how many Attribute Points (AP) you have available for the Archetype selected above.")
    
    ap_budget = st.number_input("Attribute Points (AP) Budget", min_value=1000, max_value=3500, value=2450, step=10)
    
    if st.button("Calculate Perfect Stats", type="primary"):
        with st.spinner("🧠 Writing and running Python script to distribute exactly to 0 AP... (This takes about 30-45 seconds)"):
            try:
                # Load only the files needed for Phase 2
                playstyles = pd.read_csv("PLAYSTYLES.csv").to_csv(index=False)
                master_cost = pd.read_csv("MASTER_COST_DATA.csv").to_csv(index=False)
                
                prompt_2 = f"""
                You are an FC 26 Optimizer using a Python Code Interpreter. 
                Distribute EXACTLY {ap_budget} Attribute Points (AP) based on this blueprint:
                
                {st.session_state.scout_report}
                
                Databases provided:
                --- PLAYSTYLES ---
                {playstyles}
                --- MASTER_COST_DATA ---
                {master_cost}
                
                Instructions for your Python code:
                1. Dynamically read the MASTER_COST_DATA provided. 
                2. Base stats cost 0 AP.
                3. Upgrade all required Playstyle/Specialisation minimums first.
                4. Loop to exhaust Core attributes point-by-point.
                5. Loop to exhaust Secondary attributes point-by-point.
                6. Spend any remaining budget exclusively on Tertiary attributes by sorting cheapest first until budget is EXACTLY 0.
                7. Keep a strict ledger of exactly how much AP is spent on each attribute.
                
                Output a beautiful final card showing all categories (Pace, Shooting, Passing, Dribbling, Defending, Physicality, Skill Moves, Weak Foot) and Playstyles.
                Next to every stat, you MUST print: `(Spent: [AP] AP)`.
                """
                response_2 = model.generate_content(prompt_2)
                
                st.success("✅ Math Engine Complete!")
                st.markdown(response_2.text)
                
                # Add a button to reset the app for the next build
                if st.button("Start New Build"):
                    st.session_state.scout_report = None
                    st.session_state.player_request = ""
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Something went wrong: {e}")
