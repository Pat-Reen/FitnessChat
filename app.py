import anthropic
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def gather_user_preferences():
    goal = st.selectbox("What's your main fitness goal?",
                        ["Weight Loss", "Build Muscle", "Endurance", "General Fitness"])
    experience = st.radio("What's your experience level?",
                          ["Beginner", "Intermediate", "Advanced"])
    restrictions = st.checkbox("Any injuries or limitations?")
    return goal, experience, restrictions

def craft_fitness_prompt(goal, experience, restrictions, workout_length, workout_focus, variation):
    restriction_text = (
        "The user has some injuries or limitations, so suggest modifications as needed."
        if restrictions else
        "The user has no injuries or limitations."
    )

    if workout_focus in ["Freeweights", "Circuit"]:
        detail_instruction = (
            "For each exercise, provide:\n"
            "- Sets and reps\n"
            "- A detailed description of how to perform it (form tips, muscles worked, equipment needed)"
        )
    else:
        detail_instruction = (
            "Provide a structured session plan including:\n"
            "- Warm-up\n"
            "- Main session (intervals or segments with duration/pace)\n"
            "- Cool-down"
        )

    variation_text = ""
    if variation > 0:
        variation_text = (
            f"\nThis is variation #{variation}, make it meaningfully different from a standard workout."
        )

    prompt = (
        f"You are an expert personal trainer. Create a {workout_length} {workout_focus} workout.\n\n"
        f"User profile:\n"
        f"- Fitness goal: {goal}\n"
        f"- Experience level: {experience}\n"
        f"- {restriction_text}\n\n"
        f"{detail_instruction}"
        f"{variation_text}"
    )
    return prompt

def process_query(goal, experience, restrictions, workout_length, workout_focus, variation):
    prompt = craft_fitness_prompt(goal, experience, restrictions, workout_length, workout_focus, variation)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# --- Streamlit UI ---
st.title("Fitness Knowledge Bot")

# Session state
if 'workout' not in st.session_state:
    st.session_state.workout = None
if 'variation' not in st.session_state:
    st.session_state.variation = 0

# Gather preferences
goal, experience, restrictions = gather_user_preferences()

# Workout options
workout_length = st.selectbox("Workout length", ["30 min", "45 min", "60 min", "90 min"])
workout_focus = st.radio("Workout focus", ["Running", "Indoor Cardio", "Freeweights", "Circuit"])

# Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Generate Workout"):
        st.session_state.variation = 0
        st.session_state.workout = process_query(
            goal, experience, restrictions, workout_length, workout_focus, st.session_state.variation
        )

with col2:
    if st.button("Generate Different Workout"):
        st.session_state.variation += 1
        st.session_state.workout = process_query(
            goal, experience, restrictions, workout_length, workout_focus, st.session_state.variation
        )

# Display workout
if st.session_state.workout:
    st.markdown(st.session_state.workout)
