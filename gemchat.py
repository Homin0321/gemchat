import streamlit as st
import google.generativeai as genai
from streamlit_paste_button import paste_image_button as pbutton
from io import BytesIO
import PIL.Image
import os

API_KEY = st.secrets["api_key"]
TEMPERATURE = 0.5

@st.dialog("Input Text", width="large")
def input_text():
    text = ''
    if "text" in st.session_state:
        text = st.session_state.text

    text = st.text_area("Edit:", text, height=600, label_visibility="collapsed")
    st.session_state.text = text

@st.dialog("Markdown Source", width="large")
def show_markdown():
    length = len(st.session_state.messages)
    if length > 0:
        st.code(st.session_state.messages[length-1]["content"], language="markdown")

# Page configuration
st.set_page_config(
    page_title="💬 Gemini Chat",
    page_icon="🤖",
    layout="wide"
)

with st.sidebar:
    st.header("Gemini Chatbot")

    paste_result = pbutton("Upload Clipboard Image", text_color="#000000",
        background_color="#FFFFFF", hover_background_color="#FF8884")

    if st.button("Input Text", use_container_width=True):
        input_text()

    if st.button("Clear Text", use_container_width=True):
        if "text" in st.session_state:
            st.session_state.text = ''

    if st.button("Show Markdown", use_container_width=True):
        show_markdown()

    if st.button("Clear Chat History", use_container_width=True, key="clear_chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        st.session_state.gemini_chat_session = None  # Reset chat session object
        st.rerun()  # Rerun the app to reflect the cleared state

    # Model Selection
    model_options = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-pro-exp-03-25"
    ]

    selected_model = st.selectbox(
        "Select Model:",
        options=model_options,
        index=0,  # Default to the first model
        key="model_select"  # Use a key for the selectbox
    )

    if st.button("Change Model", use_container_width=True): #Added a button to force model change
        st.session_state.gemini_chat_session = None #Reset the chat session
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        st.rerun()


# --- Initialization ---
# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]

# Initialize chat session object in session state
if "gemini_chat_session" not in st.session_state:
    st.session_state.gemini_chat_session = None

# --- Gemini Model Interaction ---
# Function to configure and get the chat model
def get_gemini_chat_session(model_name):
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(
            model_name,
            generation_config=genai.types.GenerationConfig(temperature=TEMPERATURE),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        )

        # Convert Streamlit message history to Gemini format
        gemini_history = []
        for msg in st.session_state.messages:
            # Map Streamlit roles ('assistant', 'user') to Gemini roles ('model', 'user')
            role = 'model' if msg["role"] == 'assistant' else msg["role"]
            # Ensure content is always treated as text parts
            parts = [{'text': str(msg["content"])}]  # Ensure content is string
            gemini_history.append({'role': role, 'parts': parts})

        # Remove the last 'model' entry if it exists, as start_chat expects user to start or empty history
        if gemini_history and gemini_history[-1]['role'] == 'model':
            # Keep the initial assistant message if it's the only one
            if len(gemini_history) > 1:
                gemini_history.pop()

        # Start the chat session with history
        return model.start_chat(history=gemini_history)

    except Exception as e:
        st.error(f"Error configuring Google AI or starting chat: {e}")
        return None


# Attempt to get/create chat session if API key is available and session doesn't exist
if st.session_state.gemini_chat_session is None:
    st.session_state.gemini_chat_session = get_gemini_chat_session(selected_model)

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])  # Use markdown for better formatting

