import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Get API key from environment or Streamlit secrets
def get_api_key():
    # Try environment variable first (local development)
    api_key = os.getenv("GEMINI_API_KEY")

    # If not found, try Streamlit secrets (cloud deployment)
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (KeyError, FileNotFoundError):
            pass

    return api_key

# Initialize Gemini client
api_key = get_api_key()
if not api_key:
    st.error("❌ GEMINI_API_KEY not found! Please add it to Streamlit secrets or your .env file.")
    st.stop()

genai.configure(api_key=api_key)

# Set page configuration
st.set_page_config(
    page_title="George's Gaming Buddy",
    page_icon="🎮",
    layout="wide"
)

# Personality system prompts
PERSONALITY_PROMPTS = {
    "Friendly 😊": "You are a friendly gaming assistant who talks like a close friend. You help gamers with game strategies, tips, recommendations, troubleshooting, and anything gaming-related. You're warm, supportive, and use casual language. You get excited about gaming with your friend and share their enthusiasm!",
    "Professional 💼": "You are a professional gaming consultant. You provide rigorous, accurate, and well-researched advice about game strategies, tips, recommendations, troubleshooting, and gaming-related topics. Your responses are clear, structured, and authoritative. You maintain a professional tone while being helpful.",
    "Humorous 😄": "You are a humorous gaming buddy who loves to crack jokes and keep things fun! You help gamers with strategies, tips, recommendations, and troubleshooting, but you do it with wit, humor, and playful banter. You make gaming discussions entertaining while still being helpful. Drop gaming memes and funny references when appropriate!"
}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personality" not in st.session_state:
    st.session_state.personality = "Friendly 😊"

# Function to reset chat with new personality
def reset_chat_with_personality(personality):
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "system",
        "content": PERSONALITY_PROMPTS[personality]
    })
    st.session_state.personality = personality

# Initialize with default personality if empty
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "system",
        "content": PERSONALITY_PROMPTS[st.session_state.personality]
    })

# App title and description
st.title("🎮 George's Gaming Buddy")
st.markdown("### Welcome, Gamer! 👋")
st.markdown("""
🎯 **What I Can Do For You:**
- 🗺️ Provide expert game strategies and walkthroughs
- 💡 Recommend games based on your preferences
- 🛠️ Help troubleshoot gaming issues and optimize performance
- 🎮 Share tips, tricks, and hidden secrets
- 📊 Discuss gaming news, trends, and competitive strategies
- 🖥️ Advise on gaming hardware and setup

Let's level up your gaming experience together! 🚀
""")

# Sidebar with information
with st.sidebar:
    st.header("🎭 AI Personality")

    # Personality selector
    selected_personality = st.selectbox(
        "Choose your AI's personality:",
        options=list(PERSONALITY_PROMPTS.keys()),
        index=list(PERSONALITY_PROMPTS.keys()).index(st.session_state.personality),
        help="Select how your AI assistant should interact with you"
    )

    # Update personality if changed
    if selected_personality != st.session_state.personality:
        reset_chat_with_personality(selected_personality)
        st.rerun()

    # Display current personality description
    personality_descriptions = {
        "Friendly 😊": "Warm and friendly, chat like friends",
        "Professional 💼": "Rigorous and professional, give accurate advice",
        "Humorous 😄": "Relaxed and humorous, interesting chat"
    }
    st.caption(f"*{personality_descriptions[selected_personality]}*")

    st.divider()

    st.header("ℹ️ About")
    st.info("""
    🎮 **George's Gaming Buddy**

    Powered by:
    - **Google Gemini API** (gemini-2.5-flash)
    - **Streamlit** for the interface

    Your personal gaming companion! 🚀
    """)

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        reset_chat_with_personality(st.session_state.personality)
        st.rerun()

# Display chat messages (excluding system message)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("💬 Ask me anything about gaming..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Build chat history for Gemini
            gemini_history = []
            system_instruction = None

            for msg in st.session_state.messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                elif msg["role"] == "user":
                    gemini_history.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
                elif msg["role"] == "assistant":
                    gemini_history.append({
                        "role": "model",
                        "parts": [msg["content"]]
                    })

            # Initialize model with system instruction
            model = genai.GenerativeModel(
                model_name='models/gemini-2.5-flash',
                system_instruction=system_instruction
            )

            # Start chat with history (excluding the current message)
            chat = model.start_chat(history=gemini_history)

            # Send the current message and get streaming response
            response = chat.send_message(prompt, stream=True)

            # Stream the response
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"❌ Error: {str(e)}\n\nPlease check your GEMINI_API_KEY in the .env file."
            message_placeholder.markdown(full_response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
