import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client, Client

st.set_page_config(page_title="Execution Ledger", layout="wide")

# --- SUPABASE DATABASE CONNECTION ---
URL = "https://voufmlkdfcfjypqhyuds.supabase.co"
KEY = "sb_publishable_0BWSXn90j0lmrvhZrcDr6w_2EJcRyl5"

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

# Data fetching functions
def load_system_data():
    response = supabase.table("system_ledger").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=["Date", "System_Hrs", "Macro_Hrs", "Sleep_Hrs", "Reading_Hrs", "BW_Kg", "Cals", "Protein"])

def load_gym_data():
    response = supabase.table("gym_ledger").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=["Date", "Exercise", "Type", "Sets", "Reps_Mins", "Weight_Kg"])

# --- CONFIGURATION ---
START_DATE = datetime.date(2026, 2, 16)

MEALS = {
    "Monday": "07:45 Banana+Coffee | 10:30 4 Eggs/Whites+2 Roti | 14:30 Dal+2 Roti+Veg+Curd | 19:30 Paneer/Tofu+Veg | 23:30 Whey/Curd",
    "Tuesday": "07:45 Banana+Coffee | 10:30 4 Eggs/Whites+2 Roti | 14:30 Rajma/Chole+Rice | 19:30 Egg Bhurji+Veg | 23:30 Whey/Curd",
    "Wednesday": "07:45 Banana+Coffee | 10:30 4 Eggs/Whites+2 Roti | 14:30 Dal+2 Roti+Veg+Curd | 19:30 Dal+Veg | 23:30 Whey/Curd",
    "Thursday": "07:45 Banana+Coffee | 10:30 4 Eggs/Whites+2 Roti | 14:30 Dal+2 Roti+Veg+Curd | 19:30 Paneer/Tofu+Veg | 23:30 Whey/Curd",
    "Friday": "07:45 Banana+Coffee | 10:30 4 Eggs/Whites+2 Roti | 14:30 Rajma/Chole+Rice | 19:30 Egg Bhurji+Veg | 23:30 Whey/Curd",
    "Saturday": "Breakfast: Oats+Whey | Lunch: Paneer+Rice | Dinner: Dal+Roti | Snack: Fruit",
    "Sunday": "Breakfast: Eggs | Lunch: Dal | Dinner: Paneer"
}

def get_workout(week, day):
    # 'R' = Resistance (Sets, Reps, Kg), 'C' = Cardio (Mins only)
    if week <= 4:
        w = {"Monday": [("Squat", 'R', 3, 12), ("Glute bridge", 'R', 3, 15), ("Reverse lunge", 'R', 3, 10), ("Calf raise", 'R', 3, 15), ("Cycle Easy", 'C', 1, 20)],
             "Tuesday": [("Cycle Zone-2", 'C', 1, 40)],
             "Wednesday": [("Push-up", 'R', 3, 8), ("Band row", 'R', 3, 12), ("Pike push-up", 'R', 3, 6), ("Plank", 'C', 3, 0.5)],
             "Thursday": [("Cycle", 'C', 1, 45), ("Stairs", 'R', 5, 1)],
             "Friday": [("Squat", 'R', 3, 12), ("Push-up", 'R', 3, 8), ("Row", 'R', 3, 12), ("Lunge", 'R', 3, 10), ("HIIT Intervals", 'C', 8, 1)],
             "Saturday": [("Outdoor Cycle", 'C', 1, 45)], "Sunday": [("Mobility", 'C', 1, 30)]}
    elif week <= 8:
        w = {"Monday": [("Squat", 'R', 4, 12), ("Lunge", 'R', 4, 10), ("Bridge", 'R', 4, 15), ("Cycle", 'C', 1, 25)],
             "Tuesday": [("Cycle Zone-2", 'C', 1, 50)],
             "Wednesday": [("Push-up", 'R', 4, 10), ("Row", 'R', 4, 12), ("Pike push-up", 'R', 4, 8)],
             "Thursday": [("Cycle", 'C', 1, 60), ("Stairs", 'R', 8, 1)],
             "Friday": [("Full-body Circuit", 'C', 4, 5), ("HIIT", 'C', 10, 1)],
             "Saturday": [("Cycle", 'C', 1, 60)], "Sunday": [("Mobility", 'C', 1, 30)]}
    else: return []
    return w.get(day, [])

# --- HEADER ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("Execution Ledger")
with col_h2:
    sel_date = st.date_input("Date", datetime.date.today())
    d_str = str(sel_date)

