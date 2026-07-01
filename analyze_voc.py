"""VOC(고객의 소리) 다채널 데이터 규칙 기반 분류기.

data/voc_multichannel.csv 를 읽어 각 건을 4가지 유형(버그/기능요청/칭찬/일반문의)과
감정(긍정/부정/중립)으로 분류하고, classified_voc.csv 로 저장한다.
"""
import csv
import sys
from pathlib import Path

INPUT_PATH = Path("data/voc_multichannel.csv")
OUTPUT_PATH = Path("classified_voc.csv")
REPORT_PATH = Path("voc_report.md")

SUMMARY_LEN = 30
CATEGORY_ORDER = ["버그", "기능요청", "칭찬", "일반문의"]
SENTIMENT_ORDER = ["긍정", "부정", "중립"]

# --- 키워드 사전 -------------------------------------------------------

BILLING_KEYWORDS = [
    "결제", "환불", "청구", "구독", "요금", "플랜", "인보이스", "영수증",
    "카드", "세금계산서", "정산", "쿠폰", "프로모션", "할인", "다운그레이드",
]

BUG_KEYWORDS = [
    "안 됩니다", "안됩니다", "안 되고", "안 되네", "안 돼", "안돼요", "안 열립니다",
    "안 열려", "안 옵니다", "안와요", "안 눌려", "안 먹힙니다", "안 맞습니다",
    "오류", "에러", "실패", "멈춥니다", "멈추고", "멈췄다가", "깨져", "깨집니다",
    "사라졌", "사라집니다", "날아갔", "무한로딩", "무한 로딩", "무한히", "튕깁니다",
    "튕겨", "응답 없음", "거부됩니다", "리셋됩니다", "복제됩니다", "틀렸다고",
    "끊깁니다", "어긋납니다", "강제 종료", "강제로 끊", "먹통", "안 잡히고",
    "안 넘어가", "안 붙", "권한 없음", "물음표로 깨져", "안 뜹니다", "밀립니다",
    "1일로 저장", "빈 페이지", "0건으로만", "위치를 잃어", "재설치해도",
    "안 보이고", "안 보입니다", "안 갑니다", "덮어써집니다", "충돌나서",
    "지워집니다", "밀려요", "중복으로", "두 번씩", "회전돼서", "저장이 안",
    "반영이 안", "동기화가 안", "인식이 안", "지연이 심해요", "늦게 옵니다",
    "계속 뜹니다", "못합니다", "못 답니다", "못 받았", "안 읽힙니다",
    "작동을 안", "쓸 수가 없습니다", "여전히", "울립니다", "놓쳤습니다",
    "최상위로", "으로 표시됩니다", "평일에 찍힙니다", "안 열리고", "빈 팝업",
    "무한 반복돼서", "캐시 문제", "영어로만 옵니다", "세션이 풀려서",
]

FEATURE_REQUEST_KEYWORDS = [
    "해주세요", "추가해주세요", "원합니다", "좋겠습니다", "있으면 좋겠",
    "지원해주세요", "만들어주세요", "제공해주세요", "원해요", "싶어요",
    "싶습니다", "됐으면", "부탁", "추가해 주세요", "주세요", "필요합니다",
    "생겼으면", "완벽할 것 같아요", "세밀했으면 합니다",
]

POSITIVE_KEYWORDS = [
    "감사", "좋아요", "만족", "최고", "훌륭", "편해졌", "편리", "도움이",
    "놀랐", "감동", "추천", "신뢰", "좋습니다", "좋아졌", "든든", "살았습니다",
    "강력 추천", "응원", "즐거워졌", "쾌적", "만능", "감사합니다", "덕분에",
    "만족합니다", "믿음", "친절", "안정적", "재밌", "완만했어요", "정확해서",
    "빨라졌", "체감", "생산성이 올라간", "잘 만드셨네요", "쉬워졌습니다", "편합니다",
    "정말 고맙습니다", "잘 만든 제품", "안심하고 협업", "스트레스 없이",
]

ESCALATION_KEYWORDS = [
    "해지하겠습니다", "해지하겠", "분쟁 접수", "당장", "즉시 조치", "말이 됩니까",
    "자격이 없", "급합니다", "업무가 마비", "마비됐", "큰 피해", "즉시", "심각",
]

