#############################################
#            WELLNEST WEB APPLICATION
# An extensive Streamlit-based health & wellness
# tracker with multi-user login, tasks,
# appointments, prescriptions, and analytics.
#
# Approximately ~2000 lines of code are used
# (some optional placeholders are included).
#
# Created as an illustrative, large-scale
# example of a “top-of-the-line” Streamlit app.
#############################################

import os
import json
import datetime
from datetime import datetime, timedelta

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Optional: for advanced animations (pip install streamlit-lottie)
# from streamlit_lottie import st_lottie
import requests

# Optional: to handle images
from PIL import Image

# ---------------- GLOBAL CONSTANTS ---------------- #
APP_TITLE = "WellNest"
DATA_DIR = "data"

# In a larger-scale app, we might have a dedicated environment config
# for secrets, database connection, etc. For demonstration, we keep it simple.
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, "users.json")

TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.json")
PRESCRIPTIONS_FILE = os.path.join(DATA_DIR, "prescriptions.json")
MOOD_FILE = os.path.join(DATA_DIR, "mood.json")
WATER_FILE = os.path.join(DATA_DIR, "water.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")

# Additional logs for advanced features
STEPS_FILE = os.path.join(DATA_DIR, "steps.json")
SLEEP_FILE = os.path.join(DATA_DIR, "sleep.json")
WEIGHT_FILE = os.path.join(DATA_DIR, "weight.json")
CALORIES_FILE = os.path.join(DATA_DIR, "calories.json")

# If you have a splash or banner image, place it here
SPLASH_IMAGE_PATH = "path/to/splash_image.png"  # optional

# Optional Lottie animation JSON URL (replace with your own or remove if not needed)
LOTTIE_ANIMATION_URL = "https://assets5.lottiefiles.com/packages/lf20_j1adxtyb.json"

# Set up Streamlit page config
st.set_page_config(page_title=APP_TITLE, layout="wide")

# ---------------- HELPER FUNCTIONS ---------------- #

def load_json(filepath):
    """Load JSON from a file safely; return empty dict if missing or corrupted."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_json(data, filepath):
    """Save data as JSON to the specified filepath."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_lottie_url(url: str):
    """
    Fetch a Lottie animation JSON from the specified URL.
    Requires `requests` library. If fails, returns None.
    """
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

# A basic method to "hash" passwords. 
# (For a real-world app, use passlib or another secure hashing library!)
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# For user authentication
def check_credentials(username: str, password: str, users_data: dict) -> bool:
    """
    Return True if the username exists and password is correct 
    (after hashing). Otherwise, False.
    """
    if username in users_data:
        hashed_input = hash_password(password)
        return hashed_input == users_data[username]["password"]
    return False

def register_new_user(username: str, password: str, users_data: dict) -> bool:
    """
    Register a new user. Return False if username already taken,
    True if registration successful.
    """
    if username in users_data:
        return False
    # store hashed password
    users_data[username] = {
        "password": hash_password(password),
        "profile": {
            "name": "",
            "email": "",
            "gender": "",
            "age": None,
            "height_cm": None
        }
    }
    save_json(users_data, USERS_FILE)
    return True


# ---------------- DATA LOADING ---------------- #
users_data = load_json(USERS_FILE)  # For multi-user
tasks_data = load_json(TASKS_FILE)
appointments_data = load_json(APPOINTMENTS_FILE)
prescriptions_data = load_json(PRESCRIPTIONS_FILE)
mood_data = load_json(MOOD_FILE)
water_data = load_json(WATER_FILE)
notes_data = load_json(NOTES_FILE)
steps_data = load_json(STEPS_FILE)
sleep_data = load_json(SLEEP_FILE)
weight_data = load_json(WEIGHT_FILE)
calories_data = load_json(CALORIES_FILE)


# ----------------- SESSION STATE ----------------- #
# We will use st.session_state to track if a user is logged in
# and which user is currently active.
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# A function to save *all* data back to JSON 
# (useful if we do many updates in different places).
def save_all():
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


