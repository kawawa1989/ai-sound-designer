"""KRONOS の .PCG ファイルを読み、バンクごとの内訳と音色どうしの参照関係を Markdown で出力する。

使い方:
    uv run python scripts/pcg_inspect.py <file.PCG> [--out report.md] [--all]

読み取り専用。.PCG と同じフォルダに同名の .KSC があれば、
サンプルの出どころとマルチサンプル名の判定に使う。

オフセットの出典は KORG 公式の MIDI Implementation 付属資料（manuals/kronos/MIDI Implementation/）。
- Prog_HD-1.txt / Prog_EXi_Common.txt: Program（名前 0–23、Oscillator Mode 2558、Category 2568、
  OSC1/OSC2 Zone 2774/3240〜 22 byte 間隔、EXi1/EXi2 Algorithm Type 2857/3909）
- CombiAndSongTimbreSet.txt: Combination（Category 4790、Timbre1 4802〜 188 byte 間隔）
- KRONOS_MIDI_SysEx.txt [33]: Timbre の Bank Number（0–30）とバンク名の対応
資料に書かれていないこと（チャンクの並び、複数 byte 値のエンディアン、バンク ID の意味）は、
実ファイルとの照合で決めた推定で、コード中に「推定」と書いている。
"""

from __future__ import annotations

import argparse
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# --- バンク名 -------------------------------------------------------------

USER_BANKS = ["U-A", "U-B", "U-C", "U-D", "U-E", "U-F", "U-G"] + [
    "U-AA",
    "U-BB",
    "U-CC",
    "U-DD",
    "U-EE",
    "U-FF",
    "U-GG",
]


def chunk_bank_name(bank_id: int) -> str:
    """PCG のバンク・チャンクの ID をバンク名にする。

    推定: 0x2000n が USER、それ未満が INT。
    """
    if bank_id >= 0x20000:
        k = bank_id - 0x20000
        return USER_BANKS[k] if k < len(USER_BANKS) else f"U-?{k}"
    return (
        "INT" if bank_id == 0 else f"INT-{'ABCDEFG'[bank_id]}" if bank_id < 7 else f"INT-?{bank_id}"
    )


def program_chunk_bank_name(bank_id: int) -> str:
    if bank_id >= 0x20000:
        return chunk_bank_name(bank_id)
    # 推定: Program INT-F の ID は 0x8000（PRELOAD.PCG の先頭が Voice Name List の F000 と一致）
    if bank_id == 0x8000:
        return "I-F"
    return f"I-{'ABCDEFG'[bank_id]}" if bank_id < 7 else f"I-?{bank_id:#x}"


def timbre_bank_name(n: int) -> str:
    """Timbre の Bank Number（KRONOS_MIDI_SysEx.txt [33] の prog 列）。"""
    if n <= 5:
        return f"I-{'ABCDEF'[n]}"
    if n == 6:
        return "GM"
    if 7 <= n <= 15:
        return f"g({n - 6})"
    if n == 16:
        return "g(d)"
    if 17 <= n <= 30:
        return USER_BANKS[n - 17]
    return f"?{n}"


# --- 列挙値 ---------------------------------------------------------------

EXI_TYPES = [
    "Off",
    "HD-1",
    "AL-1",
    "CX-3",
    "STR-1",
    "MS-20EX",
    "PolysixEX",
    "MOD-7",
    "SGX-2",
    "EP-1",
]
# Parameter Guide 01-Program_モード_HD-1 の [Single, Double, Drums, Double Drums]
HD1_OSC_MODES = ["Single", "Double", "Drums", "Double Drums"]
# Combination の Status は [Off, INT, EXT, EX2]、Sequencer は [Off, INT, BTH, EXT, EX2]。
# 値は共通構造の 0–4。
TIMBRE_STATUS = ["Off", "INT", "BTH", "EXT", "EX2"]
ZONE_TYPES = ["Off", "MS", "WS"]
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

