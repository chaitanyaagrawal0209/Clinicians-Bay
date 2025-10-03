import pandas as pd
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Clinical Diagnosis Simulator",
    page_icon="🩺",
    layout="centered"
)

# --- Load Excel Data ---
@st.cache_data
def load_data(file_path):
    """Loads and preprocesses data from an Excel file."""
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        string_cols = ["Step ID", "Options", "Is Correct", "Feedback", "Next Step ID", "Score Change", "Consequence"]
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    except FileNotFoundError:
        st.error(f"❌ **Error:** The file '{file_path}' was not found.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the Excel file: {e}")
        return None

df = load_data("clinical_cases_advanced.xlsx")

if df is None:
    st.stop()

# --- App State Initialization ---
if 'current_step' not in st.session_state:
    st.session_state.current_step = "1"
    st.session_state.score = 0
    st.session_state.selected_case = None
    st.session_state.case_history = [] # NEW: To store the scrollable history
    st.session_state.action_result = None

# --- UI Sidebar ---
st.sidebar.title("👨‍⚕️ Clinical Cases")
cases = df["Case ID"].unique()

selected_case = st.sidebar.selectbox("Select a case to begin:", cases)
if st.session_state.selected_case != selected_case:
    # Reset everything for a new case
    st.session_state.current_step = "1"
    st.session_state.score = 0
    st.session_state.case_history = []
    st.session_state.action_result = None
    st.session_state.selected_case = selected_case

case_df = df[df["Case ID"] == st.session_state.selected_case].copy()

# --- Helper Function ---
def get_step_details(step_id):
    """Fetches all details for a given step_id."""
    try:
        return case_df[case_df["Step ID"] == str(step_id)].iloc[0]
    except IndexError:
        st.error(f"Error: Step ID '{step_id}' not found. Please check the Excel file.")
        return None

# --- Main App Logic ---
st.title(f"🩺 {st.session_state.selected_case}")
st.sidebar.metric("Your Score", st.session_state.score)

# --- NEW: Display the entire case history ---
for entry in st.session_state.case_history:
    st.info(f"**Patient Status:** {entry['status']}")
    st.markdown(f"#### {entry['scenario']}")
    st.write(f"**Your Choice:** {entry['chosen_option']}")
    st.success(f"**Outcome:** {entry['feedback']}")
    st.markdown("---")

# --- Handle and display action results for INCORRECT answers ---
if 'action_result' in st.session_state and st.session_state.action_result:
    result_type, consequence, feedback = st.session_state.action_result
    
    st.error(f"**Outcome of Incorrect Action:** {consequence}")
    st.warning(f"**Analysis:** {feedback}")
    
    if st.button("Go Back and Try Again"):
        st.session_state.action_result = None
        st.rerun()
    st.stop()

# --- Logic for the current step (or final screen) ---
if st.session_state.current_step == "END":
    st.balloons()
    st.success("## Well Done! Case Completed.")
    st.markdown("### Discharging notes")
    if st.session_state.case_history:
         st.info(st.session_state.case_history[-1]['feedback'])
    
    if st.button("Restart Case"):
        st.session_state.current_step = "1"
        st.session_state.score = 0
        st.session_state.case_history = []
        st.rerun()
    st.stop()

current_step_data = get_step_details(st.session_state.current_step)

if current_step_data is not None:
    st.info(f"**Patient Status:** {current_step_data['Patient Status']}")
    st.markdown(f"### {current_step_data['Scenario/Question']}")

    options = [opt.strip() for opt in current_step_data["Options"].split('|')]
    is_correct_list = [val.strip().upper() == 'TRUE' for val in current_step_data["Is Correct"].split('|')]
    feedback_list = [fb.strip() for fb in current_step_data["Feedback"].split('|')]
    next_steps = [ns.strip() for ns in current_step_data["Next Step ID"].split('|')]
    scores = [int(float(s)) for s in current_step_data["Score Change"].split('|')]
    consequences = [c.strip() for c in current_step_data["Consequence"].split('|')]

    for i, option in enumerate(options):
        if st.button(option, key=f"step_{st.session_state.current_step}_option_{i}"):
            if is_correct_list[i]:
                # --- NEW: Add correct step to history ---
                history_entry = {
                    "status": current_step_data['Patient Status'],
                    "scenario": current_step_data['Scenario/Question'],
                    "chosen_option": option,
                    "feedback": feedback_list[i]
                }
                st.session_state.case_history.append(history_entry)
                st.session_state.score += scores[i]
                st.session_state.current_step = next_steps[i]
            else:
                # Store consequence for incorrect answer
                st.session_state.score += scores[i]
                st.session_state.action_result = ("consequence", consequences[i], feedback_list[i])
            
            st.rerun()

