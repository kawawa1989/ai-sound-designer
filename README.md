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
uv run synth-ai analyze assets/reference/lead.wav --out runs/001/   # 参照WAVを解析
uv run synth-ai test-signals assets/test                          # 確認用の合成テスト音を生成
uv run synth-ai adapters                                          # 登録済み機種と Capabilities
```

`analyze` の出力:

| ファイル | 内容 |
| --- | --- |
| `analysis.json` | ピッチ・包絡・スペクトル・倍音・時系列・注意事項（`AudioAnalysis`） |
| `envelope.png` | 波形と RMS 包絡（onset / peak / sustain / release の位置） |
| `spectrogram.png` | スペクトログラムとスペクトル重心 |
| `spectrum.png` | 定常区間のスペクトルと検出した倍音 |
| `harmonics.png` | 1〜8 次倍音のレベルの時間変化 |

入力は単音・明確なピッチの WAV を想定しています。和音、背景ノイズ、途中で切れた音などは
`analysis.json` の `issues` とコンソールの「注意」に表示されます。

## 開発

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

構成と方針は `CLAUDE.md`、計画は `plan/` を参照。
