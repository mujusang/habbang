#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
『중경방 임상강좌 각론』 읽기 화면 빌드 스크립트.

    src/*.md  →  이 폴더의 index.html / doc-NN.html

쓰는 법
    1) src/ 에 새 문서(md)를 넣는다.
    2) docs.txt 에 "파일명 | 사이드바 이름" 한 줄을 적는다. (안 적어도 뒤에 자동으로 붙는다)
    3) python3 build.py
    4) git add -A && git commit && git push

필요 패키지: python-markdown  (pip install markdown)
"""
from __future__ import annotations

import html
import os
import re
import sys
import hashlib
from pathlib import Path

try:
    import markdown
except ImportError:  # pragma: no cover
    sys.exit("python-markdown 이 필요합니다:  pip install markdown")

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
MANIFEST = HERE / "docs.txt"

SITE_TITLE = "중경방 임상강좌 각론"
SITE_SUB = "1단계 완성본 · 2026.11.25"
SITE_FOOT = "내부 학습용 정리본 — 링크를 받은 분만 열람"

MD_EXT = ["tables", "fenced_code", "toc", "sane_lists", "attr_list", "md_in_html", "nl2br"]
MD_EXT_CFG = {"toc": {"permalink": False, "toc_depth": "1-6"}}

HEAD_RE = re.compile(r"<h([1-6])([^>]*)>(.*?)</h\1>", re.S)
ID_RE = re.compile(r'id="([^"]*)"')
TAG_RE = re.compile(r"<[^>]+>")


# ── 목록 읽기 ─────────────────────────────────────────────
def read_manifest() -> list[tuple[str, str | None]]:
    items: list[tuple[str, str | None]] = []
    if MANIFEST.exists():
        for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                name, label = line.split("|", 1)
                items.append((name.strip(), label.strip() or None))
            else:
                items.append((line, None))
    seen = {n for n, _ in items}
    extra = sorted(
        p.name for p in SRC.glob("*.md") if p.name not in seen
    )
    for name in extra:
        print(f"  · docs.txt 에 없어 뒤에 붙임: {name}")
        items.append((name, None))
    return items


# ── 마크다운 → HTML ──────────────────────────────────────
LIST_START = re.compile(r"^(\- |\* |\+ |\d+\. )")


def normalize_lists(text: str) -> str:
    """문단 바로 뒤에 줄바꿈만 두고 시작한 목록은 빈 줄을 넣어 목록으로 살린다."""
    out: list[str] = []
    in_fence = False
    prev = ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            prev = line
            continue
        if (
            not in_fence
            and LIST_START.match(s)
            and prev.strip()
            and not LIST_START.match(prev.strip())
            and not prev.lstrip().startswith(("#", ">", "|"))
            and not prev.strip().startswith("---")
        ):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def split_title(text: str) -> tuple[str, str]:
    """첫 '# 제목' 줄을 떼어 낸다."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            rest = "\n".join(lines[:i] + lines[i + 1 :])
            return title, rest
    return "", text


def demote(html_text: str) -> str:
    """제목이 여러 개(H1)인 문서에서 두 번째부터 한 단계씩 내린다."""
    def repl(m: re.Match) -> str:
        lvl = min(int(m.group(1)) + 1, 6)
        return f"<h{lvl}{m.group(2)}>{m.group(3)}</h{lvl}>"

    return HEAD_RE.sub(repl, html_text)


def plain(s: str) -> str:
    return html.unescape(TAG_RE.sub("", s)).strip()


def renumber_ids(html_text: str) -> str:
    """제목 id 를 문서 순서대로 짧고 안전한 값(s-1, s-2 …)으로 다시 매긴다."""
    n = [0]

    def repl(m: re.Match) -> str:
        n[0] += 1
        new = f"s-{n[0]}"
        attrs = m.group(2)
        if re.search(r'id="[^"]*"', attrs):
            attrs = re.sub(r'id="[^"]*"', f'id="{new}"', attrs, count=1)
        else:
            attrs = f' id="{new}"' + attrs
        lvl = m.group(1)
        return f"<h{lvl}{attrs}>{m.group(3)}</h{lvl}>"

    return HEAD_RE.sub(repl, html_text)


def build_doc(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    title, body_md = split_title(raw)
    body_md = normalize_lists(body_md)
    has_many_h1 = len(re.findall(r"^# ", body_md, re.M)) > 0

    md = markdown.Markdown(extensions=MD_EXT, extension_configs=MD_EXT_CFG)
    body = md.convert(body_md)
    if has_many_h1:
        body = demote(body)
    body = renumber_ids(body)
    if not title:
        m = HEAD_RE.search(body)
        title = plain(m.group(3)) if m else path.stem

    # 첫 인용구(머리말)는 안내 카드로
    bq = body.find("<blockquote>")
    h2 = body.find("<h2")
    if bq != -1 and (h2 == -1 or bq < h2):
        body = body[:bq] + '<blockquote class="docmeta">' + body[bq + len("<blockquote>") :]

    # 표 감싸기
    body = re.sub(r"<table>(.*?)</table>", r'<div class="tablewrap"><table>\1</table></div>', body, flags=re.S)

    # 한 문단짜리 강조는 「핵심 한 줄」로 표시
    body = re.sub(r"<p><strong>(.*?)</strong></p>", r'<p class="key"><strong>\1</strong></p>', body, flags=re.S)

    # 한 문단짜리 강조는 안내 상자로
    body = re.sub(r"<p>\s*<em>(.*?)</em>\s*</p>", r'<p class="aside">\1</p>', body, flags=re.S)

    heads = []
    for m in HEAD_RE.finditer(body):
        lvl = int(m.group(1))
        if lvl not in (2, 3):
            continue
        mid = ID_RE.search(m.group(2))
        if not mid:
            continue
        heads.append((lvl, mid.group(1), plain(m.group(3))))

    return {"path": path, "title": title, "body": body, "heads": heads}


# ── HTML 조립 ────────────────────────────────────────────
def esc(s: str) -> str:
    return html.escape(s, quote=True)


def doc_href(i: int) -> str:
    return "index.html" if i == 0 else f"doc-{i + 1:02d}.html"


def sidebar(docs: list[dict], cur: int) -> str:
    out = ['<aside id="sidebar">']
    out.append('<button class="sbclose" id="sbClose" aria-label="목차 닫기">✕</button>')
    out.append(
        f'<div class="brand"><a href="{doc_href(0)}">{esc(SITE_TITLE)}</a>'
        f"<span>{esc(SITE_SUB)}</span></div>"
    )
    out.append('<div class="navlabel">문서</div><ul class="doclist">')
    for i, d in enumerate(docs):
        cls = " class=\"active\"" if i == cur else ""
        out.append(
            f'<li{cls}><a href="{doc_href(i)}"><span class="num">{i:02d}</span>'
            f"<span>{esc(d['label'])}</span></a></li>"
        )
    out.append("</ul>")

    heads = docs[cur]["heads"]
    out.append('<div class="navlabel">이 문서</div>')
    if any(h[0] == 3 for h in heads):
        out.append('<input id="tocFilter" type="search" placeholder="이 문서의 목차에서 찾기" aria-label="이 문서의 목차에서 찾기">')
    out.append('<ul class="sectionlist">')
    i = 0
    while i < len(heads):
        lvl, hid, text = heads[i]
        if lvl == 3:  # 상위 h2 없이 시작하는 소절
            i += 1
            continue
        subs = []
        j = i + 1
        while j < len(heads) and heads[j][0] == 3:
            subs.append(heads[j])
            j += 1
        chev = (
            f'<button class="chev" aria-expanded="false" aria-label="소절 펼치기">▸</button>'
            if subs
            else ""
        )
        out.append(f'<li><div class="row"><a href="#{esc(hid)}">{esc(text)}</a>{chev}</div>')
        if subs:
            out.append('<ul class="s3">')
            for _, sid, stext in subs:
                out.append(f'<li><a href="#{esc(sid)}">{esc(stext)}</a></li>')
            out.append("</ul>")
        out.append("</li>")
        i = j
    out.append("</ul>")
    out.append(f'<div class="sb-foot">{esc(SITE_FOOT)}</div>')
    out.append("</aside>")
    return "\n".join(out)


def pager(docs: list[dict], cur: int) -> str:
    out = ['<nav class="pager">']
    if cur > 0:
        p = docs[cur - 1]
        out.append(
            f'<a class="prev" href="{doc_href(cur - 1)}"><span class="k">← 이전 문서</span>'
            f'<span class="t">{esc(p["label"])}</span></a>'
        )
    else:
        out.append('<span class="empty"></span>')
    if cur < len(docs) - 1:
        n = docs[cur + 1]
        out.append(
            f'<a class="next" href="{doc_href(cur + 1)}"><span class="k">다음 문서 →</span>'
            f'<span class="t">{esc(n["label"])}</span></a>'
        )
    out.append("</nav>")
    return "\n".join(out)


PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<meta name="googlebot" content="noindex,nofollow,noarchive">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light dark">
<title>{title} · {site}</title>
<link rel="stylesheet" href="assets/style.css?v={cssv}">
</head>
<body>
<div class="progress" id="progress"></div>
<header class="topbar">
  <button id="menuBtn" aria-label="목차 열기">☰</button>
  <span class="topbar-title">{site}</span>
  <span class="topbar-doc">{label}</span>
</header>
<div class="shell">
{sidebar}
<main>
<article>
<h1 class="doctitle">{title}</h1>
{body}
</article>
{pager}
</main>
</div>
<div id="backdrop"></div>
<button id="totop" aria-label="맨 위로">↑</button>
<script src="assets/app.js?v={jsv}"></script>
</body>
</html>
"""


def asset_version(name: str) -> str:
    """css/js 를 고치면 브라우저가 새 파일을 받도록 내용 해시를 붙인다."""
    p = HERE / "assets" / name
    if not p.exists():
        return "1"
    return hashlib.md5(p.read_bytes()).hexdigest()[:8]


def main() -> None:
    entries = read_manifest()
    if not entries:
        sys.exit("src/ 에 md 문서가 없습니다.")

    docs = []
    for name, label in entries:
        p = SRC / name
        if not p.exists():
            print(f"  ! 파일 없음, 건너뜀: {name}")
            continue
        d = build_doc(p)
        d["label"] = label or d["title"]
        docs.append(d)

    for i, d in enumerate(docs):
        page = PAGE.format(
            title=esc(d["title"]),
            site=esc(SITE_TITLE),
            label=esc(d["label"]),
            sidebar=sidebar(docs, i),
            body=d["body"],
            pager=pager(docs, i),
            cssv=asset_version("style.css"),
            jsv=asset_version("app.js"),
        )
        out = HERE / doc_href(i)
        out.write_text(page, encoding="utf-8")
        print(f"  ✓ {out.name:14s} {len(page) / 1024:7.1f} KB  ({d['path'].name})")

    print(f"완료 — 문서 {len(docs)}개")


if __name__ == "__main__":
    main()
