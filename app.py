import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from io import BytesIO

# =========================
# PATH FILE
# =========================

all_officer_name = "data/all-officer-name.csv"

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Excel Performance Consolidator",
    layout="wide"
)

st.title("Performance to Master Recap")
st.caption("Upload Performance → Auto Mapping → Download → WordCloud")

# =========================
# CONSTANT DATA
# =========================
officers_topics = [
    "Officers Role",
    "Officers Handover",
    "Officers Guideline",
    "Connection Hub",
    "Work Hub",
    "Officers Synergy",
    "Social Hub",
    "Social Harmony",
    "Officers Engagement",
    "Officers Performance",
    "Officers Development"
]

departments = [
    "C-Level",
    "Human Resources",
    "Marketing Communications",
    "Finance",
    "Operations"
]

# =========================
# LOAD STATIC RECAP CSV
# =========================
@st.cache_data
def load_recap_master():
    df = pd.read_csv(all_officer_name)
    df["DEPARTMENT"] = df["DEPARTMENT"].astype(str).str.strip().str.title()
    df["NAME"] = df["NAME"].astype(str).str.strip()
    return df

recap_df = load_recap_master()

# =========================
# FILE UPLOAD
# =========================
st.subheader("Upload Performance Excel")

performance_file = st.file_uploader(
    "Upload Performance File (.xlsx)",
    type=["xlsx"]
)

# =========================
# PROCESS
# =========================
if performance_file:
    with st.spinner("Processing performance data..."):

        performance_df = pd.read_excel(performance_file)

        # =========================
        # FIX MULTIPLE NAME COLUMNS
        # =========================
        name_cols = performance_df.filter(regex="^Name")

        if not name_cols.empty:
            performance_df["Name"] = (
                name_cols
                .bfill(axis=1)
                .iloc[:, 0]
                .astype(str)
                .str.strip()
            )

            performance_df.drop(columns=name_cols.columns, inplace=True)

        # =========================
        # NORMALIZATION
        # =========================
        performance_df["Department"] = (
            performance_df["Department"]
            .astype(str)
            .str.strip()
            .str.title()
        )

        performance_df["Name"] = (
            performance_df["Name"]
            .astype(str)
            .str.strip()
        )

        # =========================
        # TIMESTAMP
        # =========================
        performance_df["Timestamp"] = pd.to_datetime(
            performance_df["Timestamp"],
            errors="coerce",
            infer_datetime_format=True
        )

        # =========================
        # HANDLE DUPLICATE RESPONSE
        # =========================
        performance_df = (
            performance_df
            .sort_values("Timestamp")
            .drop_duplicates(
                subset=["Department", "Name"],
                keep="last"
            )
        )

        # =========================
        # FORCE SCORE TO NUMERIC
        # =========================
        for col in officers_topics:
            if col in performance_df.columns:
                performance_df[col] = pd.to_numeric(
                    performance_df[col],
                    errors="coerce"
                )

        # =========================
        # LOOKUP
        # =========================
        performance_lookup = performance_df.set_index(
            ["Department", "Name"]
        )

        # =========================
        # BUILD RECAP
        # =========================

        rows = []

        for dept in departments:
            names = recap_df[
                recap_df["DEPARTMENT"] == dept
            ]["NAME"].dropna().tolist()

            for topic in officers_topics:
                for name in names:

                    value = None

                    if (dept, name) in performance_lookup.index:
                        if topic in performance_lookup.columns:
                            value = performance_lookup.loc[(dept, name), topic]

                    rows.append([
                        topic,
                        dept,
                        name,
                        value
                    ])

        recap_fixed_df = pd.DataFrame(
            rows,
            columns=[
                "INDICATORS",
                "DEPARTMENT",
                "NAME",
                "SCORE"
            ]
        )

    st.success("Data merger successfully!!")

    # =========================
    # PREVIEW
    # =========================
    st.subheader("Consolidated Data Preview")
    st.dataframe(recap_fixed_df, use_container_width=True)

    # =========================
    # DOWNLOAD
    # =========================
    buffer = BytesIO()

    recap_fixed_df.to_excel(
        buffer,
        index=False,
        engine="openpyxl"
    )

    buffer.seek(0)

    st.download_button(
        label="Download Recap Excel",
        data=buffer,
        file_name="Recap_Fixed.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # =========================
    # WORDCLOUD
    # =========================
    st.subheader("WordCloud Insight")

    wc_column = "What should SxC or your department improve for future enhancements?"

    if wc_column in performance_df.columns:

        stopwords = set(STOPWORDS)

        stopwords.update([
            "https", "dan", "yang",
            "untuk", "amp", "co",
            "-", "nya", "lebih", "kita",
            "dari", "bisa", "di", "juga"
        ])

        # =========================
        # OVERALL WORDCLOUD
        # =========================
        st.markdown("### Overall Insight")

        overall_text = " ".join(
            performance_df[wc_column]
            .fillna("")
            .astype(str)
            .tolist()
        )

        overall_wc = WordCloud(
            background_color="white",
            stopwords=stopwords,
            width=1200,
            height=500,
            max_words=400
        ).generate(overall_text)

        fig, ax = plt.subplots(figsize=(14, 6))

        ax.imshow(overall_wc, interpolation="bilinear")
        ax.axis("off")

        st.pyplot(fig)

        # =========================
        # PER DEPARTMENT WORDCLOUD
        # =========================
        st.markdown("### Department Insights")

        cols = st.columns(3)
        col_idx = 0

        for dept in departments:

            dept_df = performance_df[
                performance_df["Department"] == dept
            ]

            dept_text = " ".join(
                dept_df[wc_column]
                .fillna("")
                .astype(str)
                .tolist()
            )

            if dept_text.strip() == "":
                continue

            dept_wc = WordCloud(
                background_color="white",
                stopwords=stopwords,
                width=500,
                height=300,
                max_words=150
            ).generate(dept_text)

            with cols[col_idx]:

                st.markdown(f"**{dept}**")

                fig, ax = plt.subplots(figsize=(5, 3))
                ax.imshow(dept_wc, interpolation="bilinear")
                ax.axis("off")

                st.pyplot(fig)

            col_idx = (col_idx + 1) % 3

    else:
        st.warning("Kolom WordCloud tidak ditemukan")

else:
    st.info("Upload Performance Excel untuk memulai")