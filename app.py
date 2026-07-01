import re

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
display_df = df.rename(columns={
    "content_summary": "content 요약(30자)",
    "category": "유형 분류",
    "sentiment": "감정 분류",
})
st.dataframe(display_df, use_container_width=True)

st.header("Challenge: VoC 기반 제품 개선 기획안")

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

src = pd.read_csv("data/voc_multichannel.csv").merge(
    df[["id", "category", "sentiment"]], on="id", how="left"
)
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
