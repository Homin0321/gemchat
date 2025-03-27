# Gemini Chatbot with Streamlit

This Streamlit application provides a user-friendly interface for interacting with Google's Gemini language models. It allows users to select from different Gemini models, engage in conversational chats, and view the underlying Markdown source for the responses.

## Features

*   **Model Selection:** Choose from available Gemini models (e.g., "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-pro-exp-03-25") via a dropdown in the sidebar.
*   **Chat Interface:**  A standard chat interface with message bubbles for both user input and Gemini responses.
*   **Streaming Responses:**  Gemini responses are displayed in a streaming fashion, providing a more interactive experience.
*   **Markdown Support:**  Responses are rendered as Markdown for better formatting.
*   **Input Text Area:** Allows users to input and edit a large block of text that can be appended to the prompt.
*   **Markdown Source Viewer:**  Displays the raw Markdown source of the last Gemini response.
*   **Chat History:**  Maintains a history of the conversation, allowing users to review previous interactions.
*   **Clear Chat History:**  Clears the chat history and resets the Gemini chat session.
*   **Error Handling:**  Includes robust error handling for API issues, blocked prompts, and unexpected responses.
*   **Safety Settings:** Configures safety settings to block harmful content.

## Prerequisites

*   Python 3.7+
*   Streamlit
*   Google Generative AI (Gemini) library

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the required packages:**

    ```bash
    pip install streamlit google-generativeai
    ```

## Configuration

1.  **Set up API Key:**

    *   Obtain an API key from the Google AI Studio: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

2.  **Create a `.streamlit/secrets.toml` file:**

    Create a directory named `.streamlit` in the same directory as your `app.py` file (or whatever you named your streamlit app). Inside the `.streamlit` directory, create a file named `secrets.toml`.

    Add your API key and a password to the `secrets.toml` file:

    ```toml
    passwd = "your_password_here"
    api_key = "YOUR_API_KEY"
    ```

    Replace `"YOUR_API_KEY"` with your actual Gemini API key and `"your_password_here"` with your desired password.

## Usage

1.  **Run the Streamlit application:**

    ```bash
    streamlit run your_app_name.py
    ```

    Replace `your_app_name.py` with the name of your Python file.

2.  **Access the application in your browser:**

    Streamlit will provide a URL (usually `http://localhost:8501`) to access the application in your web browser.

3.  **Interact with the chatbot:**

    *   Select a Gemini model from the sidebar.
    *   Type your message in the chat input field and press Enter.
    *   View the streaming response from Gemini.
    *   Use the "Clear Chat History" button in the sidebar to reset the conversation.
    *   Use the "Input Text" button to open a text area to input and edit longer texts.
    *   Use the "Show Markdown" button to show the markdown source of the last response.

## Code Explanation

*   **`import streamlit as st`:** Imports the Streamlit library for creating the web application.
*   **`import google.generativeai as genai`:** Imports the Google Generative AI library for interacting with Gemini models.
*   **`import os`:** Imports the `os` module for accessing environment variables (though in this case, it's using Streamlit secrets).
*   **`PASSWORD = st.secrets["passwd"]` and `API_KEY = st.secrets["api_key"]`:** Retrieves the API key and password from Streamlit secrets.  This is the preferred way to store sensitive information.
*   **`TEMPERATURE = 0.5`:** Sets the temperature parameter for the Gemini model, controlling the randomness of the responses.
*   **`get_gemini_chat_session(model_name)`:** Configures the Gemini model with the API key, selected model name, temperature, and safety settings. It also converts the Streamlit message history into the format expected by the Gemini API.
*   **`st.session_state`:**  Uses Streamlit's session state to store the chat history (`messages`) and the Gemini chat session object (`gemini_chat_session`).  This allows the application to remember the conversation across user interactions.
*   **Chat Interface:** The code iterates through `st.session_state.messages` to display the chat history.  It uses `st.chat_message` to create message bubbles for each role (user and assistant) and `st.markdown` to render the content as Markdown.
*   **User Input:** The `st.chat_input` function creates the input field for users to type their messages.
*   **Streaming Responses:** The code uses `chat.send_message(prompt, stream=True)` to get a streaming response from Gemini.  It then iterates through the chunks of the response and updates the display in real-time using `st.empty()` to create a placeholder for the streaming text.
*   **Error Handling:** The code includes `try...except` blocks to handle potential errors during API calls, prompt blocking, and response generation.  It displays appropriate error messages to the user.
*   **Safety Settings:**  The `safety_settings` parameter is used to configure the safety filters for the Gemini model, blocking potentially harmful content.

## Security Considerations

*   **API Key Security:** Store your API key securely using Streamlit secrets.  Avoid hardcoding it directly in the code.
*   **Password Protection:**  The example code includes a password `st.secrets["passwd"]`.  It's crucial to implement proper authentication and authorization mechanisms for production deployments.  Consider using a more robust authentication method than a simple password.
*   **Input Sanitization:**  Sanitize user input to prevent potential security vulnerabilities such as cross-site scripting (XSS).
*   **Rate Limiting:**  Implement rate limiting to prevent abuse of the API.

## Future Enhancements

*   **User Authentication:** Implement user authentication to allow multiple users to have their own chat histories.
*   **Context Management:** Improve context management by storing and retrieving relevant information from previous conversations.
*   **Multimedia Support:** Add support for images and other multimedia content.
*   **Customizable Safety Settings:** Allow users to customize the safety settings for the Gemini model.
*   **Deployment:** Deploy the application to a cloud platform such as Streamlit Cloud, Google Cloud Platform, or AWS.