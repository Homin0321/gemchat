import re
from io import BytesIO

import PIL.Image
import streamlit as st
from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    ThinkingConfig,
    Tool,
    UrlContext,
)
from streamlit_paste_button import paste_image_button as pbutton

API_KEY = st.secrets["api_key"]


# Initialize the Gemini client (only once)
@st.cache_resource  # Cache the client to avoid re-initialization
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


@st.dialog("Input Text", width="large")
def input_text():
    text = st.session_state.get("text", "")  # Use get to avoid KeyError
    text = st.text_area("Edit:", text, height=600, label_visibility="collapsed")
    if st.button("Save Text"):
        st.session_state.text = text
        st.rerun()


@st.dialog("Markdown Source", width="large")
def show_markdown():
    if st.session_state.get("messages"):  # Check if messages exist
        length = len(st.session_state.messages)
        if length > 0:
            st.code(
                st.session_state.messages[length - 1]["content"], language="markdown"
            )


# Page configuration
st.set_page_config(page_title="Gemini Chat", page_icon="💬", layout="wide")

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
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]
if "gemini_chat_session" not in st.session_state:
    st.session_state.gemini_chat_session = None
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemini-flash-lite-latest"

with st.sidebar:
    st.header("Gemini Chatbot")

    paste_result = pbutton(
        "Upload Clipboard Image",
        text_color="#000000",
        background_color="#FFFFFF",
        hover_background_color="#FF8884",
    )
    if paste_result.image_data is not None:
        # Show the pasted image
        st.image(paste_result.image_data, width="stretch")
        # Persist the image as bytes in session state for safe access outside the sidebar
        _buf = BytesIO()
        paste_result.image_data.save(_buf, format="PNG")
        st.session_state.pasted_image = _buf.getvalue()

    # Simple text input for quick editing
    # flatten text for display in single-line input to avoid st.text_input error with newlines
    text_input_val = st.session_state.text.replace("\n", " ")
    quick_text = st.text_input(
        "Quick Text Input",
        value=text_input_val,
        label_visibility="collapsed",
    )
    if quick_text != text_input_val:
        st.session_state.text = quick_text
        st.rerun()

    if st.button("Input Text", width="stretch"):
        input_text()

    if st.session_state.get("text"):
        preview = st.session_state.text
        if len(preview) > 20:
            preview = preview[:20] + "..."
        st.caption(f"📝 {preview}")

    if st.button("Clear Text", width="stretch"):
        st.session_state.text = ""
        st.session_state.pasted_image = None
        st.rerun()

    if st.button("Show Markdown", width="stretch"):
        show_markdown()

    if st.button("Clear Chat History", width="stretch", key="clear_chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        st.session_state.gemini_chat_session = None  # Reset chat session object
        st.session_state.text = ""
        st.session_state.pasted_image = None
        st.rerun()  # Rerun the app to reflect the cleared state

    default_prompt_options = [
        "다음 내용 상세 정리해줘:",
        "다음 내용 부연 설명해줘:",
        "다음 내용 요약해줘:",
        "다음 번역해줘:",
        "다음 영어 표현 상세 설명해줘:",
        "다음 내용 보완해줘:",
        "다음 문장 재작성해줘:",
        "다음 논리적으로 재작성해줘:",
        "다음 간결한 표현으로 수정해줘:",
    ]

    default_prompt = st.selectbox(
        "Select Prompt:",
        options=default_prompt_options,
        index=0,
        key="default_prompt_select",
    )

    if st.button("Send Prompt", width="stretch"):
        st.session_state.selected_prompt = default_prompt
        st.rerun()

    # Model Selection
    model_options = [
        "gemini-flash-lite-latest",
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    ]

    selected_model = st.selectbox(
        "Select Model:",
        options=model_options,
        index=model_options.index(st.session_state.selected_model)
        if st.session_state.selected_model in model_options
        else 0,
        key="model_select",
    )

    # Add a checkbox to include or exclude the config
    ground_search = st.checkbox(
        "Ground Google Search", value=st.session_state.get("ground_search", False)
    )
    url_context = st.checkbox(
        "Use URL Context", value=st.session_state.get("url_context", False)
    )

    # Thinking Budget Slide
    thinking_budget = st.slider(
        "Thinking Budget",
        min_value=0,
        max_value=24576,
        value=st.session_state.get("thinking_budget", 0),
        step=1024,
    )

    # Only recreate session if model or settings actually changed
    if (
        selected_model != st.session_state.get("selected_model")
        or ground_search != st.session_state.get("ground_search")
        or url_context != st.session_state.get("url_context")
        or thinking_budget != st.session_state.get("thinking_budget")
    ):
        if st.button("Apply Changes", width="stretch"):
            st.session_state.gemini_chat_session = None
            st.session_state.selected_model = selected_model
            st.session_state.ground_search = ground_search
            st.session_state.url_context = url_context
            st.session_state.thinking_budget = thinking_budget
            st.rerun()


# --- Gemini Model Interaction ---
# Function to configure and get the chat model
def get_gemini_chat_session(model_name):
    try:
        client = get_gemini_client(API_KEY)

        tools_list = []
        thinking_budget = st.session_state.get("thinking_budget", 0)

        if st.session_state.get("ground_search", False):
            google_search_tool = Tool(google_search=GoogleSearch())
            tools_list.append(google_search_tool)
        elif st.session_state.get("url_context", False):
            url_context_tool = Tool(url_context=UrlContext())
            tools_list.append(url_context_tool)

        gemini_config = GenerateContentConfig(
            tools=tools_list,
            response_modalities=["TEXT"],
            thinking_config=ThinkingConfig(thinking_budget=thinking_budget),
        )

        chat = client.chats.create(model=model_name, config=gemini_config)

        return chat

    except Exception as e:
        st.error(f"Error configuring Google AI or starting chat: {e}")
        return None


def fix_markdown_symbol_issue(md: str) -> str:
    # Pattern to find code blocks (triple backticks or single backtick)
    # We want to exclude these from symbol escaping
    # Captures: 1. Triple backticks blocks, 2. Inline code (simple `...`)
    code_block_pattern = r"(```[\s\S]*?```|`[^`]*`)"

    parts = re.split(code_block_pattern, md)

    # Pattern for the bold fix
    bold_pattern = re.compile(r"\*\*(.+?)\*\*(\s*)", re.DOTALL)

    def bold_repl(m):
        inner = m.group(1)
        after = m.group(2)
        inner = inner.strip()
        # Add space after ** if content contains symbols and no space exists
        if re.search(r"[^0-9A-Za-z\s가-힣]", inner) and after == "":
            return f"**{inner}** "
        if inner != m.group(1):
            return f"**{inner}**{after}"
        return m.group(0)

    # Pattern for the italic fix (avoid matching bold **)
    italic_pattern = re.compile(
        r"(?<!\*)\*(?![*])(.+?)(?<!\*)\*(?![*])(\s*)", re.DOTALL
    )

    def italic_repl(m):
        inner = m.group(1)
        after = m.group(2)
        # Add space after * if content contains quotes and no space exists
        if re.search(r"['\"]", inner) and after == "":
            return f"*{inner}* "
        return m.group(0)

    for i in range(len(parts)):
        # Even indices are regular text; Odd indices are code blocks (the delimiters)
        if i % 2 == 0:
            part = parts[i]

            # 1. Escape $ only if followed by a digit (e.g. $100)
            part = re.sub(r"\$(\d)", r"\\$\1", part)

            # 2. Escape ~ to prevent strikethrough interpretation
            part = part.replace("~", "\\~")

            # 3. Apply bold spacing fix
            part = bold_pattern.sub(bold_repl, part)

            # 4. Apply italic spacing fix
            part = italic_pattern.sub(italic_repl, part)

            parts[i] = part

    return "".join(parts)


# Attempt to get/create chat session if API key is available and session doesn't exist
if st.session_state.gemini_chat_session is None:
    st.session_state.gemini_chat_session = get_gemini_chat_session(
        st.session_state.selected_model
    )

# --- Display Chat History ---
# Create a container for chat messages to prevent layout issues
chat_container = st.container()
with chat_container:
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            # Add message index for debugging if needed
            st.markdown(msg["content"])

# --- Handle User Input ---
# Place input at the bottom and handle it properly
selected_prompt = st.session_state.pop("selected_prompt", None)

user_input = st.chat_input("What would you like to ask?")

# Process input from either the form or selected prompt
prompt = None
if user_input:
    prompt = user_input
elif selected_prompt:
    prompt = selected_prompt

if prompt:
    # Ensure chat session is initialized
    if st.session_state.gemini_chat_session is None:
        with st.spinner("Initializing chat session..."):
            st.session_state.gemini_chat_session = get_gemini_chat_session(
                st.session_state.selected_model
            )

        # If it's still None after trying, show error and stop
        if st.session_state.gemini_chat_session is None:
            st.error(
                "Failed to initialize chat session. Please check API key and configuration."
            )
            st.stop()

    # Add user message to session state and display it
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)

    # Display the new user message
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

        # Show loading indicator
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤔 Thinking...")

            try:
                response_stream = chat.send_message_stream(input_payload)
                full_response_content = ""

                for chunk in response_stream:
                    chunk_text = ""
                    # Safely access nested structure based on the provided example
                    try:
                        # Check if candidates exist and have content with parts
                        if hasattr(chunk, "candidates") and chunk.candidates:
                            candidate = chunk.candidates[0]
                            if hasattr(candidate, "content") and candidate.content:
                                if (
                                    hasattr(candidate.content, "parts")
                                    and candidate.content.parts
                                ):
                                    # Iterate through parts and append text
                                    for part in candidate.content.parts:
                                        # Assuming 'text' attribute exists in each part
                                        if hasattr(part, "text") and part.text:
                                            chunk_text += part.text

                    except (AttributeError, IndexError, TypeError) as e:
                        # Continue to the next chunk if there's an error
                        continue

                    # If text was extracted from this chunk, append and update display
                    if chunk_text:
                        full_response_content += chunk_text
                        # Update placeholder with accumulated text + streaming indicator
                        message_placeholder.markdown(full_response_content + "▌")

                # After the loop, display the final full content without the indicator
                if full_response_content:
                    full_response_content = fix_markdown_symbol_issue(
                        full_response_content
                    )
                    message_placeholder.markdown(full_response_content)
                    # Add Gemini's response to session state
                    assistant_message = {
                        "role": "assistant",
                        "content": full_response_content,
                    }
                    st.session_state.messages.append(assistant_message)
                else:
                    # Handle empty response
                    error_message = "*No response generated. This might be due to content filtering or other restrictions.*"
                    message_placeholder.markdown(error_message)
                    assistant_message = {"role": "assistant", "content": error_message}
                    st.session_state.messages.append(assistant_message)

            except Exception as e:
                # Handle errors during streaming
                error_message = f"*Error generating response: {str(e)}*"
                message_placeholder.markdown(error_message)
                assistant_message = {"role": "assistant", "content": error_message}
                st.session_state.messages.append(assistant_message)

    except Exception as e:
        # Handle errors before starting the stream
        st.error(f"An error occurred while sending message: {e}")
        error_message = f"*Error: Could not send message. {str(e)}*"
        assistant_message = {"role": "assistant", "content": error_message}
        st.session_state.messages.append(assistant_message)

    # Clear text after successful message send
    st.session_state.text = ""
    st.rerun()
