#!/usr/bin/env python3
"""AI 뉴스 클리핑 JSON → HTML 렌더러 + 검증기.

usage: python build_html.py <input.json> <output.html>

- references/sources.json 화이트리스트로 URL 도메인을 검증한다.
- 발행일이 target_date 규칙(당일 또는 하루 뒤/전 — 시간대 차이 허용)에 맞는지 확인한다.
- 필수 필드, 카테고리, 다양성 규칙을 확인한다.
- ERROR가 하나라도 있으면 HTML을 쓰지 않고 exit 1.
"""
import html
import json
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "template.html"
SOURCES = SKILL_DIR / "references" / "sources.json"

CATEGORIES = ["모델·연구", "비즈니스·투자", "정책·규제", "반도체·인프라", "사회·노동", "안전·윤리"]
REQUIRED = ["rank", "title", "title_ko", "source", "url", "published", "category", "summary", "why_it_matters"]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

errors, warns = [], []

# Windows 콘솔(cp949)에서 한국어 출력이 깨지거나 죽지 않도록
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def e(s):
    return html.escape(str(s), quote=True)


def load_sources():
    data = json.loads(SOURCES.read_text(encoding="utf-8"))
    by_domain = {}
    for tier in ("tier1", "tier2"):
        for s in data.get(tier, []):
            for d in s["domains"]:
                by_domain[d.lower()] = (s["name"], tier)
    return by_domain


def match_domain(url, by_domain):
    host = (urlparse(url).hostname or "").lower()
    for d, info in by_domain.items():
        if host == d or host.endswith("." + d):
            return info
    return None


def validate(doc, by_domain):
    try:
        target = date.fromisoformat(doc["target_date"])
    except Exception:
        errors.append("target_date가 없거나 YYYY-MM-DD 형식이 아닙니다.")
        return None
    items = doc.get("items") or []
    if not items:
        errors.append("items가 비어 있습니다.")
    if len(items) < 10:
        warns.append(f"기사가 {len(items)}개입니다 (목표 10개). 페이지에 안내 문구가 표시됩니다.")
    if len(items) > 10:
        warns.append(f"기사가 {len(items)}개입니다 (목표 10개).")
    if not doc.get("overview"):
        warns.append("overview가 비어 있습니다.")

    seen_urls = set()
    for i, it in enumerate(items, 1):
        tag = f"[#{it.get('rank', i)}]"
        for f in REQUIRED:
            if not it.get(f) and it.get(f) != 0:
                errors.append(f"{tag} 필수 필드 '{f}' 누락")
        url = it.get("url", "")
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            errors.append(f"{tag} URL이 http(s)가 아님: {url}")
        elif p.path in ("", "/"):
            errors.append(f"{tag} URL이 기사 페이지가 아니라 홈으로 보입니다: {url}")
        info = match_domain(url, by_domain)
        if not info:
            errors.append(f"{tag} 허용 매체가 아님: {p.hostname}")
        else:
            it["_tier"] = info[1]
            if info[1] == "tier2":
                warns.append(f"{tag} tier2 매체 사용: {info[0]}")
        if url in seen_urls:
            errors.append(f"{tag} 중복 URL: {url}")
        seen_urls.add(url)
        try:
            pub = date.fromisoformat(str(it.get("published", ""))[:10])
            if abs((pub - target).days) > 1:
                errors.append(f"{tag} 발행일 {pub}가 대상일 {target}과 맞지 않습니다.")
            elif pub != target:
                warns.append(f"{tag} 발행일 {pub} (대상일 {target}과 하루 차이 — 시간대 차이인지 확인)")
        except ValueError:
            errors.append(f"{tag} published 형식 오류: {it.get('published')}")
        if it.get("category") not in CATEGORIES:
            errors.append(f"{tag} 알 수 없는 category: {it.get('category')} (허용: {', '.join(CATEGORIES)})")
        if it.get("verified") not in ("fetched", "snippet"):
            warns.append(f"{tag} verified 값이 'fetched' / 'snippet'이 아님: {it.get('verified')}")

    for name, n in Counter(it.get("source") for it in items).items():
        if n > 4:
            warns.append(f"다양성: '{name}' 기사가 {n}개 (최대 4)")
    for name, n in Counter(it.get("category") for it in items).items():
        if n > 4:
            warns.append(f"다양성: '{name}' 카테고리가 {n}개 (최대 4)")
    snip = sum(1 for it in items if it.get("verified") == "snippet")
    if snip:
        warns.append(f"원문 미확인(snippet) 기사 {snip}개 / {len(items)}개")
    op = sum(1 for it in items if it.get("opinion"))
    if op > 2:
        warns.append(f"다양성: 오피니언 기사가 {op}개 (최대 2)")
    ranks = [it.get("rank") for it in items]
    if sorted(ranks) != list(range(1, len(items) + 1)):
        errors.append(f"rank가 1..{len(items)} 연속값이 아닙니다: {ranks}")
    return target


