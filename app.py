import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="PM VoC 자동 분류기", layout="wide")

st.markdown("""
<style>
.stApp {background:#f6f8fb;}
.block-container {max-width:1240px; padding-top:3rem;}
.header-box {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:24px 32px; margin-top:20px; margin-bottom:28px; box-shadow:0 1px 2px rgba(15,23,42,0.04);}
.header-box h1 {margin:0 0 6px 0; font-size:24px; color:#0f172a;}
.header-box p {margin:0; color:#64748b; font-size:15px;}
div[data-testid="column"] {padding:0 10px;}
.kpi-card {border:1px solid #e5e7eb; border-radius:16px;
  padding:22px 20px; text-align:center; margin-bottom:16px;
  box-shadow:0 1px 2px rgba(15,23,42,0.04);}
.kpi-card .icon {font-size:22px;}
.kpi-card .value {font-size:38px; font-weight:800; color:#0f172a; line-height:1.2; margin-top:4px;}
.kpi-card .ratio {font-size:13px; color:#475569; margin-top:2px;}
.kpi-card .label {font-size:13px; color:#64748b; margin-top:6px;}
.kpi-blue {background:#EFF6FF;}
.kpi-orange {background:#FFF7ED;}
.kpi-red {background:#FEF2F2;}
.kpi-darkred {background:#FEE2E2;}
/* 흰색 카드 박스 (섹션/표/다운로드/기획안 공용) */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background:#ffffff; border:1px solid #e5e7eb !important; border-radius:16px !important;
  padding:8px 6px; margin-bottom:20px;}
.top3-card {background:#FEF2F2; border:1px solid #FCA5A5; border-radius:16px;
  padding:18px 22px; margin-bottom:18px;}
.top3-card h4 {margin:0 0 10px 0; color:#B91C1C;}
.top3-card p {margin:4px 0; font-size:14px; color:#1a1a1a;}
.plan-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:20px 22px; margin-bottom:16px;}
.plan-card h4 {margin:0 0 10px 0;}
.plan-card .score-badge {display:inline-block; padding:6px 14px; border-radius:8px;
  font-size:13px; font-weight:700; margin-bottom:12px;}
.plan-card .score-red {background:#FEE2E2; color:#B91C1C;}
.plan-card .score-yellow {background:#FEF3C7; color:#92400E;}
.plan-card .score-green {background:#DCFCE7; color:#166534;}
.plan-card .field {margin:10px 0;}
.plan-card .field b {display:block; font-size:13px; color:#475569; margin-bottom:3px;}
.plan-card .field span, .plan-card .field ul {font-size:14px; color:#1a1a1a; margin:0; padding-left:18px;}
.download-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:20px 22px; margin-bottom:14px;}
.download-card h4 {margin:0 0 6px 0;}
.download-card p {margin:0 0 14px 0; font-size:13px; color:#64748b;}
.side-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:14px 16px; margin-bottom:16px;}
.side-card h4 {margin:0 0 6px 0; font-size:16px; color:#0f172a;}
.side-card p, .side-card ul {font-size:13px; color:#475569; margin:0; padding-left:18px;}
h3, .stSubheader {margin-top:20px !important; margin-bottom:10px !important; color:#0f172a;}
section[data-testid="stSidebar"] h3 {font-size:18px; margin-bottom:4px; color:#0f172a;}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {font-size:13px; color:#64748b;}
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
  background:#fff; border-radius:16px !important; padding:14px 16px; margin-bottom:16px;}
</style>
<div class="header-box">
<h1>PM VoC 분석 대시보드</h1>
<p>총 300건의 고객 피드백을 분석했습니다.</p>
</div>
""", unsafe_allow_html=True)

df = pd.read_csv("classified_voc.csv")
raw = pd.read_csv("data/voc_multichannel.csv")
full_df = df.merge(raw[["id", "user_type", "severity_hint"]], on="id", how="left")
full_df["user_type"] = full_df["user_type"].fillna("").replace("", "미확인")
full_df["severity_hint"] = full_df["severity_hint"].fillna("").replace("", "미확인")

