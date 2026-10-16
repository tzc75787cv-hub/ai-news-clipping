# AI News Clipping

어제 날짜 기준으로 최상위 언론(The Economist, BBC, NYT, FT, Reuters 등)에서만 AI 관련 뉴스 10개를 골라 한국어로 요약하고, **shadcn 스타일 + 리퀴드 글래스 포인트** 디자인의 HTML 페이지로 만드는 Claude 스킬입니다.

- 📄 샘플 결과 (2026-10-15): [`index.html`](index.html) — GitHub Pages로도 볼 수 있습니다.
- 🧩 스킬 폴더: [`ai-news-clipping/`](ai-news-clipping/)
- 📦 설치용 패키지: [`ai-news-clipping.skill`](ai-news-clipping.skill)

## 구성
```
ai-news-clipping/
├── SKILL.md                 # Role · Context · Tools · Workflow · Rubric · Guardrails
├── assets/template.html     # shadcn + liquid glass 템플릿
├── references/sources.json  # 허용 매체 화이트리스트 (tier1 / tier2)
├── references/design.md     # 디자인 시스템 가이드
└── scripts/build_html.py    # JSON → HTML 렌더링 + 검증
```

## 사용
Claude에게 "어제 AI 뉴스 클리핑해줘"라고 요청하면 스킬이 실행됩니다. 직접 렌더링하려면:
```bash
python ai-news-clipping/scripts/build_html.py ai-news-2026-10-15.json ai-news-2026-10-15.html
```

> 요약은 원문을 바탕으로 새로 작성한 것이며, 정확한 내용은 각 기사 원문 링크에서 확인하세요.