def render_article(it, featured=False):
    cat = it["category"]
    kws = "".join(f'<span class="kw">{e(k)}</span>' for k in (it.get("keywords") or [])[:4])
    also = it.get("also_covered_by") or []
    also_html = f'<p class="also">함께 보도: {e(", ".join(also))}</p>' if also else ""
    lock = ' <span class="badge badge-muted" title="구독 필요">유료</span>' if it.get("paywalled") else ""
    tier2 = ' <span class="badge badge-muted">보충 매체</span>' if it.get("_tier") == "tier2" else ""
    tier2 += ' <span class="badge badge-secondary">칼럼</span>' if it.get("opinion") else ""
    rank_cls = "rank" if featured else "rank glass"
    top = '<span class="top-label">Top story</span>' if featured else ""
    inner = f"""
      <div class="article-head">
        <span class="{rank_cls}">{int(it['rank']):02d}</span>
        {top}
        <span class="badge badge-outline">{e(it['source'])}</span>
        <span class="badge cat" data-cat="{e(cat)}"><span class="dot"></span>{e(cat)}</span>{lock}{tier2}
        <span class="date">{e(it['published'])}</span>
      </div>
      <h2 class="title-ko">{e(it['title_ko'])}</h2>
      <p class="title-en"><a href="{e(it['url'])}" target="_blank" rel="noopener noreferrer">{e(it['title'])}</a></p>
      {also_html}
      <p class="summary">{e(it['summary'])}</p>
      <div class="why"><b>Why it matters</b>{e(it['why_it_matters'])}</div>
      <div class="article-foot">
        {kws}
        <a class="btn {'btn-primary' if featured else ''}" href="{e(it['url'])}" target="_blank" rel="noopener noreferrer">원문 보기
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M7 7h10v10"/></svg>
        </a>
      </div>"""
    attrs = f'data-article data-category="{e(cat)}"'
    if featured:
        return f'<div class="featured-wrap" {attrs}><div class="aura"></div><article class="featured glass article">{inner}</article></div>'
    return f'<article class="card article" {attrs}>{inner}</article>'


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    doc = json.loads(src.read_text(encoding="utf-8"))
    by_domain = load_sources()
    target = validate(doc, by_domain)

    for w in warns:
        print("WARN ", w)
    for x in errors:
        print("ERROR", x)
    if errors:
        print(f"\n{len(errors)}개 ERROR — HTML을 생성하지 않았습니다.")
        sys.exit(1)

    items = sorted(doc["items"], key=lambda it: it["rank"])
    cat_counts = Counter(it["category"] for it in items)
    sources = sorted({it["source"] for it in items})

    tabs = [f'<button class="tab" role="tab" aria-selected="true" data-filter="all">전체<span class="n">{len(items)}</span></button>']
    for c in CATEGORIES:
        if cat_counts.get(c):
            tabs.append(f'<button class="tab" role="tab" aria-selected="false" data-filter="{e(c)}">{e(c)}<span class="n">{cat_counts[c]}</span></button>')

    stats = "".join(
        f'<div class="stat glass"><b>{v}</b><span>{k}</span></div>'
        for k, v in [("기사", len(items)), ("매체", len(sources)), ("카테고리", len(cat_counts))]
    )
    notice = ""
    if len(items) < 10:
        notice = f'<div class="notice">기준(허용 매체·발행일·AI 관련성)을 충족한 기사가 {len(items)}건이어서 {len(items)}건만 실었습니다.</div>'

    gen = doc.get("generated_at") or datetime.now().astimezone().isoformat(timespec="minutes")
    label = f"{target.year}년 {target.month}월 {target.day}일 ({WEEKDAYS[target.weekday()]})"

    page = TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "__DATE_ISO__": target.isoformat(),
        "__DATE_SHORT__": f"{target.month}.{target.day} {WEEKDAYS[target.weekday()]}",
        "__DATE_LABEL__": label,
        "__COUNT__": str(len(items)),
        "__OVERVIEW__": e(doc.get("overview", "")),
        "__STATS__": stats,
        "__NOTICE__": notice,
        "__TABS__": "".join(tabs),
        "__FEATURED__": render_article(items[0], featured=True) if items else "",
        "__CARDS__": "".join(render_article(it) for it in items[1:]),
        "__SOURCES__": "".join(f'<span class="badge badge-outline">{e(s)}</span>' for s in sources),
        "__GENERATED_AT__": e(gen),
    }
    for k, v in repl.items():
        page = page.replace(k, v)
    out.write_text(page, encoding="utf-8")
    print(f"\nOK  {out}  ({len(items)}개 기사, {len(sources)}개 매체, WARN {len(warns)})")


if __name__ == "__main__":
    main()
