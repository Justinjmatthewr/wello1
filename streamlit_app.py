#############################################
#      WELLNEST WEB APPLICATION
#    Enhanced with:
#    - Blood Pressure Logging
#    - Basic “Health Status” on Home
#    - Symptom Checker (Not real medical advice)
#    - Daily Challenges
#
#   PART 1 OF 2
#############################################

import os
import json
import datetime
from datetime import datetime, timedelta

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import calendar
import smtplib
from email.mime.text import MIMEText
import hashlib

#############################################
#           GLOBAL CONSTANTS / PATHS
#############################################

APP_TITLE = "WellNest"
DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE         = os.path.join(DATA_DIR, "users.json")
TASKS_FILE         = os.path.join(DATA_DIR, "tasks.json")
APPOINTMENTS_FILE  = os.path.join(DATA_DIR, "appointments.json")
PRESCRIPTIONS_FILE = os.path.join(DATA_DIR, "prescriptions.json")
MOOD_FILE          = os.path.join(DATA_DIR, "mood.json")
WATER_FILE         = os.path.join(DATA_DIR, "water.json")
NOTES_FILE         = os.path.join(DATA_DIR, "notes.json")
STEPS_FILE         = os.path.join(DATA_DIR, "steps.json")
SLEEP_FILE         = os.path.join(DATA_DIR, "sleep.json")
WEIGHT_FILE        = os.path.join(DATA_DIR, "weight.json")
CALORIES_FILE      = os.path.join(DATA_DIR, "calories.json")

# NEW for Blood Pressure
BLOODPRESSURE_FILE = os.path.join(DATA_DIR, "bloodpressure.json")

# For Family/Circle Groups
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")

# If you have a banner image
SPLASH_IMAGE_PATH = "path/to/splash_image.png"

st.set_page_config(page_title=APP_TITLE, layout="wide")

#############################################
#            HELPER FUNCTIONS
#############################################

def load_json(filepath):
    """Load JSON from a file safely; return {} if missing or invalid."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_json(data, filepath):
    """Save a dictionary to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def hash_password(password: str) -> str:
    """Return a SHA-256 hash of a plaintext password."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username: str, password: str, users_data: dict) -> bool:
    """Validate user credentials. Return True if correct, else False."""
    if username in users_data:
        return hash_password(password) == users_data[username]["password"]
    return False

def register_new_user(username: str, password: str, users_data: dict) -> bool:
    """Register a new user. Return False if user already exists, else True."""
    if username in users_data:
        return False
    # Initialize user record
    users_data[username] = {
        "password": hash_password(password),
        "profile": {
            "name": "",
            "email": "",
            "gender": "",
            "age": None,
            "height_cm": None
        },
        "smtp": {  # optional for email
            "host": "",
            "port": 587,
            "username": "",
            "app_password": ""
        }
    }
    save_json(users_data, USERS_FILE)
    return True


#############################################
#            LOAD ALL DATA
#############################################

users_data         = load_json(USERS_FILE)
tasks_data         = load_json(TASKS_FILE)
appointments_data  = load_json(APPOINTMENTS_FILE)
prescriptions_data = load_json(PRESCRIPTIONS_FILE)
mood_data          = load_json(MOOD_FILE)
water_data         = load_json(WATER_FILE)
notes_data         = load_json(NOTES_FILE)
steps_data         = load_json(STEPS_FILE)
sleep_data         = load_json(SLEEP_FILE)
weight_data        = load_json(WEIGHT_FILE)
calories_data      = load_json(CALORIES_FILE)
groups_data        = load_json(GROUPS_FILE)
bloodpressure_data = load_json(BLOODPRESSURE_FILE)

def save_all():
    """Save all data structures to their respective JSON files."""
    save_json(users_data, USERS_FILE)
    save_json(tasks_data, TASKS_FILE)
    save_json(appointments_data, APPOINTMENTS_FILE)
    save_json(prescriptions_data, PRESCRIPTIONS_FILE)
    save_json(mood_data, MOOD_FILE)
    save_json(water_data, WATER_FILE)
    save_json(notes_data, NOTES_FILE)
    save_json(steps_data, STEPS_FILE)
    save_json(sleep_data, SLEEP_FILE)
    save_json(weight_data, WEIGHT_FILE)
    save_json(calories_data, CALORIES_FILE)
    save_json(groups_data, GROUPS_FILE)
    save_json(bloodpressure_data, BLOODPRESSURE_FILE)

st.title(APP_TITLE)

###########################################################
#    SYMPTOM CHECKER (DEMO ONLY, NOT REAL MEDICAL ADVICE)
###########################################################

def symptom_checker(symptoms: list) -> str:
    """
    A naive function that tries to guess possible conditions
    based on a list of textual symptoms.
    This is purely for demonstration; it is NOT medical advice.
    """
    # Lowercase everything
    symptoms = [s.lower().strip() for s in symptoms]

    possible_conditions = []

    # Very basic mapping logic, purely for example
    if any("cough" in s for s in symptoms) or any("sore throat" in s for s in symptoms):
        possible_conditions.append("Common Cold / Flu")
    if any("fever" in s for s in symptoms) and any("headache" in s for s in symptoms):
        possible_conditions.append("Viral infection")
    if any("chest pain" in s for s in symptoms) or any("shortness of breath" in s for s in symptoms):
        possible_conditions.append("Cardiac or Respiratory issue")
    if any("rash" in s for s in symptoms):
        possible_conditions.append("Dermatitis / Allergic reaction")

    if not possible_conditions:
        return "No matching condition found. Please consult a professional if concerned."
    else:
        # Return a simple string
        return "Possible conditions: " + ", ".join(possible_conditions)


###########################################################
#   NOTIFICATIONS & TRENDS (Optional)
###########################################################

def parse_task_datetime(date_str: str, time_str: str):
    """Parse date+time, e.g. '2025-01-12' + '14:30' => datetime obj."""
    try:
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except:
        return None

def parse_appointment_datetime(date_str: str, app_str: str):
    """Parse the time from an appointment string. E.g. '15:00 with Dr. X'."""
    try:
        time_part = app_str.split(" ")[0]
        dt_str = f"{date_str} {time_part}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except:
        return None

def check_water_trend(username: str):
    """If average water intake is <1.0L last 3 days, warn user."""
    user_water = water_data.get(username, {})
    if not user_water:
        return None
    now = datetime.now()
    total = 0.0
    count = 0
    for i in range(1,4):
        d_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        if d_str in user_water:
            total += user_water[d_str]
            count += 1
    if count == 0:
        return None
    avg = total / count
    if avg < 1.0:
        return "Water intake has been quite low. Stay hydrated!"
    return None

def check_mood_trend(username: str):
    """If mood <2 on average last 3 days, mention it."""
    user_mood = mood_data.get(username, {})
    if not user_mood:
        return None
    now = datetime.now()
    moods = []
    for i in range(1,4):
        d_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        if d_str in user_mood:
            moods.append(user_mood[d_str])
    if len(moods) < 2:
        return None
    avg = sum(moods)/len(moods)
    if avg < 2:
        return "Your recent mood is low. Consider self-care or professional support."
    return None

def send_email_notifications(username: str, messages: list):
    """Send an email with the given messages to user's stored email (if configured)."""
    user_email = users_data[username]["profile"].get("email","")
    smtp_conf  = users_data[username].get("smtp", {})
    smtp_host  = smtp_conf.get("host","")
    smtp_port  = smtp_conf.get("port",587)
    smtp_user  = smtp_conf.get("username","")
    smtp_pass  = smtp_conf.get("app_password","")

    if not (user_email and smtp_host and smtp_user and smtp_pass):
        st.error("Cannot send email: missing or incomplete SMTP configuration.")
        return

    subject = f"WellNest Notifications for {username}"
    body = "Hello,\n\nHere are your WellNest notifications:\n"
    for msg in messages:
        body += f"- {msg}\n"
    body += "\nStay healthy,\nWellNest"

    msg_obj = MIMEText(body)
    msg_obj["Subject"] = subject
    msg_obj["From"]    = smtp_user
    msg_obj["To"]      = user_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg_obj)
    except Exception as e:
        st.error(f"Error sending email: {e}")

