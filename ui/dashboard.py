import streamlit as st
import requests
from datetime import datetime

# API base URL
API_BASE = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="AI EHR Predictor - Nurse Dashboard",
    page_icon="🏥",
    layout="wide",
)

# Session state for auth
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None


def login(username: str, password: str):
    """Login and get JWT token"""
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={"username": username, "password": password},
    )
    if response.status_code == 200:
        data = response.json()
        st.session_state.token = data["access_token"]
        st.session_state.username = username
        return True
    return False


def get_headers():
    """Get auth headers"""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def logout():
    """Clear session"""
    st.session_state.token = None
    st.session_state.username = None


# ===== LOGIN PAGE =====
if not st.session_state.token:
    st.title("🏥 AI EHR Predictor")
    st.subheader("Nurse Dashboard Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.info("💡 Demo credentials: `nurse1` / `nurse123`")

# ===== MAIN DASHBOARD =====
else:
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🏥 AI EHR Predictor - Nurse Dashboard")
        st.caption(f"Logged in as: **{st.session_state.username}**")
    with col2:
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Ward Risk Board", "✅ Tasks", "🔮 Predict Risk"])

    # ===== TAB 1: WARD RISK BOARD =====
    with tab1:
        st.header("Ward Risk Board")

        # Filter
        risk_filter = st.selectbox(
            "Filter by minimum risk level:",
            ["All", "high", "medium", "low"],
            index=0,
        )

        try:
            params = {} if risk_filter == "All" else {"min_level": risk_filter}
            response = requests.get(
                f"{API_BASE}/ward/risk",
                headers=get_headers(),
                params=params,
            )

            if response.status_code == 200:
                patients = response.json()

                if patients:
                    # Display as table
                    st.dataframe(
                        patients,
                        column_config={
                            "patient_id": "Patient ID",
                            "first_name": "First Name",
                            "last_name": "Last Name",
                            "risk_score": st.column_config.NumberColumn(
                                "Risk Score",
                                format="%.2f",
                            ),
                            "risk_level": st.column_config.TextColumn("Risk Level"),
                            "los_days": "LOS (days)",
                            "los_level": "LOS Level",
                        },
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Patients", len(patients))
                    with col2:
                        high_risk = len([p for p in patients if p["risk_level"] == "high"])
                        st.metric("High Risk", high_risk)
                    with col3:
                        avg_score = sum(p["risk_score"] for p in patients) / len(patients)
                        st.metric("Avg Risk Score", f"{avg_score:.2f}")
                else:
                    st.info("No patients match the filter criteria.")
            else:
                st.error(f"Error fetching ward data: {response.status_code}")
        except Exception as e:
            st.error(f"Connection error: {e}")

    # ===== TAB 2: TASKS =====
    with tab2:
        st.header("Task Management")

        # Filter
        status_filter = st.selectbox(
            "Filter by status:",
            ["All", "open", "completed"],
            index=0,
        )

        try:
            params = {} if status_filter == "All" else {"status_filter": status_filter}
            response = requests.get(
                f"{API_BASE}/tasks",
                headers=get_headers(),
                params=params,
            )

            if response.status_code == 200:
                tasks = response.json()

                if tasks:
                    for task in tasks:
                        with st.container():
                            col1, col2, col3 = st.columns([2, 2, 1])

                            with col1:
                                st.write(f"**Task #{task['id']}** - {task['task_type']}")
                                st.caption(
                                    f"Patient ID: {task['patient_id']} | Encounter ID: {task['encounter_id']}"
                                )

                            with col2:
                                status = task["status"]
                                if status == "open":
                                    st.warning(f"Status: {status.upper()}")
                                else:
                                    st.success(f"Status: {status.upper()}")
                                    if task.get("completed_at"):
                                        st.caption(f"Completed: {task['completed_at']}")

                            with col3:
                                if task["status"] == "open":
                                    if st.button(
                                        "Complete",
                                        key=f"complete_{task['id']}",
                                        use_container_width=True,
                                    ):
                                        complete_response = requests.post(
                                            f"{API_BASE}/tasks/{task['id']}/complete",
                                            headers=get_headers(),
                                        )
                                        if complete_response.status_code == 200:
                                            st.success("Task completed!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to complete task")

                            st.divider()
                else:
                    st.info("No tasks match the filter criteria.")
            else:
                st.error(f"Error fetching tasks: {response.status_code}")
        except Exception as e:
            st.error(f"Connection error: {e}")

    # ===== TAB 3: PREDICT =====
    with tab3:
        st.header("Predict Readmission Risk")

        with st.form("predict_form"):
            col1, col2 = st.columns(2)
            with col1:
                patient_id = st.number_input("Patient ID", min_value=1, value=1)
            with col2:
                encounter_id = st.number_input("Encounter ID", min_value=1, value=1)

            submit = st.form_submit_button("Predict Risk")

            if submit:
                try:
                    response = requests.post(
                        f"{API_BASE}/predict/readmission",
                        headers=get_headers(),
                        json={"patient_id": patient_id, "encounter_id": encounter_id},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.success("Prediction completed!")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Risk Score", f"{data['risk_score']:.2f}")
                        with col2:
                            level = data["risk_level"]
                            color = (
                                "🔴"
                                if level == "high"
                                else "🟡" if level == "medium" else "🟢"
                            )
                            st.metric("Risk Level", f"{color} {level.upper()}")

                        st.info(
                            "ℹ️ If high risk, a nurse_review task has been auto-created."
                        )
                    elif response.status_code == 404:
                        st.error("Patient or encounter not found")
                    else:
                        st.error(f"Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
