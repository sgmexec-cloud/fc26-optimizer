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
                    
                    # Clean out any accidental code blocks from Phase 1
                    clean_report = re.sub(r'```.*?```', '', response_1.text, flags=re.DOTALL)
                    
                    st.session_state.scout_report = clean_report.strip()
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
        with st.spinner("🧠 Running strict, silent Python math logic... (Takes ~5 to 15 seconds)"):
            try:
                playstyles = pd.read_csv("PLAYSTYLES.csv").to_csv(index=False)
                all_arch_string = pd.read_csv("ALL_ARCHETYPES.csv").to_csv(index=False)
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
                --- ALL_ARCHETYPES ---
                {all_arch_string}
                --- PLAYSTYLES ---
                {playstyles}
                --- MASTER_COST_DATA (Filtered for chosen archetype) ---
                {master_cost_string}
                
                CRITICAL OPTIMIZATION & MATH RULES FOR YOUR PYTHON SCRIPT:
                1. SANITIZE DATA FIRST: Before doing any math, clean the 'Attribute' names in both ALL_ARCHETYPES and MASTER_COST_DATA. Strip all whitespace and convert to lowercase (e.g., "Sprint Speed", " SprintSpeed ", and "sprintspeed" must all become "sprintspeed"). Do the exact same thing for the attributes listed in the blueprint.
                2. Create a nested dictionary for instant lookups: `cost_dict[cleaned_attr][level] = cost`.
                3. Load the Archetype's Base and Max stats into dictionaries: `base_stats[cleaned_attr]` and `max_stats[cleaned_attr]`.
                4. Create a `current_stats` dictionary initialized to the `base_stats`. AP Spent starts at 0.
                5. Loop through the upgrades: Playstyle minimums first, then Core, Secondary, Tertiary. 
                6. UPGRADE LOGIC: To upgrade, check `cost = cost_dict[cleaned_attr].get(current_stats[cleaned_attr] + 1, 9999)`. If budget >= cost AND current_stats[cleaned_attr] < max_stats[cleaned_attr], apply the upgrade and subtract cost from budget. Keep a strict ledger of AP spent per attribute.
                7. SKILL MOVES & WEAK FOOT: Remember these max out at 5 stars, not 99.
                8. DO NOT use print() statements inside your loops. Calculate everything silently to prevent timeouts.
                
                OUTPUT FORMATTING RULE:
                Do all math silently. DO NOT put your final card inside a code block. Write the final card in plain Markdown text exactly like this:
                
                **Total AP Spent:** [Spent] / {ap_budget} (Unspent: [Remaining])

                **Pace**
                Acceleration: [Value] (Spent: [AP] AP)
                Sprint Speed: [Value] (Spent: [AP] AP)
                
                **Shooting**
                Att. Position: [Value] (Spent: [AP] AP)
                Finishing: [Value] (Spent: [AP] AP)
                Shot Power: [Value] (Spent: [AP] AP)
                Long Shots: [Value] (Spent: [AP] AP)
                Volleys: [Value] (Spent: [AP] AP)
                Penalties: [Value] (Spent: [AP] AP)

                **Passing**
                Vision: [Value] (Spent: [AP] AP)
                Crossing: [Value] (Spent: [AP] AP)
                FK. Acc.: [Value] (Spent: [AP] AP)
                Short Pass: [Value] (Spent: [AP] AP)
                Long Pass: [Value] (Spent: [AP] AP)
                Curve: [Value] (Spent: [AP] AP)

                **Dribbling**
                Agility: [Value] (Spent: [AP] AP)
                Balance: [Value] (Spent: [AP] AP)
                Reactions: [Value] (Spent: [AP] AP)
                Ball Control: [Value] (Spent: [AP] AP)
                Dribbling: [Value] (Spent: [AP] AP)
                Composure: [Value] (Spent: [AP] AP)

                **Defending**
                Interceptions: [Value] (Spent: [AP] AP)
                Heading Acc.: [Value] (Spent: [AP] AP)
                Def. Aware: [Value] (Spent: [AP] AP)
                Stand Tackle: [Value] (Spent: [AP] AP)
                Slide Tackle: [Value] (Spent: [AP] AP)

                **Physicality**
                Jumping: [Value] (Spent: [AP] AP)
                Stamina: [Value] (Spent: [AP] AP)
                Strength: [Value] (Spent: [AP] AP)
                Aggression: [Value] (Spent: [AP] AP)

                **Skill Moves**
                [Value] Stars (Spent: [AP] AP)

                **Weak Foot**
                [Value] Stars (Spent: [AP] AP)
                """
                
                # Using the API
                response_2 = model.generate_content(prompt_2)
                
                # Safely extract the text to avoid the "finish_reason 2" crash
                if not response_2.parts:
                    st.error("The AI hit a processing limit. Try generating again, or lower your AP budget slightly.")
                else:
                    raw_text = response_2.text
                    clean_text = re.sub(r'```.*?```', '', raw_text, flags=re.DOTALL).strip()
                    st.success("✅ Math Engine Complete!")
                    st.markdown(clean_text)
                
                if st.button("Start New Build"):
                    st.session_state.scout_report = None
                    st.session_state.player_request = ""
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Something went wrong: {e}")
