#############################################
#            WELLNEST WEB APPLICATION
#     WITH NOTIFICATIONS & FAMILY GROUPS
#############################################

import os
import json
import datetime
from datetime import datetime, timedelta

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Optional: if you want to use requests for Lottie
# from streamlit_lottie import st_lottie
import requests

# For hashing passwords
import hashlib

# For sending email notifications (requires smtplib, email modules)
import smtplib
from email.mime.text import MIMEText

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

# NEW: For group/family circle data
GROUPS_FILE        = os.path.join(DATA_DIR, "groups.json")

# Optional Banner / Splash
SPLASH_IMAGE_PATH = "path/to/splash_image.png"

st.set_page_config(page_title=APP_TITLE, layout="wide")

#############################################
#            HELPER FUNCTIONS
#############################################
def load_json(filepath):
    """Load JSON from file; return {} if missing or corrupted."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_json(data, filepath):
    """Save dictionary as JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def hash_password(password: str) -> str:
    """Return a SHA-256 hash of the given password string."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username: str, password: str, users_data: dict) -> bool:
    """Return True if credentials are valid for a stored user."""
    if username in users_data:
        return hash_password(password) == users_data[username]["password"]
    return False

def register_new_user(username: str, password: str, users_data: dict) -> bool:
    """Attempt to register a new user. Return False if user already exists."""
    if username in users_data:
        return False
    users_data[username] = {
        "password": hash_password(password),
        "profile": {
            "name": "",
            "email": "",
            "gender": "",
            "age": None,
            "height_cm": None
        },
        # Optionally store email server config if you want per-user email sending
        "smtp": {
            "host": "",
            "port": 587,
            "username": "",
            "app_password": ""  # For secure apps (e.g., Gmail app password)
        }
    }
    save_json(users_data, USERS_FILE)
    return True

#############################################
#            DATA LOADING
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
groups_data        = load_json(GROUPS_FILE)  # new group/family data

def save_all():
    """Save all major data dictionaries."""
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

#############################################
#     NOTIFICATION & SCHEDULING LOGIC
#############################################
def check_and_trigger_notifications(username: str):
    """
    Check tasks/appointments that are upcoming within 1 day or 1 hour.
    Also check water/mood trends.
    If we find any triggers, we display them on screen,
    and optionally email them if user has email configured.
    """
    # A naive approach: each time user logs in or visits,
    # we search for upcoming tasks/appointments in the next day/hour.

    # 1) Check tasks/appointments
    upcoming_events = []
    now = datetime.now()
    user_email = users_data[username]["profile"].get("email", "")
    
    # For day/time checks, we need tasks_data[username] with date => list of tasks
    user_tasks = tasks_data.get(username, {})
    user_apps  = appointments_data.get(username, {})

    # We'll look over the next 2 days to find anything within 1 day or 1 hour from "now"
    for day_offset in [0, 1]:
        date_candidate = (now + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        if date_candidate in user_tasks:
            for tsk in user_tasks[date_candidate]:
                # Task time might be "HH:MM" or something
                dt_obj = parse_task_datetime(date_candidate, tsk.get("time",""))
                if dt_obj:
                    diff = (dt_obj - now).total_seconds()
                    # 1 day = 86400 sec, 1 hour=3600 sec
                    if 0 < diff <= 3600:
                        upcoming_events.append(f"[1-hour ALERT] Task '{tsk['name']}' at {tsk['time']} on {date_candidate}")
                    elif 3600 < diff <= 86400:
                        upcoming_events.append(f"[1-day ALERT] Task '{tsk['name']}' at {tsk['time']} on {date_candidate}")

        if date_candidate in user_apps:
            for app_str in user_apps[date_candidate]:
                # parse out time if possible
                # we assume format "HH:MM with Dr. X @ location"
                dt_obj = parse_appointment_datetime(date_candidate, app_str)
                if dt_obj:
                    diff = (dt_obj - now).total_seconds()
                    if 0 < diff <= 3600:
                        upcoming_events.append(f"[1-hour ALERT] Appointment: {app_str} on {date_candidate}")
                    elif 3600 < diff <= 86400:
                        upcoming_events.append(f"[1-day ALERT] Appointment: {app_str} on {date_candidate}")

    # 2) Check water or mood trends
    # e.g., if last 3 days water average is < 1.0 L, we nudge the user
    # or if mood is consistently < 2
    water_alert = check_water_trend(username)
    if water_alert:
        upcoming_events.append(water_alert)

    mood_alert = check_mood_trend(username)
    if mood_alert:
        upcoming_events.append(mood_alert)

    # Display notifications on screen
    if upcoming_events:
        st.info("**NOTIFICATIONS**")
        for evt in upcoming_events:
            st.warning(evt)

        # Optionally send email
        if user_email and users_data[username].get("smtp", {}).get("host"):
            # If the user has configured an SMTP host & app password
            with st.expander("Send notifications via email"):
                if st.button("Send Email Alerts"):
                    send_email_notifications(username, upcoming_events)
                    st.success("Email alerts sent.")
    else:
        st.info("No new alerts or notifications at this time.")


def parse_task_datetime(date_str: str, time_str: str):
    """Attempt to parse date + time string to a datetime object."""
    # date_str is "YYYY-MM-DD", time_str might be "HH:MM"
    try:
        dt_str = f"{date_str} {time_str}"
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return dt_obj
    except:
        return None

def parse_appointment_datetime(date_str: str, app_str: str):
    """
    Attempt to parse date + time from an appointment string. 
    E.g. "14:30 with Dr. Bob @ SomeClinic".
    """
    try:
        time_part = app_str.split(" ")[0]  # "14:30"
        dt_str = f"{date_str} {time_part}"
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return dt_obj
    except:
        return None


def check_water_trend(username: str):
    """Check if average water intake for last 3 days is very low (< 1 L)."""
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
        return "Water intake has been quite low for the past few days. Remember to hydrate!"
    return None

def check_mood_trend(username: str):
    """Check if mood is consistently low (< 2) for the last 3 days."""
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
        return "Your recent mood has been quite low. Consider activities or reaching out for support!"
    return None


def send_email_notifications(username: str, messages: list):
    """
    Send an email containing the messages to the user,
    using the user's stored SMTP config.
    """
    user_email = users_data[username]["profile"].get("email","")
    smtp_config = users_data[username].get("smtp", {})
    smtp_host     = smtp_config.get("host")
    smtp_port     = smtp_config.get("port", 587)
    smtp_user     = smtp_config.get("username")
    smtp_password = smtp_config.get("app_password")

    if not (user_email and smtp_host and smtp_user and smtp_password):
        st.error("Cannot send email: missing or incomplete SMTP configuration.")
        return

    # Build the message
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
            server.login(smtp_user, smtp_password)
            server.send_message(msg_obj)
    except Exception as e:
        st.error(f"Error sending email: {e}")

#############################################
#    FAMILY/GROUP (CIRCLE) FUNCTIONALITY
#############################################
"""
We'll let users create or join a group. 
Groups will be stored in groups_data = {
  "group1": {
     "group_name": "SmithFamily",
     "members": ["alice","bob","charlie"]
  }
}
We then allow group members to see each other's data (some subset).
"""

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
    """Return a list of (group_id, group_name) that the user is in."""
    user_groups = []
    for gid, info in groups_data.items():
        if username in info["members"]:
            user_groups.append((gid, info["group_name"]))
    return user_groups


def family_group_view(username: str):
    st.header("Family / Circle Groups")
    st.write("Here you can create or join a group. Group members can view each other's basic stats.")
    
    # Show user’s current groups
    user_groups = list_user_groups(username)
    if user_groups:
        st.subheader("Your Groups")
        for gid, gname in user_groups:
            st.write(f"- **{gname}** (ID: {gid})")
            if st.button(f"Leave {gname}", key=f"btn_leave_{gid}"):
                leave_group(gid, username)
                st.success(f"You left {gname}.")
                st.experimental_rerun()
    else:
        st.info("You're not in any group.")

    st.write("---")
    st.subheader("Join Existing Group")
    join_gid = st.text_input("Enter Group ID to join")
    if st.button("Join Group", key="btn_join_grp"):
        if join_gid.strip():
            if join_group(join_gid.strip(), username):
                st.success(f"Joined group {join_gid}")
                st.experimental_rerun()
            else:
                st.error("Group not found or other error.")
        else:
            st.error("Please enter a Group ID.")

    st.write("---")
    st.subheader("Create a New Group")
    new_gid = st.text_input("New Group ID", key="grp_new_id")
    new_gname = st.text_input("New Group Name", key="grp_new_name")
    if st.button("Create Group", key="btn_create_grp"):
        if new_gid.strip() and new_gname.strip():
            if create_group(new_gid.strip(), new_gname.strip()):
                st.success("Group created. You can now join it.")
            else:
                st.error("Group ID already exists.")
        else:
            st.error("Please fill in both fields.")


    st.write("---")
    # If user is in any group, show the members' data
    if user_groups:
        st.subheader("Family / Friends Stats")
        for gid, gname in user_groups:
            st.write(f"**Group**: {gname} (ID: {gid})")
            members = groups_data[gid]["members"]
            if not members:
                st.write("- No members in this group?")
                continue
            st.write(f"**Members**: {', '.join(members)}")

            # Show each member's basic stats (today's water, mood, steps, etc.)
            for m in members:
                st.write(f"### {m}'s Stats")
                show_limited_stats(m)


def show_limited_stats(username: str):
    """
    Show a minimal set of stats for a given user
    (like today's water, steps, mood, etc.),
    to share with group members.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Water
    water_val = water_data.get(username, {}).get(today_str, 0.0)
    st.write(f"- Water Today: {water_val} L")

    # Mood
    mood_val = mood_data.get(username, {}).get(today_str, None)
    if mood_val is not None:
        st.write(f"- Mood Today: {mood_val}/5")
    else:
        st.write("- Mood Today: Not logged")

    # Steps
    steps_val = steps_data.get(username, {}).get(today_str, 0)
    st.write(f"- Steps Today: {steps_val}")

    # Weight (just show last entry within the last 7 days)
    w_dict = weight_data.get(username, {})
    if w_dict:
        # find last 7 days if any
        recent_weight = None
        for i in range(7):
            d_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if d_str in w_dict:
                recent_weight = w_dict[d_str]
                break
        if recent_weight:
            st.write(f"- Recent Weight: {recent_weight['weight_kg']} kg (BMI: {recent_weight['bmi']:.1f})")

#############################################
#      STREAMLIT SESSION/ AUTH
#############################################
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

def main():
    if not st.session_state["logged_in"]:
        show_login_screen()
    else:
        # Each time we land here, let's run notification checks
        check_and_trigger_notifications(st.session_state["current_user"])
        show_main_app()

def show_login_screen():
    st.title("Welcome to WellNest")
    st.subheader("Login or Sign Up")

    tab_login, tab_signup = st.tabs(["Login","Sign Up"])

    with tab_login:
        uname = st.text_input("Username", key="login_username")
        pwd   = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In"):
            if check_credentials(uname, pwd, users_data):
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = uname
                st.success("You are now logged in.")
                st.experimental_rerun()
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
                    st.success("Account created. Please log in now.")
                else:
                    st.warning("Username already taken.")

def show_main_app():
    st.sidebar.title(f"Hello, {st.session_state['current_user']}!")
    menu = st.sidebar.radio("Menu", [
        "Home",
        "Tasks & Appointments",
        "Prescriptions",
        "Health Tracking",
        "Analytics",
        "Notes",
        "Family / Circle",
        "Settings"
    ])

    st.title(APP_TITLE)
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
    elif menu == "Settings":
        show_settings_tab()

#############################################
#          EXISTING TABS / FEATURES
#############################################

def show_home_tab():
    colA, colB = st.columns([2,3])
    with colA:
        # Show a splash or banner if desired
        if os.path.isfile(SPLASH_IMAGE_PATH):
            try:
                img = Image.open(SPLASH_IMAGE_PATH)
                st.image(img, use_column_width=True)
            except:
                st.write("Welcome to WellNest!")
        else:
            st.write("Welcome to WellNest!")

    with colB:
        st.subheader("Dashboard Overview")
        user = st.session_state["current_user"]
        today_str = datetime.now().strftime("%Y-%m-%d")

        tasks_today = tasks_data.get(user, {}).get(today_str, [])
        st.write(f"- **Tasks Today**: {len(tasks_today)}")

        apps_today = appointments_data.get(user, {}).get(today_str, [])
        st.write(f"- **Appointments Today**: {len(apps_today)}")

        mood_today = mood_data.get(user, {}).get(today_str, None)
        if mood_today is not None:
            st.write(f"- **Today's Mood**: {mood_today}/5")
        else:
            st.write("- **Today's Mood**: Not Logged")

        water_today = water_data.get(user, {}).get(today_str, 0)
        st.write(f"- **Water Intake**: {water_today} L")

        steps_today = steps_data.get(user, {}).get(today_str, 0)
        st.write(f"- **Steps**: {steps_today}")

    st.write("---")
    st.subheader("Quick Actions")
    with st.expander("Log Today's Mood"):
        mood_val = st.slider("Mood (1=Sad, 5=Happy)", 1, 5, 3)
        if st.button("Save Mood"):
            if st.session_state["current_user"] not in mood_data:
                mood_data[st.session_state["current_user"]] = {}
            mood_data[st.session_state["current_user"]][today_str] = mood_val
            save_all()
            st.success("Mood logged.")

    with st.expander("Add Today's Water Intake"):
        add_water = st.number_input("Liters to add", min_value=0.0, step=0.1)
        if st.button("Add Water"):
            curr_val = water_data.get(st.session_state["current_user"], {}).get(today_str, 0)
            new_val  = curr_val + add_water
            if st.session_state["current_user"] not in water_data:
                water_data[st.session_state["current_user"]] = {}
            water_data[st.session_state["current_user"]][today_str] = new_val
            save_all()
            st.success(f"Water updated. Total: {new_val} L")

    with st.expander("Log Steps"):
        add_steps = st.number_input("Steps to add", min_value=0, step=100)
        if st.button("Add Steps"):
            curr_val = steps_data.get(st.session_state["current_user"], {}).get(today_str, 0)
            new_val  = curr_val + add_steps
            if st.session_state["current_user"] not in steps_data:
                steps_data[st.session_state["current_user"]] = {}
            steps_data[st.session_state["current_user"]][today_str] = new_val
            save_all()
            st.success(f"Steps updated to {new_val} today.")

def show_tasks_appointments_tab():
    st.header("Tasks & Appointments")
    user = st.session_state["current_user"]
    if user not in tasks_data:
        tasks_data[user] = {}
    if user not in appointments_data:
        appointments_data[user] = {}

    sel_date = st.date_input("Select date", value=datetime.now())
    date_str = sel_date.strftime("%Y-%m-%d")
    st.write(f"Selected date: {date_str}")

    # Ensure date keys exist
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
                st.write(f"{i+1}. **{tsk['name']}** @ {tsk['time']} (Assignee: {tsk.get('assignee','N/A')} | Status: {tsk['status']})")
        else:
            st.info("No tasks.")

        with st.expander("Add a new task"):
            tname = st.text_input("Task Name")
            tassn = st.text_input("Assigned To")
            ttime = st.text_input("Time (HH:MM)")
            tstatus = st.selectbox("Status", ["Pending","In-progress","Completed"])
            if st.button("Save Task"):
                if tname and ttime:
                    new_task = {
                        "name": tname,
                        "assignee": tassn,
                        "time": ttime,
                        "status": tstatus
                    }
                    tasks_data[user][date_str].append(new_task)
                    save_all()
                    st.success("Task added.")
                else:
                    st.error("Task name and time required.")

    with col2:
        st.subheader("Appointments")
        day_apps = appointments_data[user][date_str]
        if day_apps:
            for i, a in enumerate(day_apps):
                st.write(f"{i+1}. {a}")
        else:
            st.info("No appointments.")

        with st.expander("Add a new appointment"):
            atime = st.text_input("Time (HH:MM)")
            doc   = st.text_input("Doctor's Name")
            loc   = st.text_input("Location")
            if st.button("Save Appointment"):
                if atime and doc and loc:
                    desc = f"{atime} with Dr. {doc} @ {loc}"
                    appointments_data[user][date_str].append(desc)
                    save_all()
                    st.success("Appointment added.")
                else:
                    st.error("Fill out all fields.")


def show_prescriptions_tab():
    st.header("Prescriptions")
    user = st.session_state["current_user"]
    if user not in prescriptions_data:
        prescriptions_data[user] = {}

    # List existing
    st.subheader("Your Prescriptions")
    if prescriptions_data[user]:
        for rx_name, rx_info in prescriptions_data[user].items():
            with st.expander(rx_name):
                minfo = rx_info.get("Medication Info", {})
                st.write(f"**Description**: {minfo.get('Description','N/A')}")
                st.write(f"**Taken with food?** {minfo.get('Taken with food','N/A')}")

                if "Schedule" in rx_info:
                    for entry in rx_info["Schedule"]:
                        y, m, d = entry["Year"], entry["Month"], entry["Day"]
                        stt = entry.get("Status", "scheduled")
                        st.write(f" - {y}-{m:02d}-{d:02d} [{stt}]")

                if st.button(f"Delete {rx_name}"):
                    del prescriptions_data[user][rx_name]
                    save_all()
                    st.experimental_rerun()
    else:
        st.info("No prescriptions yet.")

    # Add new
    st.write("---")
    st.subheader("Add a New Prescription")
    rx_name = st.text_input("Prescription Name")
    rx_desc = st.text_input("Description")
    rx_food = st.selectbox("Taken with food?", ["Yes","No"])
    rx_start = st.date_input("Start Date", value=datetime.now())
    rx_days  = st.text_input("Days of Week (e.g. Mon,Wed,Fri)")
    rx_weeks = st.text_input("Number of Weeks", value="4")

    if st.button("Create Prescription"):
        if rx_name.strip():
            sched = schedule_prescriptions(rx_start.strftime("%Y-%m-%d"), rx_days, rx_weeks)
            if sched is None:
                st.error("Invalid scheduling data.")
            else:
                prescriptions_data[user][rx_name] = {
                    "Medication Info": {
                        "Description": rx_desc,
                        "Taken with food": rx_food
                    },
                    "Schedule": sched
                }
                save_all()
                st.success(f"Prescription '{rx_name}' created.")
        else:
            st.error("Name is required.")

    st.write("---")
    st.subheader("Update Prescription Status")
    if prescriptions_data[user]:
        selected_rx = st.selectbox("Select Prescription", list(prescriptions_data[user].keys()))
        sel_date = st.date_input("Date to update", value=datetime.now())
        new_status = st.selectbox("New Status", ["scheduled","taken on time","missed"])
        if st.button("Update Status"):
            found_entry = None
            for e in prescriptions_data[user][selected_rx]["Schedule"]:
                dt = datetime(e["Year"], e["Month"], e["Day"])
                if dt.date() == sel_date:
                    found_entry = e
                    break
            if found_entry:
                found_entry["Status"] = new_status
                save_all()
                st.success("Updated.")
            else:
                st.warning("No matching date in schedule.")
    else:
        st.info("No prescriptions to update.")


def show_health_tracking_tab():
    st.header("Health Tracking")
    # (Same logic as the older example for mood, water, steps, sleep, weight, calories.)
    # You can replicate or keep your advanced code from the previous example.

    user = st.session_state["current_user"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Ensure sub-dicts
    if user not in mood_data:     mood_data[user] = {}
    if user not in water_data:    water_data[user] = {}
    if user not in steps_data:    steps_data[user] = {}
    if user not in sleep_data:    sleep_data[user] = {}
    if user not in weight_data:   weight_data[user] = {}
    if user not in calories_data: calories_data[user] = {}

    col1, col2, col3 = st.columns(3)
    # Mood, Sleep, Water, Steps, Weight/BMI, Calories
    with col1:
        st.subheader("Mood")
        curr_mood = mood_data[user].get(today_str, None)
        if curr_mood: 
            st.write(f"Today's Mood: {curr_mood}/5")
        log_mood = st.slider("Log Mood", 1, 5, 3)
        if st.button("Set Mood"):
            mood_data[user][today_str] = log_mood
            save_all()
            st.success("Mood set.")

        st.subheader("Sleep")
        curr_sleep = sleep_data[user].get(today_str, None)
        if curr_sleep is not None:
            st.write(f"Today: {curr_sleep} hours")
        log_sleep = st.number_input("Hours of sleep", 0.0, 24.0, 7.0, step=0.5)
        if st.button("Log Sleep"):
            sleep_data[user][today_str] = log_sleep
            save_all()
            st.success(f"Sleep logged: {log_sleep} hrs")

    with col2:
        st.subheader("Water Intake")
        water_val = water_data[user].get(today_str, 0.0)
        st.write(f"Today so far: {water_val} L")
        add_water = st.number_input("Liters to add", 0.0, 10.0, 0.5, step=0.1)
        if st.button("Add Water"):
            new_total = water_val + add_water
            water_data[user][today_str] = new_total
            save_all()
            st.success(f"Updated total: {new_total} L")

        st.subheader("Steps")
        steps_val = steps_data[user].get(today_str, 0)
        st.write(f"Today so far: {steps_val}")
        add_steps = st.number_input("Steps to add", 0, 30000, 1000, step=500)
        if st.button("Add Steps"):
            new_st = steps_val + add_steps
            steps_data[user][today_str] = new_st
            save_all()
            st.success(f"Steps updated: {new_st}")

    with col3:
        st.subheader("Weight & BMI")
        w_dict = weight_data[user].get(today_str, None)
        if w_dict:
            st.write(f"Today: {w_dict['weight_kg']} kg, BMI: {w_dict['bmi']:.1f}")
        else:
            st.write("No weight for today.")
        weight_kg = st.number_input("Weight (kg)", 30.0, 300.0, 70.0)
        # Grab user’s height from profile or default
        height_cm = users_data[user]["profile"].get("height_cm", 170)
        if st.button("Log Weight"):
            bmi_val = round(weight_kg / ((height_cm/100)**2),2)
            weight_data[user][today_str] = {
                "weight_kg": weight_kg,
                "bmi": bmi_val
            }
            save_all()
            st.success(f"Weight logged: {weight_kg} kg (BMI={bmi_val})")

        st.subheader("Calories")
        c_val = calories_data[user].get(today_str, 0)
        st.write(f"Today: {c_val} kcal")
        add_cal = st.number_input("Add Calories", 0, 5000, 500, step=100)
        if st.button("Add Calories"):
            new_c = c_val + add_cal
            calories_data[user][today_str] = new_c
            save_all()
            st.success(f"Calories updated: {new_c}")

def show_analytics_tab():
    st.header("Analytics & Trends")
    user = st.session_state["current_user"]
    sub_tab = st.selectbox("Analytics Sub-Sections", [
        "Water Intake", 
        "Mood History", 
        "Steps History", 
        "Weight/BMI Progress", 
        "Prescription Status",
        "Calorie Intake"
    ])

    # (Same logic as earlier for each sub-section, with charts.)
    # You can copy from previous examples.

    if sub_tab == "Water Intake":
        st.subheader("Water (Last 14 Days)")
        user_water = water_data.get(user, {})
        date_list = []
        val_list  = []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            date_list.append(d_str)
            val_list.append(user_water.get(d_str,0))

        fig, ax = plt.subplots()
        ax.bar(date_list, val_list, color="blue")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_ylabel("Liters")
        ax.set_title("Water Intake Over 14 Days")
        st.pyplot(fig)

    elif sub_tab == "Mood History":
        st.subheader("Mood (Last 14 Days)")
        user_mood = mood_data.get(user, {})
        date_list = []
        mood_list = []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            date_list.append(d_str)
            mood_list.append(user_mood.get(d_str,0))

        fig, ax = plt.subplots()
        ax.plot(date_list, mood_list, marker="o", color="red")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_ylim(0,6)
        ax.set_title("Mood Trend")
        st.pyplot(fig)

    elif sub_tab == "Steps History":
        st.subheader("Steps (Last 14 Days)")
        user_steps = steps_data.get(user, {})
        date_list = []
        steps_list = []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            date_list.append(d_str)
            steps_list.append(user_steps.get(d_str,0))

        fig, ax = plt.subplots()
        ax.bar(date_list, steps_list, color="green")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_ylabel("Steps")
        ax.set_title("Steps Trend")
        st.pyplot(fig)

    elif sub_tab == "Weight/BMI Progress":
        st.subheader("Weight & BMI (Last 30 Days)")
        w_dict = weight_data.get(user, {})
        date_list = []
        weight_vals = []
        bmi_vals    = []
        for i in range(30):
            d_str = (datetime.now()-timedelta(days=29-i)).strftime("%Y-%m-%d")
            date_list.append(d_str)
            if d_str in w_dict:
                weight_vals.append(w_dict[d_str]["weight_kg"])
                bmi_vals.append(w_dict[d_str]["bmi"])
            else:
                weight_vals.append(None)
                bmi_vals.append(None)

        fig, ax = plt.subplots()
        ax.plot(date_list, weight_vals, marker="o", label="Weight (kg)", color="blue")
        ax2 = ax.twinx()
        ax2.plot(date_list, bmi_vals, marker="s", label="BMI", color="orange")

        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_ylabel("Weight (kg)")
        ax2.set_ylabel("BMI")
        ax.set_title("Weight & BMI Over 30 Days")

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1+lines2, labels1+labels2, loc="upper left")

        st.pyplot(fig)

    elif sub_tab == "Prescription Status":
        st.subheader("Medication Status Distribution")
        user_rx = prescriptions_data.get(user, {})
        statuses = {"scheduled":0, "taken on time":0, "missed":0}
        for rx_name, rx_info in user_rx.items():
            for entry in rx_info.get("Schedule",[]):
                stt = entry.get("Status","scheduled")
                if stt not in statuses:
                    statuses[stt] = 0
                statuses[stt] += 1

        labels = list(statuses.keys())
        values = list(statuses.values())
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct="%1.1f%%")
        ax.set_title("Prescription Status Overview")
        st.pyplot(fig)

    elif sub_tab == "Calorie Intake":
        st.subheader("Calories (Last 14 Days)")
        c_dict = calories_data.get(user, {})
        date_list = []
        cals_list = []
        for i in range(14):
            d_str = (datetime.now()-timedelta(days=13-i)).strftime("%Y-%m-%d")
            date_list.append(d_str)
            cals_list.append(c_dict.get(d_str,0))

        fig, ax = plt.subplots()
        ax.bar(date_list, cals_list, color="purple")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_ylabel("kcal")
        ax.set_title("Calorie Intake")
        st.pyplot(fig)

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
                if st.button(f"Delete Note #{i+1}", key=f"btn_del_note_{i}"):
                    day_notes.pop(i)
                    save_all()
                    st.experimental_rerun()
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
                st.experimental_rerun()
            else:
                st.error("Note cannot be empty.")

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
        height_val= st.number_input("Height (cm)", 100,250, value=profile.get("height_cm") or 170)

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
        st.write("Fill these if you want email notifications.")
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
        st.experimental_rerun()

#############################################
#           RUN THE APP
#############################################
if __name__ == "__main__":
    main()
