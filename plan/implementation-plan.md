# AI Sound Designer — 実現性評価と実装計画

作成日: 2026-10-18 / 対象: `plan/roadmap/roadmap.md` v1.2

---

## 1. 結論（実現性判断）

**MVP（Phase 0〜3）は十分に実現可能。** ただし、技術的に一番難しいのは音声解析ではなく、**「音響特徴 → KRONOSのパラメータ値」の翻訳**。ここを公式資料の転記だけで解決しようとすると、「方向は合っているが値が当たらない」レシピになりやすい。対策として、**実機キャリブレーション（パラメータを動かして録音・測定し、対応表を作る工程）** をPhase 2に追加することを推奨する。

| Phase | 内容 | 実現性 | 主なリスク | 判断 |
| --- | --- | --- | --- | --- |
| 0 | 環境・接続・Adapter契約 | **高** | macOSでのUSB Audio/MIDI認識、ターミナルのマイク権限 | 半日〜2日。駄目でも手動録音で回避可 |
| 1 | 参照WAV解析 | **高** | 参照音のリバーブ・ノイズ、ピッチ推定の失敗 | 確立した技術（librosa）で完結 |
| 2 | SoundSpec＋AL-1レシピ | **中〜高** | パラメータ値の非線形性（0–99等の値と実際のHz/msの対応が不明） | キャリブレーションを入れれば高 |
| 3 | 比較・改善ループ | **高** | 音程・音量・開始位置のアライメント、録音経路差 | 前処理を丁寧にすれば安定 |
| 4 | 独自波形・HD-1サンプル | **中〜高** | 取り込みは手動手順、ループ品質 | 手動取り込み前提なら実現可 |
| 5 | PC3A8 Adapter | **中〜高**（手動レシピ） | V.A.S.T.の資料整理量、録音経路が外部IF | Core設計が守られていれば追加は素直 |
| 6 | SysEx自動編集 | **低〜中** | KRONOSのパラメータ変更SysExの網羅性・実機挙動、事故時の影響 | 調査依存。MVPの価値には不要 |

**総合判断: Go。** ロードマップの「分析と提案 → 実機録音 → パラメータ編集」の順序と「自動化は必須ではない」という方針は、リスクの大きい部分を後回しにしており妥当。

### 1.1 ロードマップに対する修正提案

1. **実機キャリブレーション工程の追加（最重要）**
   AL-1のフィルターCutoff・EG時間・Resonance等は、表示値と実際の音響量の関係が非線形かつ資料に数値が載っていない場合が多い。
   → テスト用Programで「1パラメータだけを数段階変えて録音 → 解析」し、`data/kronos_calibration/*.json` に保存。レシピの推奨値はこの対応表から逆引きする。PC3A8でも同じ仕組みを使える（Core側は「パラメータ値 ↔ 音響特徴の対応表」を機種非依存の形で扱える）。
2. **SoundSpecに定量目標も持たせる**
   `"attack": "fast"` のようなラベルだけだとレシピ値の根拠が弱く、比較の基準にも使えない。ラベルと並べて単位付きの目標値（`attack_ms`, `centroid_hz` の時系列、倍音減衰率など）と許容幅を持たせる。どちらも機種非依存なので原則に反しない。
3. **Python 3.15を使わない**
   この環境の `python3` は 3.15.0。librosaが依存するnumbaは最新Pythonへの対応が遅れることが多い。**uvでPython 3.12を固定**する。
4. **macOSの権限・デバイス名を最初に確認**
   `sounddevice` での録音には、実行するアプリ（Terminal / Claude）へのマイク許可が必要。最初に詰まりやすい点なので、Phase 0の最初に確認する。
5. **Claude Codeの役割を明確にする**
   MVPでは、Pythonが決定的な解析・比較・候補ルールを担い、Claude Codeは出力されたJSON/Markdownを読んで解釈・説明・次の一手を提示する。**Anthropic APIをコードに組み込む必要はない。** API組み込みやMCP化は、CLIが安定した後（Phase 3以降）に検討する。

---

## 2. 技術的な判断の根拠