INQUIRY_KEYWORDS = ["어떻게", "어디서", "가능한가요", "궁금합니다", "인가요", "되나요", "?"]

# 즉시 대응 TOP3 선별용 긴급 키워드 및 사람이 읽기 좋은 라벨
URGENT_KEYWORD_LABELS = {
    "환불": "환불", "결제": "결제", "구독": "구독", "오류": "오류",
    "장애": "장애", "안됨": "기능 미작동", "안 돼요": "기능 미작동",
    "튕김": "앱 튕김", "로그인": "로그인 장애", "데이터": "데이터",
    "유실": "데이터 유실", "삭제": "삭제", "저장": "저장", "동기화": "동기화",
    "복구": "복구", "불편": "불편",
}
URGENT_KEYWORDS = list(URGENT_KEYWORD_LABELS.keys())
PRIORITY_USER_TYPES = ("유료", "기업고객")

# 내부 7분류 -> 과제 요구 4분류 매핑
CATEGORY_MAP = {
    "버그신고": "버그",
    "결제/과금 오류": "버그",
    "사용문의": "일반문의",
    "결제/과금": "일반문의",
    "기능요청": "기능요청",
    "칭찬": "칭찬",
}


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def classify_internal_category(content: str) -> str:
    """세부 분류(7종). 최종 4분류로 매핑하기 전 단계."""
    if contains_any(content, BILLING_KEYWORDS) and (
        contains_any(content, BUG_KEYWORDS) or contains_any(content, ["안 되고", "안 됩니다", "청구됐"])
    ):
        return "결제/과금 오류"
    if contains_any(content, BILLING_KEYWORDS):
        return "결제/과금"
    if contains_any(content, BUG_KEYWORDS):
        return "버그신고"
    if contains_any(content, FEATURE_REQUEST_KEYWORDS):
        return "기능요청"
    if contains_any(content, POSITIVE_KEYWORDS):
        return "칭찬"
    if contains_any(content, INQUIRY_KEYWORDS):
        return "사용문의"
    return "기타"


def to_final_category(internal_category: str) -> str:
    """과제 Basic 기준 4분류(버그/기능요청/칭찬/일반문의)로 통일.

    '기타'는 별도 규칙으로 걸러진 게 없다는 뜻이므로, 내용상 애매한 건으로 보고
    일반문의로 보낸다.
    """
    return CATEGORY_MAP.get(internal_category, "일반문의")


def classify_sentiment(content: str, internal_category: str) -> str:
    if internal_category in ("버그신고", "결제/과금 오류"):
        return "부정"
    if contains_any(content, ESCALATION_KEYWORDS):
        return "부정"
    has_pos = contains_any(content, POSITIVE_KEYWORDS)
    has_neg = contains_any(content, BUG_KEYWORDS)
    if has_pos and not has_neg:
        return "긍정"
    if has_neg and not has_pos:
        return "부정"
    return "중립"


def summarize(content: str, length: int = SUMMARY_LEN) -> str:
    content = content.strip()
    if len(content) <= length:
        return content
    return content[:length] + "..."


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def classify_rows(rows: list[dict]) -> list[dict]:
    results = []
    for row in rows:
        content = row.get("content", "").strip()
        channel = row.get("channel", "").strip() or "미확인"

        internal_category = classify_internal_category(content)
        category = to_final_category(internal_category)
        sentiment = classify_sentiment(content, internal_category)

        results.append({
            "id": row.get("id", ""),
            "channel": channel,
            "content_summary": summarize(content),
            "category": category,
            "sentiment": sentiment,
        })
    return results


