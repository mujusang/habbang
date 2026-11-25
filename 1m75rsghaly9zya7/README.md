# 중경방 임상강좌 각론 — 읽기 화면 (1단계)

원장님 개인 열람용 정리본입니다. 링크를 받은 분만 열도록 임의 주소로 두었고, 모든 페이지에
`noindex,nofollow,noarchive` 를 넣었으며 어디에서도 이 주소로 가는 링크를 만들지 않았습니다.

## 화면 구성

- `index.html` — 문서 01 (전체 목차와 결)
- `doc-02.html` …, `doc-04.html` — 문서 02~04
- `assets/style.css`, `assets/app.js` — 조판·목차·진행 표시
- `src/*.md` — 원본 마크다운
- `docs.txt` — 문서 순서와 사이드바 이름
- `build.py` — 빌드 스크립트

## 2·3단계에서 갱신하는 법

```bash
# 1. 새 md 를 src/ 에 넣는다 (파일명 예: 각론_part2_2군.md)
cp /path/각론_part2_2군.md src/

# 2. docs.txt 에 한 줄 추가  (안 적어도 뒤에 자동으로 붙는다)
echo "각론_part2_2군.md | 2군" >> docs.txt

# 3. 빌드 · 배포
pip install markdown      # 처음 한 번만
python3 build.py
cd .. && git add -A && git commit -m "각론 2단계 반영" && git push
```

주소는 그대로입니다. `src/*.md` 를 고치고 `build.py` 만 다시 돌려도 됩니다.
