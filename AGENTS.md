# AI Sound Designer

参照WAVを解析 → 機種非依存の `SoundSpec` → 機種別Adapterで `PatchRecipe` → 実機録音と比較して改善する。
計画: `plan/roadmap/roadmap.md`（v1.2）、`plan/implementation-plan.md`（スプリント計画）。

## コマンド

- テスト: `uv run pytest`
- Lint/整形: `uv run ruff check . && uv run ruff format .`
- 型: `uv run mypy`
- CLI: `uv run synth-ai --help`

Python は 3.12 固定（uv 管理）。システムの python3 は使わない。

## 公式資料

- KRONOS のマニュアルは `manuals/kronos/INDEX.md` で章を絞り、`manuals/kronos/text/` を grep して読む。
- パラメータ名・値を書くときは出典を「Parameter Guide 本文p.200」のように本文ページで残す。
- 図・表が必要なときは INDEX の PDF ページを元PDFから Read する。
- PDF と `text/` は git 管理外。`text/` が無ければ `uv run python scripts/convert_manuals.py manuals/kronos` で再生成する（要 poppler）。

## 依存ルール（tests/architecture で強制）

- `synth_ai.core` は `synth_ai.core` と `synth_ai.adapters.base` 以外を import しない。
- core に機種名・エンジン名（KRONOS, PC3A8, AL-1 など）を書かない。`if synth == ...` 分岐を置かない。
- 各 Adapter は他の Adapter を import しない。
- Adapter の選択・注入はアプリケーション層（`registry.py`, `cli.py`）で行う。
- 新しい Adapter は `tests/adapter_contract/test_contract.py` の `ADAPTERS` に追加する。

## データ形式

- `AudioAnalysis`（観測値）/ `SoundSpec`（機種非依存）/ `PatchRecipe`（機種固有）を混在させない。
- すべて frozen・`schema_version` 付き。Adapter は SoundSpec を変更しない。
- Capabilities は `supported / unsupported / unverified`。unverified は使用不可として扱う。

## 禁止事項（実機の安全）

詳細は `docs/safety.md`。ノートの送信は `infrastructure/midi/sender.py` で Note On/Off と All Notes Off に制限している。
実機に音を出すコマンド（midi-probe, capture, calibrate）と、実機の状態を読み書きするコマンド
（SysEx を使うもの）は、ユーザーの指示なしに実行しない。

- KRONOS の OS 更新（System 3.1.3 固定）。
- `docs/safety.md` の「SysEx の扱い」で「使う」としたもの以外の SysEx を送ること。
  書き込み（43 Parameter Change）は同ページの「書き込みの条件」をすべて満たすときだけ。
- ツールから Global 設定を変えること、本体に保存（Write）すること、既存 Program を上書きすること。
  テスト用 Bank/Program 以外を触らない。
- 公式資料で確認していない KRONOS / PC3A8 のパラメータ名・ページ名・値を生成しない。不明なら「要確認」とする。