def check_and_trigger_notifications(username: str):
    """Check tasks/appointments within 1 day or 1 hr; also check water/mood trends."""
    upcoming_events = []
    now = datetime.now()

    user_tasks = tasks_data.get(username, {})
    user_apps  = appointments_data.get(username, {})

    for day_offset in [0,1]:
        dt_candidate = now + timedelta(days=day_offset)
        date_str = dt_candidate.strftime("%Y-%m-%d")

        # tasks
        if date_str in user_tasks:
            for tsk in user_tasks[date_str]:
                dt_obj = parse_task_datetime(date_str, tsk.get("time",""))
                if dt_obj:
                    diff = (dt_obj - now).total_seconds()
                    if 0 < diff <= 3600:
                        upcoming_events.append(f"[1-Hour Alert] Task '{tsk['name']}' at {tsk['time']}")
                    elif 3600 < diff <= 86400:
                        upcoming_events.append(f"[1-Day Alert] Task '{tsk['name']}' at {tsk['time']}")

        # appointments
        if date_str in user_apps:
            for app_str in user_apps[date_str]:
                dt_obj = parse_appointment_datetime(date_str, app_str)
                if dt_obj:
                    diff = (dt_obj - now).total_seconds()
                    if 0 < diff <= 3600:
                        upcoming_events.append(f"[1-Hour Alert] Appointment: {app_str}")
                    elif 3600 < diff <= 86400:
                        upcoming_events.append(f"[1-Day Alert] Appointment: {app_str}")

    # water / mood
    walert = check_water_trend(username)
    if walert:
        upcoming_events.append(walert)
    malert = check_mood_trend(username)
    if malert:
        upcoming_events.append(malert)

    if upcoming_events:
        st.warning("**NOTIFICATIONS**")
        for evt in upcoming_events:
            st.info(evt)
        if st.button("Send Email Alerts"):
            send_email_notifications(username, upcoming_events)
            st.success("Email alerts sent.")
    else:
        st.info("No new alerts at this time.")


###############################################################
#   PART 1 ENDS HERE. CONTINUE WITH PART 2 BELOW.
###############################################################
#############################################
#  WELLNEST WEB APPLICATION (CONTINUED)
#  PART 2 OF 2
#############################################

#############################################
#   FAMILY GROUP / CIRCLE FEATURES
#############################################
def create_group(group_id: str, group_name: str):
    if group_id in groups_data:
        return False
    groups_data[group_id] = {
        "group_name": group_name,
        "members": []
    }
    save_all()
    return True

def join_group(group_id: str, username: str):
    if group_id not in groups_data:
        return False
    if username not in groups_data[group_id]["members"]:
        groups_data[group_id]["members"].append(username)
        save_all()
    return True

