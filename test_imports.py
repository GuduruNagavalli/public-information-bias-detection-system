import streamlit as st
import pandas as pd
import re
from textblob import TextBlob
from deep_translator import GoogleTranslator
from langdetect import detect
import plotly.graph_objects as go
from collections import Counter
from PIL import Image
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Public Information Bias Detector System",
    layout="wide",
    page_icon="👁️‍🗨️"
)

# ======================
# PREMIUM CSS
# ======================
st.markdown("""
<style>
.stApp{
background:linear-gradient(-45deg,#0E1117,#111827,#1f2937,#0f172a);
background-size:400% 400%;
animation:gradient 12s ease infinite;
color:white;
}
@keyframes gradient{
0%{background-position:0% 50%;}
50%{background-position:100% 50%;}
100%{background-position:0% 50%;}
}
.main-title{
font-size:46px;
font-weight:900;
text-align:center;
background:linear-gradient(45deg,#ff4b4b,#ff8f00);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
text-shadow:0 0 20px rgba(255,75,75,0.6);
}
.card{
background:rgba(255,255,255,0.08);
backdrop-filter:blur(15px);
border-radius:20px;
padding:20px;
}
.highlight{
background:rgba(255,75,75,0.25);
color:#ff4b4b;
padding:2px 5px;
border-radius:5px;
font-weight:bold;
}
.stButton>button{
background:linear-gradient(45deg,#ff4b4b,#ff8f00);
color:white;
font-weight:bold;
border-radius:12px;
height:52px;
font-size:18px;
box-shadow:0 0 25px rgba(255,75,75,0.7);
}
</style>
""", unsafe_allow_html=True)

# ======================
# HEADER IMAGE (optional)
# ======================
try:
    img = Image.open("bias.png")
    st.image(img, width=900)
except:
    pass

st.markdown(
    "<div class='main-title'>👁️‍🗨️ Public Information Bias Detector System</div>",
    unsafe_allow_html=True
)

# ======================
# DATA
# ======================
BIASED_WORDS = {
    "outrageous","terrible","disastrous","shocking",
    "heroic","evil","radical","worst","fake","crazy",
    "insane","furious","pathetic","ridiculous"
}

# ======================
# FUNCTIONS
# ======================
def extract_words(text):
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())

def highlight_text(text, words):
    for w in set(words):
        text = re.sub(
            rf"\b({w})\b",
            r"<span class='highlight'>\1</span>",
            text,
            flags=re.IGNORECASE
        )
    return text

def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    txt = ""
    for p in reader.pages:
        page_text = p.extract_text()
        if page_text:
            txt += page_text + " "
    return txt

def get_youtube_transcript(url):
    vid = url.split("v=")[-1].split("&")[0]
    try:
        transcript = YouTubeTranscriptApi.get_transcript(vid)
        return " ".join([t["text"] for t in transcript])
    except TranscriptsDisabled:
        raise Exception("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise Exception("No transcript found for this video.")
    except VideoUnavailable:
        raise Exception("Video is unavailable.")
    except Exception as e:
        raise Exception(f"Error fetching transcript: {str(e)}")

# ===== SMART CONTENT TYPE (FIXED) =====
def classify_text(text):
    t = text.lower()

    # SOCIAL POST PRIORITY
    post_keywords = [
        "i think","my opinion","guys",
        "honestly","today i","friends","lol"
    ]
    if any(k in t for k in post_keywords):
        return "📱 Social Media Post"

    news_keywords = [
        "government","minister","official",
        "breaking","report","news","policy"
    ]
    article_keywords = [
        "analysis","research","study",
        "discussion","article"
    ]

    news_score = sum(1 for k in news_keywords if k in t)
    article_score = sum(1 for k in article_keywords if k in t)

    if news_score > article_score:
        return "📰 News"
    elif article_score > news_score:
        return "📄 Article"
    else:
        return "General Text"

def analyze(text):
    blob = TextBlob(text)
    pol = blob.sentiment.polarity
    subj = blob.sentiment.subjectivity

    words = extract_words(text)
    found = [w for w in words if w in BIASED_WORDS]

    ratio = len(found) / (len(words) + 1)

    score = min(subj*60 + abs(pol)*20 + min(ratio*300,20), 100)
    conf = min(subj*50 + ratio*500, 100)
    fake = min(len(found)*8 + abs(pol)*40, 100)

    return (
        round(score,1),
        pol,
        subj,
        found,
        words,
        round(conf,1),
        round(fake,1)
    )

# ======================
# INPUT SECTION
# ======================
mode = st.radio(
    "Choose Input Type",
    ["Text","PDF","YouTube Video"],
    horizontal=True
)

text = ""

if mode == "Text":
    text = st.text_area("Enter Text", height=170)

elif mode == "PDF":
    pdf = st.file_uploader("Upload PDF", type=["pdf"])
    if pdf:
        text = read_pdf(pdf)
        st.success("PDF Loaded")

else:
    url = st.text_input("Enter YouTube URL")
    if st.button("Fetch Transcript"):
        try:
            text = get_youtube_transcript(url)
            st.success("Transcript Loaded")
        except Exception as e:
            st.error(str(e))

# ======================
# ANALYZE BUTTON
# ======================
if st.button("🚀 Analyze Information for Bias"):

    if not text.strip():
        st.warning("Provide input first")
        st.stop()

    try:
        lang = detect(text)
    except:
        lang = "en"

    if lang != "en":
        text = GoogleTranslator(source='auto', target='en').translate(text)

    text_type = classify_text(text)

    score, pol, subj, found, words, conf, fake = analyze(text)

    st.markdown("## 📊 AI Dashboard")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔥 Bias Score", f"{score}%")
    c2.metric("🤖 Confidence", f"{conf}%")
    c3.metric("🧠 Content Type", text_type)
    c4.metric("⚠️ Fake News", f"{fake}%")
    c5.metric("📌 Biased Words", len(found))

    # Gauge Chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "%"},
        gauge={
            'axis': {'range': [0,100]},
            'steps': [
                {'range':[0,score], 'color':'#FF4B4B'},
                {'range':[score,100], 'color':'#2D3748'}
            ]
        }
    ))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # Explainable AI
    st.markdown("### 🧠 Explainable AI")
    st.info(f"""
Subjectivity Contribution: {round(subj*60,1)}
Emotion Contribution: {round(abs(pol)*20,1)}
Loaded Words Contribution: {min(len(found)*2,20)}
""")

    # AI Suggestion
    st.markdown("### 🤖 AI Suggestion")
    if score > 70:
        st.success("Use neutral words and avoid emotional language.")
    elif score > 40:
        st.success("Try balancing opinions with facts.")
    else:
        st.success("Text looks objective.")

    # Top words
    st.markdown("### 📈 Top Words")
    freq = Counter(words)
    df = pd.DataFrame(freq.most_common(10), columns=["Word","Count"])
    st.bar_chart(df.set_index("Word"))

    # Highlighted evidence
    st.markdown("### 🔍 Highlighted Bias Evidence")
    st.markdown(
        f"<div class='card'>{highlight_text(text, found)}</div>",
        unsafe_allow_html=True
    )