WS_INT_COUNT = 150  # INT のウェーブ・シーケンス数（WBK1 INT の件数）
WS_USER_SIZE = 32
KORG_ROM_PREFIX = b"KORG"


def note(n: int) -> str:
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 1}"


def text(b: bytes) -> str:
    return b.split(b"\0")[0].decode("latin1").rstrip()


# --- データ ---------------------------------------------------------------


@dataclass
class Zone:
    osc: int
    zone: int
    kind: str  # MS / WS
    bank_uuid: bytes
    number: int


@dataclass
class Program:
    bank: str
    index: int
    name: str
    engine: str  # "HD-1 Single" / "EXi: AL-1 + CX-3" など
    category: int
    zones: list[Zone] = field(default_factory=list)

    @property
    def ref(self) -> str:
        return f"{self.bank}{self.index:03d}"


@dataclass
class Timbre:
    number: int
    status: str
    bank: str
    program: int
    channel: int
    volume: int
    mute: bool
    key_bottom: int
    key_top: int

    @property
    def ref(self) -> str:
        return f"{self.bank}{self.program:03d}"

    @property
    def sounding(self) -> bool:
        """本体の鍵盤で弾いたときに鳴るか。

        Global MIDI Channel を 1 と仮定し、Ch1 と Gch のティンバーだけを鳴るとみなす。
        """
        return (
            self.status in ("INT", "BTH")
            and self.volume > 0
            and not self.mute
            and self.channel in (0, 16)
        )


@dataclass
class Combi:
    bank: str
    index: int
    name: str
    category: int
    timbres: list[Timbre]

    @property
    def ref(self) -> str:
        return f"{self.bank}{self.index:03d}"


@dataclass
class NamedEntry:
    bank: str
    index: int
    name: str


@dataclass
class Pcg:
    programs: list[Program] = field(default_factory=list)
    combis: list[Combi] = field(default_factory=list)
    drumkits: list[NamedEntry] = field(default_factory=list)
    wavesequences: list[NamedEntry] = field(default_factory=list)
    banks: list[tuple[str, str, int, int]] = field(
        default_factory=list
    )  # (種類, バンク, 名前あり, 枠数)


# --- 読み込み -------------------------------------------------------------

# 推定: チャンクは「ID 4 byte + サイズ 4 byte（big endian）+ 4 byte」の
# 12 byte ヘッダーの後に本体が続く。バンク・チャンクの本体は
# 「件数・1 件のサイズ・バンク ID（各 4 byte big endian）」の後にデータが並ぶ。
CONTAINERS = {b"PCG1", b"PRG1", b"CMB1", b"DKT1", b"WSQ1"}


def iter_bank_chunks(d: bytes) -> list[tuple[bytes, int, int, int, int]]:
    """(チャンク ID, 件数, 1 件のサイズ, バンク ID, データ先頭) の一覧。"""
    out = []

    def walk(o: int, end: int) -> None:
        while o + 12 <= end:
            cid = d[o : o + 4]
            if not cid.isalnum():
                return
            size = struct.unpack(">I", d[o + 4 : o + 8])[0]
            if cid in CONTAINERS:
                walk(o + 12, o + 12 + size)
            elif cid.endswith(b"BK1") and size >= 12:
                n, esz, bid = struct.unpack(">III", d[o + 12 : o + 24])
                out.append((cid, n, esz, bid, o + 24))
            o += 12 + size

    if d[:4] != b"KORG":
        raise ValueError("KORG のファイルではありません")
    walk(0x10, len(d))
    return out


