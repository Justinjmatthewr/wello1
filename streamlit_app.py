import os
import json
import datetime
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import streamlit as st

# ---------------------------------------------------------
#                 GLOBAL CONFIG & CONSTANTS
# ---------------------------------------------------------
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

# Load and save functions for JSON files
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# Initialize data
tasks = load_json(TASKS_FILE)
appointments = load_json(APPOINTMENTS_FILE)
prescriptions = load_json(PRESCRIPTIONS_FILE)
mood_logs = load_json(MOOD_FILE)
water_logs = load_json(WATER_FILE)
notes = load_json(NOTES_FILE)

# ---------------------------------------------------------
#                     STREAMLIT APP
# ---------------------------------------------------------
st.title("WellNest Web App")
st.sidebar.header("Navigation")
option = st.sidebar.selectbox(
    "Choose a section:",
    ["Home", "Tasks", "Appointments", "Prescriptions", "Analytics", "Settings"],
)

# ---------------------------------------------------------
#                 SECTION: HOME
# ---------------------------------------------------------
if option == "Home":
    st.header("Welcome to WellNest!")
    st.write("Your personal health and wellness tracker.")
    st.write("Use the sidebar to navigate different sections of the app.")

    # Show today's quick stats
    today = datetime.now().strftime("%Y-%m-%d")
    st.subheader("Today's Stats")
    st.write(f"- Tasks Today: {len(tasks.get(today, []))}")
    st.write(f"- Water Intake Today: {water_logs.get(today, 0)} L")

# ---------------------------------------------------------
#                 SECTION: TASKS
# ---------------------------------------------------------
elif option == "Tasks":
    st.header("Manage Tasks")
    date = st.date_input("Select a date", value=datetime.now())
    date_str = date.strftime("%Y-%m-%d")
    
    if date_str not in tasks:
        tasks[date_str] = []

    # Add a new task
    with st.form(key="add_task"):
        task_name = st.text_input("Task Name")
        task_time = st.time_input("Task Time")
        if st.form_submit_button("Add Task"):
            tasks[date_str].append({"name": task_name, "time": task_time.isoformat(), "status": "Pending"})
            save_json(tasks, TASKS_FILE)
            st.success("Task added successfully!")

    # View tasks
    st.subheader(f"Tasks for {date_str}")
    for task in tasks[date_str]:
        st.write(f"- **{task['name']}** at {task['time']}")

# ---------------------------------------------------------
#                 SECTION: APPOINTMENTS
# ---------------------------------------------------------
elif option == "Appointments":
    st.header("Manage Appointments")
    date = st.date_input("Select a date", value=datetime.now())
    date_str = date.strftime("%Y-%m-%d")
    
    if date_str not in appointments:
        appointments[date_str] = []

    # Add a new appointment
    with st.form(key="add_appointment"):
        appointment_name = st.text_input("Appointment Name")
        appointment_time = st.time_input("Appointment Time")
        if st.form_submit_button("Add Appointment"):
            appointments[date_str].append({"name": appointment_name, "time": appointment_time.isoformat()})
            save_json(appointments, APPOINTMENTS_FILE)
            st.success("Appointment added successfully!")

    # View appointments
    st.subheader(f"Appointments for {date_str}")
    for app in appointments[date_str]:
        st.write(f"- **{app['name']}** at {app['time']}")

# ---------------------------------------------------------
#                 SECTION: PRESCRIPTIONS
# ---------------------------------------------------------
elif option == "Prescriptions":
    st.header("Manage Prescriptions")
    prescription_name = st.text_input("Prescription Name")
    description = st.text_area("Description")
    if st.button("Save Prescription"):
        prescriptions[prescription_name] = {"description": description}
        save_json(prescriptions, PRESCRIPTIONS_FILE)
        st.success("Prescription saved successfully!")

# ---------------------------------------------------------
#                 SECTION: ANALYTICS
# ---------------------------------------------------------
elif option == "Analytics":
    st.header("Analytics")
    st.write("Water Intake (Last 7 Days)")

    # Create a bar chart for water intake
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)][::-1]
    intakes = [water_logs.get(date, 0) for date in dates]

    fig, ax = plt.subplots()
    ax.bar(dates, intakes, color="blue")
    ax.set_ylabel("Liters")
    ax.set_title("Water Intake")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# ---------------------------------------------------------
#                 SECTION: SETTINGS
# ---------------------------------------------------------
elif option == "Settings":
    st.header("Settings")
    st.write("Manage your application settings here.")

