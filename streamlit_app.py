import os
import json
import datetime
from datetime import datetime, timedelta

import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image

# ---------------------------------------------------------
#                 GLOBAL CONFIG & CONSTANTS
# ---------------------------------------------------------
st.set_page_config(page_title="WellNest", layout="wide")
APP_TITLE = "WellNest"

# OPTIONAL: Provide an image path for your "splash" or banner on the Home page
SPLASH_IMAGE_PATH = "path/to/your_splash_image.png"  # Change if you have an image

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# JSON file paths
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.json")
PRESCRIPTIONS_FILE = os.path.join(DATA_DIR, "prescriptions.json")
MOOD_FILE = os.path.join(DATA_DIR, "mood.json")
WATER_FILE = os.path.join(DATA_DIR, "water.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")

# ---------------------------------------------------------
#                    DATA FUNCTIONS
# ---------------------------------------------------------
def load_json(path):
    """Load JSON data safely, returning {} if invalid or missing."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_json(data, path):
    """Write JSON data to file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------
#             INITIALIZE (LOAD) ALL DATA
# ---------------------------------------------------------
tasks = load_json(TASKS_FILE)
appointments = load_json(APPOINTMENTS_FILE)
prescriptions = load_json(PRESCRIPTIONS_FILE)
mood_logs = load_json(MOOD_FILE)
water_logs = load_json(WATER_FILE)
notes = load_json(NOTES_FILE)

# ---------------------------------------------------------
#                   HELPER FUNCTIONS
# ---------------------------------------------------------
def save_all_data():
    """Save all dictionaries to their respective JSON files."""
    save_json(tasks, TASKS_FILE)
    save_json(appointments, APPOINTMENTS_FILE)
    save_json(prescriptions, PRESCRIPTIONS_FILE)
    save_json(mood_logs, MOOD_FILE)
    save_json(water_logs, WATER_FILE)
    save_json(notes, NOTES_FILE)

# A small function to automatically schedule prescription dates, 
# similar to your Tkinter logic:
def create_prescription_schedule(start_date_str, days_of_week_str, num_weeks):
    """
    Return a list of dictionaries with {Day, Month, Year, Status}
    for each date in the schedule.
    """
    # Validate date
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        return None
    
    # Validate number of weeks
    try:
        num_weeks = int(num_weeks)
    except ValueError:
        return None
    
    # Map day names to weekday numbers (Monday=1 ... Sunday=7)
    day_map = {
        "mon": 1, "tue": 2, "wed": 3,
        "thu": 4, "fri": 5, "sat": 6, "sun": 7
    }
    raw_days = [d.strip().lower() for d in days_of_week_str.split(",") if d.strip()]
    valid_daynums = [day_map[d] for d in raw_days if d in day_map]

    schedule = []
    for w in range(num_weeks):
        # We'll get each 'week-block' start
        block_start = start_dt + timedelta(weeks=w)
        # For each day in valid_daynums, compute the date
        for dnum in valid_daynums:
            offset = (dnum - block_start.isoweekday()) % 7
            p_date = block_start + timedelta(days=offset)
            schedule.append({
                "Day": p_date.day,
                "Month": p_date.month,
                "Year": p_date.year,
                "Status": "scheduled"
            })
    return schedule

# For medication status charts, we might map statuses to numeric.
STATUS_MAP = {
    "scheduled": 0,
    "taken on time": 1,
    "missed": -1
}

# ---------------------------------------------------------
#                   STREAMLIT UI
# ---------------------------------------------------------
st.title(APP_TITLE + " – A Web-Based Wellness Tracker")

# Create horizontal tabs (new in Streamlit > 1.10),
# or use the sidebar (up to you). Here we'll demonstrate tabs:
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Home",
    "Calendar & Tasks",
    "Prescriptions",
    "Health Stats",
    "Settings"
])