days_active = (sel_date - START_DATE).days
current_week = max(1, (days_active // 7) + 1)
day_name = sel_date.strftime("%A")
tgt_cals = 2400 if current_week <= 4 else (2200 if current_week <= 12 else 2000)

# --- TODAY's DIRECTIVES ---
st.markdown("---")
st.markdown(f"### 📋 Plan for {day_name}, Week {current_week}")
st.info(f"**Diet Target:** {tgt_cals} kcal, 220g Protein\n\n**Menu:** {MEALS[day_name]}")

# --- INPUT SECTION ---
st.markdown("---")
st.markdown("### ✍️ Daily Log")

# Pull live data from Supabase
df_data = load_system_data()
day_data = df_data[df_data["Date"] == d_str]
df_gym = load_gym_data()
day_gym = df_gym[df_gym["Date"] == d_str]

with st.form("ledger_form", border=False):
    # 1. 7-Column Input for Life & Body Metrics
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    
    v_sys = float(day_data["System_Hrs"].iloc[0]) if not day_data.empty else 7.25
    v_mac = float(day_data["Macro_Hrs"].iloc[0]) if not day_data.empty else 3.0
    v_slp = float(day_data["Sleep_Hrs"].iloc[0]) if not day_data.empty else 4.25
    v_rdg = float(day_data["Reading_Hrs"].iloc[0]) if not day_data.empty else 1.0
    v_bw  = float(day_data["BW_Kg"].iloc[0]) if not day_data.empty else 0.0
    v_cal = int(day_data["Cals"].iloc[0]) if not day_data.empty else tgt_cals
    v_pro = int(day_data["Protein"].iloc[0]) if not day_data.empty else 220

    inp_sys = c1.number_input("System (Hrs)", value=v_sys, step=0.25)
    inp_mac = c2.number_input("Macro (Hrs)", value=v_mac, step=0.25)
    inp_slp = c3.number_input("Sleep (Hrs)", value=v_slp, step=0.25)
    inp_rdg = c4.number_input("Reading (Hrs)", value=v_rdg, step=0.25)
    inp_bw  = c5.number_input("Weight (Kg)", value=v_bw, step=0.1)
    inp_cal = c6.number_input("Calories", value=v_cal, step=50)
    inp_pro = c7.number_input("Protein (g)", value=v_pro, step=5)
    
    st.write("") 

    # 2. Gym Inputs
    st.markdown(f"**Workout Execution**")
    raw_w = get_workout(current_week, day_name)
    gym_logs = []
    
    if not raw_w:
        st.write("*Rest / Active Recovery*")
    else:
        h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
        h1.caption("EXERCISE")
        h2.caption("SETS")
        h3.caption("REPS / MINS")
        h4.caption("WEIGHT (KG)")

        for ex, g_type, t_sets, t_reps in raw_w:
            a_s = t_sets; a_r = float(t_reps); a_w = 0.0
            if not day_gym.empty:
                match = day_gym[day_gym["Exercise"] == ex]
                if not match.empty:
                    a_s = int(match["Sets"].iloc[0])
                    a_r = float(match["Reps_Mins"].iloc[0])
                    a_w = float(match["Weight_Kg"].iloc[0])

            r1, r2, r3, r4 = st.columns([2, 1, 1, 1])
            r1.markdown(f"**{ex}** <br> <span style='color:gray; font-size:0.8em;'>Target: {t_sets} x {t_reps}</span>", unsafe_allow_html=True)
            
            if g_type == 'R': 
                i_s = r2.number_input("Sets", value=a_s, key=f"s_{ex}", label_visibility="collapsed")
                i_r = r3.number_input("Reps", value=a_r, step=1.0, key=f"r_{ex}", label_visibility="collapsed")
                i_w = r4.number_input("Kg", value=a_w, step=2.5, key=f"w_{ex}", label_visibility="collapsed")
                gym_logs.append({"Date": d_str, "Exercise": ex, "Type": g_type, "Sets": i_s, "Reps_Mins": i_r, "Weight_Kg": i_w})
            else: 
                r2.markdown("<div style='padding-top:10px; color:gray;'><i>1</i></div>", unsafe_allow_html=True)
                i_m = r3.number_input("Mins", value=a_r, step=5.0, key=f"m_{ex}", label_visibility="collapsed")
                r4.markdown("<div style='padding-top:10px; color:gray;'><i>N/A</i></div>", unsafe_allow_html=True)
                gym_logs.append({"Date": d_str, "Exercise": ex, "Type": g_type, "Sets": 1, "Reps_Mins": i_m, "Weight_Kg": 0.0})

    st.write("")
    submitted = st.form_submit_button("💾 Save to Cloud", use_container_width=True)

    if submitted:
        # Upsert System Ledger
        sys_payload = {"Date": d_str, "System_Hrs": inp_sys, "Macro_Hrs": inp_mac, "Sleep_Hrs": inp_slp, "Reading_Hrs": inp_rdg, "BW_Kg": inp_bw, "Cals": inp_cal, "Protein": inp_pro}
        supabase.table("system_ledger").upsert(sys_payload).execute()
        
        # Replace Gym Ledger for the day
        if gym_logs:
            supabase.table("gym_ledger").delete().eq("Date", d_str).execute()
            supabase.table("gym_ledger").insert(gym_logs).execute()
            
        st.success("Entry Saved to Supabase Database.")
        st.rerun()

# --- ANALYTICS SECTION ---
st.markdown("---")
st.markdown("### 📈 Analytics")

# Re-fetch fresh data for charts
df_data = load_system_data()
df_gym = load_gym_data()

if df_data.empty:
    st.info("Awaiting cloud data. Save an entry above.")
else:
    # Sort dates sequentially for accurate charting
    df_data = df_data.sort_values(by="Date")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        df_melt = df_data.melt(id_vars=["Date"], value_vars=["System_Hrs", "Macro_Hrs", "Sleep_Hrs", "Reading_Hrs"], var_name="Domain", value_name="Hours")
        fig_time = px.line(df_melt, x="Date", y="Hours", color="Domain", markers=True, title="Time Allocation Trends",
                           color_discrete_map={"System_Hrs": "#3498db", "Macro_Hrs": "#9b59b6", "Sleep_Hrs": "#34495e", "Reading_Hrs": "#2ecc71"})
        st.plotly_chart(fig_time, use_container_width=True)

    with chart_col2:
        fig_bw = make_subplots(specs=[[{"secondary_y": True}]])
        fig_bw.add_trace(go.Scatter(x=df_data['Date'], y=df_data['BW_Kg'], name="Bodyweight (kg)", line=dict(color="#e74c3c", width=3)), secondary_y=False)
        fig_bw.add_trace(go.Bar(x=df_data['Date'], y=df_data['Cals'], name="Calories", opacity=0.3), secondary_y=True)
        fig_bw.update_layout(title="Thermodynamics: BW vs Intake")
        fig_bw.update_yaxes(title_text="Kilograms", secondary_y=False)
        fig_bw.update_yaxes(title_text="Kcal", secondary_y=True)
        st.plotly_chart(fig_bw, use_container_width=True)

    if not df_gym.empty:
        df_gym = df_gym.sort_values(by="Date")
        r_df = df_gym[df_gym["Type"] == 'R'].copy()
        c_df = df_gym[df_gym["Type"] == 'C'].copy()
        
        if not r_df.empty:
            st.markdown("#### Resistance Progression")
            sel_r = st.selectbox("Select Exercise", r_df['Exercise'].unique())
            ex_r = r_df[r_df['Exercise'] == sel_r].copy()
            
            ex_r["Volume"] = ex_r["Sets"] * ex_r["Reps_Mins"]
            ex_r["Tonnage"] = ex_r["Sets"] * ex_r["Reps_Mins"] * ex_r["Weight_Kg"]
            
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                fig_vol = px.line(ex_r, x="Date", y="Volume", markers=True, title=f"Total Reps (Volume): {sel_r}")
                fig_vol.update_traces(line_color="#f1c40f")
                st.plotly_chart(fig_vol, use_container_width=True)
            with r_col2:
                fig_ton = px.line(ex_r, x="Date", y="Tonnage", markers=True, title=f"Total Tonnage (Kg): {sel_r}")
                fig_ton.update_traces(line_color="#e67e22")
                st.plotly_chart(fig_ton, use_container_width=True)
                
        if not c_df.empty:
            st.markdown("#### Cardio & Endurance")
            sel_c = st.selectbox("Select Cardio Activity", c_df['Exercise'].unique())
            ex_c = c_df[c_df['Exercise'] == sel_c]
            fig_c = px.line(ex_c, x="Date", y="Reps_Mins", markers=True, title=f"Total Minutes: {sel_c}")
            fig_c.update_traces(line_color="#3498db")
            st.plotly_chart(fig_c, use_container_width=True)