### 2.1 解析（Phase 1）— 既存技術で足りる
- 基音: `librosa.pyin`（単音・明確なピッチという前提に合う）
- 包絡: RMS（短いhop）＋ onset検出 → attack / decay / sustain / release 区間の推定
- 音色: スペクトル重心・ロールオフ・平坦度（ノイズ感）を時系列で計算、倍音ごとの振幅（f0の整数倍付近のピーク）と非調和性
- 品質チェック: クリップ率、SNR推定、無音、多重音（pyinの有声確率が低い）→ 警告
- 合成テスト音（numpyでSaw/Square/Pluck/FM/ノイズ入り）を自動生成すれば、**正解が分かっている入力**で回帰テストが書ける

### 2.2 比較（Phase 3）— 前処理が品質を決める
- アライメント: onset位置を揃える → ノート長を揃える → RMSかLUFSで音量正規化 → ピッチずれはセント値で報告（補正はしない。チューニング差も差分のひとつ）
- 差分: マルチ解像度STFT距離、帯域別エネルギー差（オクターブ/1/3オクターブ帯）、包絡差、重心の時系列差、倍音ごとの振幅差
- 出力: 単一スコアではなく「アタック区間の2–5kHzが+6dB」のような**区間×帯域の文章化された差分**。ここからClaude Codeが次の変更を最大3件に絞る

### 2.3 レシピ（Phase 2）— データ整備が本体
- KRONOS Parameter GuideのAL-1章からページ名・パラメータ名・値域を `data/kronos_parameters/al1.json` に整理する（人手確認つき）。「資料にないパラメータは生成しない」は、**レシピの全パラメータIDがこのJSONに存在すること**をスキーマ検証で保証する
- エンジン選定はルールベース（整数倍音性・非調和性・ノイズ比・時間変化から AL-1 / MOD-7 / HD-1 のスコアと理由を出す）
- 値の決定はキャリブレーション表からの逆引き。表がないパラメータは「方向のみ」（上げる/下げる）＋「要調整」と明記

### 2.4 Adapter分離 — テストで強制する
- `tests/architecture/test_imports.py` で `synth_ai.core` 配下が `synth_ai.adapters.*` をimportしていないことをASTで検査（またはimport-linter）
- 契約テストを `tests/adapter_contract/` に置き、FakeAdapter・Kronos2Adapter（・将来PC3A8Adapter）を同じテストでパラメータ化して実行

---

## 3. 実装計画（スプリント単位）

想定: 個人開発＋Claude Code、週10〜15時間程度。期間は目安。

### Sprint 0 — 開発基盤と境界（2〜3日）

| # | タスク | 成果物 |
| --- | --- | --- |
| 0-1 | `uv init`、Python 3.12固定、依存追加（numpy, scipy, soundfile, librosa, matplotlib, pydantic, typer, pyyaml, mido, python-rtmidi, sounddevice / dev: pytest, ruff, mypy） | `pyproject.toml`, `uv.lock` |
| 0-2 | ディレクトリ雛形（ロードマップ§9）、`git init`、`.gitignore`（`runs/`, `assets/reference/` の大きな音声） | リポジトリ |
| 0-3 | `CLAUDE.md`：依存ルール・禁止事項（OS更新・SysEx書き込み・Global変更・既存Program上書き）・コマンド一覧 | `CLAUDE.md` |
| 0-4 | 共通型（pydantic）: `AudioAnalysis`, `SoundSpec`, `PatchRecipe`, `Capabilities`（`supported/unsupported/unverified`）すべて `schema_version` 付き | `core/sound_spec/models.py`, `adapters/base.py` |
| 0-5 | `SynthAdapter` Protocol、`FakeSynthAdapter`、契約テスト、import境界テスト | `tests/adapter_contract/`, `tests/architecture/` |
| 0-6 | `Kronos2Adapter` の雛形（capabilities: `parameter_write: unverified`） | `adapters/kronos2/adapter.py` |

**完了条件**: `uv run pytest` が通り、coreからadapterへのimportがあるとテストが落ちる。

### Sprint 1 — 実機疎通（Sprint 0〜2と並行可、1〜2日）

| # | タスク | 成果物 |
| --- | --- | --- |
| 1-1 | KRONOSのバックアップ（PCG/Set List/Global、ユーザーサンプル）。テスト用Bank/Program番号を決めて `docs/safety.md` に記録 | `docs/safety.md` |
| 1-2 | `midi_probe.py`: ポート一覧、指定ポートへC4 Note On/Off（ベロシティ・長さ指定）。**Note Offの確実な送信とAll Notes Offを例外時にも実行** | `scripts/midi_probe.py` |
| 1-3 | `record_test.py`: 入力デバイス一覧、48kHz/24bitで「録音開始 → Note On → 指定長 → Note Off → リリース待ち → 停止」。ピーク監視とクリップ警告 | `scripts/record_test.py`, `assets/test/kronos_c4.wav` |
| 1-4 | デバイス名・ポート名を `config/local.yaml`（git管理外）に固定、`config/local.example.yaml` を管理 | config |

