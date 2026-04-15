import streamlit as st
from datetime import datetime
from groq import Groq
import os
import re
import random

# ====================== PAGE CONFIG & CUSTOM CSS ======================
st.set_page_config(page_title="Insighter", page_icon="✍️", layout="wide")

st.markdown("""
<style>
    .main-title { 
        font-size: 5rem !important; 
        font-weight: 700; 
        text-align: center; 
        color: #1E3A8A; 
        margin-bottom: 0.1rem; 
        font-family: 'Georgia', serif; 
    }
    .subtitle { 
        font-size: 1.7rem !important; 
        text-align: center; 
        color: #334155; 
        font-style: italic; 
        margin-bottom: 2.2rem; 
        font-family: 'Playfair Display', serif; 
    }
    .counter { 
        text-align: right; 
        color: #64748b; 
        font-size: 0.98rem; 
        margin-top: -10px; 
    }
    .brought-by {
        text-align: center;
        color: #64748b;
        font-size: 1.05rem;
        margin-top: 3.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e2e8f0;
    }
    .name {
        font-size: 1.35rem !important;
        font-weight: 600;
        color: #1E3A8A;
        margin: 0.3rem 0;
    }
    .linger {
        font-size: 1.15rem;
        font-style: italic;
        color: #475569;
        font-family: 'Playfair Display', serif;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">Insighter</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Between what is written and what is felt</p>', unsafe_allow_html=True)

# Groq Client
if "client" not in st.session_state:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter your Groq API Key:", type="password")
        if not api_key:
            st.stop()
    st.session_state.client = Groq(api_key=api_key)

client = st.session_state.client

col1, col2 = st.columns([2, 1])
with col1:
    book_title = st.text_input("Book Title", placeholder="Crime and Punishment")
with col2:
    author = st.text_input("Author (optional)", placeholder="Fyodor Dostoevsky")

tone = st.select_slider(
    "Tone",
    options=["Minimal", "Balanced", "Poetic"],
    value="Balanced"
)

highlights_text = st.text_area(
    "Paste your quotes or highlighted passages",
    height=300,
    placeholder="Paste the text you highlighted...\nSingle quotes or full paragraphs work well."
)

if highlights_text:
    words = len(re.findall(r'\b\w+\b', highlights_text))
    sentences = max(1, len(re.split(r'[.!?]+', highlights_text)) - 1)
    st.markdown(f'<p class="counter">Words: <strong>{words}</strong> &nbsp;&nbsp; Sentences: <strong>{sentences}</strong></p>', unsafe_allow_html=True)

tone_instructions = {
    "Minimal": "Use very few words. Prefer short, direct sentences. Be extremely concise.",
    "Balanced": "Keep a natural, thoughtful balance.",
    "Poetic": "Allow slightly more metaphor and rhythm, but stay restrained and quiet."
}

if st.button("Generate Insights", type="primary", use_container_width=True):
    if not highlights_text.strip():
        st.error("Please paste at least one quote or highlighted passage.")
    else:
        highlights = [para.strip() for para in highlights_text.split("\n\n") if para.strip()]
        if not highlights:
            highlights = [highlights_text.strip()]

        all_insights = []
        
        # Simple & Clean Generation Message
        status_placeholder = st.empty()
        status_placeholder.markdown("""
            <div style="text-align: center; margin: 40px 0;">
                <h3 style="color: #475569;">Generating Insights...</h3>
            </div>
        """, unsafe_allow_html=True)

        progress_bar = st.progress(0)
        
        for idx, highlight in enumerate(highlights, 1):
            progress_bar.progress(idx / len(highlights))
            
            system_prompt = f"""You are not an AI assistant. You are a quiet, introspective reader writing private notes in the margin of a book.

Avoid sounding academic, performative, or overly polished.
Do NOT use phrases like “this quote is a powerful depiction”, “masterful”, “profound”, or “captures the essence”.

Do:
- Be concise
- Leave some thoughts slightly unfinished
- Focus on subtle emotional insight
- Write like private margin notes

{tone_instructions[tone]}

Respond in this exact format:

Interpretation:
(2–3 short sentences)

Reflection:
(3–5 personal sentences)

Quiet takeaway:
(1–2 short lines)

Text:
"{highlight}"
"""

            with st.expander(f"📌 Highlight {idx}", expanded=(idx == 1)):
                st.markdown(f"> **{highlight}**")
                
                temp = 0.75 if tone == "Poetic" else 0.65
                if random.random() < 0.3:
                    temp += 0.1
                
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": system_prompt}],
                    temperature=temp,
                    max_tokens=480
                )
                
                raw_text = resp.choices[0].message.content.strip()
                
                # Clean generic phrases
                banned = ["this quote is", "masterful", "in the depths", "unbridled", "profound", 
                          "ultimately", "captures the essence", "beautifully illustrates"]
                for phrase in banned:
                    raw_text = raw_text.replace(phrase, "").replace(phrase.capitalize(), "")
                
                st.markdown(raw_text)
                all_insights.append({"highlight": highlight, "raw": raw_text})
        
        # Remove the "Generating Insights..." message
        status_placeholder.empty()

        # Download Button
        if all_insights:
            md_content = f"# Insighter\n\n**Book:** {book_title} {author and f'— {author}' or ''}\n\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"
            for item in all_insights:
                md_content += f"## Highlight\n> {item['highlight']}\n\n{item['raw']}\n\n---\n\n"
            
            st.download_button(
                label="📥 Download as Markdown",
                data=md_content,
                file_name=f"Insighter_{book_title.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )

# Footer
st.markdown("""
<p class="brought-by">
    Brought to you by<br>
    <span class="name">Abdul Ahad</span><br>
    <span class="linger"> For the readers who linger</span>
</p>
""", unsafe_allow_html=True)