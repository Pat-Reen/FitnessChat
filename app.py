import anthropic
import os
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Fitness Chat",
    page_icon="🏋️",
    layout="centered",
)

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox,
.stRadio, .stMultiSelect, .stCheckbox, .stButton, .stCaption {
    font-family: 'Inter', sans-serif !important;
}

/* Tighten top padding */
.block-container { padding-top: 2rem; padding-bottom: 3rem; }

/* Title */
h1 { font-weight: 700 !important; letter-spacing: -0.5px; }

/* Section headers — green accent */
h2 { color: #2d6a4f !important; font-weight: 600 !important; }
h3 { color: #2d6a4f !important; font-weight: 600 !important; font-size: 1.05rem !important; }

/* Subtle rule under the title */
h1 + div { border-top: 2px solid #2d6a4f; padding-top: 1rem; }

/* Make expander header a touch bolder */
[data-testid="stExpander"] summary {
    font-weight: 600;
    color: #212529;
}

/* Checkbox label size */
.stCheckbox label { font-size: 0.95rem; }

/* Caption row */
.stCaptionContainer { color: #6c757d !important; font-size: 0.85rem !important; }
</style>
"""

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

MUSCLE_GROUPS = list(EXERCISES.keys())

# ---------------------------------------------------------------------------
# Claude helper — single call
# ---------------------------------------------------------------------------

def build_workout(
    goal: str,
    experience: str,
    restrictions: str,
    duration: str,
    focus_groups: list[str],
    exercises: list[str],
    variation: int,
) -> str:
    """Single Claude call — returns a markdown workout plan."""
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
    groups_text = ", ".join(focus_groups)
    exercise_list = "\n".join(f"- {e}" for e in exercises)
    prompt = (
        f"You are an expert personal trainer. Write a structured {duration} gym workout "
        f"using ONLY the exercises listed below. The session focuses on: {groups_text}.\n\n"
        f"User profile:\n"
        f"- Goal: {goal}\n"
        f"- Experience: {experience}\n"
        f"- {restriction_line}\n"
        f"{variation_line}\n\n"
        f"Exercises to include:\n{exercise_list}\n\n"
        f"IMPORTANT: The entire session — warm-up, all sets, all rest periods, and cool-down — "
        f"must fit within {duration}. Choose an appropriate number of sets per exercise so the "
        f"timing works out. Do not over-program.\n\n"
        f"Format the plan in markdown with:\n"
        f"1. Warm-up: 10–20 minutes on the rowing machine or stationary/spin bike "
        f"(the user runs on non-gym days so do NOT suggest treadmill/running as a warm-up)\n"
        f"2. Main workout — order exercises logically for a real gym session:\n"
        f"   - Lead with the most demanding compound movements\n"
        f"   - Group exercises by area of the gym to minimise equipment changes and walking\n"
        f"   - Finish with isolation or machine work, then mat/core exercises last\n"
        f"   - You may superset antagonist muscle groups (e.g. chest + back) where it makes sense\n"
        f"   - For each exercise: sets × reps (or duration), rest period\n"
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
        "focus_groups": [],
        "selected": [],
        "workout": "",
        "variation": 0,
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
        "Fitness goal",
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
        "Injuries or limitations (leave blank if none)",
        value=st.session_state.restrictions,
    )
    duration = st.selectbox(
        "Session duration",
        ["30 min", "45 min", "60 min", "90 min"],
        index=["30 min", "45 min", "60 min", "90 min"].index(st.session_state.duration),
    )

    focus_groups = st.multiselect(
        "Focus areas (pick 1–3)",
        options=MUSCLE_GROUPS,
        default=st.session_state.focus_groups if st.session_state.focus_groups else [],
    )

    if st.button("Select Exercises", type="primary", disabled=len(focus_groups) == 0):
        st.session_state.goal = goal
        st.session_state.experience = experience
        st.session_state.restrictions = restrictions
        st.session_state.duration = duration
        st.session_state.focus_groups = focus_groups

        # Pre-select all exercises from the chosen groups (deduplicated)
        seen: set[str] = set()
        preselected: list[str] = []
        for group in focus_groups:
            for ex in EXERCISES.get(group, []):
                if ex not in seen:
                    seen.add(ex)
                    preselected.append(ex)

        st.session_state.selected = preselected
        st.session_state.variation = 0
        st.session_state.stage = "selection"
        st.rerun()


def render_selection():
    focus_groups = st.session_state.focus_groups
    st.header("Choose Your Exercises")
    st.caption(
        f"Focus: **{', '.join(focus_groups)}** · "
        f"Goal: **{st.session_state.goal}** · "
        f"Duration: **{st.session_state.duration}**"
    )

    selected = set(st.session_state.selected)
    rendered: set[str] = set()

    # --- Focus group exercises — all pre-checked ---
    for group in focus_groups:
        st.subheader(group)
        for ex in EXERCISES.get(group, []):
            if ex in rendered:
                continue
            rendered.add(ex)
            checked = st.checkbox(ex, value=(ex in selected), key=f"focus_{ex}")
            if checked:
                selected.add(ex)
            else:
                selected.discard(ex)

    # --- Other groups in an expander ---
    other_groups = [g for g in MUSCLE_GROUPS if g not in focus_groups]
    if other_groups:
        with st.expander("Add exercises from other groups"):
            for group in other_groups:
                st.markdown(f"**{group}**")
                for ex in EXERCISES.get(group, []):
                    if ex in rendered:
                        continue
                    rendered.add(ex)
                    checked = st.checkbox(ex, value=(ex in selected), key=f"other_{ex}")
                    if checked:
                        selected.add(ex)
                    else:
                        selected.discard(ex)

    st.session_state.selected = list(selected)

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
                    st.session_state.focus_groups,
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


PRINT_CSS = """
<style>
@media print {
    header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], #MainMenu,
    .stDeployButton, [data-testid="stSidebarNav"] { display: none !important; }
    .stButton, hr { display: none !important; }
    .block-container { padding: 1rem 2rem !important; }
}
</style>
"""

PRINT_BUTTON_HTML = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');
button.print-btn {
    padding: 0.4rem 1rem;
    background: #e9ecef;
    border: 1px solid #ced4da;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    color: #212529;
    font-family: 'Inter', sans-serif;
}
button.print-btn:hover { background: #dee2e6; }
</style>
<button class="print-btn" onclick="window.parent.print()">🖨️ Print / Save as PDF</button>
"""


def render_workout():
    st.markdown(PRINT_CSS, unsafe_allow_html=True)

    st.header("Your Workout")
    st.caption(
        f"Focus: **{', '.join(st.session_state.focus_groups)}** · "
        f"Goal: **{st.session_state.goal}** · "
        f"Experience: **{st.session_state.experience}** · "
        f"Duration: **{st.session_state.duration}**"
    )

    st.markdown(st.session_state.workout)

    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("Regenerate", type="primary"):
            st.session_state.variation += 1
            with st.spinner("Generating a different version…"):
                workout = build_workout(
                    st.session_state.goal,
                    st.session_state.experience,
                    st.session_state.restrictions,
                    st.session_state.duration,
                    st.session_state.focus_groups,
                    st.session_state.selected,
                    st.session_state.variation,
                )
            st.session_state.workout = workout
            st.rerun()
    with col2:
        if st.button("← Start Over"):
            st.session_state.stage = "preferences"
            st.rerun()
    with col3:
        components.html(PRINT_BUTTON_HTML, height=45)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.title("Fitness Chat")

init_state()

stage = st.session_state.stage
if stage == "preferences":
    render_preferences()
elif stage == "selection":
    render_selection()
elif stage == "workout":
    render_workout()
