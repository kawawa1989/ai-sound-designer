"""公式マニュアル（PDF / txt）を Claude Code で読みやすいテキストに変換する。

PDF を目次の章ごとに Markdown へ分割し、各ページ先頭に PDF ページ番号と
本文ページ番号（マニュアル内の「→ p.xxx」参照と同じ番号）を入れる。
`<manual_dir>/INDEX.md` に章 → ファイル → ページの対応表を書き出す。

PDF・変換テキストは再配布しないため .gitignore 対象。このスクリプトと INDEX.md だけを管理する。
pdftotext（poppler）が必要: brew install poppler

例: uv run python scripts/convert_manuals.py manuals/kronos
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

XHTML = "{http://www.w3.org/1999/xhtml}"
# 目次行: 「見出し . . . . 123」
TOC_LEADER = re.compile(r"^(?P<title>.*?)[\s.]*\.\s*(?P<page>\d+)$")
ROMAN = re.compile(r"^[ivxlc]+$")
# この行末なら次の行と連結しない（文末・見出しらしい終わり方）
NO_JOIN_END = tuple("。．.:：!！?？）)」』】>")
CJK = re.compile(r"[　-ヿ㐀-鿿＀-￯]")
SMALL_PDF_PAGES = 12  # これ以下のページ数なら章分割しない
FALLBACK_CHUNK = 40  # 目次が取れないときのページ数単位の分割


@dataclass(frozen=True)
class TocEntry:
    level: int  # 1 = 章, 2 = 節
    title: str
    printed_page: int


@dataclass(frozen=True)
class Chunk:
    title: str
    first: int  # PDF ページ（1 始まり）
    last: int
    sections: tuple[TocEntry, ...]


def run_pdftotext(pdf: Path, *args: str) -> str:
    result = subprocess.run(
        ["pdftotext", *args, str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def extract_pages(pdf: Path) -> list[str]:
    pages = run_pdftotext(pdf).split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def printed_page_number(text: str) -> int | None:
    """ページ上下端の数字だけの行を本文ページ番号とみなす。"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in (lines[-1:] + lines[:1]) if lines else []:
        if line.isdigit():
            return int(line)
    return None


def page_offset(pages: list[str]) -> int | None:
    """PDF ページ番号 - 本文ページ番号 の最頻値。"""
    diffs = Counter(
        i + 1 - n for i, text in enumerate(pages) if (n := printed_page_number(text)) is not None
    )
    if not diffs:
        return None
    offset, count = diffs.most_common(1)[0]
    return offset if count >= 3 else None


def toc_page_range(pages: list[str]) -> range | None:
    """目次ページ（点線リーダー行が多いページ）の連続範囲。"""

    def is_toc(text: str) -> bool:
        return sum(1 for line in text.splitlines() if ". . ." in line) >= 5

    start = next((i for i, text in enumerate(pages[:20]) if is_toc(text)), None)
    if start is None:
        return None
    end = start
    while end + 1 < len(pages) and is_toc(pages[end + 1]):
        end += 1
    return range(start + 1, end + 2)


