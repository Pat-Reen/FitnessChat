import pandas as pd
import anthropic
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# --- Dataset Loading (Adapt This!) ---
def load_exercise_data(csv_file):
    df = pd.read_csv(csv_file)
    # ... potentially extract relevant columns & data cleaning ... 
    return df 

# Replace 'your_data.csv' with your actual filename
exercise_data = load_exercise_data('megaGymDataset.csv') 

# ---  Process User Queries ---
def gather_user_preferences():
    goal = st.selectbox("What's your main fitness goal?", 
                        ["Weight Loss", "Build Muscle", "Endurance", "General Fitness"])
    experience = st.radio("What's your experience level?",
                          ["Beginner", "Intermediate", "Advanced"])
    restrictions = st.checkbox("Any injuries or limitations?")
    # ... more questions can be added

    return goal, experience, restrictions

def process_query(query, exercise_data, user_preferences=None):
    if user_preferences is None:
         # First Time - Gather preferences
         goal, experience, restrictions = gather_user_preferences()
         return process_query(query, exercise_data, 
                              user_preferences={"goal": goal, 
                                            "experience": experience, 
                                            "restrictions": restrictions})

    # 2. General Workout or Fitness Questions using Claude
    prompt = craft_fitness_prompt(query, exercise_data)  # Helper function below
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# --- Helper Functions (You might need to adjust) ---
def user_asks_about_exercise(query):
    # Simple keyword detection, make this smarter!
    return "describe" in query or "how to" in query 

def extract_exercise_name(query):
    # Basic extraction,  improve this with NLP techniques if needed
    return query.split("describe ")[1] 

def describe_exercise(exercise, data):
    # ... lookup  exercise in 'data' & construct a description ...
    return "Description from dataset here..." 

def craft_fitness_prompt(query, data):
    # ... construct the 'You are a fitness expert...' type prompt  ...
    return "User Query: " + query 

# --- Streamlit UI ---
st.title("Fitness Knowledge Bot")

# Gather preferences right at the start 
user_preferences = gather_user_preferences() 

user_input = st.text_input("Ask me about workouts or fitness...")

if st.button("Submit"): 
  chatbot_response = process_query(user_input, exercise_data, user_preferences)
  st.write("Chatbot:", chatbot_response) 