# ---------------------------------------------------------
#                      TAB 1: HOME
# ---------------------------------------------------------
with tab1:
    col1, col2 = st.columns([1,2])
    with col1:
        # Attempt to show a splash/banner image
        try:
            if os.path.isfile(SPLASH_IMAGE_PATH):
                splash_img = Image.open(SPLASH_IMAGE_PATH)
                st.image(splash_img, use_column_width=True)
            else:
                st.subheader("Welcome to WellNest!")
        except:
            st.subheader("Welcome to WellNest!")

        st.write("""
            This web version replicates many features from the desktop app:
            - Task Management  
            - Appointments  
            - Prescriptions (including scheduling)  
            - Mood & Water Tracking  
            - Analytics & Charts  
        """)
    with col2:
        # Show today's quick stats
        today_str = datetime.now().strftime("%Y-%m-%d")
        st.subheader("Today's Quick Stats:")

        num_tasks_today = len(tasks.get(today_str, []))
        st.write(f"- **Tasks Today**: {num_tasks_today}")

        water_today = water_logs.get(today_str, 0.0)
        st.write(f"- **Water Intake**: {water_today} L (today)")

        mood_today = mood_logs.get(today_str, None)
        if mood_today is not None:
            st.write(f"- **Mood** (1–5): {mood_today}")
        else:
            st.write("- **Mood**: No entry logged today.")

        st.write("---")

        st.subheader("Quick Actions")
        # Quick Mood Log
        with st.expander("Log Today's Mood"):
            mood_val = st.slider("Select Mood", 1, 5, 3)
            if st.button("Save Mood"):
                mood_logs[today_str] = mood_val
                save_json(mood_logs, MOOD_FILE)
                st.success(f"Saved today's mood as {mood_val}/5.")

        # Quick Water Log
        with st.expander("Add Water Intake"):
            water_val = st.number_input("Liters of water to add", 0.0, 20.0, step=0.1)
            if st.button("Add to today's water total"):
                water_logs[today_str] = round(water_logs.get(today_str, 0.0) + water_val, 2)
                save_all_data()
                st.success(f"Added {water_val} L. Total for today: {water_logs[today_str]} L")

# ---------------------------------------------------------
#               TAB 2: CALENDAR & TASKS
# ---------------------------------------------------------
with tab2:
    st.header("Calendar & Task / Appointment Management")

    # Let user pick a date
    sel_date = st.date_input("Select date for tasks or appointments", value=datetime.now())
    date_str = sel_date.strftime("%Y-%m-%d")
    st.write(f"Selected date: **{date_str}**")

    st.subheader("Tasks")
    # Show tasks for this date
    day_tasks = tasks.get(date_str, [])

    if day_tasks:
        for i, task in enumerate(day_tasks):
            st.write(f"{i+1}. **{task['name']}** at {task['time']} (Assigned to: {task.get('assignee','N/A')})")
        st.write("---")
    else:
        st.info("No tasks found for this date.")

    # Add a new task (with more fields, like assignee)
    with st.expander("Add a new task"):
        task_name = st.text_input("Task Name")
        task_assignee = st.text_input("Assigned To")
        task_time = st.text_input("Time (e.g., 14:30)")
        if st.button("Save Task"):
            if task_name and task_time:
                if date_str not in tasks:
                    tasks[date_str] = []
                tasks[date_str].append({
                    "name": task_name,
                    "assignee": task_assignee,
                    "time": task_time,
                    "status": "In-progress"
                })
                save_all_data()
                st.success("Task added successfully!")
            else:
                st.error("Please provide at least a task name and time.")

    st.subheader("Appointments")
    day_apps = appointments.get(date_str, [])

    if day_apps:
        for i, app in enumerate(day_apps):
            st.write(f"{i+1}. **{app}**")
        st.write("---")
    else:
        st.info("No appointments found for this date.")

    # Add a new appointment
    with st.expander("Add a new appointment"):
        app_time = st.text_input("Appointment Time (HH:MM)")
        doc_name = st.text_input("Doctor's Name")
        location = st.text_input("Location")
        if st.button("Save Appointment"):
            if app_time and doc_name and location:
                if date_str not in appointments:
                    appointments[date_str] = []
                desc = f"{app_time} with Dr. {doc_name} at {location}"
                appointments[date_str].append(desc)
                save_all_data()
                st.success("Appointment added successfully!")
            else:
                st.error("Please fill all fields for the appointment.")