# --- Handle User Input ---
if prompt := st.chat_input("What would you like to ask?"):
    # Ensure chat session is initialized
    if st.session_state.gemini_chat_session is None:
        st.session_state.gemini_chat_session = get_gemini_chat_session(selected_model)
        # If it's still None after trying, show error and stop
        if st.session_state.gemini_chat_session is None:
            st.error("Failed to initialize chat session. Please check API key and configuration.")
            st.stop()

    # Add user message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send user message to Gemini and get response (streaming)
    try:
        chat = st.session_state.gemini_chat_session
        # Ensure streaming is enabled
        if "text" in st.session_state:
            prompt = [prompt, st.session_state.text]

        if paste_result.image_data is not None:
            image_bytes = BytesIO()
            paste_result.image_data.save(image_bytes, format='PNG')
            image_bytes = image_bytes.getvalue()
            with open("st_image.png", 'wb') as f:
                f.write(image_bytes)
            image = PIL.Image.open("st_image.png")
            prompt = [prompt, image]
    
        response_stream = chat.send_message(prompt, stream=True)

        full_response_content = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()  # Use a placeholder for stream updates
            try:
                for chunk in response_stream:
                    chunk_text = ""
                    # Safely access nested structure based on the provided example
                    try:
                        # Check if candidates exist and have content with parts
                        if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                            # Iterate through parts and append text
                            for part in chunk.candidates[0].content.parts:
                                # Assuming 'text' attribute exists in each part
                                chunk_text += part.text

                    except (AttributeError, IndexError, TypeError) as e:
                        # Catch potential errors if chunk structure is unexpected
                        # This might happen for non-content chunks or API changes
                        # st.warning(f"Skipping chunk with unexpected structure: {e}") # Uncomment for debugging
                        pass  # Continue to the next chunk

                    # If text was extracted from this chunk, append and update display
                    if chunk_text:
                        full_response_content += chunk_text
                        # Update placeholder with accumulated text + streaming indicator
                        message_placeholder.markdown(full_response_content + "▌")

                # After the loop, display the final full content without the indicator
                message_placeholder.markdown(full_response_content)

            except genai.types.BlockedPromptException as e:
                # Handle cases where the prompt itself was blocked before streaming
                st.error(f"Your prompt was blocked: {e}")
                full_response_content = f"*Prompt blocked by safety settings.*"
                message_placeholder.markdown(full_response_content)
            except Exception as e:
                # Handle other errors during the streaming process
                st.error(f"An error occurred during response generation: {e}")
                full_response_content = f"*Error generating response.*"
                message_placeholder.markdown(full_response_content)

        # Add Gemini's full text response to session state
        # Check if the response is non-empty and not just an error message we added
        if full_response_content and not full_response_content.startswith("*"):
            st.session_state.messages.append({"role": "assistant", "content": full_response_content})
        # Handle cases where the stream finished but produced no text (e.g., safety block on response)
        elif not full_response_content:
            try:
                # Attempt to get more specific feedback if available
                feedback = chat.last_response.prompt_feedback if hasattr(chat, 'last_response') and chat.last_response else None
                finish_reason_val = chat.last_response.candidates[0].finish_reason if (
                    hasattr(chat, 'last_response') and chat.last_response and
                    chat.last_response.candidates
                ) else "Unknown"
                # Convert finish_reason enum to string if possible
                finish_reason = getattr(finish_reason_val, 'name', str(finish_reason_val))

                block_reason_val = feedback.block_reason if feedback else "Unknown"
                # Convert block_reason enum to string if possible
                block_reason = getattr(block_reason_val, 'name', str(block_reason_val))

                reason_text = f"Finish Reason: {finish_reason}, Block Reason: {block_reason}"

            except Exception as e:
                # Fallback if accessing response details fails
                reason_text = f"Unknown reason (possibly safety filter or stop sequence). Error accessing details: {e}"

            error_message = f"*Response was empty or blocked. {reason_text}*"
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            # Avoid showing a warning if we already displayed an error message during streaming
            if not full_response_content.startswith("*"):
                st.warning(error_message)  # Show warning in the main chat area too
        else:
            # If full_response_content contains one of our error messages, just add it
            st.session_state.messages.append({"role": "assistant", "content": full_response_content})

    except Exception as e:
        # Handle errors before starting the stream (e.g., connection issue, API key during send)
        st.error(f"An error occurred while sending message: {e}")
        # Add an error message to the chat history
        st.session_state.messages.append({"role": "assistant", "content": f"*Error: Could not get response. {e}*"})

