# AI Sound Designer

「こんな音を作りたい」を、使用するシンセで実現するための手順と改善サイクルに変えるツール。
初期対象は KORG KRONOS 2（System 3.1.3）。将来 Kurzweil PC3A8 に対応予定。

## セットアップ

```bash
brew install uv
uv sync
cp config/local.example.yaml config/local.yaml
```

## 使い方（現在）

```bash
uv run synth-ai adapters   # 登録済み機種と Capabilities を表示
```

## 開発

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

構成と方針は `CLAUDE.md`、計画は `plan/` を参照。