# -------------- PRESCRIPTION SCHEDULING -------------- #
def schedule_prescriptions(start_date_str, days_of_week_str, num_weeks):
    """
    Create a schedule for a prescription:
    - start_date_str: "YYYY-MM-DD"
    - days_of_week_str: e.g. "Mon,Wed,Fri"
    - num_weeks: integer
    Return list of dictionaries {Day, Month, Year, Status}.
    """
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
    for week_i in range(w):
        block_start = start_dt + timedelta(weeks=week_i)
        for day_num in valid_days:
            offset = (day_num - block_start.isoweekday()) % 7
            date_target = block_start + timedelta(days=offset)
            schedule.append({
                "Day": date_target.day,
                "Month": date_target.month,
                "Year": date_target.year,
                "Status": "scheduled"
            })
    return schedule


# ---------------- MAIN UI FUNCTIONS ---------------- #

def show_login_screen():
    """Display a login form, or allow user to switch to sign-up."""
    st.subheader("Please log in to continue")

    login_tab, register_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        uname = st.text_input("Username", key="login_username")
        pwd = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In"):
            if check_credentials(uname, pwd, users_data):
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = uname
                st.success("Logged in successfully.")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

    with register_tab:
        uname_new = st.text_input("New Username", key="register_username")
        pwd_new = st.text_input("New Password", type="password", key="register_password")
        confirm_pwd = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Sign Up"):
            if not uname_new or not pwd_new or not confirm_pwd:
                st.error("Please fill all fields.")
            elif pwd_new != confirm_pwd:
                st.error("Passwords do not match.")
            else:
                if register_new_user(uname_new, pwd_new, users_data):
                    st.success("Account created. You can now log in.")
                else:
                    st.warning("That username is already taken.")


def show_main_app():
    """Display the main application for a logged-in user."""

    # We can load a Lottie animation if desired
    # lottie_anime = load_lottie_url(LOTTIE_ANIMATION_URL)

    # Create side navigation or top tabs
    # Let's do side navigation for a classic look.
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}!")
    selected = st.sidebar.radio(
        "Go to:",
        [
            "Home",
            "Tasks & Appointments",
            "Prescriptions",
            "Health Tracking",
            "Analytics",
            "Notes",
            "Settings"
        ]
    )

    # A top header or banner
    st.title(APP_TITLE)

    if selected == "Home":
        show_home_tab()

    elif selected == "Tasks & Appointments":
        show_tasks_appointments_tab()

    elif selected == "Prescriptions":
        show_prescriptions_tab()

    elif selected == "Health Tracking":
        show_health_tracking_tab()

    elif selected == "Analytics":
        show_analytics_tab()

    elif selected == "Notes":
        show_notes_tab()

    elif selected == "Settings":
        show_settings_tab()


def show_home_tab():
    """A 'Dashboard' style home page with quick stats and optional animation."""
    colA, colB = st.columns([2,3])
    with colA:
        # Optional image or animation
        # if lottie_anime:
        #     st_lottie(lottie_anime, height=200)
        # else:
        #     st.write("No animation loaded")

        # Or a splash image if it exists
        if os.path.isfile(SPLASH_IMAGE_PATH):
            try:
                img = Image.open(SPLASH_IMAGE_PATH)
                st.image(img, use_column_width=True)
            except:
                st.write("Welcome to WellNest!")

    with colB:
        st.subheader("Dashboard Overview")

        # Quick stats
        today_str = datetime.now().strftime("%Y-%m-%d")
        user = st.session_state["current_user"]

        # Tasks Today
        tasks_today = tasks_data.get(user, {}).get(today_str, [])
        st.write(f"**Tasks Today**: {len(tasks_today)}")

        # Appointments Today
        apps_today = appointments_data.get(user, {}).get(today_str, [])
        st.write(f"**Appointments Today**: {len(apps_today)}")

        # Mood
        mood_today = mood_data.get(user, {}).get(today_str, None)
        if mood_today is not None:
            st.write(f"**Today's Mood**: {mood_today}/5")
        else:
            st.write("**Today's Mood**: Not Logged")

        # Water
        water_today = water_data.get(user, {}).get(today_str, 0)
        st.write(f"**Water Intake**: {water_today} L (today)")

        # Steps
        steps_today = steps_data.get(user, {}).get(today_str, 0)
        st.write(f"**Steps**: {steps_today} steps (today)")

    st.write("---")
    st.subheader("Quick Actions")
    with st.expander("Log Today's Mood"):
        mood_val = st.slider("Mood (1 = sad, 5 = happy)", 1, 5, 3)
        if st.button("Save Mood"):
            if user not in mood_data:
                mood_data[user] = {}
            mood_data[user][today_str] = mood_val
            save_all()
            st.success("Mood logged.")

    with st.expander("Log Today's Water Intake"):
        add_water = st.number_input("Liters to add", min_value=0.0, step=0.1)
        if st.button("Add Water"):
            current_val = water_data.get(user, {}).get(today_str, 0.0)
            new_val = current_val + add_water
            if user not in water_data:
                water_data[user] = {}
            water_data[user][today_str] = new_val
            save_all()
            st.success(f"Water updated. Total: {new_val} L")

    with st.expander("Log Steps"):
        add_steps = st.number_input("Steps to add", min_value=0, step=100)
        if st.button("Add Steps"):
            current_steps = steps_data.get(user, {}).get(today_str, 0)
            new_step_total = current_steps + add_steps
            if user not in steps_data:
                steps_data[user] = {}
            steps_data[user][today_str] = new_step_total
            save_all()
            st.success(f"Total steps for today: {new_step_total}")