def leave_group(group_id: str, username: str):
    if group_id not in groups_data:
        return False
    if username in groups_data[group_id]["members"]:
        groups_data[group_id]["members"].remove(username)
        save_all()
    return True

def list_user_groups(username: str):
    """Return list of (group_id, group_name) for groups user is in."""
    result = []
    for gid, info in groups_data.items():
        if username in info["members"]:
            result.append((gid, info["group_name"]))
    return result

def family_group_view(username: str):
    st.header("Family / Circle Groups")

    user_groups = list_user_groups(username)
    if user_groups:
        st.subheader("Your Groups")
        for gid, gname in user_groups:
            st.write(f"- **{gname}** (ID: {gid})")
            if st.button(f"Leave {gname}", key=f"leave_{gid}"):
                leave_group(gid, username)
                st.success(f"You left group {gname}.")
                st.stop()
    else:
        st.info("You are not in any group yet.")

    st.write("---")
    st.subheader("Join a Group")
    join_gid = st.text_input("Group ID to join")
    if st.button("Join Group"):
        if join_gid.strip():
            if join_group(join_gid.strip(), username):
                st.success(f"Joined group {join_gid}")
                st.stop()
            else:
                st.error("Group not found or other error.")

    st.write("---")
    st.subheader("Create a New Group")
    new_gid   = st.text_input("New Group ID", key="grp_new_id")
    new_gname = st.text_input("New Group Name", key="grp_new_name")
    if st.button("Create Group", key="btn_create_group"):
        if new_gid.strip() and new_gname.strip():
            if create_group(new_gid.strip(), new_gname.strip()):
                st.success("Group created!")
            else:
                st.error("Group ID already exists.")
        else:
            st.error("Please fill both fields.")

    st.write("---")
    if user_groups:
        st.subheader("Family / Friends Stats")
        for gid, gname in user_groups:
            st.write(f"**Group**: {gname} (ID: {gid})")
            members = groups_data[gid]["members"]
            st.write(f"**Members**: {', '.join(members)}")
            for mem in members:
                st.write(f"### {mem}'s Stats")
                show_limited_stats(mem)

def show_limited_stats(username: str):
    """Show minimal daily stats for user in the group context."""
    today_str = datetime.now().strftime("%Y-%m-%d")

    w_val = water_data.get(username, {}).get(today_str, 0.0)
    st.write(f"- Water: {w_val} L")

    mood_val = mood_data.get(username, {}).get(today_str, None)
    if mood_val is not None:
        st.write(f"- Mood: {mood_val}/5")
    else:
        st.write("- Mood: (none)")

    steps_val = steps_data.get(username, {}).get(today_str, 0)
    st.write(f"- Steps: {steps_val}")

    # Possibly weight/BMI, BP, etc.
    bp_val = bloodpressure_data.get(username, {}).get(today_str, None)
    if bp_val:
        st.write(f"- BP: {bp_val['systolic']}/{bp_val['diastolic']} mmHg")


#############################################
#           DAILY CHALLENGES
#############################################

daily_challenges = {}
# Example predefined
daily_challenges["2025-01-14"] = [
    {"challenge": "Drink 2L of water", "completed_by": []},
    {"challenge": "Log Mood Today",    "completed_by": []},
    {"challenge": "Walk 8000 Steps",   "completed_by": []}
]

def get_challenges_for_date(date_str: str):
    if date_str not in daily_challenges:
        # optionally define new ones or leave blank
        daily_challenges[date_str] = []
    return daily_challenges[date_str]

def show_daily_challenges(username: str):
    st.subheader("Daily Challenges")
    today_str = datetime.now().strftime("%Y-%m-%d")
    challenges = get_challenges_for_date(today_str)

    if not challenges:
        st.info("No challenges set for today.")
    else:
        for i, ch in enumerate(challenges):
            st.write(f"{i+1}. **{ch['challenge']}**")
            if username in ch["completed_by"]:
                st.write("   Status: **Completed**")
            else:
                st.write("   Status: Incomplete")
                if st.button(f"Complete '{ch['challenge']}'", key=f"challenge_{i}"):
                    ch["completed_by"].append(username)
                    st.success("Challenge completed!")
                    st.stop()

#############################################
#        SESSION STATE / AUTH
#############################################

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

def main():
    if not st.session_state["logged_in"]:
        show_login_screen()
    else:
        check_and_trigger_notifications(st.session_state["current_user"])
        show_main_app()

def show_login_screen():
    st.title("Welcome to WellNest - Please Login")
    tab_login, tab_signup = st.tabs(["Login","Sign Up"])

    with tab_login:
        uname = st.text_input("Username", key="login_username")
        pwd   = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In"):
            if check_credentials(uname, pwd, users_data):
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = uname
                st.success("Logged in successfully.")
                st.stop()
            else:
                st.error("Invalid username or password.")

    with tab_signup:
        uname_new = st.text_input("New Username", key="signup_username")
        pwd_new   = st.text_input("New Password", type="password", key="signup_password")
        pwd_conf  = st.text_input("Confirm Password", type="password", key="signup_confirm")
        if st.button("Sign Up"):
            if not uname_new or not pwd_new or not pwd_conf:
                st.error("Please fill all fields.")
            elif pwd_new != pwd_conf:
                st.error("Passwords do not match.")
            else:
                if register_new_user(uname_new, pwd_new, users_data):
                    st.success("Account created! You can now log in.")
                else:
                    st.warning("That username already exists.")

