# AI Sound Designer

「こんな音を作りたい」を、使用するシンセで実現するための手順と改善サイクルに変えるツール。
初期対象は KORG KRONOS 2（System 3.1.3）。将来 Kurzweil PC3A8 に対応予定。

## セットアップ

```bash
brew install uv
uv sync
cp config/local.example.yaml config/local.yaml
```

## 実機の準備（KRONOS 2）

最初に `docs/safety.md`（バックアップ、テスト用 Program、送信する MIDI の範囲）を確認してください。

```bash
uv run synth-ai devices                          # MIDI 出力ポートと録音デバイスを確認
uv run synth-ai midi-probe --port KRONOS         # PC から 1 音鳴らせるか確認（Note On/Off のみ）
uv run synth-ai capture --run runs/001/          # 参照音と同じ音程で録音し、そのまま比較
```

`config/local.yaml` に MIDI ポートと録音デバイスを書いておくと、以降は省略できます。
MIDI が使えない場合は合図に合わせて手で弾けば、同じ流れで録音・比較できます（`--manual`）。

## 使い方（現在）

```bash
uv run synth-ai analyze assets/reference/lead.wav --out runs/001/   # 参照WAVを解析
uv run synth-ai spec runs/001/                                    # 機種非依存の SoundSpec を作る
uv run synth-ai recipe runs/001/ --synth kronos2                   # KRONOS 用レシピを作る
uv run synth-ai compare runs/001/ take1.wav                       # 実機の録音と比べて次の調整案を出す
uv run synth-ai trial note runs/001/ 1 --closeness 3 --preference 4 --memo "…"  # 聴いた評価を記録
uv run synth-ai trial list runs/001/                              # 試行の一覧
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

`spec` は `sound_spec.json`（音色・包絡のラベル、単位付きの定量目標、合成方式の仮説）を、
`recipe` は `recipes/<機種>/recipe.json` と `recipe.md`（手順書）を出力します。
KRONOS の具体的なパラメータ手順には、公式資料から作るパラメータ表が必要です
（`docs/kronos_parameter_table.md`）。表がない間は、調整する項目と音響上の目標だけを示します。

`compare` は録音を参照音にそろえ（発音開始・音量、音程の差は報告のみ）、特徴量・区間ごとの音量・
区間 × 周波数帯の音色・倍音の差を出して、次の調整案を最大 3 件示します。結果は
`runs/<id>/trials/<NNN>/`（録音のコピー、comparison.md、difference.png など）に保存され、
`history.json` に一覧がまとまります。2 回目以降は前回からの改善・悪化も表示されます。
目標への近さと好みは `trial note` で別々に記録します。

入力は単音・明確なピッチの WAV を想定しています。和音、背景ノイズ、途中で切れた音などは
`analysis.json` の `issues` とコンソールの「注意」に表示されます。

## 開発

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

構成と方針は `CLAUDE.md`、計画は `plan/` を参照。
