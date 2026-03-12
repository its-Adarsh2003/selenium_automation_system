import os
import pandas as pd
import streamlit as st
import plotly.express as px
from collections import Counter
import ast


def parse_word_counts_list(raw: str) -> dict:
    """
    Input example:
    "[('and', 11), ('advertising', 6), ...]"
    Output:
    {'and': 11, 'advertising': 6, ...}
    """
    if not isinstance(raw, str):
        return {}
    raw = raw.strip()
    if not raw:
        return {}

    try:
        # Convert string representation of list of tuples to Python object
        data = ast.literal_eval(raw)
    except Exception:
        return {}

    word_dict = {}
    for item in data:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        word, count = item
        try:
            count = int(count)
        except Exception:
            continue
        word_dict[str(word)] = word_dict.get(str(word), 0) + count

    return word_dict


# ---------- Page config ----------
st.set_page_config(
    page_title="El País Opinion Dashboard",
    layout="wide"
)

st.title("📰 El País Opinion Articles – Analysis Dashboard")

CSV_PATH = "reports/results.csv"

# ---------- Load data ----------
if not os.path.exists(CSV_PATH):
    st.error(f"❌ CSV file not found at '{CSV_PATH}'. Please run the scraping pipeline first.")
    st.stop()


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    # Your CSV has NO header row, only data rows
    # Force the correct column names in the right order
    df = pd.read_csv(path, header=None)
    df.columns = [
        "article_url",
        "title_es",
        "title_en",
        "word_counts_list",
        "image_url",
        "image_paths",
    ]
    return df


df = load_data(CSV_PATH)

# Expected columns (match what we just set)
required_cols = {
    "article_url",
    "title_es",
    "title_en",
    "word_counts_list",
    "image_url",
    "image_paths",
}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"❌ Missing required columns in CSV: {missing}")
    st.info(f"Available columns: {list(df.columns)}")
    st.stop()

if df.empty:
    st.warning("⚠️ No data available. Please run the scraping pipeline first.")
    st.stop()

# ---------- Metrics ----------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Total Articles", len(df))

with col2:
    articles_with_images = len(
        df[df["image_paths"].astype(str).str.strip() != ""]
    )
    st.metric("🖼️ Articles with Images", articles_with_images)

with col3:
    st.metric("🌐 Unique Image URLs", df["image_url"].nunique())

with col4:
    st.metric("✅ Successful Scrapes", len(df[df["title_es"].notna()]))

st.divider()

# ---------- Filters ----------
st.sidebar.header("🔍 Filters")

num_articles = st.sidebar.slider(
    "Number of latest articles to include",
    min_value=1,
    max_value=len(df),
    value=min(10, len(df)),
)

filtered_df = df.tail(num_articles)
top_n = st.sidebar.slider("Top N words to show", 5, 50, 20)

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(
    ["📊 Overview", "📝 Articles", "🔤 Word Analysis"]
)

# -------- Tab 1: Overview --------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Articles with/without Images")
        image_status = filtered_df["image_paths"].astype(str).apply(
            lambda x: "With Image"
            if x.strip() not in ("", "nan", "NaN", "None", "[]")
            else "No Image"
        ).value_counts()
        fig = px.pie(
            values=image_status.values,
            names=image_status.index,
            title="Image Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Title Translation Status")
        translated = filtered_df["title_en"].notna().sum()
        not_translated = filtered_df["title_en"].isna().sum()
        fig = px.bar(
            x=["Translated", "Not Translated"],
            y=[translated, not_translated],
            title="Spanish to English Translation",
            color_discrete_sequence=["#2ecc71", "#e74c3c"],
        )
        st.plotly_chart(fig, use_container_width=True)

# -------- Tab 2: Articles --------
with tab2:
    st.subheader("📋 Article Details")

    display_cols = ["article_url", "title_es", "title_en", "image_url"]
    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        height=400,
    )

# -------- Tab 3: Word Analysis --------
with tab3:
    st.subheader("🔤 Word Repetition Analysis")

    # Spanish & English stopwords
    stopwords = {
        "de", "la", "el", "y", "a", "un", "en", "una", "que", "del",
        "los", "las", "se", "es", "por", "con", "para", "al", "lo",
        "the", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "is", "are", "was", "be", "been", "have", "has",
    }

    # Parse word counts from CSV
    all_words = Counter()

    for word_counts_str in filtered_df["word_counts_list"].dropna():
        word_dict = parse_word_counts_list(word_counts_str)
        if word_dict:
            all_words.update(word_dict)

    # Remove stopwords
    for sw in stopwords:
        all_words.pop(sw, None)

    # Get top N words
    if all_words:
        top_words = dict(all_words.most_common(top_n))

        fig = px.bar(
            x=list(top_words.keys()),
            y=list(top_words.values()),
            title=f"Top {top_n} Most Repeated Words",
            labels={"x": "Word", "y": "Frequency"},
            color=list(top_words.values()),
            color_continuous_scale="Viridis",
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False,
            margin=dict(l=40, r=20, t=60, b=150),
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Total Unique Words", len(all_words))
        with col2:
            st.metric("🔤 Total Word Count", sum(all_words.values()))

        st.subheader("Top Words Table")
        top_df = pd.DataFrame(list(top_words.items()), columns=["Word", "Count"])
        st.dataframe(top_df, use_container_width=True)
    else:
        st.warning("⚠️ No word analysis data available")

st.divider()
st.caption(
    f"🚀 Selenium Automation Dashboard | Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