with open("voc_report.md", encoding="utf-8") as f:
    report = f.read()
top3_section = report.split("## 5. 즉시 대응 필요 TOP3")[1]

# --- 사이드바: CSV 업로드 / 데이터 정제 결과 / 분류·처리 기준 (HTML 카드형) -
st.sidebar.markdown(
    '<div class="side-card"><h4>📤 CSV 업로드</h4>'
    '<p>classified_voc.csv 형식 파일을 업로드하면 대시보드 데이터가 교체됩니다.</p></div>',
    unsafe_allow_html=True,
)
uploaded_file = st.sidebar.file_uploader("classified_voc.csv 형식 업로드 (선택)", type="csv",
                                          label_visibility="collapsed")
if uploaded_file is not None:
    uploaded_df = pd.read_csv(uploaded_file)
    required_cols = {"id", "channel", "content_summary", "category", "sentiment"}
    if required_cols.issubset(uploaded_df.columns):
        df = uploaded_df
        full_df = df.merge(raw[["id", "user_type", "severity_hint"]], on="id", how="left")
        full_df["user_type"] = full_df["user_type"].fillna("").replace("", "미확인")
        full_df["severity_hint"] = full_df["severity_hint"].fillna("").replace("", "미확인")
        st.sidebar.success(f"{len(df)}건 업로드 반영")
    else:
        st.sidebar.warning("classified_voc.csv 형식과 일치하지 않아 기본 데이터를 사용합니다.")

st.sidebar.markdown(
    '<div class="side-card"><h4>🧹 데이터 정제 결과</h4><ul>'
    '<li>분석 대상 300건</li>'
    '<li>날짜 형식 통일 완료</li>'
    '<li>결측 채널 3건</li>'
    '<li>결측 사용자 2건</li>'
    '<li>중복 데이터 1건</li>'
    '</ul></div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="side-card"><h4>🏷️ 분류·처리 기준</h4>'
    '<p>규칙 기반 키워드 매칭으로 유형 4종(버그/기능요청/칭찬/일반문의)과 '
    '감정 3종(긍정/부정/중립)을 판정합니다.</p></div>',
    unsafe_allow_html=True,
)

filtered = full_df

# --- Challenge 개선 후보 산출 (전체 데이터 기준, 탭1/탭4 공용) -------------
src = raw.merge(df[["id", "category", "sentiment"]], on="id", how="left")
IMPACT_KW = ["로그인", "저장", "동기화", "결제", "유실"]
CANDIDATES = {
    "로그인·접속 안정화": (["로그인", "접속", "튕김", "세션", "오류"],
        "로그인/접속 실패, 세션 끊김 등 접속 관련 문제가 발생",
        "인증·세션 유지 로직 점검 및 안정성 강화",
        "신규 인증 방식(SSO 등) 추가는 별도 과제"),
    "저장·동기화 안정화": (["저장", "동기화", "반영", "사라짐", "데이터"],
        "저장 실패, 동기화 오류로 데이터가 사라지거나 반영되지 않는 문제",
        "저장/동기화 재시도 로직 및 실패 알림 체계 도입",
        "오프라인 모드 등 신규 저장 방식 추가는 범위 아님"),
    "결제·구독 개선": (["결제", "환불", "요금제", "구독", "청구"],
        "결제/구독/청구 처리 오류 및 환불 지연 문제",
        "결제 프로세스 검증 강화 및 환불 처리 자동화",
        "신규 결제 수단 추가는 별도 과제"),
    "협업 기능 개선": (["공유", "권한", "댓글", "멘션", "공동편집"],
        "공유/권한/댓글/멘션 등 협업 기능 관련 불편 사항",
        "권한 세분화 및 협업 기능 안정성 개선",
        "신규 협업 도구 연동은 범위 아님"),
    "화면·사용성 개선": (["정렬", "필터", "다크모드", "보기", "UI"],
        "정렬/필터/다크모드 등 화면 사용성 관련 요청 다수",
        "필터·정렬 옵션 확장 및 UI 일관성 개선",
        "전면 리디자인은 별도 과제"),
    "알림·캘린더 개선": (["알림", "캘린더", "일정", "리마인드"],
        "알림 누락/지연, 캘린더 일정 오류 관련 피드백 다수",
        "알림 발송 안정화 및 캘린더 동기화 정확도 개선",
        "외부 캘린더 신규 연동은 범위 아님"),
}

