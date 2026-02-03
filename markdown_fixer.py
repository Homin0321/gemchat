import streamlit as st

from utils import fix_markdown_symbol_issue

# --- Streamlit UI ---
st.set_page_config(page_title="Markdown Symbol Fixer", layout="wide", page_icon="🛠️")

st.title("🛠️ Markdown Symbol Fixer")
st.write(
    "This tool applies `fix_markdown_symbol_issue` to your text to check how it handles symbols like `$`, `~`, `**`, and `*`."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Markdown")
    input_text = st.text_area(
        "Paste your markdown here:",
        height=600,
        placeholder="e.g. Price is $100, approx ~50 items.",
    )

with col2:
    st.subheader("Processed Output")
    if input_text:
        processed_text = fix_markdown_symbol_issue(input_text)

        tab_render, tab_source = st.tabs(["🖼️ Rendered View", "📝 Source Code"])

        with tab_render:
            st.markdown(processed_text)

        with tab_source:
            st.code(processed_text, language="markdown")
    else:
        st.info("Waiting for input...")