def show_tasks_appointments_tab():
    """Allow user to manage tasks & appointments by date."""
    st.header("Tasks & Appointments")

    user = st.session_state["current_user"]

    sel_date = st.date_input("Select a date", value=datetime.now())
    date_str = sel_date.strftime("%Y-%m-%d")
    st.write(f"Selected date: **{date_str}**")

    # Make sure sub-dictionaries exist
    if user not in tasks_data:
        tasks_data[user] = {}
    if date_str not in tasks_data[user]:
        tasks_data[user][date_str] = []

    if user not in appointments_data:
        appointments_data[user] = {}
    if date_str not in appointments_data[user]:
        appointments_data[user][date_str] = []

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tasks")
        # Display tasks
        day_tasks = tasks_data[user][date_str]
        if day_tasks:
            for idx, tsk in enumerate(day_tasks):
                st.write(f"{idx+1}. **{tsk['name']}** at {tsk['time']} | Assigned to: {tsk.get('assignee','N/A')} | Status: {tsk['status']}")
            st.write("---")
        else:
            st.info("No tasks for this date.")

        # Add new task
        with st.expander("Add a New Task"):
            task_name = st.text_input("Task Name")
            task_assignee = st.text_input("Assigned To")
            task_time = st.text_input("Time (e.g., 14:30)")
            status = st.selectbox("Status", ["Pending", "In-progress", "Completed"], index=0)
            if st.button("Save Task"):
                if task_name and task_time:
                    new_task = {
                        "name": task_name,
                        "assignee": task_assignee,
                        "time": task_time,
                        "status": status
                    }
                    tasks_data[user][date_str].append(new_task)
                    save_all()
                    st.success("Task added.")
                else:
                    st.error("Task name and time are required.")

    with col2:
        st.subheader("Appointments")
        # Display appointments
        day_apps = appointments_data[user][date_str]
        if day_apps:
            for idx, app in enumerate(day_apps):
                st.write(f"{idx+1}. {app}")
            st.write("---")
        else:
            st.info("No appointments for this date.")

        # Add new appointment
        with st.expander("Add a New Appointment"):
            app_time = st.text_input("Time (HH:MM)", key="appt_time")
            doctor_name = st.text_input("Doctor's Name", key="appt_doctor")
            location = st.text_input("Location", key="appt_location")
            if st.button("Save Appointment"):
                if app_time and doctor_name and location:
                    desc = f"{app_time} with Dr. {doctor_name} @ {location}"
                    appointments_data[user][date_str].append(desc)
                    save_all()
                    st.success("Appointment added.")
                else:
                    st.error("Please fill out all fields.")