freqs = {}
stats = {}
for name, (kws, problem, proposal, exclusion) in CANDIDATES.items():
    mask = src["content"].apply(lambda c: any(k in str(c) for k in kws))
    sub = src[mask]
    freqs[name] = len(sub)
    stats[name] = {
        "kws": kws, "problem": problem, "proposal": proposal, "exclusion": exclusion,
        "neg": int((sub["sentiment"] == "부정").sum()),
        "high_sev": int((sub["severity_hint"] == "높음").sum()),
        "value": int(sub["user_type"].isin(["유료", "기업고객"]).sum()),
        "impact_hits": int(sub["content"].apply(lambda c: any(k in str(c) for k in IMPACT_KW)).sum()),
        "examples": sub["content"].head(2).tolist(),
    }

# --- 즉시 대응 TOP3용 긴급도 점수 (decisions.md 기준과 동일한 규칙) -------
URGENT_KEYWORDS = ["환불", "결제", "구독", "오류", "장애", "안됨", "안 돼요", "튕김",
                    "로그인", "데이터", "유실", "삭제", "저장", "동기화", "복구", "불편"]


def calc_urgency(row):
    score = 0
    if row["severity_hint"] == "높음":
        score += 3
    elif row["severity_hint"] == "보통":
        score += 1
    if row["sentiment"] == "부정":
        score += 2
    if row["user_type"] in ("유료", "기업고객"):
        score += 1
    if any(k in str(row["content"]) for k in URGENT_KEYWORDS):
        score += 1
    return score


src["urgency_score"] = src.apply(calc_urgency, axis=1)
urgency_by_id = dict(zip(src["id"], src["urgency_score"]))

top3_pattern = re.compile(
    r"### (TOP \d+)\. \[(F\d+)\]\n"
    r"- 채널: .*\n"
    r"- 사용자 구분: (.*)\n"
    r"- 심각도: (.*)\n"
    r"- 유형: .*\n"
    r"- 감정: (.*)\n"
    r"- 원문: (.*)\n"
    r"- 선별 이유: (.*)"
)
top3_items = top3_pattern.findall(top3_section)

# =========================================================================
# 요약 대시보드 (탭 없이 한 화면 카드 레이아웃)
# =========================================================================

# --- 2. KPI 4개 가로 카드 -------------------------------------------------
total_n = len(filtered) or 1
neg_n = int((filtered["sentiment"] == "부정").sum())
high_n = int((filtered["severity_hint"] == "높음").sum())
urgent_n = int(((filtered["severity_hint"] == "높음") & (filtered["sentiment"] == "부정")).sum())

kpi_values = [
    ("📊", "kpi-blue", "전체 피드백 수", len(filtered), None),
    ("⚠️", "kpi-orange", "부정 VoC 수", neg_n, neg_n / total_n * 100),
    ("🔴", "kpi-red", "심각도 '높음' 수", high_n, high_n / total_n * 100),
    ("🚨", "kpi-darkred", "즉시 대응 후보 수", urgent_n, urgent_n / total_n * 100),
]
kpi_cols = st.columns(4)
for col, (icon, tone, label, value, ratio) in zip(kpi_cols, kpi_values):
    ratio_html = f'<div class="ratio">전체의 {ratio:.1f}%</div>' if ratio is not None else ""
    col.markdown(
        f'<div class="kpi-card {tone}"><div class="icon">{icon}</div>'
        f'<div class="value">{value}</div>{ratio_html}'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )

