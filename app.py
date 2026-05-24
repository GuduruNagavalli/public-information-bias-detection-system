import streamlit as st
import pandas as pd
import re
from textblob import TextBlob
from deep_translator import GoogleTranslator
from langdetect import detect
import plotly.graph_objects as go
from collections import Counter
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Public Information Bias Detector System",
    layout="wide",
    page_icon="👁️‍🗨️"
)

# ======================
# CSS DESIGN
# ======================
st.markdown("""
<style>
.stApp{
background:
radial-gradient(circle at 20% 30%, rgba(255,75,75,0.3), transparent 40%),
radial-gradient(circle at 80% 70%, rgba(255,140,0,0.3), transparent 40%),
radial-gradient(circle at 50% 50%, #000000 40%, #000000 100%);
color:white;
}
.main-title{
font-size:42px;
font-weight:800;
text-align:center;
background:linear-gradient(45deg,#ff4b4b,#ff8f00);
-webkit-background-clip:text;
color:transparent;
}
.highlight-bias{
background:rgba(255,75,75,0.3);
color:#ff4b4b;
padding:2px 5px;
border-radius:5px;
}
.highlight-emotion{
background:rgba(255,165,0,0.3);
color:orange;
padding:2px 5px;
border-radius:5px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# HEADER
# ======================
st.markdown(
'<img src="https://viso.ai/wp-content/uploads/2024/04/bias-detection-computer-vision-1280x768.jpg" width="100%">',
unsafe_allow_html=True
)
st.markdown("<div class='main-title'>👁️‍🗨️ Public Information Bias Detector System</div>",unsafe_allow_html=True)

# ======================
# SIDEBAR
# ======================
st.sidebar.title("📂 Features")
page = st.sidebar.radio(
    "Open Section",
    ["📊 Dashboard","📈 Graphs","🤖 AI Suggestions",
     "✍ Neutral Rewrite","🔍 Bias Evidence",
     "🔥 Emotional Words","🧠 Explainable AI"]
)

# ======================
# DATA
# ======================
BIASED_WORDS={
"outrageous","terrible","disastrous","shocking",
"heroic","evil","radical","worst","fake","crazy",
"insane","furious","pathetic","ridiculous"
}

EMOTIONAL_WORDS={
"love","hate","angry","furious","amazing",
"shocking","disaster","great","worst","crazy"
}

# ======================
# FUNCTIONS
# ======================
def extract_words(text):
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())

def highlight_bias(text, words):
    for w in set(words):
        text=re.sub(rf"\b({w})\b",
        r"<span class='highlight-bias'>\1</span>",
        text,flags=re.IGNORECASE)
    return text

def highlight_emotion(text, words):
    for w in set(words):
        text=re.sub(rf"\b({w})\b",
        r"<span class='highlight-emotion'>\1</span>",
        text,flags=re.IGNORECASE)
    return text

def read_pdf(file):
    reader=PyPDF2.PdfReader(file)
    txt=""
    for p in reader.pages:
        t=p.extract_text()
        if t:
            txt+=t
    return txt

def get_youtube_transcript(url):
    try:
        if "v=" in url:
            vid=url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            vid=url.split("youtu.be/")[1].split("?")[0]
        else:
            return "error"

        try:
            tr=YouTubeTranscriptApi.get_transcript(vid)
            return " ".join([x["text"] for x in tr])
        except:
            api=YouTubeTranscriptApi()
            tr=api.fetch(vid)
            return " ".join([x.text for x in tr])

    except:
        return "error"

def analyze_text(text):
    blob=TextBlob(text)
    pol=blob.sentiment.polarity
    subj=blob.sentiment.subjectivity

    words=extract_words(text)
    bias_found=[w for w in words if w in BIASED_WORDS]
    emo_found=[w for w in words if w in EMOTIONAL_WORDS]

    ratio=len(bias_found)/(len(words)+1)

    score=min(subj*60+abs(pol)*20+min(ratio*300,20),100)
    conf=min(subj*50+ratio*500,100)
    fake=min(len(bias_found)*8+abs(pol)*40,100)

    return round(score,1),pol,subj,bias_found,emo_found,words,round(conf,1),round(fake,1)

def neutral_rewrite(text):
    replace={
        "terrible":"difficult",
        "worst":"less effective",
        "outrageous":"controversial",
        "disastrous":"challenging"
    }
    for k,v in replace.items():
        text=text.replace(k,v)
    return text

def ai_summary(score,bias_found,emo_found):
    if score>70:
        return f"⚠️ HIGH bias detected ({len(bias_found)} loaded words)."
    elif score>40:
        return f"🟠 MODERATE bias with emotional influence ({len(emo_found)} emotional words)."
    else:
        return "🟢 Mostly neutral and factual content."

# ======================
# INPUT
# ======================
mode=st.radio("Choose Input Type",
["Text","PDF","YouTube Video"],horizontal=True)

text=""

if mode=="Text":
    text=st.text_area("Enter Text",height=170)

elif mode=="PDF":
    pdf=st.file_uploader("Upload PDF",type=["pdf"])
    if pdf:
        text=read_pdf(pdf)

else:
    url=st.text_input("Enter YouTube URL")

    if "yt_text" not in st.session_state:
        st.session_state["yt_text"]=""

    if st.button("Fetch Transcript"):
        r=get_youtube_transcript(url)
        if r=="error":
            st.error("Transcript not available")
        else:
            st.session_state["yt_text"]=r
            st.success("Transcript fetched!")

    text=st.session_state.get("yt_text","")

# ======================
# ANALYZE
# ======================
if st.button("🚀 Analyze Information for Bias"):

    if not text.strip():
        st.warning("Provide input")
        st.stop()

    try:
        lang=detect(text)
    except:
        lang="en"

    st.session_state["detected_lang"]=lang

    if lang!="en":
        translated=GoogleTranslator(source='auto',target='en').translate(text)
    else:
        translated=text

    st.session_state["translated_text"]=translated
    st.session_state["analysis"]=analyze_text(translated)

# ======================
# RESULTS
# ======================
if "analysis" in st.session_state:

    score,pol,subj,bias_found,emo_found,words,conf,fake=st.session_state["analysis"]
    text=st.session_state["translated_text"]

    if page=="📊 Dashboard":

        st.info(f"Detected Language: {st.session_state['detected_lang']}")

        st.markdown("### 🌍 Converted English Text")
        st.write(text[:800]+"...")

        c1,c2,c3,c4=st.columns(4)
        c1.metric("Bias Score",f"{score}%")
        c2.metric("Confidence",f"{conf}%")
        c3.metric("Fake News",f"{fake}%")
        c4.metric("Emotional Words",len(emo_found))

        st.markdown("### 🤖 AI Quick Summary")
        st.info(ai_summary(score,bias_found,emo_found))

    elif page=="📈 Graphs":

        gauge=go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={'suffix':"%"},
            gauge={'axis':{'range':[0,100]}}
        ))
        gauge.update_layout(paper_bgcolor="black")
        st.plotly_chart(gauge,use_container_width=True)

        df=pd.DataFrame(
            Counter(words).most_common(10),
            columns=["Word","Count"]
        )

        fig=go.Figure(data=[go.Bar(
            x=df["Word"],
            y=df["Count"],
            marker_color="#ff4b4b"
        )])

        fig.update_layout(
            paper_bgcolor="black",
            plot_bgcolor="black",
            font=dict(color="white")
        )

        st.plotly_chart(fig,use_container_width=True)

    elif page=="🤖 AI Suggestions":
        st.success("Use more neutral factual language and avoid emotional exaggeration.")

    elif page=="✍ Neutral Rewrite":
        st.write(neutral_rewrite(text))

    elif page=="🔍 Bias Evidence":
        st.markdown(highlight_bias(text,bias_found),unsafe_allow_html=True)

    elif page=="🔥 Emotional Words":
        st.markdown(highlight_emotion(text,emo_found),unsafe_allow_html=True)

    elif page=="🧠 Explainable AI":
        st.write(f"""
Subjectivity Contribution: {round(subj*60,1)}
Emotion Contribution: {round(abs(pol)*20,1)}
Bias Words Contribution: {len(bias_found)}
""")