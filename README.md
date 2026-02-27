# FitnessChat

A personalized AI fitness companion that generates tailored workout plans based on your goals, experience level, and preferred workout type.

## Features

- **Structured workout generation** — select your workout length and focus type, then generate a plan with one click
- **Generate Different Workout** — get a meaningfully varied alternative without changing your settings
- **Tailored prompts by workout type:**
  - **Freeweights / Circuit** — exercises with sets, reps, form tips, muscles worked, and equipment needed
  - **Running / Indoor Cardio** — structured session plan with warm-up, main intervals/segments, and cool-down
- **User profile** — personalizes output based on fitness goal, experience level, and any injuries or limitations

## Technologies

- **Python**
- **Anthropic Claude** (`claude-sonnet-4-6`) — workout generation
- **Streamlit** — web UI

## How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Pat-Reen/FitnessChat.git
   cd FitnessChat
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**

   Create a `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Run the app:**
   ```bash
   python -m streamlit run app.py
   ```

   The app will be available at `http://localhost:8501`.

## License

MIT
