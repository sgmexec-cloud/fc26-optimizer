import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

# Set up the look of the web page
st.set_page_config(page_title="FC 26 Build Engine", page_icon="⚽", layout="centered")
st.title("⚽ FC 26 Attribute Optimizer")

# Connect to the Gemini Brain
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash', tools='code_execution')
except Exception as e:
    st.error("Error connecting to Gemini API. Please check your Secrets.")

# Set up the App's "Memory"
if "scout_report" not in st.session_state:
    st.session_state.scout_report = None
if "player_request" not in st.session_state:
    st.session_state.player_request = ""

st.divider()

# ==========================================
# DATA STITCHING FUNCTION
# ==========================================
@st.cache_data
def load_master_costs():
    try:
        df1 = pd.read_csv("COST_1.csv")
        df2 = pd.read_csv("COST_2.csv")
        df3 = pd.read_csv("COST_3.csv")
        df4 = pd.read_csv("COST_4.csv")
        master_df = pd.concat([df1, df2, df3, df4], ignore_index=True)
        return master_df
    except Exception as e:
        st.error(f"Waiting for COST files 1-4 to be uploaded... ({e})")
        return pd.DataFrame()

# ==========================================
# STEP 1: THE SCOUTING PHASE
# ==========================================
st.header("Step 1: Scout the Blueprint")
player_input = st.text_input("Player Identity & Position", placeholder="e.g., Micky van de Ven CB", value=st.session_state.player_request)

if st.button("Generate Scouting Report"):
    if player_input:
        with st.spinner("🕵️‍♂️ Analyzing databases to find the perfect Archetype & Playstyles..."):
            try:
                all_arch = pd.read_csv("ALL_ARCHETYPES.csv").to_csv(index=False)
                arch_profile = pd.read_csv("ARCHETYPE_PROFILE.csv").to_csv(index=False)
                ps_info = pd.read_csv("PLAYSTYLE_INFO.csv").to_csv(index=False)
                specs = pd.read_csv("SPECIALISATIONS.csv").to_csv(index=False)
                playstyles = pd.read_csv("PLAYSTYLES.csv").to_csv(index=False)
                
                cost_df = load_master_costs()
                
                if not cost_df.empty:
                    available_archetypes = cost_df['Archetype'].str.upper().unique().tolist()
                    
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
                    --- PLAYSTYLES ---
                    {playstyles}
                    
                    Instructions:
                    1. Pick the best Archetype from ARCHETYPE_PROFILE. 
                       **CRITICAL RESTRICTION: You MUST ONLY select an Archetype from this exact list: {available_archetypes}.**
                    2. Equip EXACTLY 3 Playstyle+ (Read Base_Playstyle_Plus).
                    3. Pick the 8 best standard Playstyles based on PLAYSTYLE_INFO.
                    4. Check SPECIALISATIONS. Swap 1 Base Playstyle+ for the bonus one if realistic.
                    5. Sort attributes into Core (6-8), Secondary (10-12), and Tertiary (the rest).
                    6. Assign target Skill Moves and Weak Foot.
                    
                    OUTPUT FORMATTING RULE:
                    You MUST start your response with this exact line at the very top:
                    [ARCHETYPE: Insert Name Here]
                    
                    Then, print the rest of your clean, readable Scouting Report below it. DO NOT MENTION ATTRIBUTE POINTS.
                    CRITICAL: Look at PLAYSTYLES. List the exact Attribute minimums required for each of the 8 Playstyles next to their name.
                    """
                    response_1 = model.generate_content(prompt_1)
                    
                    st.session_state.scout_report = response_1.text
                    st.session_state.player_request = player_input
                    st.rerun() 
                
            except Exception as e:
                st.error(f"Something went wrong: {e}")
    else:
        st.warning("Please enter a player identity.")

# ==========================================
# STEP 2: THE MATH ENGINE
# ==========================================
if st.session_state.scout_report:
    st.success("✅ Scouting Complete!")
    st.markdown(st.session_state.scout_report)
    
    st.divider()
    st.header("Step 2: The Math Engine")
    st.info("Check your game to see how many Attribute Points (AP) you have available for the Archetype selected above.")
    
    ap_budget = st.number_input("Attribute Points (AP) Budget", min_value=1000, max_value=3500, value=2450, step=10)
    
    if st.button("Calculate Perfect Stats", type="primary"):
        with st.spinner("🧠 Calculating the exact point distribution... (This should only take a few seconds now!)"):
            try:
                playstyles = pd.read_csv("PLAYSTYLES.csv").to_csv(index=False)
                cost_df = load_master_costs()
                
                # MAGIC FILTER: Find the chosen archetype in the text and slice the database!
                match = re.search(r'\[ARCHETYPE:\s*(.+?)\]', st.session_state.scout_report)
                chosen_arch = match.group(1).strip() if match else ""
                
                if chosen_arch:
                    # Keep ONLY the rows for the selected archetype!
                    filtered_cost_df = cost_df[cost_df['Archetype'].str.upper() == chosen_arch.upper()]
                    master_cost_string = filtered_cost_df.to_csv(index=False)
                else:
                    # Fallback just in case
                    master_cost_string = cost_df.to_csv(index=False)

                prompt_2 = f"""
                You are an FC 26 Optimizer using a Python Code Interpreter. 
                Distribute EXACTLY {ap_budget} Attribute Points (AP) based on this blueprint:
                
                {st.session_state.scout_report}
                
                Databases provided:
                --- PLAYSTYLES ---
                {playstyles}
                --- MASTER_COST_DATA (Filtered for chosen archetype) ---
                {master_cost_string}
                
                Instructions for your Python code:
                1. Parse the MASTER_COST_DATA string directly into a Pandas DataFrame using `io.StringIO`.
                2. Base stats cost 0 AP.
                3. Upgrade all required Playstyle minimums first point-by-point.
                4. Loop to exhaust Core attributes point-by-point.
                5. Loop to exhaust Secondary attributes point-by-point.
                6. Spend any remaining budget exclusively on Tertiary attributes by sorting cheapest first until budget is EXACTLY 0.
                
                Output a beautiful final card showing Pace, Shooting, Passing, Dribbling, Defending, Physicality, Skill Moves, and Weak Foot.
                Next to every stat, you MUST print: `(Spent: [AP] AP)`.
                """
                response_2 = model.generate_content(prompt_2)
                
                st.success("✅ Math Engine Complete!")
                st.markdown(response_2.text)
                
                if st.button("Start New Build"):
                    st.session_state.scout_report = None
                    st.session_state.player_request = ""
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Something went wrong: {e}")
