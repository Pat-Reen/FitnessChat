import json
import anthropic
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ---------------------------------------------------------------------------
# Curated exercise list — Fitness First-style Australian gym
# ---------------------------------------------------------------------------
EXERCISES = {
    "Chest": [
        "Barbell Bench Press (Flat)", "Barbell Bench Press (Incline)",
        "Dumbbell Bench Press", "Dumbbell Fly", "Cable Fly / Crossover",
        "Chest Press Machine", "Chest Fly Machine", "Smith Machine Bench Press",
    ],
    "Back": [
        "Lat Pulldown", "Seated Cable Row", "Barbell Bent-Over Row",
        "Dumbbell Bent-Over Row", "Dumbbell Single-Arm Row", 
        "Deadlift", "Romanian Deadlift",
        "Pull-Up / Chin-Up", "Face Pull (Cable)",
    ],
    "Legs": [
        "Barbell Back Squat", "Romanian Deadlift", "Leg Press Machine",
        "Leg Extension Machine", "Leg Curl Machine", "Dumbbell Lunge",
        "Smith Machine Squat", "Calf Raise", "Step-Up (Plyometric Box)",
    ],
    "Shoulders": [
        "Barbell Overhead Press", "Dumbbell Shoulder Press",
        "Dumbbell Lateral Raise", "Cable Lateral Raise", "Face Pull (Cable)",
        "Arnold Press", "Upright Row",
    ],
    "Arms": [
        "Barbell Bicep Curl", "Dumbbell Bicep Curl", "Hammer Curl",
        "Cable Bicep Curl", "Tricep Pushdown (Cable)", "Skull Crusher",
        "Dumbbell Overhead Tricep Extension", "Tricep Dip",
    ],
    "Core (Equipment)": [
        "Cable Crunch", "Hanging Leg Raise",
        "Russian Twist (Medicine Ball)",
        "Bench Crunch", "Pallof Press (Cable)",
    ],
    "Mat Core": [
        "Dead Bug", "Hollow Body Hold", "Bird Dog",
        "Full Plank", "Side Plank (Left)", "Side Plank (Right)",
        "High Side Plank", "Side Plank Reach Through",
        "Bicycle Crunch", "Reverse Crunch", "V-Up",
        "Glute Bridge", "Wall Sit",
    ],
    "Cardio": [
        "Rowing Machine", "Stationary Bike", "Spin Bike",
        "Elliptical Trainer", "Stair Climber", "Treadmill Run/Walk",
    ],
    "Full Body / Functional": [
        "Kettlebell Swing", "Kettlebell Turkish Get-Up",
        "Barbell Clean & Press", "Burpee", "Deadlift",
    ],
}

ALL_EXERCISES = sorted({ex for group in EXERCISES.values() for ex in group})

# ---------------------------------------------------------------------------
# Claude helpers
# ---------------------------------------------------------------------------