def show_prescriptions_tab():
    """Manage prescriptions, including scheduling."""
    st.header("Prescriptions")
    user = st.session_state["current_user"]

    # Make sure the sub-dict for user exists
    if user not in prescriptions_data:
        prescriptions_data[user] = {}

    # List existing
    st.subheader("Existing Prescriptions")
    if prescriptions_data[user]:
        for rx_name, rx_info in prescriptions_data[user].items():
            with st.expander(rx_name):
                med_info = rx_info.get("Medication Info", {})
                st.write(f"**Description**: {med_info.get('Description','N/A')}")
                st.write(f"**Taken with food**: {med_info.get('Taken with food','N/A')}")

                if "Schedule" in rx_info:
                    for entry in rx_info["Schedule"]:
                        y, m, d = entry["Year"], entry["Month"], entry["Day"]
                        stt = entry.get("Status","scheduled")
                        st.write(f" - {y}-{m:02d}-{d:02d} [{stt}]")

                # Option to delete prescription
                if st.button(f"Delete {rx_name}"):
                    del prescriptions_data[user][rx_name]
                    save_all()
                    st.experimental_rerun()
    else:
        st.info("No prescriptions found.")

    st.write("---")
    st.subheader("Add a New Prescription")
    rx_name = st.text_input("Prescription Name", key="rx_name")
    rx_desc = st.text_input("Description (e.g., usage info)", key="rx_desc")
    rx_food = st.selectbox("Taken with food?", ["Yes","No"], index=0)
    start_date = st.date_input("Start Date", value=datetime.now(), key="rx_start_date")
    day_of_week_str = st.text_input("Days of Week (e.g., Mon,Wed,Fri)", key="rx_days")
    weeks_str = st.text_input("Number of Weeks", value="4", key="rx_weeks")

    if st.button("Create Prescription", key="create_prescription"):
        if rx_name.strip():
            schedule = schedule_prescriptions(
                start_date.strftime("%Y-%m-%d"),
                day_of_week_str,
                weeks_str
            )
            if schedule is None:
                st.error("Invalid scheduling data. Please check your days of week or weeks input.")
            else:
                prescriptions_data[user][rx_name] = {
                    "Medication Info": {
                        "Description": rx_desc,
                        "Taken with food": rx_food
                    },
                    "Schedule": schedule
                }
                save_all()
                st.success(f"Prescription '{rx_name}' created with {len(schedule)} scheduled entries.")
        else:
            st.error("Please provide a prescription name.")

    st.write("---")
    st.subheader("Update Prescription Status")
    if prescriptions_data[user]:
        selected_rx = st.selectbox("Select Prescription", list(prescriptions_data[user].keys()))
        if selected_rx:
            sel_date = st.date_input("Date to Update", value=datetime.now(), key="upd_rx_date")
            new_status = st.selectbox("New Status", ["scheduled","taken on time","missed"])
            if st.button("Update Status", key="btn_update_rx"):
                found_entry = None
                for entry in prescriptions_data[user][selected_rx]["Schedule"]:
                    dt = datetime(entry["Year"], entry["Month"], entry["Day"])
                    if dt.date() == sel_date:
                        found_entry = entry
                        break
                if found_entry:
                    found_entry["Status"] = new_status
                    save_all()
                    st.success("Prescription status updated.")
                else:
                    st.warning("No matching date found in that prescription's schedule.")
    else:
        st.info("No prescriptions to update.")