# --- 3. 차트 3개 가로 카드 (유형별 / 감정별 / 반복 이슈 TOP5) -------------
st.markdown("###")
chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    with st.container(border=True):
        st.subheader("유형별 건수·비율")
        st.caption("전체 데이터 기준 유형별 분포입니다.")
        cat = filtered["category"].value_counts().rename_axis("유형").reset_index(name="건수")
        if len(filtered):
            cat["비율(%)"] = (cat["건수"] / len(filtered) * 100).round(1)
        st.table(cat)

with chart_col2:
    with st.container(border=True):
        st.subheader("감정별 건수")
        st.caption("전체 데이터 기준 감정 분포입니다.")
        sent = filtered["sentiment"].value_counts().rename_axis("감정").reset_index(name="건수")
        st.table(sent)

with chart_col3:
    with st.container(border=True):
        st.subheader("반복 이슈 TOP5")
        st.caption("전체 데이터 기준 반복 키워드 그룹 상위 5건입니다.")
        top5 = pd.DataFrame(
            sorted(freqs.items(), key=lambda x: -x[1])[:5], columns=["이슈 그룹", "건수"]
        )
        st.table(top5)

# --- 4. 2열: 즉시 대응 TOP3 | 제품 개선 기획안 TOP2 -----------------------
st.markdown("###")
top3_col, plan_col = st.columns(2)

with top3_col:
    st.subheader("즉시 대응 TOP3")
    st.caption("전체 300건 기준으로 산출된 결과입니다.")
    for rank, fid, user_type, severity, sentiment, content, reason in top3_items:
        st.markdown(
            f'<div class="top3-card"><h4>{rank}. [{fid}]</h4>'
            f'<p><b>원문</b>: {content}</p>'
            f'<p><b>고객유형</b>: {user_type} &nbsp;|&nbsp; '
            f'<b>심각도</b>: {severity} &nbsp;|&nbsp; <b>감정</b>: {sentiment} &nbsp;|&nbsp; '
            f'<b>긴급도 점수</b>: {urgency_by_id.get(fid, "-")}</p>'
            f'<p><b>선별 이유</b>: {reason}</p></div>',
            unsafe_allow_html=True,
        )

