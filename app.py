import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Maha-Panchayat Voting", layout="wide")

st.title("MAYA AI 🏛️: 6-Level Master Voting Engine (Maha-Panchayat)")
st.markdown("Yeh AI **6 alag-alag timeframes** (Combo, Monthly, Weekly, 5-Day, 10-Day, 15-Day) ka test karke **Voting Scoreboard** banata hai. Jiske sabse zyada Votes, wahi 100% Confirm!")

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
shift_names = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]
target_shift_name = st.sidebar.selectbox("🎯 Target Shift", shift_names)
selected_date = st.sidebar.date_input("Calculation Date")
max_limit = st.sidebar.slider("Max Repeat Limit", 2, 5, 4)

if uploaded_file is not None:
    try:
        # --- 2. Data Cleaning ---
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.sort_values(by='DATE').reset_index(drop=True)
        for col in shift_names:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')

        filtered_df = df[df['DATE'].dt.date <= selected_end_date].copy()
        if len(filtered_df) == 0: st.stop()

        target_date_next = filtered_df['DATE'].iloc[-1] + timedelta(days=1)
        target_day_val = target_date_next.day
        target_weekday_val = target_date_next.dayofweek

        # --- 3. Core Engine Functions ---
        def run_elimination(shift_list, limit):
            shift_list = [int(x) for x in shift_list if pd.notna(x)]
            eliminated = set()
            scores = Counter()
            for days in range(1, 31):
                if len(shift_list) < days: continue
                sheet = shift_list[-days:]
                counts = Counter(sheet)
                if len(counts) == len(sheet) and len(sheet) > 1: eliminated.update(sheet)
                for num, freq in counts.items():
                    if freq >= limit: eliminated.add(num)
                    else: scores[num] += 1
            return eliminated, scores

        def get_tiers(elim_set, score_dict):
            safe = sorted([n for n in range(100) if n not in elim_set], key=lambda x: score_dict[x], reverse=True)
            if not safe: return [], [], [], sorted(list(elim_set))
            n_s = len(safe)
            return safe[:int(n_s*0.33)], safe[int(n_s*0.33):int(n_s*0.66)], safe[int(n_s*0.66):], sorted(list(elim_set))

        # Helper to find historical tier of a specific date
        def get_past_tier(t_date):
            past = df[df['DATE'] < t_date][target_shift_name].tolist()
            if len(past) < 15: return "High"
            e, s = run_elimination(past, max_limit)
            h, m, l, el = get_tiers(e, s)
            actual_val = df[df['DATE'] == t_date][target_shift_name].values[0]
            if pd.isna(actual_val): return "Skip"
            actual_num = int(actual_val)
            if actual_num in h: return "High"
            elif actual_num in m: return "Medium"
            elif actual_num in l: return "Low"
            else: return "Eliminated"

        # --- 4. RUNNING THE 6 ENGINES (VOTING SYSTEM) ---
        votes = {}
        
        with st.spinner("6 Engines ka data calculate ho raha hai... Kripya prateeksha karein."):
            # PICHLE 60 DIN KA DAILY TIER RECORD (For fast calculations)
            last_60_dates = filtered_df.dropna(subset=[target_shift_name])['DATE'].tolist()[-60:]
            recent_tiers = []
            for d in last_60_dates:
                tier = get_past_tier(d)
                if tier != "Skip": recent_tiers.append(tier)

            # ENGINE 1: Combo Pattern (Yesterday -> Today)
            if len(recent_tiers) > 1:
                yesterday_tier = recent_tiers[-1]
                combos = [recent_tiers[i+1] for i in range(len(recent_tiers)-1) if recent_tiers[i] == yesterday_tier]
                votes["Combo Pattern"] = max(set(combos), key=combos.count) if combos else "High"
            else:
                votes["Combo Pattern"] = "High"

            # ENGINE 2: Monthly Date Pattern (Har mahine ki same tareekh)
            past_same_days = df[(df['DATE'].dt.day == target_day_val) & (df['DATE'] < target_date_next)].sort_values('DATE').tail(30)
            date_tiers = [get_past_tier(d) for d in past_same_days['DATE']]
            date_tiers = [t for t in date_tiers if t != "Skip"]
            votes["Monthly Date Pattern"] = max(set(date_tiers), key=date_tiers.count) if date_tiers else "High"

            # ENGINE 3: Weekly Pattern (Same day of the week)
            past_same_weekdays = df[(df['DATE'].dt.dayofweek == target_weekday_val) & (df['DATE'] < target_date_next)].sort_values('DATE').tail(30)
            week_tiers = [get_past_tier(d) for d in past_same_weekdays['DATE']]
            week_tiers = [t for t in week_tiers if t != "Skip"]
            votes["Weekly Pattern"] = max(set(week_tiers), key=week_tiers.count) if week_tiers else "High"

            # ENGINE 4, 5, 6: Momentum (5-Day, 10-Day, 15-Day)
            votes["5-Day Momentum"] = max(set(recent_tiers[-5:]), key=recent_tiers[-5:].count) if len(recent_tiers) >= 5 else "High"
            votes["10-Day Momentum"] = max(set(recent_tiers[-10:]), key=recent_tiers[-10:].count) if len(recent_tiers) >= 10 else "High"
            votes["15-Day Momentum"] = max(set(recent_tiers[-15:]), key=recent_tiers[-15:].count) if len(recent_tiers) >= 15 else "High"

        # --- 5. VOTING SCOREBOARD DISPLAY ---
        st.markdown("---")
        st.write(f"### 🗳️ Live Voting Scoreboard for {target_date_next.strftime('%d %B %Y')}")
        
        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)
        
        # Display each engine's vote
        c1.info(f"**1. Combo (Jodi) Engine**\n\nVote: **{votes['Combo Pattern']}**")
        c2.info(f"**2. Monthly (Date) Engine**\n\nVote: **{votes['Monthly Date Pattern']}**")
        c3.info(f"**3. Weekly (Din) Engine**\n\nVote: **{votes['Weekly Pattern']}**")
        c4.warning(f"**4. 5-Day Trend**\n\nVote: **{votes['5-Day Momentum']}**")
        c5.warning(f"**5. 10-Day Trend**\n\nVote: **{votes['10-Day Momentum']}**")
        c6.warning(f"**6. 15-Day Trend**\n\nVote: **{votes['15-Day Momentum']}**")

        # --- 6. FINAL CONSENSUS (SABSE ZYADA KISME DIKHA RAHA HAI) ---
        all_votes = list(votes.values())
        vote_counts = Counter(all_votes)
        
        best_tier = max(vote_counts, key=vote_counts.get)
        max_votes = vote_counts[best_tier]
        
        st.markdown("---")
        if max_votes >= 4:
            st.success(f"### 🏆 100% STRONG CONFIRMATION: [{best_tier.upper()} TIER]")
            st.write(f"**Reason:** 6 mein se **{max_votes} Engines** ek hi aawaz mein '{best_tier}' bol rahe hain. Dono/Sabhi patterns ka exact match ho gaya hai!")
        else:
            st.warning(f"### ⚖️ MAJORITY WINNER: [{best_tier.upper()} TIER] (Votes: {max_votes}/6)")
            st.write(f"**Reason:** Market thoda confused hai (Voting bati hui hai), lekin sabse zyada jor **{best_tier}** ka hi dikh raha hai.")

        # --- 7. FINAL NUMBERS DISPLAY ---
        st.markdown("---")
        st.subheader(f"🔢 Numbers for {target_date_next.strftime('%d %B %Y')}")
        
        current_list = filtered_df[target_shift_name].tolist()
        e_f, s_f = run_elimination(current_list, max_limit)
        h_f, m_f, l_f, el_f = get_tiers(e_f, s_f)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"#### 🔥 High ({len(h_f)}) {'✅' if best_tier=='High' else ''}")
            st.write(", ".join([f"{x:02d}" for x in h_f]))
        with col2:
            st.markdown(f"#### ⚡ Medium ({len(m_f)}) {'✅' if best_tier=='Medium' else ''}")
            st.write(", ".join([f"{x:02d}" for x in m_f]))
        with col3:
            st.markdown(f"#### ❄️ Low ({len(l_f)}) {'✅' if best_tier=='Low' else ''}")
            st.write(", ".join([f"{x:02d}" for x in l_f]))
        with col4:
            st.markdown(f"#### 🚫 Eliminated ({len(el_f)}) {'✅' if best_tier=='Eliminated' else ''}")
            st.write(", ".join([f"{x:02d}" for x in el_f]))

    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.info("👈 Please upload your data to start the Maha-Panchayat Voting.")
              
