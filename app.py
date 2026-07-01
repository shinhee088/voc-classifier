import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="PM VoC 자동 분류기", layout="wide")

st.markdown("""
<style>
.stApp {background:#F8FAFC;}
.block-container {max-width:1180px; padding-top:3.5rem;}
.header-box {background:#fff; border:1px solid #e6e9ee; border-radius:14px;
  padding:20px 32px; margin-top:28px; margin-bottom:22px; box-shadow:0 1px 2px rgba(15,23,42,0.04);}
.header-box h1 {margin:0 0 6px 0; font-size:24px; color:#0f172a;}
.header-box p {margin:0; color:#64748b; font-size:15px;}
.header-box .nav-caption {margin-top:8px; font-size:14px; color:#64748b;}
div[data-testid="column"] {padding:0 8px;}
.kpi-card {background:#fff; border:1px solid #e6e9ee; border-radius:14px;
  padding:24px 20px; text-align:center; margin-bottom:14px;
  box-shadow:0 1px 2px rgba(15,23,42,0.04);}
.kpi-card .value {font-size:40px; font-weight:800; color:#0f172a; line-height:1.25;}
.kpi-card .label {font-size:13px; color:#64748b; margin-top:6px;}
h3, .stSubheader {margin-top:36px !important; margin-bottom:10px !important; color:#0f172a;}
section[data-testid="stSidebar"] h3 {font-size:19px; margin-bottom:4px; color:#0f172a;}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {font-size:13px; color:#64748b;}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {margin-bottom:10px;}
div[data-baseweb="tab-list"] {gap:16px; margin:4px 0 24px 0;}
button[data-baseweb="tab"] {font-size:18px !important; font-weight:700 !important;
  color:#475569 !important; padding:16px 26px !important; margin-right:8px !important;
  border-radius:8px 8px 0 0 !important; white-space:nowrap !important; background:transparent;}
button[data-baseweb="tab"][aria-selected="true"] {color:#D92D20 !important;
  font-weight:700 !important; background-color:#FFF5F5 !important;
  border-bottom:3px solid #D92D20 !important;}
div[data-baseweb="tab-highlight"] {background-color:transparent !important;}
div[data-baseweb="tab-border"] {background:transparent !important;}
</style>
<div class="header-box">
<h1>PM VoC 자동 분류기</h1>
<p>300건의 멀티채널 VoC를 유형·감정별로 분류하고, 즉시 대응 TOP3와 제품 개선 기획안 TOP2를 자동 산출합니다.</p>
<p class="nav-caption">필터 조건에 따라 요약 지표와 분류표를 확인하고, 전체 데이터 기준의 긴급 이슈와 제품 개선안을 검토합니다.</p>
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

# --- 사이드바 필터 -------------------------------------------------------
st.sidebar.markdown("### 🔎 VoC 필터")
st.sidebar.caption("분류표와 요약 지표를 조건별로 확인할 수 있습니다.")
st.sidebar.divider()
cat_filter = st.sidebar.selectbox("유형 분류", ["전체", "버그", "기능요청", "칭찬", "일반문의"])
sent_filter = st.sidebar.selectbox("감정 분류", ["전체", "긍정", "부정", "중립"])
user_filter = st.sidebar.selectbox("사용자 구분", ["전체", "무료", "유료", "기업고객"])
sev_filter = st.sidebar.selectbox("심각도", ["전체", "낮음", "보통", "높음"])
st.sidebar.divider()
st.sidebar.caption("⚠️ 즉시 대응 TOP3·제품 개선 기획안에는 필터가 반영되지 않습니다(전체 데이터 기준). "
                    "필터를 초기화하려면 각 항목을 '전체'로 다시 선택하세요.")

filtered = full_df.copy()
if cat_filter != "전체":
    filtered = filtered[filtered["category"] == cat_filter]
if sent_filter != "전체":
    filtered = filtered[filtered["sentiment"] == sent_filter]
if user_filter != "전체":
    filtered = filtered[filtered["user_type"] == user_filter]
if sev_filter != "전체":
    filtered = filtered[filtered["severity_hint"] == sev_filter]

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["요약 대시보드", "즉시 대응 TOP3", "전체 분류표", "제품 개선 기획안", "리포트/사용법"]
)

# --- 탭1: 요약 대시보드 (필터 반영) --------------------------------------
with tab1:
    kpi_values = [
        ("전체 피드백 수", len(filtered)),
        ("부정 VoC 수", int((filtered["sentiment"] == "부정").sum())),
        ("버그 VoC 수", int((filtered["category"] == "버그").sum())),
        ("즉시 대응 후보 수",
         int(((filtered["severity_hint"] == "높음") & (filtered["sentiment"] == "부정")).sum())),
    ]
    kpi_cols = st.columns(4)
    for col, (label, value) in zip(kpi_cols, kpi_values):
        col.markdown(
            f'<div class="kpi-card"><div class="value">{value}</div>'
            f'<div class="label">{label}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("###")
    st.subheader("유형별 건수·비율")
    st.caption("선택한 필터 조건 기준의 유형별 분포입니다.")
    cat = filtered["category"].value_counts().rename_axis("유형").reset_index(name="건수")
    if len(filtered):
        cat["비율(%)"] = (cat["건수"] / len(filtered) * 100).round(1)
    st.table(cat)

    st.subheader("감정별 건수")
    st.caption("선택한 필터 조건 기준의 감정 분포입니다.")
    sent = filtered["sentiment"].value_counts().rename_axis("감정").reset_index(name="건수")
    st.table(sent)

# --- 탭2: 즉시 대응 TOP3 (전체 데이터 기준 고정) --------------------------
with tab2:
    st.caption("필터와 무관하게 전체 300건 기준으로 산출된 결과입니다.")
    st.markdown(top3_section)

# --- 탭3: 전체 분류표 (필터 반영) ----------------------------------------
with tab3:
    st.subheader(f"분류표 ({len(filtered)}건)")
    st.caption("현재 필터가 반영된 결과입니다.")
    display_df = filtered.rename(columns={
        "content_summary": "content 요약(30자)",
        "category": "유형 분류",
        "sentiment": "감정 분류",
    })
    st.dataframe(display_df, use_container_width=True)

# --- 탭4: 제품 개선 기획안 (Challenge, 전체 데이터 기준 고정) -------------
with tab4:
    st.caption("필터와 무관하게 전체 300건 기준으로 산출된 결과입니다.")
    st.markdown("""
**1. 우선순위 판단 기준**
- 빈도 30% / 임팩트 30% / 긴급도 30% / 고객가치 10%
- 🔴 높음: 즉시 대응 필요 / 🟡 중간: 다음 스프린트 검토 / 🟢 낮음: 모니터링

**2. Impact × Urgency 매트릭스**

| 임팩트 \\ 긴급도 | 높음 | 낮음 |
|---|---|---|
| **높음** | 🔴 즉시 대응 | 🟡 다음 스프린트 검토 |
| **낮음** | 🟡 CS 확인 | 🟢 모니터링 |

**3. 제품 개선 기획안 TOP2 (데이터 기반 자동 산출)**
""")

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

    cols = st.columns(2)
    for col, (name, score, freq, s, *_rest) in zip(cols, top2):
        badge, box = ("🔴", st.error) if score >= 55 else ("🟡", st.warning) if score >= 30 else ("🟢", st.success)
        with col:
            st.markdown(f"### {badge} {name}")
            box(f"우선순위 점수 {score}/100 | 관련 VoC {freq}건 | 부정 {s['neg']}건 | "
                f"심각도 높음 {s['high_sev']}건 | 유료/기업고객 {s['value']}건")
            examples_md = "\n".join(f"- {e}" for e in s["examples"]) or "- 해당 없음"
            st.markdown(f"**대표 VoC 원문**\n{examples_md}")

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

    st.markdown("**각 기획안 상세 설명**")
    for name, score, freq, s, *_rest in top2:
        st.markdown(f"#### {name}")
        st.markdown(f"**문제 정의**\n- {s['problem']}")
        st.markdown(f"**개선 제안**\n- {s['proposal']}")
        st.markdown(f"**우선순위 판단 근거**\n- 관련 VoC {freq}건 중 부정 {s['neg']}건, "
                     f"심각도 높음 {s['high_sev']}건, 유료/기업고객 {s['value']}건으로 산출")
        st.markdown(f"**제외 범위**\n- {s['exclusion']}")

    st.markdown("**팀별 액션 제안**")
    top3_ids = re.findall(r"\[(F\d+)\]", top3_section)
    cs_actions = [f"{i} 건 24시간 내 1차 답변 및 보상/환불 조치 확인" for i in top3_ids]
    pm_actions = [f"{name}: {s['proposal']} (다음 스프린트 검토)" for name, _, _, s, *_ in top2]
    st.markdown("- CS팀 즉시 대응:\n" + "\n".join(f"  - {a}" for a in cs_actions))
    st.markdown("- 제품팀 다음 스프린트 검토:\n" + "\n".join(f"  - {a}" for a in pm_actions))

# --- 탭5: 리포트/사용법 --------------------------------------------------
with tab5:
    st.subheader("사용법")
    st.markdown("""
1. `py analyze_voc.py` 실행 → `classified_voc.csv`, `voc_report.md` 생성
2. `streamlit run app.py` 실행 → 이 대시보드 확인
3. 좌측 사이드바 필터로 유형/감정/사용자 구분/심각도별 데이터를 탐색
   (단, 즉시 대응 TOP3와 제품 개선 기획안은 전체 데이터 기준으로 고정)
""")
    st.subheader("voc_report.md 전문")
    st.markdown(report)