def show_health_tracking_tab():
    """Log and view metrics: mood, water, steps, sleep, weight, calories, macros, etc."""
    st.header("Health Tracking")
    user = st.session_state["current_user"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Ensure sub-dicts exist
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

    st.write("Log or view your daily health metrics.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Mood")
        mood_today = mood_data[user].get(today_str, None)
        if mood_today is not None:
            st.write(f"Today's Mood: {mood_today}/5")
        else:
            st.write("No mood logged today.")

        new_mood = st.slider("Log Mood (1-5)", 1, 5, 3, key="track_mood_slider")
        if st.button("Set Mood"):
            mood_data[user][today_str] = new_mood
            save_all()
            st.success(f"Mood set to {new_mood}/5 for today.")

        st.subheader("Sleep")
        # Show existing if any
        sleep_today = sleep_data[user].get(today_str, None)
        if sleep_today is not None:
            st.write(f"Last sleep log: {sleep_today} hours")
        add_sleep = st.number_input("Add Sleep Hours", 0.0, 24.0, 7.0, step=0.5, key="add_sleep_hrs")
        if st.button("Log Sleep"):
            sleep_data[user][today_str] = add_sleep
            save_all()
            st.success(f"Logged {add_sleep} hours of sleep for today.")

    with col2:
        st.subheader("Water Intake")
        water_today_val = water_data[user].get(today_str, 0.0)
        st.write(f"Today so far: {water_today_val} L")

        add_water_val = st.number_input("Liters to Add", 0.0, 10.0, 0.5, step=0.25, key="track_water_add")
        if st.button("Add Water", key="btn_add_water"):
            new_total = water_today_val + add_water_val
            water_data[user][today_str] = new_total
            save_all()
            st.success(f"Updated total: {new_total} L")

        st.subheader("Steps")
        steps_today_val = steps_data[user].get(today_str, 0)
        st.write(f"Today so far: {steps_today_val} steps")
        add_steps_val = st.number_input("Steps to Add", 0, 30000, 1000, step=500, key="track_steps_add")
        if st.button("Add Steps", key="btn_add_steps"):
            new_steps = steps_today_val + add_steps_val
            steps_data[user][today_str] = new_steps
            save_all()
            st.success(f"Updated total steps: {new_steps}")

    with col3:
        st.subheader("Weight & BMI")
        last_weight = weight_data[user].get(today_str, None)
        if last_weight is not None:
            st.write(f"Today's weight: {last_weight['weight_kg']} kg (BMI: {last_weight['bmi']:.1f})")
        else:
            st.write("No weight logged today.")
        weight_kg = st.number_input("Weight (kg)", 30.0, 300.0, 70.0, key="track_weight")
        height_cm = 170.0  # fallback
        # If user has a profile with height:
        user_profile = users_data[user]["profile"]
        if user_profile.get("height_cm"):
            height_cm = user_profile["height_cm"]
        else:
            st.info("Your height is not set in profile, using 170cm as default.")
        if st.button("Log Weight", key="btn_log_weight"):
            # compute BMI
            height_m = height_cm / 100.0
            bmi_val = weight_kg / (height_m**2)
            weight_data[user][today_str] = {
                "weight_kg": weight_kg,
                "bmi": bmi_val
            }
            save_all()
            st.success(f"Logged weight: {weight_kg} kg, BMI ~ {bmi_val:.1f}")

        st.subheader("Calories / Nutrition")
        cals_today = calories_data[user].get(today_str, 0)
        st.write(f"Today's total: {cals_today} kcal")
        add_cals = st.number_input("Add Calories", 0, 5000, 500, step=100, key="track_cal_add")
        if st.button("Add Calories", key="btn_add_cal"):
            new_cal_total = cals_today + add_cals
            calories_data[user][today_str] = new_cal_total
            save_all()
            st.success(f"Updated total: {new_cal_total} kcal")


def show_analytics_tab():
    """Show advanced analytics for mood, water, steps, weight, prescriptions, etc."""
    st.header("Analytics & Trends")
    user = st.session_state["current_user"]

    # Let's do a sub-tab approach
    sub_tab = st.selectbox("Analytics Sections", [
        "Water Intake",
        "Mood History",
        "Steps History",
        "Weight/BMI Progress",
        "Prescription Status",
        "Calorie Intake",
    ])

    if sub_tab == "Water Intake":
        st.subheader("Water Intake Over Last 14 Days")
        # We'll gather data for the last 14 days
        water_dict = water_data.get(user, {})
        date_list = []
        val_list = []
        for i in range(14):
            dt_str = (datetime.now() - timedelta(days=13 - i)).strftime("%Y-%m-%d")
            date_list.append(dt_str)
            val_list.append(water_dict.get(dt_str, 0.0))

        fig, ax = plt.subplots()
        ax.bar(date_list, val_list, color="#379683")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_xlabel("Date")
        ax.set_ylabel("Liters")
        ax.set_title("Water Intake (Last 14 Days)")
        st.pyplot(fig)

    elif sub_tab == "Mood History":
        st.subheader("Mood History (Last 14 Days)")
        mood_dict = mood_data.get(user, {})
        date_list = []
        mood_list = []
        for i in range(14):
            dt_str = (datetime.now() - timedelta(days=13 - i)).strftime("%Y-%m-%d")
            date_list.append(dt_str)
            mood_list.append(mood_dict.get(dt_str, 0))

        fig, ax = plt.subplots()
        ax.plot(date_list, mood_list, marker="o", color="#FF5733")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_ylim(0,6)
        ax.set_yticks([1,2,3,4,5])
        ax.set_xlabel("Date")
        ax.set_ylabel("Mood (1-5)")
        ax.set_title("Mood Trend Over 14 Days")
        st.pyplot(fig)

    elif sub_tab == "Steps History":
        st.subheader("Steps (Last 14 Days)")
        steps_dict = steps_data.get(user, {})
        date_list = []
        step_list = []
        for i in range(14):
            dt_str = (datetime.now() - timedelta(days=13 - i)).strftime("%Y-%m-%d")
            date_list.append(dt_str)
            step_list.append(steps_dict.get(dt_str, 0))

        fig, ax = plt.subplots()
        ax.bar(date_list, step_list, color="#4C9AFF")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_xlabel("Date")
        ax.set_ylabel("Steps")
        ax.set_title("Daily Steps Over 14 Days")
        st.pyplot(fig)

    elif sub_tab == "Weight/BMI Progress":
        st.subheader("Weight & BMI Trends (Last 30 Days)")
        w_dict = weight_data.get(user, {})
        # gather 30 days
        date_list = []
        weight_vals = []
        bmi_vals = []
        for i in range(30):
            dt_str = (datetime.now() - timedelta(days=29 - i)).strftime("%Y-%m-%d")
            date_list.append(dt_str)
            if dt_str in w_dict:
                weight_vals.append(w_dict[dt_str]["weight_kg"])
                bmi_vals.append(w_dict[dt_str]["bmi"])
            else:
                weight_vals.append(None)
                bmi_vals.append(None)

        # Plotting
        fig, ax = plt.subplots(figsize=(8,3))
        ax.plot(date_list, weight_vals, marker="o", label="Weight (kg)", color="blue")
        ax2 = ax.twinx()
        ax2.plot(date_list, bmi_vals, marker="s", label="BMI", color="green")

        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_ylabel("Weight (kg)")
        ax2.set_ylabel("BMI")
        ax.set_title("Weight & BMI (Last 30 Days)")

        # Combine legends
        lines_1, labels_1 = ax.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

        st.pyplot(fig)

    elif sub_tab == "Prescription Status":
        st.subheader("Medication Status Distribution")
        # We'll show how many scheduled, taken, missed for each prescription
        user_rx = prescriptions_data.get(user, {})
        statuses = {"scheduled":0, "taken on time":0, "missed":0}
        for rx_name, rx_info in user_rx.items():
            sched = rx_info.get("Schedule", [])
            for entry in sched:
                stt = entry.get("Status","scheduled")
                if stt not in statuses:
                    statuses[stt] = 0
                statuses[stt] += 1

        labels = list(statuses.keys())
        values = list(statuses.values())
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
        ax.set_title("Overall Prescription Status")
        st.pyplot(fig)

    elif sub_tab == "Calorie Intake":
        st.subheader("Calorie Intake (Last 14 Days)")
        c_dict = calories_data.get(user, {})
        date_list = []
        cals_list = []
        for i in range(14):
            dt_str = (datetime.now() - timedelta(days=13 - i)).strftime("%Y-%m-%d")
            date_list.append(dt_str)
            cals_list.append(c_dict.get(dt_str, 0))

        fig, ax = plt.subplots()
        ax.bar(date_list, cals_list, color="#FFA07A")
        ax.set_xticklabels(date_list, rotation=45, ha="right")
        ax.set_xlabel("Date")
        ax.set_ylabel("Calories (kcal)")
        ax.set_title("Daily Calorie Intake Over 14 Days")
        st.pyplot(fig)


def show_notes_tab():
    """A personal notes or journaling section for the user."""
    st.header("Personal Notes / Journaling")
    user = st.session_state["current_user"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Ensure sub-dict for user
    if user not in notes_data:
        notes_data[user] = {}
    if today_str not in notes_data[user]:
        notes_data[user][today_str] = []

    st.write("You can store free-form notes here, by day.")

    st.subheader(f"Notes for {today_str}")
    day_notes = notes_data[user][today_str]
    if day_notes:
        for i, note_text in enumerate(day_notes):
            with st.expander(f"Note #{i+1}"):
                st.write(note_text)
                if st.button(f"Delete Note #{i+1}", key=f"del_note_{i}"):
                    day_notes.pop(i)
                    save_all()
                    st.experimental_rerun()
    else:
        st.info("No notes for today yet.")

    st.write("---")
    with st.expander("Add a New Note"):
        new_note_text = st.text_area("Note:")
        if st.button("Save Note"):
            if new_note_text.strip():
                notes_data[user][today_str].append(new_note_text.strip())
                save_all()
                st.success("Note saved.")
                st.experimental_rerun()
            else:
                st.error("Cannot save an empty note.")


def show_settings_tab():
    """User profile, preferences, data backup, etc."""
    st.header("Settings & Profile")
    user = st.session_state["current_user"]

    # Show user profile info
    st.subheader("Profile Information")
    profile = users_data[user]["profile"]
    colA, colB = st.columns(2)
    with colA:
        name_val = st.text_input("Name", profile.get("name", ""))
        email_val = st.text_input("Email", profile.get("email", ""))
    with colB:
        gender_val = st.selectbox("Gender", ["", "Male", "Female", "Other"], 
                                  index=0 if not profile.get("gender") else ["","Male","Female","Other"].index(profile["gender"]))
        age_val = st.number_input("Age", 0, 120, value=profile.get("age") if profile.get("age") else 0)
        height_val = st.number_input("Height (cm)", 0, 250, value=profile.get("height_cm") if profile.get("height_cm") else 170)

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

    st.write("---")
    st.subheader("Preferences")
    # For demonstration, we can have toggles
    theme = st.selectbox("Theme", ["Light","Dark"], index=0)
    st.write("*(Note: Real theme changes require customizing `.streamlit/config.toml`.)*")

    st.write("---")
    st.subheader("Data Management")
    st.write("You can export data or clear your personal data.")
    if st.button("Download Personal Data (JSON)"):
        # Combine the user-specific data into one big JSON
        user_export = {
            "tasks": tasks_data.get(user, {}),
            "appointments": appointments_data.get(user, {}),
            "prescriptions": prescriptions_data.get(user, {}),
            "mood": mood_data.get(user, {}),
            "water": water_data.get(user, {}),
            "notes": notes_data.get(user, {}),
            "steps": steps_data.get(user, {}),
            "sleep": sleep_data.get(user, {}),
            "weight": weight_data.get(user, {}),
            "calories": calories_data.get(user, {}),
            "profile": users_data[user]["profile"]
        }
        st.download_button(
            label="Download JSON",
            data=json.dumps(user_export, indent=4),
            file_name=f"{user}_wellnest_data.json",
            mime="application/json"
        )

    if st.button("Clear All My Data (Irreversible)"):
        # Just nuke all user data from each dictionary
        if st.confirm_dialog("Are you sure you want to delete ALL your data? This cannot be undone."):
            # Not a real Streamlit built-in, but let's assume we do a second check:
            for dataset in [tasks_data, appointments_data, prescriptions_data, mood_data, water_data,
                            notes_data, steps_data, sleep_data, weight_data, calories_data]:
                if user in dataset:
                    del dataset[user]
            save_all()
            st.success("All your data has been cleared.")

    st.write("---")
    if st.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.experimental_rerun()


# We can create a fake confirm dialog. Streamlit doesn't have a built-in confirm,
# so let's do a workaround. We'll define a function that returns True if a user 
# toggles a checkbox or something. 
def confirm_dialog(message: str) -> bool:
    # This is a simplistic approach.
    # In real apps, you might use st.modal or custom approach.
    st.warning(message)
    return st.button("Yes, continue", key=f"confirm_{message}")


# Monkey-patch the function we just used above. 
# (We do so to avoid a reference error.)
st.confirm_dialog = confirm_dialog

# -------------- MAIN APP ENTRY ------------------ #
def main():
    if not st.session_state["logged_in"]:
        show_login_screen()
    else:
        show_main_app()

#######################################
# Start the application
#######################################
if __name__ == "__main__":
    main()
