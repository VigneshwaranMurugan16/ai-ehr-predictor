# ui/streamlit_app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime


# API base URL
API_BASE = "http://localhost:8000"


# Page config
st.set_page_config(
    page_title="AI EHR - Nurse Dashboard",
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
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def logout():
    """Clear session"""
    st.session_state.token = None
    st.session_state.username = None


# ===== LOGIN PAGE =====
if not st.session_state.token:
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🏥 AI EHR System")
        st.subheader("Nurse Dashboard Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🔐 Login", use_container_width=True)

            if submit:
                if login(username, password):
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

        st.info("💡 Demo: `nurse1` / `nurse123`")


# ===== MAIN DASHBOARD =====
else:
    # Header with logout
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🏥 Nurse Dashboard")
        st.caption(f"Welcome back, **{st.session_state.username}**")
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    st.divider()

    # Main Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Patient Risk Board", "✅ My Tasks", "🔮 Check Patient Risk"])


        # ===== TAB 1: WARD RISK BOARD (SIMPLIFIED) =====
    with tab1:
        st.subheader("📊 Current Patients - Risk Levels")
        
        # Simple filter with refresh
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            risk_filter = st.radio(
                "Show patients:",
                ["All Patients", "High Risk Only", "Medium Risk Only", "Low Risk Only"],
                horizontal=True
            )
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Map display names to API values
        filter_map = {
            "All Patients": None,
            "High Risk Only": "high",
            "Medium Risk Only": "medium",
            "Low Risk Only": "low"
        }
        
        try:
            params = {}
            if filter_map[risk_filter]:
                params["min_level"] = filter_map[risk_filter]
            
            response = requests.get(
                f"{API_BASE}/ward/risk",
                headers=get_headers(),
                params=params,
            )

            if response.status_code == 200:
                patients = response.json()

                if patients:
                    # Summary metrics at top
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📋 Total Patients", len(patients))
                    with col2:
                        high_risk = len([p for p in patients if p.get("risk_level") == "high"])
                        st.metric("🔴 High Risk", high_risk)
                    with col3:
                        medium_risk = len([p for p in patients if p.get("risk_level") == "medium"])
                        st.metric("🟡 Medium Risk", medium_risk)

                    st.divider()

                    # Display patient cards (simpler than table)
                    for idx, patient in enumerate(patients):
                        risk_level = patient.get("risk_level", "low")
                        risk_score = patient.get("risk_score", 0)
                        patient_id = patient.get('patient_id')
                        
                        # Color coding based on risk
                        if risk_level == "high":
                            card_color = "🔴"
                        elif risk_level == "medium":
                            card_color = "🟡"
                        else:
                            card_color = "🟢"

                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                st.markdown(f"**{card_color} {patient.get('first_name')} {patient.get('last_name')}**")
                                st.caption(f"Patient ID: {patient_id}")
                            
                            with col2:
                                st.write(f"Risk: **{risk_score*100:.1f}%**")
                            
                            with col3:
                                st.write(f"Level: **{risk_level.upper()}**")
                            
                            with col4:
                                # Use unique key with index to avoid duplicates
                                if st.button("📋 View", key=f"view_patient_{patient_id}_{idx}", use_container_width=True):
                                    st.session_state[f'show_detail_{patient_id}'] = True
                            
                            # Show patient details if View button was clicked
                            if st.session_state.get(f'show_detail_{patient_id}', False):
                                with st.expander("👤 **Patient Details**", expanded=True):
                                    # Fetch detailed patient info
                                    try:
                                        detail_response = requests.get(
                                            f"{API_BASE}/predict/readmission/{patient.get('encounter_id', 1)}",
                                            headers=get_headers(),
                                        )
                                        
                                        if detail_response.status_code == 200:
                                            detail_data = detail_response.json()
                                            
                                            # Patient info
                                            col_a, col_b, col_c = st.columns(3)
                                            with col_a:
                                                st.metric("Patient ID", patient_id)
                                            with col_b:
                                                st.metric("Risk Score", f"{risk_score*100:.1f}%")
                                            with col_c:
                                                st.metric("Risk Level", risk_level.upper())
                                            
                                            st.divider()
                                            
                                            # Risk factors
                                            st.write("**📊 Key Risk Factors:**")
                                            risk_factors = detail_data.get('risk_factors', [])
                                            
                                            if risk_factors:
                                                for i, factor in enumerate(risk_factors[:5], 1):
                                                    feature = factor['feature'].replace('_', ' ').title()
                                                    value = factor['value']
                                                    impact = factor['impact']
                                                    direction = "⬆️" if factor['direction'] == "increases" else "⬇️"
                                                    
                                                    st.write(f"{i}. **{feature}**: {value:.1f} {direction} (Impact: {abs(impact):.3f})")
                                            
                                            st.divider()
                                            
                                            # Close button
                                            if st.button("❌ Close Details", key=f"close_{patient_id}_{idx}"):
                                                st.session_state[f'show_detail_{patient_id}'] = False
                                                st.rerun()
                                        else:
                                            st.warning("⚠️ Could not load detailed information")
                                    except Exception as e:
                                        st.error(f"Error loading details: {e}")
                            
                            st.divider()

                else:
                    st.info("ℹ️ No patients found with selected filter")
            else:
                st.error(f"❌ Error loading patients: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")



    # ===== TAB 2: TASKS (SIMPLIFIED) =====
    with tab2:
        st.subheader("✅ Task Management")

        # Simple filter
        col1, col2 = st.columns([3, 1])
        with col1:
            task_filter = st.radio(
                "Show tasks:",
                ["Open Tasks", "Completed Tasks", "All Tasks"],
                horizontal=True
            )
        with col2:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_tasks"):
                st.rerun()

        # Map to API values
        status_map = {
            "Open Tasks": "open",
            "Completed Tasks": "completed",
            "All Tasks": None
        }

        try:
            params = {}
            if status_map[task_filter]:
                params["status_filter"] = status_map[task_filter]
            
            response = requests.get(
                f"{API_BASE}/ward/tasks",
                headers=get_headers(),
                params=params,
            )

            if response.status_code == 200:
                tasks = response.json()

                if tasks:
                    # Task summary
                    open_count = len([t for t in tasks if t.get("status") == "open"])
                    completed_count = len([t for t in tasks if t.get("status") == "completed"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🔓 Open", open_count)
                    with col2:
                        st.metric("✅ Completed", completed_count)

                    st.divider()

                    # Display tasks as simple cards
                    for task in tasks:
                        task_id = task.get('task_id') or task.get('id')
                        status = task.get("status", "unknown")
                        
                        with st.container():
                            col1, col2, col3 = st.columns([3, 2, 1])

                            with col1:
                                task_type = task.get('task_type', 'Task')
                                st.markdown(f"**{task_type}**")
                                st.caption(f"Patient ID: {task.get('patient_id')} | Task #{task_id}")

                            with col2:
                                if status == "open":
                                    st.warning("📌 OPEN")
                                elif status == "in_progress":
                                    st.info("⏳ IN PROGRESS")
                                else:
                                    st.success("✅ COMPLETED")

                            with col3:
                                if status in ["open", "in_progress"]:
                                    if st.button("✅ Done", key=f"complete_{task_id}", use_container_width=True):
                                        complete_response = requests.post(
                                            f"{API_BASE}/ward/tasks/{task_id}/complete",
                                            headers=get_headers(),
                                        )
                                        if complete_response.status_code == 200:
                                            st.success("Task completed!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to complete")

                            st.divider()
                else:
                    st.info("ℹ️ No tasks found")
            else:
                st.error(f"❌ Error loading tasks: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")


    # ===== TAB 3: PREDICT (NURSE-FRIENDLY) =====
    with tab3:
        st.subheader("🔮 Check Patient Readmission Risk")
        st.caption("Enter encounter ID to see if patient needs extra care")

        # Simpler form
        col1, col2 = st.columns([2, 1])
        
        with col1:
            encounter_id = st.number_input(
                "Encounter ID", 
                min_value=1, 
                max_value=200,
                value=1,
                help="Enter the encounter number from patient chart"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            predict_btn = st.button("🔮 Check Risk", use_container_width=True, type="primary")

        if predict_btn:
            try:
                with st.spinner("Analyzing patient data..."):
                    response = requests.get(
                        f"{API_BASE}/predict/readmission/{encounter_id}",
                        headers=get_headers(),
                    )

                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("✅ Analysis Complete")
                    st.divider()

                    # Big, clear risk display
                    risk_score = data['risk_score']
                    level = data["risk_level"]
                    
                    # Visual alert box
                    if level == "high":
                        st.error("### 🔴 HIGH RISK ALERT")
                        st.markdown(f"### This patient has a **{risk_score*100:.1f}% chance** of being readmitted within 30 days")
                        st.warning("⚠️ **Action Required:** Consider discharge planning, follow-up appointments, and patient education")
                    elif level == "medium":
                        st.warning("### 🟡 MEDIUM RISK")
                        st.markdown(f"### This patient has a **{risk_score*100:.1f}% chance** of readmission")
                        st.info("ℹ️ **Recommended:** Enhanced monitoring and discharge instructions")
                    else:
                        st.success("### 🟢 LOW RISK")
                        st.markdown(f"### This patient has a **{risk_score*100:.1f}% chance** of readmission")
                        st.info("✅ **Status:** Standard discharge procedures appropriate")

                    st.divider()

                    # Key risk factors in simple language
                    st.subheader("📋 Main Risk Factors")
                    risk_factors = data.get('risk_factors', [])
                    
                    if risk_factors:
                        # Show top 5 factors only
                        for i, factor in enumerate(risk_factors[:5], 1):
                            feature = factor['feature'].replace('_', ' ').title()
                            value = factor['value']
                            direction = "⬆️ Increases" if factor['direction'] == "increases" else "⬇️ Decreases"
                            
                            with st.expander(f"**{i}. {feature}** - Value: {value:.1f}", expanded=(i <= 3)):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Current Value", f"{value:.1f}")
                                with col2:
                                    st.write(f"**Effect:** {direction} risk")
                    
                    st.divider()
                    
                    # Action buttons for nurses
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📞 Schedule Follow-up", use_container_width=True):
                            st.info("Follow-up scheduling feature coming soon")
                    with col2:
                        if st.button("📝 Add Care Notes", use_container_width=True):
                            st.info("Care notes feature coming soon")
                    with col3:
                        if st.button("👨‍⚕️ Notify Doctor", use_container_width=True):
                            st.info("Notification feature coming soon")

                elif response.status_code == 404:
                    st.error("❌ Encounter not found. Please check the ID and try again.")
                else:
                    st.error(f"❌ Error: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Connection error: {e}")


# Minimal sidebar
with st.sidebar:
    st.header("🏥 System Status")
    
    # API health check
    try:
        health = requests.get(f"{API_BASE}/predict/readmission/1", timeout=2)
        if health.status_code in [200, 404]:
            st.success("✅ Connected")
        else:
            st.warning("⚠️ Connection Issue")
    except:
        st.error("❌ Offline")
    
    st.divider()
    
    st.caption("**AI EHR Predictor**")
    st.caption("Version 1.0")
    st.caption("© 2026")
