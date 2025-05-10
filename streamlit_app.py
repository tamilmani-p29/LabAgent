import streamlit as st
from sqlalchemy import create_engine
from sql_agent import agent, Dependencies
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the database engine
db_engine = create_engine(os.getenv("DATABASE_URL"))
deps = Dependencies(db_engine=db_engine)

# Streamlit app configuration
st.set_page_config(page_title="Lab360 Insights Agent", layout="wide")

# App title
st.title("Lab360 Insights Agent")

# Initialize chat history if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add initial system message
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I'm your database insights assistant. How can I help you today?"
    })

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the agent and display assistant response
    try:
        with st.spinner("Processing..."):
            response = agent.run_sync(prompt, deps=deps)

        if response and response.output:
            assistant_response = response.output.detail
            # Display and store assistant response
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response
            })
        else:
            with st.chat_message("assistant"):
                st.error("I'm having trouble responding right now. Please try again.")
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Error: {str(e)}")