# ---------------------------------------------------------
#             TAB 3: PRESCRIPTIONS (ADVANCED)
# ---------------------------------------------------------
with tab3:
    st.header("Manage Prescriptions")
    st.write("""
        Here you can store detailed prescription info, including 
        medication schedule across specific days of the week.
    """)

    # Show existing prescriptions
    st.subheader("Existing Prescriptions")
    if prescriptions:
        for pname, pinfo in prescriptions.items():
            with st.expander(pname):
                med_info = pinfo.get("Medication Info", {})
                st.write(f"**Description**: {med_info.get('Description', 'N/A')}")
                st.write(f"**Taken with food**: {med_info.get('Taken with food', 'N/A')}")
                
                # Show each scheduled date
                if "Prescription" in pinfo:
                    for entry in pinfo["Prescription"]:
                        y, m, d = entry["Year"], entry["Month"], entry["Day"]
                        status = entry.get("Status", "scheduled")
                        st.write(f" - {y}-{m:02d}-{d:02d} [{status}]")

                # Buttons to update or delete
                if st.button(f"Delete '{pname}'"):
                    del prescriptions[pname]
                    save_all_data()
                    st.experimental_rerun()
    else:
        st.info("No prescriptions found.")

    st.write("---")
    st.subheader("Add New Prescription")
    rx_name = st.text_input("Prescription Name (e.g. 'Lipitor')")
    rx_desc = st.text_input("Medication Description (e.g. 'Used for cholesterol')")
    rx_food = st.text_input("Taken with food? (Yes/No)", value="Yes")

    # We'll let user pick a start date, days of the week, and # of weeks
    rx_start_date = st.date_input("Start Date", value=datetime.now())
    rx_days_str = st.text_input("Days of Week (e.g. Mon,Wed,Fri)", value="Mon,Wed,Fri")
    rx_num_weeks = st.text_input("Number of Weeks", value="4")

    if st.button("Create Prescription"):
        if rx_name:
            schedule = create_prescription_schedule(
                start_date_str=rx_start_date.strftime("%Y-%m-%d"),
                days_of_week_str=rx_days_str,
                num_weeks=rx_num_weeks
            )
            if schedule is None:
                st.error("Invalid scheduling data. Check date format or number of weeks.")
            else:
                prescriptions[rx_name] = {
                    "Medication Info": {
                        "Description": rx_desc,
                        "Taken with food": rx_food
                    },
                    "Prescription": schedule
                }
                save_all_data()
                st.success(f"Prescription '{rx_name}' added with {len(schedule)} scheduled dates.")
        else:
            st.error("Please enter a prescription name.")

    st.write("---")
    st.subheader("Update Prescription Status")
    st.write("Select a prescription, then pick the exact date to mark as 'taken on time' or 'missed'.")

    # Let user pick from existing
    if prescriptions:
        rx_choice = st.selectbox("Prescription", list(prescriptions.keys()))
        rx_date = st.date_input("Date to update", value=datetime.now())
        new_status = st.selectbox("Status", ["taken on time", "missed"])

        if st.button("Update Status"):
            # Find date in that prescription's schedule
            found = False
            for entry in prescriptions[rx_choice]["Prescription"]:
                dt = datetime(entry["Year"], entry["Month"], entry["Day"])
                if dt.date() == rx_date:
                    entry["Status"] = new_status
                    found = True
                    break
            if found:
                save_all_data()
                st.success(f"Status updated to '{new_status}' for {rx_choice} on {rx_date}.")
            else:
                st.warning("No matching date in that prescription schedule.")
    else:
        st.info("No prescriptions to update.")