def parse_program(e: bytes, bank: str, index: int, is_exi_bank: bool) -> Program:
    name = text(e[:24])
    category = e[2568] & 0x1F
    if is_exi_bank:
        types = [EXI_TYPES[t] if t < len(EXI_TYPES) else f"?{t}" for t in (e[2857], e[3909])]
        engine = "EXi: " + " + ".join(t for t in types if t != "Off")
        return Program(bank, index, name, engine, category)
    mode = e[2558] & 0x07
    engine = "HD-1 " + (
        HD1_OSC_MODES[mode] if mode < len(HD1_OSC_MODES) else f"Mode?{mode}（要確認）"
    )
    zones = []
    oscs = [(1, 2774)] + ([(2, 3240)] if mode in (1, 3) else [])
    for osc, base in oscs:
        for z in range(8):
            zo = base + 22 * z
            kind = e[zo] & 0x03
            if kind == 0:
                continue
            # 推定: MS Number は little endian（ROM の番号が Voice Name List と一致する）
            number = struct.unpack("<H", e[zo + 18 : zo + 20])[0]
            zones.append(
                Zone(osc, z + 1, ZONE_TYPES[kind] if kind < 3 else "?", e[zo + 1 : zo + 17], number)
            )
    return Program(bank, index, name, engine, category, zones)


def parse_combi(e: bytes, bank: str, index: int) -> Combi:
    timbres = []
    for t in range(16):
        o = 4802 + 188 * t
        st = e[o + 2] >> 5
        timbres.append(
            Timbre(
                number=t + 1,
                status=TIMBRE_STATUS[st] if st < len(TIMBRE_STATUS) else f"?{st}",
                bank=timbre_bank_name(e[o + 1]),
                program=e[o],
                channel=e[o + 2] & 0x1F,
                volume=e[o + 5],
                mute=bool(e[o + 34] & 0x80),
                key_top=e[o + 37],
                key_bottom=e[o + 38],
            )
        )
    return Combi(bank, index, text(e[:24]), e[4790] & 0x1F, timbres)


def load_pcg(path: Path) -> Pcg:
    d = path.read_bytes()
    pcg = Pcg()
    for cid, n, esz, bid, start in iter_bank_chunks(d):
        entries = [d[start + i * esz : start + (i + 1) * esz] for i in range(n)]
        names = [text(e[:24]) for e in entries]
        named = sum(1 for x in names if x)
        if cid in (b"MBK1", b"PBK1"):
            # 推定: MBK1 が EXi バンク、PBK1 が HD-1 バンク（中身の Oscillator Mode と一致）
            bank = program_chunk_bank_name(bid)
            pcg.banks.append(("Program " + ("EXi" if cid == b"MBK1" else "HD-1"), bank, named, n))
            for i, e in enumerate(entries):
                if names[i]:
                    pcg.programs.append(parse_program(e, bank, i, cid == b"MBK1"))
        elif cid == b"CBK1":
            bank = program_chunk_bank_name(bid)
            pcg.banks.append(("Combination", bank, named, n))
            for i, e in enumerate(entries):
                if names[i]:
                    pcg.combis.append(parse_combi(e, bank, i))
        elif cid in (b"DBK1", b"WBK1"):
            bank = chunk_bank_name(bid)
            kind = "Drum Kit" if cid == b"DBK1" else "Wave Sequence"
            pcg.banks.append((kind, bank, named, n))
            target = pcg.drumkits if cid == b"DBK1" else pcg.wavesequences
            target.extend(NamedEntry(bank, i, x) for i, x in enumerate(names) if x)
    return pcg


# 推定: プログラムが指すパック内マルチサンプルの番号は、.KSC に並ぶ .KMP の順番 + 2。
# IAW21 で 9 件すべて名前が音色名と合ったことからの推定で、資料では確認していない。
KSC_MS_NUMBER_OFFSET = 2


def kmp_name(path: Path) -> str | None:
    """.KMP 先頭の MSP1 チャンクにあるマルチサンプル名。"""
    try:
        head = path.read_bytes()[:26]
    except OSError:
        return None
    return text(head[8:24]) if head[:4] == b"MSP1" else None


