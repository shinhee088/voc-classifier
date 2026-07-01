import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="PM VoC 분석 대시보드", layout="wide")

# --- Power BI 스타일 차트 함수 --------------------------------------------
POWERBI_COLORS = {
    "blue": "#2563EB",
    "red": "#EF4444",
    "green": "#22C55E",
    "orange": "#F97316",
    "purple": "#7C3AED",
    "gray": "#9CA3AF",
}


def apply_powerbi_layout(fig, height=300):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color="#111827"),
        showlegend=False,
    )
    return fig


def render_type_donut(cat_df, total_count):
    labels = cat_df["유형"].tolist()
    values = cat_df["건수"].tolist()
    ratios = cat_df["비율(%)"].tolist() if "비율(%)" in cat_df else [
        round(v / total_count * 100, 1) for v in values
    ]
    legend_labels = [f"{n} {v} ({p}%)" for n, v, p in zip(labels, values, ratios)]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=legend_labels,
                values=values,
                hole=0.62,
                sort=False,
                direction="clockwise",
                textinfo="none",
                hovertemplate="<b>%{label}</b><extra></extra>",
                marker=dict(
                    colors=[
                        POWERBI_COLORS["blue"],
                        POWERBI_COLORS["red"],
                        POWERBI_COLORS["green"],
                        POWERBI_COLORS["purple"],
                    ],
                    line=dict(color="white", width=3),
                ),
            )
        ]
    )

    fig.add_annotation(
        text=f"<b>{total_count}</b><br><span style='font-size:12px'>Total</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=22, color="#111827"),
    )

    fig.update_layout(title="유형별 건수 및 비율")
    fig = apply_powerbi_layout(fig, height=320)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02,
                    font=dict(size=12)),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_sentiment_bar(sent_df):
    color_map = {
        "부정": POWERBI_COLORS["red"],
        "중립": POWERBI_COLORS["gray"],
        "긍정": POWERBI_COLORS["green"],
    }

    sent_df = sent_df.copy()
    sent_df["color"] = sent_df["감정"].map(color_map).fillna(POWERBI_COLORS["blue"])
    total = sent_df["건수"].sum()
    bar_labels = [
        f"{v}건 ({v / total * 100:.1f}%)" if total else f"{v}건" for v in sent_df["건수"]
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=sent_df["감정"],
                y=sent_df["건수"],
                text=bar_labels,
                textposition="outside",
                marker=dict(
                    color=sent_df["color"],
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{x}</b><br>%{y}건<extra></extra>",
            )
        ]
    )

    y_max = float(sent_df["건수"].max()) if len(sent_df) else 0

    fig.update_layout(
        title="감정별 건수",
        showlegend=False,
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor="#E5E7EB",
            zeroline=False,
            range=[0, y_max * 1.25 if y_max else 1],
        ),
        xaxis=dict(title=""),
    )

    fig = apply_powerbi_layout(fig, height=320)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_top5_issue_bar(top5_df):
    top5_df = top5_df.sort_values("건수", ascending=True)
    bar_labels = [f"{v}건" for v in top5_df["건수"]]
    x_max = float(top5_df["건수"].max()) if len(top5_df) else 0

    fig = go.Figure(
        data=[
            go.Bar(
                x=top5_df["건수"],
                y=top5_df["이슈 그룹"],
                orientation="h",
                text=bar_labels,
                textposition="outside",
                marker=dict(
                    color=POWERBI_COLORS["blue"],
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{y}</b><br>%{x}건<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="반복 이슈 TOP5",
        showlegend=False,
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor="#E5E7EB",
            zeroline=False,
            range=[0, x_max * 1.2 if x_max else 1],
        ),
        yaxis=dict(title=""),
    )

    fig = apply_powerbi_layout(fig, height=320)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("""
<style>
.stApp {background:#f6f8fb;}
.stApp .block-container {max-width:1240px; padding-top:5rem !important;}
.header-box {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  width:100%; box-sizing:border-box; overflow:visible !important; height:auto !important;
  position:relative !important; top:auto !important; transform:none !important;
  padding:24px; margin-top:24px !important; margin-bottom:20px; box-shadow:0 1px 2px rgba(15,23,42,0.04);}
.header-box h1 {margin:0 0 6px 0; font-size:24px; color:#0f172a;}
.header-box p {margin:0; color:#64748b; font-size:15px;}
div[data-testid="column"] {padding:0 10px;}
.kpi-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:20px; text-align:center; margin-bottom:16px; box-shadow:0 1px 2px rgba(15,23,42,0.04);}
.kpi-card .value {font-size:36px; font-weight:800; color:#0f172a; line-height:1.2;}
.kpi-card .ratio {font-size:13px; color:#475569; margin-top:2px;}
.kpi-card .label {font-size:13px; color:#64748b; margin-top:6px;}
.insight-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:20px; margin-bottom:20px;}
.insight-card h4 {margin:0 0 10px 0; color:#0f172a;}
.insight-card p {margin:6px 0; font-size:14px; color:#1a1a1a;}
div[data-testid="stVerticalBlockBorderWrapper"] {
  background:#ffffff; border:1px solid #e5e7eb !important; border-radius:16px !important;
  padding:8px 6px; margin-bottom:20px;}
.top3-card {background:#FEF2F2; border:1px solid #FCA5A5; border-radius:16px;
  padding:12px 18px; margin-bottom:8px;}
.top3-card h4 {margin:0 0 6px 0; color:#B91C1C; display:flex; align-items:center; gap:8px;}
.top3-card p {margin:2px 0; font-size:14px; color:#1a1a1a;}
.rank-badge {display:inline-flex; align-items:center; justify-content:center;
  width:22px; height:22px; border-radius:5px; font-size:13px; font-weight:800; color:#fff;}
.rank-red {background:#EF4444;}
.rank-blue {background:#2563EB;}
.plan-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:14px 16px; margin-bottom:10px;}
.plan-card .plan-header {display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;}
.plan-card .plan-header h4 {margin:0;}
.plan-card .type-badge {background:#EFF6FF; color:#2563EB; font-size:11px; font-weight:700;
  padding:3px 9px; border-radius:999px; margin-left:8px;}
.plan-card .priority-badge {font-size:11px; font-weight:700; padding:3px 9px; border-radius:999px;}
.plan-card .priority-red {background:#FEE2E2; color:#B91C1C;}
.plan-card .priority-yellow {background:#FEF3C7; color:#92400E;}
.plan-card .field {margin:6px 0;}
.plan-card .field b {display:block; font-size:13px; color:#475569; margin-bottom:2px;}
.plan-card .field span, .plan-card .field ul {font-size:14px; color:#1a1a1a; margin:0; padding-left:18px;}
.download-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
  padding:20px; margin-bottom:14px;}
.download-card h4 {margin:0 0 6px 0;}
.download-card p {margin:0 0 14px 0; font-size:13px; color:#64748b;}
h3 {margin-top:10px !important; margin-bottom:6px !important; color:#0f172a;}
</style>
<div class="header-box">
<h1>PM VoC 분석 대시보드</h1>
<p>classified_voc.csv 기준으로 유형·감정별 현황과 즉시 대응 TOP3, 제품 개선 기획안 TOP2를 한 화면에서 확인합니다.</p>
</div>
""", unsafe_allow_html=True)

# --- 데이터 로드 (classified_voc.csv 기본, TOP3 표시용 심각도/고객유형만
#     data/voc_multichannel.csv에서 보충 — 분류/선정 로직은 그대로 유지) ----
df = pd.read_csv("classified_voc.csv")
_raw = pd.read_csv("data/voc_multichannel.csv")
df = df.merge(_raw[["id", "user_type", "severity_hint", "content"]], on="id", how="left")
df["user_type"] = df["user_type"].fillna("").replace("", "미확인")
df["severity_hint"] = df["severity_hint"].fillna("").replace("", "미확인")

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


df["urgency_score"] = df.apply(calc_urgency, axis=1)

# --- 반복 이슈 TOP5 / 개선 기획안 후보 그룹 (app.py와 동일한 키워드 그룹을
#     content_summary 텍스트에 그대로 재적용, 새 분류 로직 아님) -----------
CANDIDATES = {
    "로그인·접속 안정화": (["로그인", "접속", "튕김", "세션", "오류"],
        "로그인/접속 실패, 세션 끊김 등 접속 관련 문제가 발생",
        "인증·세션 유지 로직 점검 및 안정성 강화"),
    "저장·동기화 안정화": (["저장", "동기화", "반영", "사라짐", "데이터"],
        "저장 실패, 동기화 오류로 데이터가 사라지거나 반영되지 않는 문제",
        "저장/동기화 재시도 로직 및 실패 알림 체계 도입"),
    "결제·구독 개선": (["결제", "환불", "요금제", "구독", "청구"],
        "결제/구독/청구 처리 오류 및 환불 지연 문제",
        "결제 프로세스 검증 강화 및 환불 처리 자동화"),
    "협업 기능 개선": (["공유", "권한", "댓글", "멘션", "공동편집"],
        "공유/권한/댓글/멘션 등 협업 기능 관련 불편 사항",
        "권한 세분화 및 협업 기능 안정성 개선"),
    "화면·사용성 개선": (["정렬", "필터", "다크모드", "보기", "UI"],
        "정렬/필터/다크모드 등 화면 사용성 관련 요청 다수",
        "필터·정렬 옵션 확장 및 UI 일관성 개선"),
    "알림·캘린더 개선": (["알림", "캘린더", "일정", "리마인드"],
        "알림 누락/지연, 캘린더 일정 오류 관련 피드백 다수",
        "알림 발송 안정화 및 캘린더 동기화 정확도 개선"),
}

freqs, examples = {}, {}
for name, (kws, _problem, _proposal) in CANDIDATES.items():
    mask = df["content_summary"].apply(lambda c: any(k in str(c) for k in kws))
    sub = df[mask]
    freqs[name] = len(sub)
    examples[name] = sub["content_summary"].head(2).tolist()

top2_names = sorted(freqs, key=lambda n: -freqs[n])[:2]

# --- 1. KPI 4개 가로 카드 -------------------------------------------------
total_n = len(df)
bug_n = int((df["category"] == "버그").sum())
feature_n = int((df["category"] == "기능요청").sum())
neg_n = int((df["sentiment"] == "부정").sum())

cat = df["category"].value_counts().rename_axis("유형").reset_index(name="건수")
cat["비율(%)"] = (cat["건수"] / total_n * 100).round(1)
sent = df["sentiment"].value_counts().rename_axis("감정").reset_index(name="건수")
top5 = pd.DataFrame(
    sorted(freqs.items(), key=lambda x: -x[1])[:5], columns=["이슈 그룹", "건수"]
)

kpi_cols = st.columns(4)
for col, (label, value) in zip(kpi_cols, [
    ("전체 피드백 수", total_n),
    ("버그 VoC 수", bug_n),
    ("기능요청 VoC 수", feature_n),
    ("부정 VoC 수", neg_n),
]):
    ratio = (value / total_n * 100) if total_n else 0
    col.markdown(
        f'<div class="kpi-card"><div class="value">{value}건</div>'
        f'<div class="ratio">{ratio:.1f}%</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )

# --- PM 핵심 인사이트 카드 (기존 계산값 재사용, 새 로직 없음) -------------
_top_cat_row = cat.sort_values("건수", ascending=False).iloc[0]
_urgent_total = int(((df["severity_hint"] == "높음") & (df["sentiment"] == "부정")).sum())
_top_issue_name = top5.iloc[0]["이슈 그룹"] if len(top5) else "-"
_top_plan_name = top2_names[0] if top2_names else "-"

st.markdown(
    f'<div class="insight-card"><h4>PM 핵심 인사이트</h4>'
    f'<p>• 가장 많은 유형 : {_top_cat_row["유형"]} ({_top_cat_row["비율(%)"]}%)</p>'
    f'<p>• 부정 감정 : {neg_n}건 ({neg_n / total_n * 100:.1f}%)</p>'
    f'<p>• 반복 이슈 : {_top_issue_name}</p>'
    f'<p>• 즉시 대응 후보 : {_urgent_total}건</p>'
    f'<p>• 우선 개선 기능 : {_top_plan_name}</p>'
    f'</div>',
    unsafe_allow_html=True,
)

# --- 2. 유형별 / 감정별 / 반복 이슈 TOP5 카드 -----------------------------
chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    with st.container(border=True):
        render_type_donut(cat, total_n)

with chart_col2:
    with st.container(border=True):
        render_sentiment_bar(sent)

with chart_col3:
    with st.container(border=True):
        render_top5_issue_bar(top5)

# --- 3. 즉시 대응 TOP3 (유형=버그 & 감정=부정 상위 3건) --------------------
st.subheader("즉시 대응 TOP3")
st.caption("classified_voc.csv 기준 유형=버그 & 감정=부정 조건의 상위 3건입니다.")
urgent_rows = df[(df["category"] == "버그") & (df["sentiment"] == "부정")].head(3)
for rank, (_, row) in enumerate(urgent_rows.iterrows(), start=1):
    st.markdown(
        f'<div class="top3-card"><h4><span class="rank-badge rank-red">{rank}</span> '
        f'[{row["id"]}]</h4>'
        f'<p><b>채널</b>: {row["channel"]} &nbsp;|&nbsp; '
        f'<b>고객유형</b>: {row["user_type"]} &nbsp;|&nbsp; '
        f'<b>심각도</b>: {row["severity_hint"]} &nbsp;|&nbsp; '
        f'<b>긴급도 점수</b>: {row["urgency_score"]}</p>'
        f'<p><b>유형</b>: {row["category"]} &nbsp;|&nbsp; <b>감정</b>: {row["sentiment"]}</p>'
        f'<p><b>내용 요약</b>: {row["content_summary"]}</p></div>',
        unsafe_allow_html=True,
    )

# --- 4. 제품 개선 기획안 TOP2 (반복 이슈 빈도 상위 2개 그룹) ---------------
st.subheader("제품 개선 기획안 TOP2")
st.caption("classified_voc.csv 기준 반복 이슈 그룹 빈도 상위 2건입니다.")
plan_cols = st.columns(2)
for rank, (col, name) in enumerate(zip(plan_cols, top2_names), start=1):
    _kws, problem, proposal = CANDIDATES[name]
    freq = freqs[name]
    tone = "priority-red" if rank == 1 else "priority-yellow"
    examples_html = "".join(f"<li>{e}</li>" for e in examples[name]) or "<li>해당 없음</li>"
    col.markdown(
        f'<div class="plan-card">'
        f'<div class="plan-header"><h4><span class="rank-badge rank-blue">{rank}</span> '
        f'{name}<span class="type-badge">반복 이슈</span></h4>'
        f'<span class="priority-badge {tone}">{rank}순위</span></div>'
        f'<div class="field"><b>문제 정의</b><span>{problem}</span></div>'
        f'<div class="field"><b>근거 VoC 수</b><span>{freq}건</span></div>'
        f'<div class="field"><b>대표 VoC</b><ul>{examples_html}</ul></div>'
        f'<div class="field"><b>개선 제안</b><span>{proposal}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# --- 5. 전체 분류표 카드 --------------------------------------------------
st.subheader(f"전체 분류표 ({total_n}건)")
with st.container(border=True):
    display_df = df.rename(columns={
        "content_summary": "content 요약(30자)",
        "category": "유형 분류",
        "sentiment": "감정 분류",
        "user_type": "고객유형",
        "severity_hint": "심각도",
        "urgency_score": "긴급도 점수",
    })[["id", "channel", "content 요약(30자)", "유형 분류", "감정 분류",
        "고객유형", "심각도", "긴급도 점수"]]

    TYPE_COLORS = {"버그": "#EF4444", "기능요청": "#2563EB", "칭찬": "#22C55E", "일반문의": "#7C3AED"}
    SENTIMENT_COLORS = {"부정": "#EF4444", "중립": "#9CA3AF", "긍정": "#22C55E"}

    def _urgency_color(v):
        if v >= 7:
            return "#EF4444"
        if v >= 4:
            return "#F97316"
        return "#22C55E"

    styled_df = display_df.style.map(
        lambda v: f"background-color:#ffffff; color:{TYPE_COLORS.get(v, '#1a1a1a')}; font-weight:600;",
        subset=["유형 분류"],
    ).map(
        lambda v: f"background-color:#ffffff; color:{SENTIMENT_COLORS.get(v, '#1a1a1a')}; font-weight:600;",
        subset=["감정 분류"],
    ).map(
        lambda v: f"background-color:#ffffff; color:{_urgency_color(v)}; font-weight:600;",
        subset=["긴급도 점수"],
    )
    st.dataframe(styled_df, use_container_width=True, height=360)

    _legend_spacer, _legend_col = st.columns([3, 1])
    with _legend_col:
        with st.expander("색상 기준 보기"):
            st.markdown("""
- **유형 분류**: 버그 빨강 / 기능요청 파랑 / 칭찬 초록 / 일반문의 보라
- **감정 분류**: 부정 빨강 / 중립 회색 / 긍정 초록
- **긴급도 점수**: 7점 이상 빨강 / 4~6점 주황 / 1~3점 초록
""")

# --- 6. 다운로드 카드 (CSV + Markdown, classified_voc.csv 기반 생성) ------
st.markdown(
    '<div class="download-card"><h4>⬇️ 다운로드</h4>'
    '<p>분류 결과를 CSV 또는 요약 Markdown으로 내려받을 수 있습니다.</p></div>',
    unsafe_allow_html=True,
)
dl_col1, dl_col2 = st.columns(2)
with dl_col1:
    with open("classified_voc.csv", "rb") as f:
        st.download_button("classified_voc.csv 다운로드", f, file_name="classified_voc.csv",
                            mime="text/csv")
with dl_col2:
    def df_to_md_list(frame):
        return "\n".join(f"- {' / '.join(str(v) for v in row)}" for row in frame.values)

    summary_md = (
        f"# VoC 대시보드 요약\n\n"
        f"- 전체 피드백 수: {total_n}건\n"
        f"- 버그 VoC 수: {bug_n}건\n"
        f"- 기능요청 VoC 수: {feature_n}건\n"
        f"- 부정 VoC 수: {neg_n}건\n\n"
        f"## 유형별 건수·비율\n{df_to_md_list(cat)}\n\n"
        f"## 감정별 건수\n{df_to_md_list(sent)}\n\n"
        f"## 반복 이슈 TOP5\n{df_to_md_list(top5)}\n"
    )
    st.download_button("summary.md 다운로드", summary_md, file_name="summary.md",
                        mime="text/markdown")