def verify(source_rows: list[dict], result_rows: list[dict]) -> None:
    print("[검수 결과]")

    ok_count = len(source_rows) == len(result_rows) == 300
    print(f"1) 행 수 일치 (원본 {len(source_rows)}행 / 결과 {len(result_rows)}행, 300행 기준): "
          f"{'PASS' if ok_count else 'FAIL'}")

    categories = sorted({r["category"] for r in result_rows})
    expected_categories = {"버그", "기능요청", "칭찬", "일반문의"}
    cat_ok = set(categories) == expected_categories
    print(f"2) 유형 분류 4종만 존재: {'PASS' if cat_ok else 'FAIL'} -> {categories}")

    sentiments = sorted({r["sentiment"] for r in result_rows})
    expected_sentiments = {"긍정", "부정", "중립"}
    sent_ok = set(sentiments) == expected_sentiments
    print(f"3) 감정 분류 3종만 존재: {'PASS' if sent_ok else 'FAIL'} -> {sentiments}")

    def counter(key):
        c = {}
        for r in result_rows:
            c[r[key]] = c.get(r[key], 0) + 1
        return dict(sorted(c.items(), key=lambda x: -x[1]))

    print("\n[유형별 건수]")
    for k, v in counter("category").items():
        print(f"  {k}: {v}")
    print("\n[감정별 건수]")
    for k, v in counter("sentiment").items():
        print(f"  {k}: {v}")


def count_by(rows: list[dict], key: str, order: list[str]) -> dict:
    counts = {label: 0 for label in order}
    for r in rows:
        counts[r[key]] = counts.get(r[key], 0) + 1
    return counts


def compute_priority(row: dict) -> tuple[int, list[str]]:
    """즉시 대응 점수와 매칭된 긴급 키워드 라벨(중복 제거, 등장 순서 유지) 계산."""
    severity_hint = row.get("severity_hint", "")
    sentiment = row.get("sentiment", "")
    user_type = row.get("user_type", "")
    content = row.get("content", "")

    score = 0
    if severity_hint == "높음":
        score += 3
    elif severity_hint == "보통":
        score += 1

    if sentiment == "부정":
        score += 2

    if user_type in PRIORITY_USER_TYPES:
        score += 1

    matched_labels = []
    for kw in URGENT_KEYWORDS:
        if kw in content:
            label = URGENT_KEYWORD_LABELS[kw]
            if label not in matched_labels:
                matched_labels.append(label)
    if matched_labels:
        score += 1

    return score, matched_labels


def build_reason(row: dict, score: int, matched_labels: list[str]) -> str:
    severity_hint = row.get("severity_hint", "")
    sentiment = row.get("sentiment", "")
    user_type = row.get("user_type", "")

    segments = []
    if severity_hint == "높음":
        segments.append("심각도 높음")
    if sentiment == "부정":
        segments.append("부정 감정")

    user_label = user_type if user_type.endswith("고객") else f"{user_type} 고객"
    is_priority_user = user_type in PRIORITY_USER_TYPES
    if is_priority_user and matched_labels:
        segments.append(f"{user_label}의 {matched_labels[0]} 이슈")
    elif is_priority_user:
        segments.append(f"{user_label} 이슈")
    elif matched_labels:
        segments.append(f"{matched_labels[0]} 이슈")
    else:
        segments.append("복합 리스크 이슈")

    return " + ".join(segments) + "로 이탈 가능성이 높아 즉시 대응이 필요합니다."


def merge_for_priority(source_rows: list[dict], classified_rows: list[dict]) -> list[dict]:
    class_by_id = {r["id"]: r for r in classified_rows}
    merged = []
    for row in source_rows:
        rid = row.get("id", "")
        cls = class_by_id.get(rid, {})
        merged.append({
            "id": rid,
            "channel": (row.get("channel", "").strip() or "미확인"),
            "user_type": (row.get("user_type", "").strip() or "미확인"),
            "severity_hint": row.get("severity_hint", "").strip(),
            "content": row.get("content", "").strip(),
            "category": cls.get("category", ""),
            "sentiment": cls.get("sentiment", ""),
        })
    return merged


def select_top3(merged_rows: list[dict]) -> list[dict]:
    scored = []
    for row in merged_rows:
        score, matched_labels = compute_priority(row)
        scored.append((row, score, matched_labels))

    def sort_key(item):
        row, score, matched_labels = item
        severity_rank = 0 if row["severity_hint"] == "높음" else 1
        sentiment_rank = 0 if row["sentiment"] == "부정" else 1
        return (-score, severity_rank, sentiment_rank, -len(matched_labels), row["id"])

    scored.sort(key=sort_key)
    top3 = []
    for rank, (row, score, matched_labels) in enumerate(scored[:3], start=1):
        top3.append({
            "rank": rank,
            "id": row["id"],
            "channel": row["channel"],
            "user_type": row["user_type"],
            "severity_hint": row["severity_hint"],
            "category": row["category"],
            "sentiment": row["sentiment"],
            "content": row["content"],
            "reason": build_reason(row, score, matched_labels),
        })
    return top3