def load_ksc_names(pcg_path: Path) -> tuple[set[bytes], dict[int, str]]:
    """同名の .KSC から、このパックのサンプル・バンク UUID と マルチサンプル番号→名前 を集める。"""
    uuids: set[bytes] = set()
    names: dict[int, str] = {}
    ksc = pcg_path.with_suffix(".KSC")
    if not ksc.exists():
        return uuids, names
    kmps = []
    for line in ksc.read_text("latin1").splitlines():
        line = line.strip()
        if line.startswith("#uuid:"):
            uuids.add(bytes.fromhex(line[6:].replace("-", "")))
        elif line.upper().endswith(".KMP") and not line.startswith("#"):
            kmps.append(line)
    for i, kmp in enumerate(kmps):
        hits = list(ksc.parent.rglob(kmp))
        name = kmp_name(hits[0]) if hits else None
        names[i + KSC_MS_NUMBER_OFFSET] = f"{name or kmp}（{kmp}）"
    return uuids, names


# --- 出力 -----------------------------------------------------------------


def ws_ref(n: int) -> str:
    if n < WS_INT_COUNT:
        return f"INT{n:03d}"
    k, i = divmod(n - WS_INT_COUNT, WS_USER_SIZE)
    return f"{USER_BANKS[k] if k < len(USER_BANKS) else '?'}{i:02d}"


def describe_zone(z: Zone, pack_uuids: set[bytes], ms_names: dict[int, str]) -> str:
    if z.kind == "WS":
        return f"Wave Seq {ws_ref(z.number)}"
    if z.bank_uuid.startswith(KORG_ROM_PREFIX):
        sub = struct.unpack(">H", z.bank_uuid[14:16])[0]
        src = "ROM" if sub == 0 else f"KORG EXs（ID {sub}、どの EXs かは要確認）"
        return f"{src} MS {z.number}"
    # 推定: UUID の末尾 1 byte だけ違うもの（…de / …df）も同じ KSC 由来として扱う
    if any(z.bank_uuid[:15] == u[:15] for u in pack_uuids):
        name = ms_names.get(z.number)
        return f"パックのサンプル #{z.number}" + (f" {name}（推定）" if name else "")
    return f"外部サンプル {z.bank_uuid.hex()[:8]}… #{z.number}"


def md_escape(s: str) -> str:
    return s.replace("|", "\\|") or "(名前なし)"