with plan_col:
    st.subheader("제품 개선 기획안 TOP2")
    st.caption("전체 300건 기준으로 산출된 결과입니다.")

    max_freq = max(freqs.values()) or 1
    scored = []
    for name, s in stats.items():
        freq = freqs[name]
        freq_score = freq / max_freq * 30
        impact_score = (s["impact_hits"] / freq * 30) if freq else 0
        urgency_score = ((s["neg"] + s["high_sev"]) / (2 * freq) * 30) if freq else 0
        value_score = (s["value"] / freq * 10) if freq else 0
        total = round(freq_score + impact_score + urgency_score + value_score, 1)
        scored.append((name, total, freq, s, round(freq_score, 1), round(impact_score, 1),
                       round(urgency_score, 1), round(value_score, 1)))

    scored.sort(key=lambda x: -x[1])
    top2 = scored[:2]

    for name, score, freq, s, *_rest in top2:
        badge, tone = ("🔴", "score-red") if score >= 55 else \
            ("🟡", "score-yellow") if score >= 30 else ("🟢", "score-green")
        examples_html = "".join(f"<li>{e}</li>" for e in s["examples"]) or "<li>해당 없음</li>"
        st.markdown(
            f'<div class="plan-card">'
            f'<h4>{badge} {name}</h4>'
            f'<span class="score-badge {tone}">우선순위 점수 {score}/100</span>'
            f'<div class="field"><b>문제 정의</b><span>{s["problem"]}</span></div>'
            f'<div class="field"><b>근거 VoC 수</b><span>{freq}건</span></div>'
            f'<div class="field"><b>대표 VoC</b><ul>{examples_html}</ul></div>'
            f'<div class="field"><b>개선 제안</b><span>{s["proposal"]}</span></div>'
            f'<div class="field"><b>우선순위 판단 근거</b><span>관련 VoC {freq}건 중 부정 {s["neg"]}건, '
            f'심각도 높음 {s["high_sev"]}건, 유료/기업고객 {s["value"]}건으로 산출</span></div>'
            f'<div class="field"><b>제외 범위</b><span>{s["exclusion"]}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# --- Challenge 부가 정보 (판단 기준/매트릭스/시각화/분해표/팀별 액션) ------
with st.container(border=True):
    st.markdown("""
**우선순위 판단 기준**: 빈도 30% / 임팩트 30% / 긴급도 30% / 고객가치 10%
(🔴 높음: 즉시 대응 필요 / 🟡 중간: 다음 스프린트 검토 / 🟢 낮음: 모니터링)

**Impact × Urgency 매트릭스**

| 임팩트 \\ 긴급도 | 높음 | 낮음 |
|---|---|---|
| **높음** | 🔴 즉시 대응 | 🟡 다음 스프린트 검토 |
| **낮음** | 🟡 CS 확인 | 🟢 모니터링 |
""")
    st.markdown("**우선순위 점수 시각화**")
    for name, total, _freq, _s, f, i, u, v in top2:
        st.markdown(f"{name}  **{total} / 100**")
        st.progress(min(total, 100) / 100)
        st.caption(f"빈도 {f} | 임팩트 {i} | 긴급도 {u} | 고객가치 {v}")

    st.markdown("**개선 후보 점수 분해표**")
    breakdown = pd.DataFrame(
        [(n, f, i, u, v, t) for n, t, _, _, f, i, u, v in top2],
        columns=["후보명", "빈도 점수", "임팩트 점수", "긴급도 점수", "고객가치 점수", "총점"],
    )
    st.table(breakdown)

    st.markdown("**팀별 액션 제안**")
    top3_ids = re.findall(r"\[(F\d+)\]", top3_section)
    cs_actions = [f"{i} 건 24시간 내 1차 답변 및 보상/환불 조치 확인" for i in top3_ids]
    pm_actions = [f"{name}: {s['proposal']} (다음 스프린트 검토)" for name, _, _, s, *_ in top2]
    st.markdown("- CS팀 즉시 대응:\n" + "\n".join(f"  - {a}" for a in cs_actions))
    st.markdown("- 제품팀 다음 스프린트 검토:\n" + "\n".join(f"  - {a}" for a in pm_actions))

# --- 5. 2열: 전체 분류표 | CSV/Markdown 다운로드 --------------------------
st.markdown("###")
table_col, download_col = st.columns(2)

with table_col:
    with st.container(border=True):
        st.subheader(f"전체 분류표 ({len(filtered)}건)")
        st.caption("전체 데이터 기준입니다.")
        display_df = filtered.rename(columns={
            "content_summary": "content 요약(30자)",
            "category": "유형 분류",
            "sentiment": "감정 분류",
        })
        st.dataframe(display_df, use_container_width=True, height=360)

with download_col:
    st.markdown(
        '<div class="download-card"><h4>⬇️ 다운로드</h4>'
        '<p>분류 결과와 주간 리포트를 파일로 내려받을 수 있습니다.</p></div>',
        unsafe_allow_html=True,
    )
    with open("classified_voc.csv", "rb") as f:
        st.download_button("classified_voc.csv 다운로드", f, file_name="classified_voc.csv",
                            mime="text/csv")
    st.download_button("weekly_voc_report.md 다운로드", report, file_name="weekly_voc_report.md",
                        mime="text/markdown")

    with st.container(border=True):
        st.subheader("사용법")
        st.markdown("""
1. `py analyze_voc.py` 실행 → `classified_voc.csv`, `voc_report.md` 생성
2. `streamlit run app.py` 실행 → 이 대시보드 확인
3. 좌측 사이드바에서 classified_voc.csv 형식 파일을 업로드하면 해당 데이터로 대시보드가 갱신됩니다.
   (단, 즉시 대응 TOP3와 제품 개선 기획안은 전체 데이터 기준으로 고정)
""")

with st.container(border=True):
    st.subheader("voc_report.md 전문")
    st.markdown(report)