def suggest_exercises(goal: str, experience: str, restrictions: str, duration: str) -> list[str]:
    """Call 1 — returns a JSON list of 6-8 exercise names."""
    master = json.dumps(ALL_EXERCISES)
    restriction_line = (
        f"The user has these restrictions/injuries: {restrictions}."
        if restrictions.strip()
        else "The user has no injuries or limitations."
    )
    prompt = (
        f"You are an expert personal trainer. Choose 6 to 8 exercises from the list below "
        f"that best suit this user's profile. Return ONLY a valid JSON array of exercise names "
        f"(no other text, no markdown fences).\n\n"
        f"User profile:\n"
        f"- Goal: {goal}\n"
        f"- Experience: {experience}\n"
        f"- {restriction_line}\n"
        f"- Session duration: {duration}\n\n"
        f"Master exercise list:\n{master}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    try:
        exercises = json.loads(raw)
        # Keep only names that exist in our master list
        return [e for e in exercises if e in ALL_EXERCISES]
    except json.JSONDecodeError:
        return []


def build_workout(
    goal: str,
    experience: str,
    restrictions: str,
    duration: str,
    exercises: list[str],
    variation: int,
) -> str:
    """Call 2 — returns a markdown workout plan."""
    restriction_line = (
        f"The user has these restrictions/injuries: {restrictions}. Provide modifications where relevant."
        if restrictions.strip()
        else "The user has no injuries or limitations."
    )
    variation_line = (
        f"\nThis is variation #{variation} — make it meaningfully different "
        f"(different rep schemes, tempo, supersets, ordering) from a standard version."
        if variation > 0
        else ""
    )
    exercise_list = "\n".join(f"- {e}" for e in exercises)
    prompt = (
        f"You are an expert personal trainer. Write a structured {duration} gym workout "
        f"using ONLY the exercises listed below.\n\n"
        f"User profile:\n"
        f"- Goal: {goal}\n"
        f"- Experience: {experience}\n"
        f"- {restriction_line}\n"
        f"{variation_line}\n\n"
        f"Exercises to include:\n{exercise_list}\n\n"
        f"Format the plan in markdown with:\n"
        f"1. Warm-up: 10–20 minutes on the rowing machine or stationary/spin bike "
        f"(the user runs on non-gym days so do NOT suggest treadmill/running as a warm-up)\n"
        f"2. For each exercise: sets × reps (or duration), rest period, "
        f"and 1–2 concise form cues (key points only, no essays)\n"
        f"3. A brief cool-down note"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def init_state():
    defaults = {
        "stage": "preferences",
        "suggested": [],
        "selected": [],
        "workout": "",
        "variation": 0,
        # Capture preferences so Stage 2/3 can reference them
        "goal": "Build Muscle",
        "experience": "Intermediate",
        "restrictions": "",
        "duration": "60 min",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Stage renderers
# ---------------------------------------------------------------------------

def render_preferences():
    st.header("Your Preferences")

    goal = st.selectbox(
        "What's your main fitness goal?",
        ["Build Muscle", "Weight Loss", "Endurance", "General Fitness"],
        index=["Build Muscle", "Weight Loss", "Endurance", "General Fitness"].index(
            st.session_state.goal
        ),
    )
    experience = st.radio(
        "Experience level",
        ["Beginner", "Intermediate", "Advanced"],
        index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.experience),
    )
    restrictions = st.text_input(
        "Any injuries or limitations? (leave blank if none)",
        value=st.session_state.restrictions,
    )
    duration = st.selectbox(
        "Session duration",
        ["30 min", "45 min", "60 min", "90 min"],
        index=["30 min", "45 min", "60 min", "90 min"].index(st.session_state.duration),
    )

    if st.button("Suggest Plan", type="primary"):
        st.session_state.goal = goal
        st.session_state.experience = experience
        st.session_state.restrictions = restrictions
        st.session_state.duration = duration

        with st.spinner("Asking Claude to suggest exercises…"):
            suggested = suggest_exercises(goal, experience, restrictions, duration)

        if not suggested:
            st.warning(
                "Claude's suggestion couldn't be parsed. Showing the full exercise list — "
                "please pick the ones you'd like."
            )
            suggested = []

        st.session_state.suggested = suggested
        st.session_state.selected = list(suggested)  # pre-select suggestions
        st.session_state.variation = 0
        st.session_state.stage = "selection"
        st.rerun()


def render_selection():
    st.header("Choose Your Exercises")
    st.caption(
        f"Goal: **{st.session_state.goal}** · "
        f"Experience: **{st.session_state.experience}** · "
        f"Duration: **{st.session_state.duration}**"
    )

    suggested = st.session_state.suggested
    selected = set(st.session_state.selected)

    # --- Suggested exercises as pre-checked checkboxes ---
    if suggested:
        st.subheader("Claude's suggestions")
        for ex in suggested:
            checked = st.checkbox(ex, value=(ex in selected), key=f"sugg_{ex}")
            if checked:
                selected.add(ex)
            else:
                selected.discard(ex)
    else:
        st.info("No suggestions available — browse the full list below.")

    # --- Full list in an expander ---
    # Track which exercises have already been rendered to avoid duplicate keys
    rendered_in_expander: set[str] = set()
    with st.expander("Add more exercises"):
        for group, exercises in EXERCISES.items():
            st.markdown(f"**{group}**")
            for ex in exercises:
                if ex in suggested:
                    continue  # already shown above
                if ex in rendered_in_expander:
                    continue  # skip duplicates across groups (e.g. Face Pull)
                rendered_in_expander.add(ex)
                checked = st.checkbox(ex, value=(ex in selected), key=f"full_{ex}")
                if checked:
                    selected.add(ex)
                else:
                    selected.discard(ex)

    st.session_state.selected = sorted(selected)

    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Build Workout", type="primary", disabled=len(selected) == 0):
            with st.spinner("Building your workout…"):
                workout = build_workout(
                    st.session_state.goal,
                    st.session_state.experience,
                    st.session_state.restrictions,
                    st.session_state.duration,
                    st.session_state.selected,
                    st.session_state.variation,
                )
            st.session_state.workout = workout
            st.session_state.stage = "workout"
            st.rerun()
    with col2:
        if st.button("← Start Over"):
            st.session_state.stage = "preferences"
            st.rerun()


def render_workout():
    st.header("Your Workout")
    st.caption(
        f"Goal: **{st.session_state.goal}** · "
        f"Experience: **{st.session_state.experience}** · "
        f"Duration: **{st.session_state.duration}**"
    )

    st.markdown(st.session_state.workout)

    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Regenerate", type="primary"):
            st.session_state.variation += 1
            with st.spinner("Generating a different version…"):
                workout = build_workout(
                    st.session_state.goal,
                    st.session_state.experience,
                    st.session_state.restrictions,
                    st.session_state.duration,
                    st.session_state.selected,
                    st.session_state.variation,
                )
            st.session_state.workout = workout
            st.rerun()
    with col2:
        if st.button("← Start Over"):
            st.session_state.stage = "preferences"
            st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.title("Fitness Chat")

init_state()

stage = st.session_state.stage
if stage == "preferences":
    render_preferences()
elif stage == "selection":
    render_selection()
elif stage == "workout":
    render_workout()
