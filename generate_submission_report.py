"""제출용 단일 HTML 리포트 생성.

기존 analyze_voc.py / app.py / csv 파일은 전혀 수정하지 않고,
이미 생성된 classified_voc.csv, voc_report.md, decisions.md,
data/voc_multichannel.csv 만 읽어 voc_classifier_report.html 로 합친다.
외부 라이브러리 없이 HTML/CSS만 사용(단, 표 생성을 위해 표준 라이브러리인
pandas는 이미 프로젝트에서 쓰던 것을 그대로 사용).
"""
import re

import pandas as pd

OUT_PATH = "voc_classifier_report.html"
STREAMLIT_URL = "https://voc-classifier.streamlit.app/"

df = pd.read_csv("classified_voc.csv")
src = pd.read_csv("data/voc_multichannel.csv").merge(
    df[["id", "category", "sentiment"]], on="id", how="left"
)
with open("voc_report.md", encoding="utf-8") as f:
    report_md = f.read()
with open("decisions.md", encoding="utf-8") as f:
    decisions_md = f.read()

top3_section = report_md.split("## 5. 즉시 대응 필요 TOP3")[1]


def bold(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def md_section_to_html(body: str) -> str:
    """decisions.md 의 '## N. 제목' 아래 불릿 목록만 있는 단순 구조를 변환."""
    lines = [l for l in body.strip().split("\n") if l.strip()]
    html, in_list = "", False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                html += "<ul>"
                in_list = True
            html += f"<li>{bold(stripped[2:])}</li>"
        else:
            if in_list:
                html += "</ul>"
                in_list = False
            html += f"<p>{bold(stripped)}</p>"
    if in_list:
        html += "</ul>"
    return html


decisions_sections = re.split(r"\n## \d+\. ", decisions_md)[1:]
decisions_sections = [s.split("\n", 1)[1] if "\n" in s else "" for s in decisions_sections]
decisions_titles = re.findall(r"\n## \d+\. (.+)", decisions_md)
decisions_by_title = dict(zip(decisions_titles, decisions_sections))

classification_html = "".join(
    f"<h4>{t}</h4>{md_section_to_html(decisions_by_title[t])}"
    for t in decisions_titles if t != "즉시 대응 TOP3 선별 기준"
)
top3_criteria_html = md_section_to_html(decisions_by_title["즉시 대응 TOP3 선별 기준"])

# --- 유형/감정 집계 -------------------------------------------------
cat = df["category"].value_counts().rename_axis("유형").reset_index(name="건수")
cat["비율(%)"] = (cat["건수"] / len(df) * 100).round(1)
sent = df["sentiment"].value_counts().rename_axis("감정").reset_index(name="건수")

top3_blocks = re.findall(r"### (TOP \d+)\. \[(F\d+)\]\n((?:- .+\n?)+)", top3_section)
top3_html = ""
for title, fid, body in top3_blocks:
    rows = "".join(f"<li>{line[2:].strip()}</li>" for line in body.strip().split("\n"))
    top3_html += f"<div class='card'><h4>{title}. [{fid}]</h4><ul>{rows}</ul></div>"

display_df = df.rename(columns={
    "content_summary": "content 요약(30자)", "category": "유형 분류", "sentiment": "감정 분류",
})

# --- Challenge: 개선 후보 자동 산출 (app.py와 동일 로직) -----------------
IMPACT_KW = ["로그인", "저장", "동기화", "결제", "유실"]
CANDIDATES = {
    "로그인·접속 안정화": (["로그인", "접속", "튕김", "세션", "오류"],
        "인증·세션 유지 로직 점검 및 안정성 강화", "신규 인증 방식(SSO 등) 추가는 별도 과제"),
    "저장·동기화 안정화": (["저장", "동기화", "반영", "사라짐", "데이터"],
        "저장/동기화 재시도 로직 및 실패 알림 체계 도입", "오프라인 모드 등 신규 저장 방식 추가는 범위 아님"),
    "결제·구독 개선": (["결제", "환불", "요금제", "구독", "청구"],
        "결제 프로세스 검증 강화 및 환불 처리 자동화", "신규 결제 수단 추가는 별도 과제"),
    "협업 기능 개선": (["공유", "권한", "댓글", "멘션", "공동편집"],
        "권한 세분화 및 협업 기능 안정성 개선", "신규 협업 도구 연동은 범위 아님"),
    "화면·사용성 개선": (["정렬", "필터", "다크모드", "보기", "UI"],
        "필터·정렬 옵션 확장 및 UI 일관성 개선", "전면 리디자인은 별도 과제"),
    "알림·캘린더 개선": (["알림", "캘린더", "일정", "리마인드"],
        "알림 발송 안정화 및 캘린더 동기화 정확도 개선", "외부 캘린더 신규 연동은 범위 아님"),
}

freqs, stats = {}, {}
for name, (kws, proposal, exclusion) in CANDIDATES.items():
    mask = src["content"].apply(lambda c: any(k in str(c) for k in kws))
    sub = src[mask]
    freqs[name] = len(sub)
    stats[name] = {
        "proposal": proposal, "exclusion": exclusion,
        "neg": int((sub["sentiment"] == "부정").sum()),
        "high_sev": int((sub["severity_hint"] == "높음").sum()),
        "value": int(sub["user_type"].isin(["유료", "기업고객"]).sum()),
        "impact_hits": int(sub["content"].apply(lambda c: any(k in str(c) for k in IMPACT_KW)).sum()),
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

cards_html, viz_html = "", ""
for name, score, freq, s, fsc, isc, usc, vsc in top2:
    badge = "🔴" if score >= 55 else "🟡" if score >= 30 else "🟢"
    cards_html += (
        f"<div class='card'><h4>{badge} {name}</h4>"
        f"<p class='badge'>우선순위 점수 {score}/100 | 관련 VoC {freq}건 | 부정 {s['neg']}건 | "
        f"심각도 높음 {s['high_sev']}건 | 유료/기업고객 {s['value']}건</p>"
        f"<p><b>개선 제안</b> {s['proposal']}</p>"
        f"<p><b>제외 범위</b> {s['exclusion']}</p></div>"
    )
    viz_html += (
        f"<div class='viz'><div>{name} <b>{score} / 100</b></div>"
        f"<div class='bar'><div class='bar-fill' style='width:{min(score,100)}%'></div></div>"
        f"<div class='caption'>빈도 {fsc} | 임팩트 {isc} | 긴급도 {usc} | 고객가치 {vsc}</div></div>"
    )

breakdown = pd.DataFrame(
    [(n, f, i, u, v, t) for n, t, _, _, f, i, u, v in top2],
    columns=["후보명", "빈도 점수", "임팩트 점수", "긴급도 점수", "고객가치 점수", "총점"],
)

top3_ids = re.findall(r"\[(F\d+)\]", top3_section)
cs_actions = "".join(f"<li>{i} 건 24시간 내 1차 답변 및 보상/환불 조치 확인</li>" for i in top3_ids)
pm_actions = "".join(f"<li>{name}: {s['proposal']} (다음 스프린트 검토)</li>" for name, _, _, s, *_ in top2)

html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>VoC 자동 분류기 - 제출 리포트</title>
<style>
body {{ font-family: -apple-system, "Malgun Gothic", sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 16px; color:#1a1a1a; line-height:1.6; }}
h1 {{ border-bottom: 3px solid #333; padding-bottom: 8px; }}
h2 {{ margin-top: 44px; border-bottom: 1px solid #ddd; padding-bottom: 6px; }}
h3, h4 {{ margin-top: 20px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 14px; }}
th {{ background: #f5f5f5; }}
.metric {{ font-size: 28px; font-weight: bold; }}
.card {{ border: 1px solid #ddd; border-radius: 8px; padding: 14px 18px; margin: 10px 0; background: #fafafa; }}
.badge {{ background: #eef; padding: 6px 10px; border-radius: 6px; display: inline-block; }}
.viz {{ margin: 14px 0; }}
.bar {{ background: #e0e0e0; border-radius: 6px; height: 18px; width: 100%; }}
.bar-fill {{ background: #4c8bf5; height: 100%; border-radius: 6px; }}
.caption {{ color: #666; font-size: 13px; margin-top: 4px; }}
.scroll-table {{ max-height: 500px; overflow-y: auto; border: 1px solid #eee; }}
.url-box {{ background:#f5f5f5; padding:10px 14px; border-radius:6px; display:inline-block; }}
</style></head>
<body>
<h1>PM VoC 자동 분류기 - 제출 리포트</h1>

<h2>1. 프로젝트 개요</h2>
<p>다채널(슬랙/CS티켓/앱스토어/인앱설문)로 수집된 VoC 300건을 규칙 기반으로 자동 분류하고,
즉시 대응이 필요한 이슈와 제품 개선 방향을 자동 산출하는 파이프라인입니다.
classified_voc.csv(분류 결과) → voc_report.md(요약 리포트) → app.py(Streamlit 대시보드) 순으로 구성됩니다.</p>

<h2>2. 동작 화면 URL</h2>
<p class="url-box"><a href="{STREAMLIT_URL}" target="_blank">{STREAMLIT_URL}</a></p>

<h2>3. Basic 산출물</h2>
<h3>전체 피드백 수</h3>
<div class="metric">{len(df)}건</div>

<h3>유형별 건수·비율</h3>
{cat.to_html(index=False, border=0)}

<h3>감정별 건수</h3>
{sent.to_html(index=False, border=0)}

<h3>즉시 대응 필요 TOP3</h3>
{top3_html}

<h3>전체 분류표 (300행)</h3>
<div class="scroll-table">
{display_df.to_html(index=False, border=0)}
</div>

<h2>4. 분류 기준</h2>
{classification_html}

<h2>5. 즉시 대응 TOP3 선별 기준</h2>
{top3_criteria_html}

<h2>6. Standard 확장</h2>
<h3>재사용 가능한 파이프라인</h3>
<p>analyze_voc.py 하나로 원본 CSV(data/voc_multichannel.csv) → classified_voc.csv → voc_report.md 가
자동 생성됩니다. 원본 CSV만 동일한 스키마(id/date/channel/content/user_type/severity_hint)로 교체하면
분류 로직 수정 없이 재실행할 수 있습니다.</p>
<h3>실행 방법</h3>
<p><code>py analyze_voc.py</code> 실행 → classified_voc.csv, voc_report.md 생성<br>
<code>streamlit run app.py</code> 실행 → 대시보드 화면 확인</p>
<h3>주간 리포트 구성 의도</h3>
<p>매주 새로 수집된 VoC로 원본 CSV를 교체해 동일 파이프라인을 재실행하면,
유형·감정 분포 추이와 즉시 대응 TOP3 변화를 주간 단위로 추적할 수 있도록 설계했습니다.</p>

<h2>7. Challenge 확장</h2>
<h3>우선순위 판단 기준</h3>
<p>빈도 30% / 임팩트 30% / 긴급도 30% / 고객가치 10%<br>
🔴 높음: 즉시 대응 필요 / 🟡 중간: 다음 스프린트 검토 / 🟢 낮음: 모니터링</p>

<h3>Impact × Urgency 매트릭스</h3>
<table>
<tr><th>임팩트 \\ 긴급도</th><th>높음</th><th>낮음</th></tr>
<tr><th>높음</th><td>🔴 즉시 대응</td><td>🟡 다음 스프린트 검토</td></tr>
<tr><th>낮음</th><td>🟡 CS 확인</td><td>🟢 모니터링</td></tr>
</table>

<h3>제품 개선 기획안 TOP2</h3>
{cards_html}

<h3>우선순위 점수 시각화</h3>
{viz_html}

<h3>개선 후보 점수 분해표</h3>
{breakdown.to_html(index=False, border=0)}

<h3>팀별 액션 제안</h3>
<b>CS팀 즉시 대응</b><ul>{cs_actions}</ul>
<b>제품팀 다음 스프린트 검토</b><ul>{pm_actions}</ul>

<h2>8. 제외 범위</h2>
<ul>
<li>파일 업로드, 로그인 인증, DB 연동 기능은 구현하지 않음(정적 CSV 기반)</li>
<li>복잡한 시각화 라이브러리(예: Plotly, matplotlib) 대신 Streamlit 기본 컴포넌트만 사용</li>
<li>실시간 외부 API 연동, 자동 알림 발송(Slack/메일 등)은 범위 밖</li>
<li>키워드 사전 기반 규칙 분류이며, 머신러닝 기반 분류 모델은 적용하지 않음</li>
</ul>

<h2>9. 한 줄 회고</h2>
<p>규칙 기반 키워드 분류만으로도 VoC 우선순위를 빠르게 가시화할 수 있음을 확인했고,
다음 단계로는 키워드 사전을 실제 라벨링 데이터로 검증·고도화하는 것이 과제로 남았습니다.</p>

</body></html>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"저장 완료: {OUT_PATH}")