def parse_toc(pdf: Path, toc_pages: range) -> list[TocEntry]:
    """目次の文字サイズで章（最大サイズ）と節（次のサイズ）を判定する。"""
    xml = run_pdftotext(
        pdf, "-f", str(toc_pages.start), "-l", str(toc_pages.stop - 1), "-bbox-layout"
    )
    root = ET.fromstring(re.sub(r"<!DOCTYPE[^>]*>", "", xml))

    raw: list[tuple[float, str]] = []
    for line in root.iter(f"{XHTML}line"):
        words = [w for w in line.iter(f"{XHTML}word") if w.text]
        if not words:
            continue
        height = round(float(words[0].get("yMax", 0)) - float(words[0].get("yMin", 0)), 1)
        raw.append((height, " ".join(w.text or "" for w in words)))

    # 見出しが2行に折り返された目次行を連結する
    joined: list[tuple[float, str]] = []
    pending: tuple[float, str] | None = None
    for height, text in raw:
        # 2行目が点線とページ番号だけの場合は文字サイズが少し違うので、見出し側のサイズを使う
        leader_only = re.fullmatch(r"[\s.]*\d+", text) is not None
        if pending and (abs(pending[0] - height) < 0.3 or leader_only):
            sep = "" if CJK.match(pending[1][-1]) and CJK.match(text[0]) else " "
            height, text = pending[0], f"{pending[1]}{sep}{text}"
        pending = None
        if TOC_LEADER.match(text):
            joined.append((height, text))
        elif not text.isdigit() and not ROMAN.match(text):
            pending = (height, text)

    heights = sorted({h for h, _ in joined}, reverse=True)
    if not heights:
        return []
    top = heights[0]
    level1 = {h for h in heights if h >= top - 1.0}
    rest = [h for h in heights if h not in level1]
    level2 = {h for h in rest if rest and h >= rest[0] - 0.45}

    entries: list[TocEntry] = []
    for height, text in joined:
        m = TOC_LEADER.match(text)
        if not m or height not in level1 | level2:
            continue
        title = re.sub(r"\s+", " ", m["title"]).strip(" .")
        entries.append(TocEntry(1 if height in level1 else 2, title, int(m["page"])))
    # 2段組みの目次は読み順が前後するので本文ページ順に並べ直す
    entries.sort(key=lambda e: (e.printed_page, e.level))
    return entries


def plan_chunks(pages: list[str], pdf: Path) -> tuple[list[Chunk], int | None]:
    total = len(pages)
    offset = page_offset(pages)
    if total <= SMALL_PDF_PAGES:
        return [Chunk(pdf.stem, 1, total, ())], offset

    toc_pages = toc_page_range(pages)
    entries = parse_toc(pdf, toc_pages) if toc_pages and offset is not None else []
    chapters = [e for e in entries if e.level == 1]
    if offset is None or not chapters:
        chunks = [
            Chunk(
                f"p{s}-{min(s + FALLBACK_CHUNK - 1, total)}",
                s,
                min(s + FALLBACK_CHUNK - 1, total),
                (),
            )
            for s in range(1, total + 1, FALLBACK_CHUNK)
        ]
        return chunks, offset

    starts = [max(1, c.printed_page + offset) for c in chapters]
    chunks = []
    if starts[0] > 1:
        chunks.append(Chunk("前付け・目次", 1, starts[0] - 1, ()))
    for i, chapter in enumerate(chapters):
        first = starts[i]
        last = starts[i + 1] - 1 if i + 1 < len(starts) else total
        if last < first:
            continue
        sections = tuple(
            e for e in entries if e.level == 2 and first <= e.printed_page + offset <= last
        )
        chunks.append(Chunk(chapter.title, first, last, sections))
    return chunks, offset


def join_wrapped_lines(text: str) -> str:
    """段組みの折り返しで切れた日本語の行を連結し、語が行をまたがないようにする。"""
    lines = text.splitlines()
    lengths = sorted(len(line) for line in lines if line.strip())
    if not lengths:
        return ""
    full = lengths[int(len(lengths) * 0.8)]
    out: list[str] = []
    for line in lines:
        stripped = line.rstrip()
        prev = out[-1] if out else ""
        if (
            prev
            and stripped
            and len(prev) >= full * 0.85
            and not prev.endswith(NO_JOIN_END)
            and CJK.match(prev[-1])
            and CJK.match(stripped[0])
        ):
            out[-1] = prev + stripped
        else:
            out.append(stripped)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def slugify(title: str) -> str:
    slug = re.sub(r"[\s/\\:：,、()（）]+", "_", title)
    slug = re.sub(r"[^\w\-.]", "", slug)
    return slug.strip("_.")[:60] or "chunk"


def printed_label(pdf_page: int, offset: int | None) -> str:
    if offset is None or pdf_page - offset < 1:
        return ""
    return f" 本文p.{pdf_page - offset}"