**完了条件**: コマンド1つで同一条件のC4単音が録音できる。不可の場合は手動演奏＋外部録音の手順を `docs/` に書いて先へ進む。

### Sprint 2 — 解析MVP（1〜1.5週）

| # | タスク | 成果物 |
| --- | --- | --- |
| 2-1 | テスト音生成器（Saw+LPF sweep、Pluck=Karplus-Strong、FMベル、ノイズ付き、リバーブ付き、和音＝異常系） | `tests/fixtures/synth_signals.py` |
| 2-2 | 読み込み・検証（モノ化、48kHz統一、クリップ、無音トリム、長さ）→ 警告リスト | `core/audio/load.py` |
| 2-3 | 特徴量の純粋関数群: f0(pyin)、RMS包絡、onset、ADSR区間、重心/ロールオフ/平坦度の時系列、倍音振幅・非調和性 | `core/audio/features.py` |
| 2-4 | `AudioAnalysis` 組み立て（観測値／信頼度／警告を区別） | `core/audio/analyze.py` |
| 2-5 | プロット: 波形+包絡、スペクトログラム、倍音の時間変化、重心推移 | `core/audio/plots.py` |
| 2-6 | CLI `synth-ai analyze ref.wav --out runs/<id>/` | `cli.py` |
| 2-7 | テスト: 既知の入力で値が期待通りになる（Sawは重心が高い、LPF sweepで重心が下がる、Pluckは減衰が速い、FMは非調和性が高い）、同じ入力なら同じ結果 | `tests/core/audio/` |

**完了条件**: 合成音5種＋手持ちの単音3種で、耳の印象と矛盾しない `analysis.json` と図が出る。

### Sprint 3 — SoundSpecとAL-1レシピ（1.5〜2週）

| # | タスク | 成果物 |
| --- | --- | --- |
| 3-1 | `AudioAnalysis → SoundSpec` 変換（ラベル＋定量目標＋許容幅、仮説候補） | `core/sound_spec/derive.py` |
| 3-2 | KRONOS Parameter GuideのAL-1章からパラメータ表を整理（ページ/タブ/名前/値域/単位/資料のページ番号）。**資料の該当ページ番号を必ず残す** | `data/kronos_parameters/al1.json`, `docs/kronos_references.md` |
| 3-3 | **キャリブレーション**: テストProgramでOsc波形・Filter Cutoff・Resonance・Filter EG Amount・Amp/Filter EGのAttack/Decayを数段階ずつ変えて録音し、解析値との対応表を作成（パラメータ変更は手動、発音・録音・解析は自動） | `scripts/calibrate.py`, `data/kronos_calibration/al1_*.json` |
| 3-4 | エンジン選定ルール（AL-1/MOD-7/HD-1のスコアと理由） | `adapters/kronos2/engine_select.py` |
| 3-5 | `create_recipe`: SoundSpec → AL-1 PatchRecipe（手順順序: 初期化 → Osc → Filter → Filter EG → Amp EG → 微調整）。値はキャリブレーション表から逆引き、表がなければ方向のみ | `adapters/kronos2/recipe.py` |
| 3-6 | `manual_instructions`: 本体の画面名に沿ったMarkdown | `recipe.md` 出力 |
| 3-7 | 検証: レシピ内の全パラメータIDが `al1.json` に存在、値が値域内、SoundSpecが変更されない | `tests/adapters/kronos2/` |
| 3-8 | CLI `synth-ai recipe runs/<id>/ --synth kronos2` | `cli.py` |

**完了条件**: `recipe.md` だけを見てAL-1で1音作れる。曖昧な指定（「適当に」「好みで」）が出ない。

### Sprint 4 — 比較と改善ループ（1〜1.5週）