def build_report(rows: list[dict], top3: list[dict]) -> str:
    total = len(rows)
    cat_counts = count_by(rows, "category", CATEGORY_ORDER)
    sent_counts = count_by(rows, "sentiment", SENTIMENT_ORDER)

    def pct(n: int) -> str:
        return f"{(n / total * 100):.1f}%" if total else "0.0%"

    top_category = max(cat_counts, key=cat_counts.get)
    negative_count = sent_counts.get("부정", 0)

    lines = []
    lines.append("# VoC 분류 요약 리포트")
    lines.append("")
    lines.append("## 1. 분석 개요")
    lines.append(f"- 전체 피드백 수: {total}건")
    lines.append(f"- 분석 대상 파일: `{OUTPUT_PATH.name}`")
    lines.append(f"- 생성 파일: `{REPORT_PATH.name}`")
    lines.append("")
    lines.append("## 2. 유형별 건수·비율")
    for label in CATEGORY_ORDER:
        n = cat_counts.get(label, 0)
        lines.append(f"- {label}: {n}건 ({pct(n)})")
    lines.append("")
    lines.append("## 3. 감정별 건수")
    for label in SENTIMENT_ORDER:
        n = sent_counts.get(label, 0)
        lines.append(f"- {label}: {n}건 ({pct(n)})")
    lines.append("")
    lines.append("## 4. PM 1차 인사이트")
    lines.append(
        f"- 가장 많이 접수된 유형은 **{top_category}**({cat_counts.get(top_category, 0)}건, "
        f"{pct(cat_counts.get(top_category, 0))})으로, 우선 검토가 필요합니다."
    )
    lines.append(
        f"- 부정 감정 피드백은 전체 {total}건 중 {negative_count}건({pct(negative_count)})으로, "
        "고객 경험에 부정적인 영향을 미치는 이슈가 적지 않게 존재합니다."
    )
    lines.append(
        "- 다음 단계에서는 이 리포트를 기반으로 즉시 대응이 필요한 TOP3 항목을 선별할 예정입니다."
    )
    lines.append("")
    lines.append("## 5. 즉시 대응 필요 TOP3")
    lines.append("")
    for item in top3:
        lines.append(f"### TOP {item['rank']}. [{item['id']}]")
        lines.append(f"- 채널: {item['channel']}")
        lines.append(f"- 사용자 구분: {item['user_type']}")
        lines.append(f"- 심각도: {item['severity_hint']}")
        lines.append(f"- 유형: {item['category']}")
        lines.append(f"- 감정: {item['sentiment']}")
        lines.append(f"- 원문: {item['content']}")
        lines.append(f"- 선별 이유: {item['reason']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not INPUT_PATH.exists():
        print(f"입력 파일을 찾을 수 없습니다: {INPUT_PATH}", file=sys.stderr)
        sys.exit(1)

    source_rows = load_rows(INPUT_PATH)
    classified = classify_rows(source_rows)

    fieldnames = ["id", "channel", "content_summary", "category", "sentiment"]
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(classified)

    print(f"분류 결과 저장: {OUTPUT_PATH} ({len(classified)}행)\n")
    verify(source_rows, classified)

    report_rows = load_rows(OUTPUT_PATH)
    merged_rows = merge_for_priority(source_rows, report_rows)
    top3 = select_top3(merged_rows)

    REPORT_PATH.write_text(build_report(report_rows, top3), encoding="utf-8")
    print(f"\n리포트 저장: {REPORT_PATH} (존재 여부: {REPORT_PATH.exists()})\n")

    cat_counts = count_by(report_rows, "category", CATEGORY_ORDER)
    total = len(report_rows)
    print("[유형별 건수·비율]")
    for label in CATEGORY_ORDER:
        n = cat_counts.get(label, 0)
        print(f"  {label}: {n}건 ({(n / total * 100):.1f}%)")

    print("\n[즉시 대응 필요 TOP3]")
    for item in top3:
        print(f"  TOP{item['rank']}. {item['id']} | {item['severity_hint']} | {item['sentiment']} | "
              f"{item['user_type']} | {item['content'][:40]}")


if __name__ == "__main__":
    main()
