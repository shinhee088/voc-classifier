import pandas as pd
import streamlit as st

st.title("PM VoC 자동 분류기")

df = pd.read_csv("classified_voc.csv")

st.subheader("전체 피드백 수")
st.metric("전체 건수", len(df))

st.subheader("유형별 건수·비율")
cat = df["category"].value_counts().rename_axis("유형").reset_index(name="건수")
cat["비율(%)"] = (cat["건수"] / len(df) * 100).round(1)
st.table(cat)

st.subheader("감정별 건수")
sent = df["sentiment"].value_counts().rename_axis("감정").reset_index(name="건수")
st.table(sent)

st.subheader("즉시 대응 필요 TOP3")
with open("voc_report.md", encoding="utf-8") as f:
    report = f.read()
top3_section = report.split("## 5. 즉시 대응 필요 TOP3")[1]
st.markdown(top3_section)

st.subheader("전체 분류표 (300행)")
st.dataframe(df, use_container_width=True)
