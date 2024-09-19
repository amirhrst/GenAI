import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
from langchain.llms import OpenAI
import os

# App Configuration
st.set_page_config(page_title="LangChain: Chat with SQL DB")
st.title("LangChain: Chat with SQL DB")
st.subheader("Ener your custom api key,press Enter.")
st.subheader("Choose your sql database and start interacting!")

# Constants
LOCALDB = "USE_LOCALDB"
MYSQL = "USE_MYSQL"
UPLOADDB = "UPLOAD_DB"

# Sidebar Options
radio_opt = ["Use SQLite 3 Database - student.db", "Connect to your MySQL Database", "Upload your SQLite Database"]
selected_opt = st.sidebar.radio(label="Choose the DB you want to chat with", options=radio_opt)

# Variables for uploaded file
uploaded_db_file = None
db_uri = None

# Handle DB selection and input
if radio_opt.index(selected_opt) == 1:
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("Provide MySQL Host")
    mysql_user = st.sidebar.text_input("MySQL User")
    mysql_password = st.sidebar.text_input("MySQL Password", type="password")
    mysql_db = st.sidebar.text_input("MySQL Database")
elif radio_opt.index(selected_opt) == 2:
    db_uri = UPLOADDB
    uploaded_db_file = st.sidebar.file_uploader("Upload SQLite .db file (max 5MB)", type=["db"], accept_multiple_files=False)
    if uploaded_db_file is not None:
        if uploaded_db_file.size > 5 * 1024 * 1024:  # Check if the file size exceeds 5MB
            st.sidebar.error("File size exceeds 5MB limit. Please upload a smaller file.")
            uploaded_db_file = None  # Reset the file if it's too large
else:
    db_uri = LOCALDB

# API Selection
api_selection = st.radio("Select API Provider", ["Groq API", "OpenAI"])

# API Key Input based on selection
api_key = None
if api_selection == "Groq API":
    api_key = st.sidebar.text_input("Enter your Groq API Key", type="password")
    if not api_key:
        st.info("Please add the Groq API key.")
        st.stop()
    # Initialize the Groq LLM model
    llm = ChatGroq(groq_api_key=api_key, model_name="Llama3-8b-8192", streaming=True)
elif api_selection == "OpenAI":
    api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
    if not api_key:
        st.info("Please add the OpenAI API key.")
        st.stop()
    # Initialize the OpenAI LLM model
    llm = OpenAI(openai_api_key=api_key)

# Function to configure the database connection
@st.cache_resource(ttl=7200)
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None, uploaded_db_path=None):
    try:
        if db_uri == LOCALDB:
            dbfilepath = (Path(__file__).parent / "student.db").absolute()
            creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
            return SQLDatabase(create_engine("sqlite:///", creator=creator))
        elif db_uri == MYSQL:
            # Ensure all MySQL parameters are provided
            if not mysql_host or not mysql_user or not mysql_password or not mysql_db:
                st.error("Incomplete MySQL connection details.")
                return None
            return SQLDatabase(create_engine(
                f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
            ))
        elif db_uri == UPLOADDB and uploaded_db_path is not None:
            creator = lambda: sqlite3.connect(f"file:{uploaded_db_path}?mode=ro", uri=True)
            return SQLDatabase(create_engine("sqlite:///", creator=creator))
    except Exception as e:
        st.error(f"Error configuring the database: {e}")
        return None

# Save uploaded database to temporary path if uploaded
db = None
if db_uri == UPLOADDB and uploaded_db_file:
    # Save uploaded file to a temporary location
    temp_db_path = os.path.join("temp_db", uploaded_db_file.name)
    os.makedirs(os.path.dirname(temp_db_path), exist_ok=True)
    with open(temp_db_path, "wb") as f:
        f.write(uploaded_db_file.getbuffer())

    # Configure the uploaded database
    db = configure_db(db_uri, uploaded_db_path=temp_db_path)
elif db_uri == MYSQL:
    # Ensure all MySQL parameters are filled before configuring the database
    if not mysql_host or not mysql_user or not mysql_password or not mysql_db:
        st.error("Please provide all MySQL connection details.")
    else:
        db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db)
else:
    # Configure the SQLite database
    db = configure_db(db_uri)

# Check if the db is correctly configured
if db is None:
    st.error("Failed to configure the database. Please check your database settings and try again.")
    st.stop()

# Initialize the toolkit and agent with enhanced error handling
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Creating the agent with parsing error handling
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True  # Enables automatic retry on parsing errors
)

# Initialize chat history if not already present
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Display existing chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Handle user query input
user_query = st.chat_input(placeholder="Ask anything from the database")

# Process the user query if provided
if user_query:
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    # Combine the conversation history into a single prompt for the LLM
    conversation_prompt = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state["messages"]]
    )

    # Run the agent and display the response
    with st.chat_message("assistant"):
        try:
            streamlit_callback = StreamlitCallbackHandler(st.container())
            response = agent.run(conversation_prompt, callbacks=[streamlit_callback])

            # Append the response to session state
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(response)
        except Exception as e:
            st.error(f"An error occurred while processing your query: {e}")
