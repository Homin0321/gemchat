import streamlit as st
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, ThinkingConfig, UrlContext
from streamlit_paste_button import paste_image_button as pbutton
from io import BytesIO
import PIL.Image

API_KEY = st.secrets["api_key"]

# Initialize the Gemini client (only once)
@st.cache_resource  # Cache the client to avoid re-initialization
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

@st.dialog("Input Text", width="large")
def input_text():
    text = st.session_state.get("text", "")  # Use get to avoid KeyError
    text = st.text_area("Edit:", text, height=600, label_visibility="collapsed")
    st.session_state.text = text

@st.dialog("Markdown Source", width="large")
def show_markdown():
    if st.session_state.get("messages"):  # Check if messages exist
        length = len(st.session_state.messages)
        if length > 0:
            st.code(st.session_state.messages[length - 1]["content"], language="markdown")

# Page configuration
st.set_page_config(
    page_title="Gemini Chat",
    page_icon="💬",
    layout="wide"
)

# --- Session State Defaults ---
if "text" not in st.session_state:
    st.session_state.text = ""
if "pasted_image" not in st.session_state:
    st.session_state.pasted_image = None
if "thinking_budget" not in st.session_state:
    st.session_state.thinking_budget = 0
if "ground_search" not in st.session_state:
    st.session_state.ground_search = False
if "url_context" not in st.session_state:
    st.session_state.url_context = False

with st.sidebar:
    st.header("Gemini Chatbot")

    paste_result = pbutton("Upload Clipboard Image", text_color="#000000",
        background_color="#FFFFFF", hover_background_color="#FF8884")
    if paste_result.image_data is not None:
        # Show the pasted image
        st.image(paste_result.image_data, use_container_width=True)
        # Persist the image as bytes in session state for safe access outside the sidebar
        _buf = BytesIO()
        paste_result.image_data.save(_buf, format='PNG')
        st.session_state.pasted_image = _buf.getvalue()

    if st.button("Input Text", use_container_width=True):
        input_text()

    if st.session_state.get("text"):
        preview = st.session_state.text
        if len(preview) > 20:
            preview = preview[:20] + "..."
        st.caption(f"📝 {preview}")

    if st.button("Clear Text", use_container_width=True):
        st.session_state.text = ''
        st.session_state.pasted_image = None
        st.rerun()

    if st.button("Show Markdown", use_container_width=True):
        show_markdown()

    if st.button("Clear Chat History", use_container_width=True, key="clear_chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        st.session_state.gemini_chat_session = None  # Reset chat session object
        st.session_state.text = ''
        st.session_state.pasted_image = None
        st.rerun()  # Rerun the app to reflect the cleared state

    default_prompt_options = [
        "다음 내용 상세 정리해줘:",
        "다음 내용 요약해줘:",
        "다음 내용 부연 설명해줘:"
    ]

    default_prompt = st.selectbox(
        "Select Prompt:",
        options=default_prompt_options,
        index=0,
        key="default_prompt_select"
    )

    if st.button("Send Prompt", use_container_width=True):
        st.session_state.selected_prompt = default_prompt
        st.rerun()

    # Model Selection
    model_options = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
    ]

    selected_model = st.selectbox(
        "Select Model:",
        options=model_options,
        index=0,  # Default to the first model
        key="model_select"  # Use a key for the selectbox
    )

    # Add a checkbox to include or exclude the config
    ground_search = st.checkbox("Ground Google Search", value=False)
    url_context = st.checkbox("Use URL Context", value=False)

    # Thinking Budget Slide
    thinking_budget = st.slider(
        "Thinking Budget", min_value=0, max_value=24576,
        value=st.session_state.get("thinking_budget", 0), step=1024
    )

    if st.button("Change Model", use_container_width=True):
        st.session_state.gemini_chat_session = None
        st.session_state.ground_search = ground_search
        st.session_state.url_context = url_context
        st.session_state.thinking_budget = thinking_budget
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
        client = get_gemini_client(API_KEY)

        tools_list = []
        thinking_budget = st.session_state.get("thinking_budget", 0)

        if st.session_state.get("ground_search", False):
            google_search_tool = Tool(
                google_search=GoogleSearch()
            )
            tools_list.append(google_search_tool)
        elif st.session_state.get("url_context", False):
            url_context_tool = Tool(
                url_context=UrlContext()
            )
            tools_list.append(url_context_tool)

        gemini_config = GenerateContentConfig(
            tools=tools_list,
            response_modalities=["TEXT"],
            thinking_config=ThinkingConfig(thinking_budget=thinking_budget)
        )

        chat = client.chats.create(
            model=model_name,
            config=gemini_config
        )

        return chat

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
selected_prompt = st.session_state.pop("selected_prompt", None)
prompt = selected_prompt or st.chat_input("What would you like to ask?")

if prompt:
    # Ensure st.session_state.text is initialized and persists
    if "text" not in st.session_state:
        st.session_state.text = ""
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

        # Build a clean list of parts to send (text, optional extra text, optional image)
        parts = [prompt]
        if st.session_state.text:
            parts.append(st.session_state.text)

        if st.session_state.pasted_image is not None:
            try:
                image = PIL.Image.open(BytesIO(st.session_state.pasted_image))
                parts.append(image)
            except Exception as e:
                st.error(f"Error processing image: {e}")
            finally:
                # Clear after attempting to attach once so we don't resend repeatedly
                st.session_state.pasted_image = None

        # If only one part (just the prompt), send a string; otherwise send the list of parts
        input_payload = parts[0] if len(parts) == 1 else parts

        response_stream = chat.send_message_stream(input_payload)

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
                                if hasattr(part, 'text') and part.text:
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
                last_resp = getattr(chat, 'last_response', None)
                feedback = getattr(last_resp, 'prompt_feedback', None)
                candidate0 = None
                if last_resp and getattr(last_resp, 'candidates', None):
                    candidate0 = last_resp.candidates[0]
                finish_reason_val = getattr(candidate0, 'finish_reason', 'Unknown')
                finish_reason = getattr(finish_reason_val, 'name', str(finish_reason_val))
                block_reason_val = getattr(feedback, 'block_reason', 'Unknown')
                block_reason = getattr(block_reason_val, 'name', str(block_reason_val))
                reason_text = f"Finish Reason: {finish_reason}, Block Reason: {block_reason}"
            except Exception as e:
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