def show_main_app():
    st.sidebar.header(f"Welcome, {st.session_state['current_user']}!")
    menu = st.sidebar.radio("Navigation", [
        "Home",
        "Tasks & Appointments",
        "Prescriptions",
        "Health Tracking",
        "Analytics",
        "Notes",
        "Family / Circle",
        "Symptom Checker",
        "Settings"
    ])

    if menu == "Home":
        show_home_tab()
    elif menu == "Tasks & Appointments":
        show_tasks_appointments_tab()
    elif menu == "Prescriptions":
        show_prescriptions_tab()
    elif menu == "Health Tracking":
        show_health_tracking_tab()
    elif menu == "Analytics":
        show_analytics_tab()
    elif menu == "Notes":
        show_notes_tab()
    elif menu == "Family / Circle":
        family_group_view(st.session_state["current_user"])
    elif menu == "Symptom Checker":
        show_symptom_checker_tab()
    elif menu == "Settings":
        show_settings_tab()

#############################################
#  BUILD A "HEALTH STATUS" HELPER
#############################################
def get_health_status(username: str) -> str:
    """
    Very basic logic to say "Healthy" or "Some concerns" based on
    recent metrics: BMI, blood pressure, steps, water, etc.
    This is purely demonstrative, not medical advice.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1) BMI
    user_bmi = None
    if today_str in weight_data.get(username, {}):
        user_bmi = weight_data[username][today_str]["bmi"]

    # 2) Blood Pressure
    bp_entry = bloodpressure_data.get(username, {}).get(today_str, None)
    # We'll consider normal if ~120/80, high if systolic>140 or diastolic>90
    if bp_entry:
        sys_bp = bp_entry["systolic"]
        dia_bp = bp_entry["diastolic"]
    else:
        sys_bp, dia_bp = None, None

    # 3) Steps
    steps_val = steps_data.get(username, {}).get(today_str, 0)

    # 4) Water
    water_val = water_data.get(username, {}).get(today_str, 0.0)

    # Evaluate
    concerns = []
    if user_bmi is not None:
        if user_bmi < 18.5 or user_bmi > 25:
            concerns.append("BMI out of normal range")
    if sys_bp is not None and dia_bp is not None:
        if sys_bp > 140 or dia_bp > 90:
            concerns.append("High Blood Pressure")
        if sys_bp < 90 or dia_bp < 60:
            concerns.append("Low Blood Pressure")
    if steps_val < 3000:
        concerns.append("Low activity (under 3000 steps)")
    if water_val < 1.0:
        concerns.append("Low water intake (<1L)")

    if concerns:
        return "Potential Concerns: " + ", ".join(concerns)
    else:
        return "All recent metrics appear within normal ranges."

#############################################
# HOME TAB
#############################################
def show_home_tab():
    st.header("Home / Dashboard")
    user = st.session_state["current_user"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Display Health Status
    st.subheader("Overall Health Status (Demo)")
    health_message = get_health_status(user)
    st.write(f"**{health_message}** (Not medical advice)")

    # Monthly Calendar
    now = datetime.now()
    with st.expander("Monthly Overview Calendar"):
        colCal1, colCal2 = st.columns(2)
        with colCal1:
            picked_year = st.number_input("Year", value=now.year, min_value=1900, max_value=2100)
        with colCal2:
            picked_month = st.selectbox("Month", list(range(1,13)), index=now.month-1)
        cal_html = make_monthly_calendar_html(int(picked_year), int(picked_month), user)
        st.markdown(cal_html, unsafe_allow_html=True)

    st.write("---")
    st.subheader("Daily Challenges")
    show_daily_challenges(user)

    st.write("---")
    st.subheader("Today's Quick Stats")
    tasks_today = tasks_data.get(user, {}).get(today_str, [])
    st.write(f"- **Tasks Today**: {len(tasks_today)}")

    apps_today = appointments_data.get(user, {}).get(today_str, [])
    st.write(f"- **Appointments Today**: {len(apps_today)}")

    mood_today = mood_data.get(user, {}).get(today_str, None)
    if mood_today is not None:
        st.write(f"- **Mood**: {mood_today}/5")
    else:
        st.write("- **Mood**: Not logged")

    water_today = water_data.get(user, {}).get(today_str, 0.0)
    st.write(f"- **Water Intake**: {water_today} L")

    steps_today = steps_data.get(user, {}).get(today_str, 0)
    st.write(f"- **Steps**: {steps_today}")

    bp_today = bloodpressure_data.get(user, {}).get(today_str, None)
    if bp_today:
        st.write(f"- **Blood Pressure**: {bp_today['systolic']}/{bp_today['diastolic']} mmHg")

#############################################
#  MAKE MONTHLY CALENDAR (SHOWING EVENTS)
#############################################
def make_monthly_calendar_html(year: int, month: int, user: str) -> str:
    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    month_name = calendar.month_name[month]

    user_tasks = tasks_data.get(user, {})
    user_apps  = appointments_data.get(user, {})
    user_rx    = prescriptions_data.get(user, {})

    html = (f"<table style='border-collapse:collapse; width:100%; font-size:14px;'>"
            f"<caption style='text-align:center; font-weight:bold; font-size:18px; margin-bottom:8px;'>"
            f"{month_name} {year}</caption>")

    days_of_week = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    html += "<thead><tr>"
    for dow in days_of_week:
        html += f"<th style='border:1px solid #999; padding:6px; background-color:#DDD;'>{dow}</th>"
    html += "</tr></thead>"

    html += "<tbody>"
    for week in cal.monthdatescalendar(year, month):
        html += "<tr>"
        for day in week:
            style = "border:1px solid #999; vertical-align:top; padding:6px;"
            if day.month == month:
                day_str = day.strftime("%Y-%m-%d")
                content_html = f"<strong>{day.day}</strong>"
                day_events = []

                # tasks
                day_tasks = user_tasks.get(day_str, [])
                if day_tasks:
                    day_events.append("<u>Tasks</u>:<ul style='margin:0; padding-left:14px;'>"
                                      + "".join([f"<li>{t['name']} @ {t['time']}</li>" for t in day_tasks])
                                      + "</ul>")

                # appointments
                day_apps = user_apps.get(day_str, [])
                if day_apps:
                    day_events.append("<u>Appointments</u>:<ul style='margin:0; padding-left:14px;'>"
                                      + "".join([f"<li>{a}</li>" for a in day_apps])
                                      + "</ul>")

                # prescriptions
                presc_list = []
                for rx_name, rx_info in user_rx.items():
                    sched = rx_info.get("Schedule", [])
                    for entry in sched:
                        if (entry["Year"] == day.year and entry["Month"] == day.month and entry["Day"] == day.day):
                            stt = entry.get("Status", "scheduled")
                            presc_list.append(f"{rx_name} [{stt}]")
                if presc_list:
                    day_events.append("<u>Prescriptions</u>:<ul style='margin:0; padding-left:14px;'>"
                                      + "".join([f"<li>{p}</li>" for p in presc_list])
                                      + "</ul>")

                if day_events:
                    content_html += "<br>" + "<br>".join(day_events)
                html += f"<td style='{style}'>{content_html}</td>"
            else:
                html += f"<td style='{style} color:#CCC;'>{day.day}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

#############################################
#  TASKS & APPOINTMENTS TAB
#############################################
def show_tasks_appointments_tab():
    st.header("Tasks & Appointments")
    user = st.session_state["current_user"]
    if user not in tasks_data:
        tasks_data[user] = {}
    if user not in appointments_data:
        appointments_data[user] = {}

    sel_date = st.date_input("Select date", value=datetime.now())
    date_str = sel_date.strftime("%Y-%m-%d")
    st.write(f"Selected date: **{date_str}**")

    # Ensure date keys
    if date_str not in tasks_data[user]:
        tasks_data[user][date_str] = []
    if date_str not in appointments_data[user]:
        appointments_data[user][date_str] = []

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tasks")
        day_tasks = tasks_data[user][date_str]
        if day_tasks:
            for i, tsk in enumerate(day_tasks):
                st.write(f"{i+1}. **{tsk['name']}** @ {tsk['time']} (Status: {tsk['status']})")
        else:
            st.info("No tasks for this date.")

        with st.expander("Add a New Task"):
            tname = st.text_input("Task Name", key="task_name")
            ttime = st.text_input("Time (HH:MM)", key="task_time")
            tstatus = st.selectbox("Status", ["Pending","In-progress","Completed"], key="task_status")
            if st.button("Save Task"):
                if tname and ttime:
                    tasks_data[user][date_str].append({
                        "name": tname,
                        "time": ttime,
                        "status": tstatus
                    })
                    save_all()
                    st.success("Task added.")
                else:
                    st.error("Task name and time are required.")

    with col2:
        st.subheader("Appointments")
        day_apps = appointments_data[user][date_str]
        if day_apps:
            for i, a in enumerate(day_apps):
                st.write(f"{i+1}. {a}")
        else:
            st.info("No appointments for this date.")

        with st.expander("Add a New Appointment"):
            ap_time = st.text_input("Time (HH:MM)", key="app_time")
            ap_doc  = st.text_input("Doctor's Name", key="app_doc")
            ap_loc  = st.text_input("Location", key="app_loc")
            if st.button("Save Appointment", key="btn_save_appt"):
                if ap_time and ap_doc and ap_loc:
                    desc = f"{ap_time} with Dr. {ap_doc} @ {ap_loc}"
                    appointments_data[user][date_str].append(desc)
                    save_all()
                    st.success("Appointment added.")
                else:
                    st.error("All fields required.")

#############################################
#  PRESCRIPTIONS TAB
#############################################
def schedule_prescriptions(start_date_str, days_of_week_str, num_weeks):
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    except:
        return None
    try:
        w = int(num_weeks)
    except:
        return None
    day_map = {
        "mon": 1, "tue": 2, "wed": 3,
        "thu": 4, "fri": 5, "sat": 6, "sun": 7
    }
    raw_days = [x.strip().lower() for x in days_of_week_str.split(",") if x.strip()]
    valid_days = [day_map[d] for d in raw_days if d in day_map]
    schedule = []
    for wk in range(w):
        block_start = start_dt + timedelta(weeks=wk)
        for dnum in valid_days:
            offset = (dnum - block_start.isoweekday()) % 7
            date_target = block_start + timedelta(days=offset)
            schedule.append({
                "Day": date_target.day,
                "Month": date_target.month,
                "Year": date_target.year,
                "Status": "scheduled"
            })
    return schedule

def show_prescriptions_tab():
    st.header("Manage Prescriptions")
    user = st.session_state["current_user"]
    if user not in prescriptions_data:
        prescriptions_data[user] = {}

    st.subheader("Your Prescriptions")
    if prescriptions_data[user]:
        for rx_name, rx_info in list(prescriptions_data[user].items()):
            with st.expander(rx_name):
                minfo = rx_info.get("Medication Info", {})
                st.write(f"**Description**: {minfo.get('Description','N/A')}")
                st.write(f"**Taken with food?** {minfo.get('Taken with food','N/A')}")
                sched = rx_info.get("Schedule", [])
                if sched:
                    for entry in sched:
                        y,m,d = entry["Year"], entry["Month"], entry["Day"]
                        stt   = entry["Status"]
                        st.write(f"- {y}-{m:02d}-{d:02d} [{stt}]")
                else:
                    st.info("No schedule found.")

                if st.button(f"Delete {rx_name}", key=f"del_{rx_name}"):
                    del prescriptions_data[user][rx_name]
                    save_all()
                    st.success(f"Prescription '{rx_name}' deleted.")
                    st.stop()
    else:
        st.info("No prescriptions found.")

    st.write("---")
    st.subheader("Add New Prescription")
    rxname_val = st.text_input("Prescription Name", key="rx_new_name")
    rxdesc_val = st.text_input("Description", key="rx_new_desc")
    rxfood_val = st.selectbox("Taken with food?", ["Yes","No"], key="rx_food")
    rxstart    = st.date_input("Start Date", datetime.now(), key="rx_start")
    rxdays     = st.text_input("Days of Week (Mon,Wed,Fri)", key="rx_days")
    rxweeks    = st.text_input("Number of Weeks", "4", key="rx_weeks")

    if st.button("Create Prescription", key="rx_btn_create"):
        if rxname_val.strip():
            sched = schedule_prescriptions(rxstart.strftime("%Y-%m-%d"), rxdays, rxweeks)
            if sched is None:
                st.error("Invalid scheduling data.")
            else:
                prescriptions_data[user][rxname_val] = {
                    "Medication Info": {
                        "Description": rxdesc_val,
                        "Taken with food": rxfood_val
                    },
                    "Schedule": sched
                }
                save_all()
                st.success(f"Prescription '{rxname_val}' created with {len(sched)} entries.")
        else:
            st.error("Name is required.")

    st.write("---")
    st.subheader("Update Prescription Status")
    if prescriptions_data[user]:
        pick_rx = st.selectbox("Select Prescription", list(prescriptions_data[user].keys()))
        upd_date = st.date_input("Date to Update", datetime.now(), key="upd_rx_date")
        upd_status = st.selectbox("New Status", ["scheduled","taken on time","missed"], key="upd_rx_status")
        if st.button("Update Status", key="btn_upd_rx"):
            found_entry = None
            for e in prescriptions_data[user][pick_rx]["Schedule"]:
                dt = datetime(e["Year"], e["Month"], e["Day"])
                if dt.date() == upd_date:
                    found_entry = e
                    break
            if found_entry:
                found_entry["Status"] = upd_status
                save_all()
                st.success("Prescription status updated.")
            else:
                st.warning("No matching date found.")
    else:
        st.info("No prescriptions to update.")


#############################################
#   HEALTH TRACKING (with Blood Pressure)
#############################################
def show_health_tracking_tab():
    st.header("Health Tracking")
    user = st.session_state["current_user"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # ensure subdict
    if user not in mood_data:
        mood_data[user] = {}
    if user not in water_data:
        water_data[user] = {}
    if user not in steps_data:
        steps_data[user] = {}
    if user not in sleep_data:
        sleep_data[user] = {}
    if user not in weight_data:
        weight_data[user] = {}
    if user not in calories_data:
        calories_data[user] = {}
    if user not in bloodpressure_data:
        bloodpressure_data[user] = {}

    col1, col2, col3 = st.columns(3)

    # MOOD + SLEEP
    with col1:
        st.subheader("Mood")
        curr_mood = mood_data[user].get(today_str, None)
        st.write(f"Today: {curr_mood}/5" if curr_mood is not None else "No mood logged.")
        new_mood = st.slider("Set Mood (1–5)", 1, 5, 3)
        if st.button("Save Mood"):
            mood_data[user][today_str] = new_mood
            save_all()
            st.success("Mood updated.")

        st.subheader("Sleep")
        curr_sleep = sleep_data[user].get(today_str, None)
        st.write(f"Today: {curr_sleep} hours" if curr_sleep else "Not logged.")
        new_sleep = st.number_input("Sleep (hrs)", 0.0, 24.0, 7.0, step=0.5)
        if st.button("Log Sleep"):
            sleep_data[user][today_str] = new_sleep
            save_all()
            st.success("Sleep logged.")

    # WATER + STEPS
    with col2:
        st.subheader("Water Intake")
        curr_water = water_data[user].get(today_str, 0.0)
        st.write(f"Today so far: {curr_water} L")
        add_water = st.number_input("Liters to add", 0.0, 10.0, 0.5, step=0.25)
        if st.button("Add Water"):
            new_total = curr_water + add_water
            water_data[user][today_str] = new_total
            save_all()
            st.success(f"Water updated: {new_total} L")

        st.subheader("Steps")
        curr_steps = steps_data[user].get(today_str, 0)
        st.write(f"Today so far: {curr_steps} steps")
        add_stp = st.number_input("Steps to add", 0, 30000, 1000, step=500)
        if st.button("Add Steps"):
            new_st = curr_steps + add_stp
            steps_data[user][today_str] = new_st
            save_all()
            st.success(f"Steps updated: {new_st}")

    # WEIGHT + BP + CALORIES
    with col3:
        st.subheader("Weight & BMI")
        w_dict = weight_data[user].get(today_str, None)
        if w_dict:
            st.write(f"Today: {w_dict['weight_kg']} kg (BMI: {w_dict['bmi']:.1f})")
        else:
            st.write("No weight logged today.")

        w_kg = st.number_input("Weight (kg)", 30.0, 300.0, 70.0)
        user_height = users_data[user]["profile"].get("height_cm", 170)
        if user_height <= 0:
            user_height = 170
        if st.button("Log Weight"):
            bmi_val = round(w_kg / ((user_height/100)**2), 1)
            weight_data[user][today_str] = {"weight_kg": w_kg, "bmi": bmi_val}
            save_all()
            st.success(f"Weight logged: {w_kg} kg (BMI={bmi_val:.1f})")

        st.subheader("Blood Pressure")
        bp_entry = bloodpressure_data[user].get(today_str, None)
        if bp_entry:
            st.write(f"Today: {bp_entry['systolic']}/{bp_entry['diastolic']} mmHg")
        sys_val = st.number_input("Systolic", 70, 250, 120, step=1)
        dia_val = st.number_input("Diastolic", 40, 180, 80, step=1)
        if st.button("Save BP"):
            bloodpressure_data[user][today_str] = {
                "systolic": sys_val,
                "diastolic": dia_val
            }
            save_all()
            st.success(f"Blood pressure logged: {sys_val}/{dia_val} mmHg")

        st.subheader("Calories")
        cal_today = calories_data[user].get(today_str, 0)
        st.write(f"Today: {cal_today} kcal")
        add_cal = st.number_input("Add Calories", 0, 5000, 500, step=100)
        if st.button("Add Calories"):
            new_cal = cal_today + add_cal
            calories_data[user][today_str] = new_cal
            save_all()
            st.success(f"Calories updated: {new_cal}")

#############################################
#  ANALYTICS TAB
#############################################
def show_analytics_tab():
    st.header("Analytics & Trends")
    user = st.session_state["current_user"]
    sub_tab = st.selectbox("Analytics Sections", [
        "Water Intake", 
        "Mood History", 
        "Steps History", 
        "Weight/BMI Progress", 
        "Prescription Status",
        "Calorie Intake",
        "Blood Pressure History"
    ])

    if sub_tab == "Water Intake":
        st.subheader("Water (Last 14 Days)")
        w_dict = water_data.get(user, {})
        datelist, vals = [], []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            datelist.append(d_str)
            vals.append(w_dict.get(d_str, 0.0))
        fig, ax = plt.subplots()
        ax.bar(datelist, vals, color="blue")
        ax.set_xticklabels(datelist, rotation=45, ha="right")
        ax.set_ylabel("Liters")
        ax.set_title("Water Intake")
        st.pyplot(fig)

    elif sub_tab == "Mood History":
        st.subheader("Mood (Last 14 Days)")
        m_dict = mood_data.get(user, {})
        datelist, moods = [], []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            datelist.append(d_str)
            moods.append(m_dict.get(d_str, 0))
        fig, ax = plt.subplots()
        ax.plot(datelist, moods, marker="o", color="red")
        ax.set_xticklabels(datelist, rotation=45, ha="right")
        ax.set_yticks([1,2,3,4,5])
        ax.set_title("Mood Trend")
        st.pyplot(fig)

    elif sub_tab == "Steps History":
        st.subheader("Steps (Last 14 Days)")
        s_dict = steps_data.get(user, {})
        datelist, stepsvals = [], []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            datelist.append(d_str)
            stepsvals.append(s_dict.get(d_str, 0))
        fig, ax = plt.subplots()
        ax.bar(datelist, stepsvals, color="green")
        ax.set_xticklabels(datelist, rotation=45, ha="right")
        ax.set_title("Steps Trend")
        st.pyplot(fig)

    elif sub_tab == "Weight/BMI Progress":
        st.subheader("Weight & BMI (Last 30 Days)")
        w_dict = weight_data.get(user, {})
        datelist, weights, bmis = [], [], []
        for i in range(30):
            d_str = (datetime.now()-timedelta(days=29-i)).strftime("%Y-%m-%d")
            datelist.append(d_str)
            if d_str in w_dict:
                weights.append(w_dict[d_str]["weight_kg"])
                bmis.append(w_dict[d_str]["bmi"])
            else:
                weights.append(None)
                bmis.append(None)
        fig, ax = plt.subplots()
        ax.plot(datelist, weights, marker="o", color="blue", label="Weight (kg)")
        ax2 = ax.twinx()
        ax2.plot(datelist, bmis, marker="s", color="orange", label="BMI")

        ax.set_xticklabels(datelist, rotation=45, ha="right")
        ax.set_ylabel("Weight (kg)")
        ax2.set_ylabel("BMI")
        ax.set_title("Weight & BMI")
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1+lines2, labels1+labels2, loc="upper left")
        st.pyplot(fig)

    elif sub_tab == "Prescription Status":
        st.subheader("Prescription Status Distribution")
        rx_dict = prescriptions_data.get(user, {})
        if not rx_dict:
            st.info("No prescriptions found.")
            return
        statuses = {"scheduled":0, "taken on time":0, "missed":0}
        for rx_name, rx_info in rx_dict.items():
            for e in rx_info.get("Schedule", []):
                stt = e.get("Status","scheduled")
                if stt not in statuses:
                    statuses[stt] = 0
                statuses[stt] += 1

        labels, values = list(statuses.keys()), list(statuses.values())
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct="%1.1f%%")
        ax.set_title("Prescription Status Overview")
        st.pyplot(fig)

    elif sub_tab == "Calorie Intake":
        st.subheader("Calorie Intake (Last 14 Days)")
        c_dict = calories_data.get(user, {})
        datelist, calsvals = [], []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            datelist.append(d_str)
            calsvals.append(c_dict.get(d_str, 0))
        fig, ax = plt.subplots()
        ax.bar(datelist, calsvals, color="purple")
        ax.set_xticklabels(datelist, rotation=45, ha="right")
        ax.set_ylabel("kcal")
        ax.set_title("Calorie Intake")
        st.pyplot(fig)

    elif sub_tab == "Blood Pressure History":
        st.subheader("Blood Pressure (Last 14 Days)")
        bp_dict = bloodpressure_data.get(user, {})
        if not bp_dict:
            st.info("No blood pressure logs found.")
            return
        # We'll create lists for date, systolic, diastolic
        datelist, sys_vals, dia_vals = [], [], []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            datelist.append(d_str)
            entry = bp_dict.get(d_str, None)
            if entry:
                sys_vals.append(entry["systolic"])
                dia_vals.append(entry["diastolic"])
            else:
                sys_vals.append(None)
                dia_vals.append(None)

        fig, ax = plt.subplots()
        ax.plot(datelist, sys_vals, marker="o", color="red", label="Systolic")
        ax.plot(datelist, dia_vals, marker="s", color="blue", label="Diastolic")
        ax.set_xticklabels(datelist, rotation=45, ha="right")
        ax.set_ylabel("mmHg")
        ax.set_title("Blood Pressure Trend")
        ax.legend()
        st.pyplot(fig)

#############################################
#   SYMPTOM CHECKER TAB
#############################################
def show_symptom_checker_tab():
    st.header("Symptom Checker (Demo)")
    st.write("Disclaimer: This is NOT real medical advice. For demonstration only.")

    user = st.session_state["current_user"]
    symptom_input = st.text_area("Enter your symptoms, separated by commas (e.g. 'cough, fever, headache')")
    if st.button("Analyze Symptoms"):
        if symptom_input.strip():
            symptom_list = [s.strip() for s in symptom_input.split(",")]
            result = symptom_checker(symptom_list)
            st.write(f"**Result**: {result}")
        else:
            st.error("Please enter at least one symptom.")

#############################################
#     NOTES / JOURNAL TAB
#############################################
def show_notes_tab():
    st.header("Personal Notes / Journaling")
    user = st.session_state["current_user"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    if user not in notes_data:
        notes_data[user] = {}
    if today_str not in notes_data[user]:
        notes_data[user][today_str] = []

    st.subheader(f"Notes for {today_str}")
    day_notes = notes_data[user][today_str]
    if day_notes:
        for i, note_txt in enumerate(day_notes):
            with st.expander(f"Note #{i+1}"):
                st.write(note_txt)
                if st.button(f"Delete Note #{i+1}", key=f"delnote_{i}"):
                    day_notes.pop(i)
                    save_all()
                    st.success("Note deleted.")
                    st.stop()
    else:
        st.info("No notes for today.")

    st.write("---")
    with st.expander("Add a New Note"):
        new_note = st.text_area("Write your note:")
        if st.button("Save Note"):
            if new_note.strip():
                notes_data[user][today_str].append(new_note.strip())
                save_all()
                st.success("Note saved.")
                st.stop()
            else:
                st.error("Cannot save an empty note.")

#############################################
#         SETTINGS TAB
#############################################
def show_settings_tab():
    st.header("Settings & Profile")
    user = st.session_state["current_user"]
    profile = users_data[user]["profile"]

    colA, colB = st.columns(2)
    with colA:
        name_val = st.text_input("Name", profile.get("name", ""))
        email_val= st.text_input("Email", profile.get("email", ""))
        gender_val= st.selectbox("Gender", ["","Male","Female","Other"], 
                     index=0 if not profile.get("gender") else ["","Male","Female","Other"].index(profile["gender"]))
        age_val   = st.number_input("Age", 0,120, value=profile.get("age") or 0)
        height_val= st.number_input("Height (cm)", 1,250, value=profile.get("height_cm") or 170)

        if st.button("Save Profile"):
            users_data[user]["profile"] = {
                "name": name_val,
                "email": email_val,
                "gender": gender_val,
                "age": age_val,
                "height_cm": height_val
            }
            save_all()
            st.success("Profile updated.")

    with colB:
        st.subheader("SMTP / Email Config")
        st.write("Configure for email notifications (optional).")
        smtp_host = st.text_input("SMTP Host", users_data[user]["smtp"].get("host",""))
        smtp_port = st.number_input("SMTP Port", 1,99999, users_data[user]["smtp"].get("port",587))
        smtp_user = st.text_input("SMTP Username", users_data[user]["smtp"].get("username",""))
        smtp_pass = st.text_input("SMTP App Password", users_data[user]["smtp"].get("app_password",""), type="password")

        if st.button("Save SMTP"):
            users_data[user]["smtp"]["host"]        = smtp_host
            users_data[user]["smtp"]["port"]        = smtp_port
            users_data[user]["smtp"]["username"]    = smtp_user
            users_data[user]["smtp"]["app_password"]= smtp_pass
            save_all()
            st.success("SMTP settings saved.")

    st.write("---")
    if st.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.success("You have been logged out.")
        st.stop()

#############################################
#           RUN THE APP
#############################################
if __name__ == "__main__":
    main()