| # | タスク | 成果物 |
| --- | --- | --- |
| 4-1 | アライメント（onset・長さ・音量）、ピッチずれ（セント）の報告 | `core/audio/align.py` |
| 4-2 | 差分計算: マルチ解像度STFT、帯域×区間エネルギー差、包絡差、重心差、倍音差 | `core/audio/compare.py` |
| 4-3 | 差分の文章化（区間×帯域×大きさ、優先度順） | `comparison.json`, `comparison.md`, `difference.png` |
| 4-4 | 次の一手: 差分 → 関係するパラメータの候補（Adapterが「どの特徴をどのパラメータが動かすか」を提供、Coreは機種名を知らない） | `SynthAdapter.suggest_adjustments()`（任意メソッドとしてCapabilitiesで宣言） |
| 4-5 | 試行履歴: `runs/<ref_id>/trials/<n>/` に recipe・録音・比較・主観メモ（近さ/好みを別項目で） | `core/history/` |
| 4-6 | CLI `synth-ai compare`, `synth-ai trial new/note/list`、Sprint 1の録音スクリプトを `synth-ai capture` として統合 | `cli.py` |

**完了条件 = MVP達成**: リード・ベース・プラックの3音で「レシピ → 録音 → 比較 → 修正 → 再比較」を各2周以上行い、成功例と難しかった例を `docs/mvp_report.md` にまとめる。

### Sprint 5以降（MVP後）

- **Phase 4（2〜3週）**: 定常区間から1周期波形/ループ素材の再合成、ループ点・クロスフェード・DC除去。HD-1への取り込みは手動手順書。Capabilityで `user_sample_import: supported` の機種にだけ提案。
- **Phase 5（3〜4週）**: PC3A8資料整理 → `pc3a8/` Adapter → 同じ契約テストに追加 → キャリブレーションを同じ仕組みで実施 → 1音で一周。Coreに差分が出ないことを確認。
- **Phase 6（調査次第）**: まずKORG MIDI Implementationを読み、**読み取り（ダンプ要求）だけ**でテストProgramの状態を取得できるか確認。書き込みは1パラメータ・テストProgram限定・事前ダンプ保存・明示確認つきで検証。成功した場合はSprint 3-3のキャリブレーションを全自動化でき、効果が大きい。

---

## 4. 全体スケジュール目安

```
週  1      2      3      4      5      6      7      8
    [S0][S1]
         [--- S2 解析 ---]
                     [------ S3 レシピ＋キャリブ ------]
                                            [--- S4 比較 ---]
                                                         ▲MVP
```

MVPまで **6〜8週間**（週10〜15時間の場合）。一番ぶれやすいのはSprint 3のパラメータ表とキャリブレーション作業。

---

## 5. リスクと対策

| リスク | 影響 | 対策 |
| --- | --- | --- |
| 音響特徴とパラメータ値の対応が不明 | レシピの値が外れる | 実機キャリブレーション表。表がなければ「方向のみ」と明示 |
| 参照WAVの質（リバーブ、ミックス、ノイズ） | 解析を誤る | 品質チェックで警告、信頼度を下げる、ドライな参照音を推奨 |
| 公式資料の転記ミス・架空パラメータ | 信頼性低下 | パラメータIDのスキーマ検証、資料ページ番号の保持、人手レビュー |
| USB Audio/MIDIがmacOS 26で動かない | 自動録音不可 | オーディオIF経由・手動演奏に切り替え（ロードマップ通り） |
| 実機の誤操作（上書き） | 音色の損失 | Sprint 1で先にバックアップ、テストBank限定、SysEx書き込みはコード上で拒否 |
| Coreへの機種依存の混入 | PC3A8で作り直し | import境界テスト＋契約テストをCIで常時実行 |
| 範囲の膨張（エンジン追加・自動化を急ぐ） | MVP未達 | ロードマップ§3.7の基準で判断。MOD-7/HD-1はMVPではスコアと理由の提示まで |

---

## 6. 着手前にユーザーが行うこと

1. KRONOSのバックアップ（作業はSprint 1-1、実施は本人）
2. KRONOS Parameter Guide / MIDI ImplementationのPDFを入手し、`docs/references/`（git管理外）に置く
3. 検証用の参照WAVを3つ用意（リード・ベース・プラック。ドライ・単音・C4付近が望ましい）
4. KRONOSとMacをUSB接続し、Audio MIDI設定にKRONOSが見えるか確認

これらと並行して、Sprint 0（環境構築・型・Adapter契約・テスト）はすぐに着手できる。