# ---------------------------------------------------------
#             TAB 4: HEALTH STATS & ANALYTICS
# ---------------------------------------------------------
with tab4:
    st.header("Health Stats & Analytics")

    # WATER INTAKE CHART (last 7 days)
    st.subheader("Water Intake (Last 7 Days)")
    today = datetime.now()
    last_7_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    last_7_days.reverse()  # oldest to newest

    daily_intakes = [water_logs.get(d, 0) for d in last_7_days]

    fig1, ax1 = plt.subplots(figsize=(6,3))
    ax1.bar(last_7_days, daily_intakes, color="#379683")
    ax1.set_ylabel("Liters")
    ax1.set_title("Water Intake (Last 7 Days)")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    # MOOD (just show today's, or we can do more advanced chart if you store more data)
    st.write("---")
    st.subheader("Today's Mood")
    today_mood = mood_logs.get(datetime.now().strftime("%Y-%m-%d"))
    if today_mood is not None:
        st.write(f"**Mood**: {today_mood}/5")
    else:
        st.write("No mood entry for today.")

    # MEDICATION STATUS CHART (Scatter or timeline)
    st.write("---")
    st.subheader("Medication Status Overview")
    # Gather all scheduled meds from prescriptions
    all_dates_taken = []
    all_dates_missed = []
    all_dates_scheduled = []

    for med_name, details in prescriptions.items():
        for entry in details.get("Prescription", []):
            try:
                d = datetime(entry["Year"], entry["Month"], entry["Day"])
                stt = entry.get("Status", "scheduled")
                if stt == "taken on time":
                    all_dates_taken.append(d)
                elif stt == "missed":
                    all_dates_missed.append(d)
                else:
                    all_dates_scheduled.append(d)
            except ValueError:
                pass

    if len(all_dates_taken) + len(all_dates_missed) + len(all_dates_scheduled) == 0:
        st.info("No medication status data to display yet.")
    else:
        fig2, ax2 = plt.subplots(figsize=(6,3))
        if all_dates_taken:
            ax2.scatter(all_dates_taken, [1]*len(all_dates_taken), color="green", marker="o", label="Taken")
        if all_dates_missed:
            ax2.scatter(all_dates_missed, [0]*len(all_dates_missed), color="red", marker="x", label="Missed")
        if all_dates_scheduled:
            ax2.scatter(all_dates_scheduled, [-1]*len(all_dates_scheduled), color="blue", marker=".", label="Scheduled")

        ax2.set_yticks([-1, 0, 1])
        ax2.set_yticklabels(["Scheduled", "Missed", "Taken"])  
        ax2.set_title("Medication Status Timeline")
        ax2.legend()
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        st.pyplot(fig2)

# ---------------------------------------------------------
#                 TAB 5: SETTINGS
# ---------------------------------------------------------
with tab5:
    st.header("Settings & Data")
    st.write("Manage user information, data storage, or exit. (In a browser, 'exit' just means closing tab.)")

    st.subheader("User Profile (Example)")
    st.write("Name: Jane Doe")
    st.write("Email: jane.doe@example.com")

    st.write("---")
    st.subheader("Backup & Export Data")
    st.write("""
        All data is stored in JSON format within the `data` folder.
        You can manually copy those files for backup or version control.
    """)

    st.write("---")
    st.subheader("Danger Zone")
    if st.button("Clear All Data (Irreversible!)"):
        st.warning("Are you sure you want to clear all data? This cannot be undone!")
        confirm = st.button("Yes, wipe everything!")
        if confirm:
            # Just remove the JSON files
            for f in [TASKS_FILE, APPOINTMENTS_FILE, PRESCRIPTIONS_FILE, MOOD_FILE, WATER_FILE, NOTES_FILE]:
                if os.path.exists(f):
                    os.remove(f)
            st.success("All data cleared. Please refresh or restart the app.")
    
    st.write("")

# (Optionally) At the bottom, you could do more disclaimers or additional info.
st.markdown("---")
st.markdown("**Thank you for using WellNest!**")