def convert_pdf(pdf: Path, out_root: Path, rel_root: Path) -> list[str]:
    pages = extract_pages(pdf)
    chunks, offset = plan_chunks(pages, pdf)
    doc_dir = out_root / slugify(pdf.stem)
    doc_dir.mkdir(parents=True, exist_ok=True)

    index = [f"### {pdf.stem}", ""]
    index.append(f"- 元PDF: `{pdf.relative_to(rel_root)}`（{len(pages)}ページ）")
    if offset is not None:
        index.append(f"- 本文ページ番号 = PDFページ番号 - {offset}")
    index += ["", "| ファイル | 章 | PDFページ | 本文ページ |", "|---|---|---|---|"]

    sections_md: list[str] = []
    for n, chunk in enumerate(chunks):
        name = (
            f"{n:02d}-{slugify(chunk.title)}.md" if len(chunks) > 1 else f"{slugify(pdf.stem)}.md"
        )
        path = doc_dir / name
        body = [
            f"# {pdf.stem}: {chunk.title}",
            "",
            f"> 元PDF `{pdf.name}` の PDF p.{chunk.first}–{chunk.last} から自動抽出。"
            "図・表・画面写真は欠落しているので、必要なら元PDFの該当ページを読むこと。",
            "",
        ]
        for p in range(chunk.first, chunk.last + 1):
            body.append(f"<!-- page: PDF p.{p}{printed_label(p, offset)} -->")
            body.append(join_wrapped_lines(pages[p - 1]))
            body.append("")
        path.write_text("\n".join(body), encoding="utf-8")

        printed = ""
        if offset is not None and chunk.first - offset >= 1:
            printed = f"{chunk.first - offset}–{chunk.last - offset}"
        rel = path.relative_to(rel_root)
        index.append(
            f"| [{name}]({rel}) | {chunk.title} | {chunk.first}–{chunk.last} | {printed} |"
        )
        if chunk.sections:
            items = ", ".join(f"{s.title} (p.{s.printed_page})" for s in chunk.sections)
            sections_md.append(f"- **{chunk.title}**: {items}")

    if sections_md:
        index += ["", "節（本文ページ）:", "", *sections_md]
    return [*index, ""]


def convert_texts(src_dir: Path, out_root: Path, rel_root: Path) -> list[str]:
    """MIDI Implementation などの txt は改行を LF に揃えてコピーする。"""
    txts = sorted(src_dir.rglob("*.txt"))
    if not txts:
        return []
    out_dir = out_root / "txt"
    out_dir.mkdir(parents=True, exist_ok=True)
    index = [
        "### テキスト資料（MIDI Implementation など）",
        "",
        "| ファイル | 先頭行 |",
        "|---|---|",
    ]
    for txt in txts:
        text = txt.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        dest = out_dir / txt.name
        dest.write_text(text, encoding="utf-8")
        first = next((line.strip() for line in text.splitlines() if line.strip()), "")
        first = re.sub(r"\s{2,}", " ", first).replace("|", "\\|")[:80]
        index.append(f"| [{txt.name}]({dest.relative_to(rel_root)}) | {first} |")
    return [*index, ""]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manual_dir", type=Path, help="PDF と txt を置いたディレクトリ")
    args = parser.parse_args()
    manual_dir: Path = args.manual_dir

    if shutil.which("pdftotext") is None:
        raise SystemExit("pdftotext が見つかりません: brew install poppler")

    out_root = manual_dir / "text"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir()

    index = [
        f"# {manual_dir.name} 資料インデックス",
        "",
        "`scripts/convert_manuals.py` で自動生成。手で編集しない。",
        "",
        "- 調べるときは、まずこの表で章を絞り、`text/` 以下を grep する。",
        "- 各ページの先頭に `<!-- page: PDF p.N 本文p.M -->` がある。出典は本文ページで書く"
        "（マニュアル内の「→ p.xxx」も本文ページ）。",
        "- 図・表・画面写真は抽出されないので、必要なら元PDFの該当 PDF ページを Read する。",
        "- `text/` と元PDFは著作物のため git 管理外。無ければ"
        f" `uv run python scripts/convert_manuals.py {manual_dir}` で再生成する。",
        "",
    ]
    for pdf in sorted(manual_dir.rglob("*.pdf")):
        print(f"変換中: {pdf}")
        index += convert_pdf(pdf, out_root, manual_dir)
    index += convert_texts(manual_dir, out_root, manual_dir)

    (manual_dir / "INDEX.md").write_text("\n".join(index), encoding="utf-8")
    print(f"完了: {manual_dir / 'INDEX.md'}")


if __name__ == "__main__":
    main()
