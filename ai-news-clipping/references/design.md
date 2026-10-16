# 디자인 시스템 — shadcn 메인 + 리퀴드 글래스 포인트

디자인 수정 요청이 있을 때만 읽는다. 모든 스타일은 `assets/template.html`의 `<style>` 안에 있다.

## 원칙
- **본문은 shadcn/ui.** 읽는 영역(기사 카드, 탭, 버튼, 배지)은 zinc 팔레트, 1px border, `--radius: 0.75rem`, 얕은 그림자. 정보 밀도와 가독성이 우선이다.
- **리퀴드 글래스는 포인트로만.** 유리 효과(`.glass`)는 다음 4곳에만 쓴다. 더 늘리면 본문 가독성이 떨어지고 "포인트"가 아니게 된다.
  1. 상단 sticky 내비게이션 (pill 형태)
  2. 히어로의 eyebrow 배지와 통계 칩
  3. 1위 기사(Top story) 카드 + 뒤의 오로라 글로우
  4. 2–10위 카드의 순위 번호 칩
- 유리 배경 뒤에는 색이 있어야 유리처럼 보인다. 그래서 히어로 영역에만 블러 처리된 컬러 블롭(`.aurora`)을 깔고, 아래로 갈수록 배경색으로 페이드한다.

## 토큰
| 토큰 | 용도 |
|---|---|
| `--background / --foreground / --card / --muted / --border / --primary` | shadcn 표준 토큰 (light/dark) |
| `--glass-bg / --glass-border / --glass-hi / --glass-lo / --glass-shadow` | 유리 표면, 윗면 하이라이트, 아랫면 반사, 그림자 |
| `--blob-1..4`, `--blob-opacity` | 오로라 색상 |
| `--cat-*` | 카테고리 배지 색 (6종) |

다크 모드는 `prefers-color-scheme`와 `data-theme` 속성 둘 다 지원한다. 토큰을 바꿀 때는 세 곳(`:root`, `@media dark`, `[data-theme="dark"]`)을 함께 바꾼다.

## 카테고리 추가
`scripts/build_html.py`의 `CATEGORIES`, `template.html`의 `.cat[data-cat=...]` 규칙, `SKILL.md`의 카테고리 목록을 함께 수정한다.
