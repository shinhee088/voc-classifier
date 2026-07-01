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

st.header("Challenge: VoC 기반 제품 개선 기획안")

st.markdown("""
**1. 우선순위 판단 기준**
- 빈도 30%
- 임팩트 30%
- 긴급도 30%
- 고객가치 10%

**2. 제품 개선 기획안 TOP2**

**① 로그인·동기화 오류 안정화**
- 문제 정의: 로그인 실패, 세션 끊김, 캘린더/외부 연동 동기화 오류가 반복 발생
- 근거 VoC 요약: 버그 유형 중 로그인·동기화 관련 부정 피드백 다수, TOP3에도 유사 이슈 포함
- 개선 제안: 로그인 세션 유지 로직 점검, 동기화 재시도·오류 알림 체계 도입
- 우선순위: 상
- 제외 범위: 신규 로그인 방식(SSO 등) 추가는 별도 과제

**② 반복 기능요청 관리**
- 문제 정의: 다크모드, 알림 커스터마이징 등 동일 유형 기능요청이 반복 접수
- 근거 VoC 요약: 기능요청이 전체 유형 중 가장 높은 비중(95건) 차지
- 개선 제안: 반복 요청 태깅 후 로드맵 우선순위에 정례 반영
- 우선순위: 중
- 제외 범위: 개별 요청 즉시 개발은 본 기획안 범위 아님
""")