def render(pcg: Pcg, path: Path, show_all: bool) -> str:
    pack_uuids, ms_names = load_ksc_names(path)
    progs = {p.ref: p for p in pcg.programs}
    used_by: dict[str, list[str]] = defaultdict(list)
    for c in pcg.combis:
        for t in c.timbres:
            if t.sounding and c.ref not in used_by[t.ref]:
                used_by[t.ref].append(c.ref)

    out = [f"# {path.name} の内訳", ""]
    out += ["## 含まれるバンク", "", "| 種類 | バンク | 名前あり / 枠数 |", "|---|---|---|"]
    out += [f"| {k} | {b} | {n} / {total} |" for k, b, n, total in pcg.banks]
    out += [
        "",
        "PCG を丸ごとロードすると、上の表のバンクがすべて上書きされる。",
        "名前のない枠も中身は入っているので、上書きの対象になる。",
        "",
    ]

    out += [
        "## プログラム",
        "",
        "| 番号 | 名前 | 音源 | Cat | 使うサンプル / WS | 使っているコンビ |",
        "|---|---|---|---|---|---|",
    ]
    for p in pcg.programs:
        srcs = sorted({describe_zone(z, pack_uuids, ms_names) for z in p.zones})
        users = used_by.get(p.ref, [])
        out.append(
            f"| {p.ref} | {md_escape(p.name)} | {p.engine} | {p.category} | "
            f"{'<br>'.join(srcs) or '—'} | {', '.join(users) if users else '—'} |"
        )
    out.append("")

    out += ["## コンビネーション", ""]
    out += [
        "鳴るティンバー（Status が INT/BTH、Volume > 0、Mute でない、Ch1 か Gch）だけを示す。",
        "Ch は Global MIDI Channel が 1 の前提。全ティンバーを見るときは --all を付ける。",
        "「PCG 外」は、このファイルに入っていないプログラムを参照していることを表す",
        "（本体側の音に依存する）。",
        "",
        "| 番号 | 名前 | Cat | ティンバー（T番号: プログラム / Ch / 鍵域 / Vol） |",
        "|---|---|---|---|",
    ]
    external: dict[str, list[str]] = defaultdict(list)
    for c in pcg.combis:
        parts = []
        for t in c.timbres:
            if not (t.sounding or show_all):
                continue
            target = progs.get(t.ref)
            if target:
                pname = md_escape(target.name)
            else:
                pname = "**PCG 外**"
                if t.sounding and c.ref not in external[t.ref]:
                    external[t.ref].append(c.ref)
            ch = "Gch" if t.channel == 16 else str(t.channel + 1)
            keys = (
                ""
                if (t.key_bottom, t.key_top) == (0, 127)
                else f" / {note(t.key_bottom)}–{note(t.key_top)}"
            )
            flag = "" if t.sounding else f" [{t.status}{' Mute' if t.mute else ''} Vol{t.volume}]"
            parts.append(f"T{t.number}: {t.ref} {pname} / Ch{ch}{keys} / Vol{t.volume}{flag}")
        out.append(
            f"| {c.ref} | {md_escape(c.name)} | {c.category} | "
            f"{'<br>'.join(parts) or '（鳴るティンバーなし）'} |"
        )
    out.append("")

    out += ["## 依存関係のまとめ", ""]
    pack_progs = sorted({ref for ref in used_by if ref in progs})
    out.append(f"- コンビから使われているプログラム（PCG 内）: {len(pack_progs)} 個")
    unused = [p.ref for p in pcg.programs if p.ref not in used_by]
    out.append(f"- どのコンビからも使われていないプログラム: {', '.join(unused) or 'なし'}")
    groups = {
        "U": "USER バンク（本体のその番号にある自分の音で鳴る。要注意）",
        "I": "INT バンク（工場出荷の音。上書きしていなければ想定どおり鳴る）",
        "G": "GM バンク（固定なので常に同じ音）",
    }
    if not external:
        out.append("- PCG 外のプログラムへの参照: なし")
    for key, label in groups.items():
        refs = [r for r in sorted(external) if r[0].upper() == key]
        if refs:
            out.append(f"- PCG 外の参照 — {label}:")
            out += [f"  - {r}: {', '.join(external[r])}" for r in refs]
    pack_sample_progs = [
        p.ref
        for p in pcg.programs
        if any(describe_zone(z, pack_uuids, ms_names).startswith("パック") for z in p.zones)
    ]
    out.append(
        f"- パックのサンプル（KSC）が必要なプログラム: {', '.join(pack_sample_progs) or 'なし'}"
    )
    ws_used = sorted({ws_ref(z.number) for p in pcg.programs for z in p.zones if z.kind == "WS"})
    out.append(f"- 使われているウェーブ・シーケンス: {', '.join(ws_used) or 'なし'}")
    out.append("")

    for title, entries in (
        ("ドラムキット", pcg.drumkits),
        ("ウェーブ・シーケンス", pcg.wavesequences),
    ):
        out += [f"## {title}（バンクごとの件数と先頭の名前）", ""]
        by_bank: dict[str, list[NamedEntry]] = defaultdict(list)
        for x in entries:
            by_bank[x.bank].append(x)
        for bank, xs in by_bank.items():
            head = ", ".join(md_escape(x.name) for x in xs[:4])
            out.append(f"- {bank}: {len(xs)} 件（{head}{' …' if len(xs) > 4 else ''}）")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="KRONOS .PCG の内訳を Markdown で出力する（読み取り専用）"
    )
    ap.add_argument("pcg", type=Path)
    ap.add_argument("--out", type=Path, help="出力先（省略時は標準出力）")
    ap.add_argument("--all", action="store_true", help="鳴らないティンバーも表示する")
    args = ap.parse_args()
    report = render(load_pcg(args.pcg), args.pcg, args.all)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"書き出しました: {args.out}", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
