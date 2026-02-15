# Gemini Chatbot with Streamlit

This Streamlit application provides a sophisticated interface for interacting with Google's Gemini language models. It leverages the latest `google-genai` SDK and includes advanced features like Google Search grounding, URL context analysis, image inputs, and "thinking" budget configuration for reasoning models.

## Features

*   **Model Selection:** Choose from the latest Gemini models, including:
    *   `gemini-flash-lite-latest`
    *   `gemini-3-flash-preview`
    *   `gemini-3-pro-preview`
    *   `gemini-2.5-flash-lite`
    *   `gemini-2.5-flash`
*   **Advanced Tools:**
    *   **Ground Google Search:** Enable the model to perform Google Searches to ground its responses in real-time data.
    *   **URL Context:** Allow the model to utilize context from URLs.
    *   **Thinking Budget:** Configure the "thinking" budget for reasoning-capable models (up to 24k tokens).
*   **Multimedia Support:**
    *   **Clipboard Image Upload:** Paste images directly from your clipboard to send to the model.
*   **Enhanced Input Options:**
    *   **Pre-defined Prompts:** Quickly select from a list of useful prompts (summarization, translation, editing, etc.).
    *   **Quick Text Input:** A sidebar input for quick text appending.
    *   **Large Text Editor:** A dedicated dialog for inputting and editing large blocks of text.
*   **Chat Interface:**
    *   Streaming responses for immediate feedback.
    *   Markdown rendering with custom fixes for better display (LaTeX, bold/italic spacing).
    *   Chat history management (view and clear).
    *   Raw Markdown source viewer.

## Prerequisites

*   Python 3.8+
*   A Google Cloud Project with the Gemini API enabled (or an API key from Google AI Studio).

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd gemchat
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate     # On Windows
    ```

3.  **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Obtain an API Key:**
    Get your API key from Google AI Studio: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

2.  **Create a `.env` file:**
    Create a file named `.env` in the root directory of the project. Add your API key:

    ```env
    API_KEY=your_actual_api_key_here
    ```

## Usage

1.  **Run the Streamlit application:**

    ```bash
    streamlit run app.py
    ```

2.  **Interact with the Chatbot:**
    *   **Sidebar Controls:**
        *   **Upload Clipboard Image:** Paste an image from your clipboard.
        *   **Quick/Input Text:** Add context text to be sent with your prompt.
        *   **Select Prompt:** Choose a template for common tasks.
        *   **Select Model:** Switch between different Gemini versions.
        *   **Ground Google Search / Use URL Context:** Toggle tools.
        *   **Thinking Budget:** Adjust the reasoning capability slider.
        *   **Apply Changes:** Click this if you change model settings during a session.
    *   **Chat Input:** Type your message at the bottom of the screen.

## Code Structure

*   **`app.py`:** The main application logic.
    *   Initializes the `google-genai` client.
    *   Manages Streamlit session state for chat history, settings, and inputs.
    *   Handles the chat interface, sidebar, and tool configurations.
    *   Streams responses from the Gemini API.
*   **`utils.py`:** Contains helper functions, specifically `fix_markdown_symbol_issue` to ensure Markdown renders correctly in Streamlit (handling LaTeX symbols and formatting edge cases).
*   **`requirements.txt`:** Lists dependencies: `streamlit`, `streamlit_paste_button`, `google-genai`, `python-dotenv`.

## Future Enhancements

*   **Multi-modal History:** Better visualization of images in the chat history.
*   **File Uploads:** Support for PDF or text file uploads for context.
*   **Custom System Instructions:** Allow users to set a system prompt.