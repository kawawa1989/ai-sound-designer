# PC3A8 対応（Phase 5）の Issue 案

2026-11-13 に起票済み: 親 Issue #15、Sub-Issue #16〜#23（P1 = #16 … P8 = #23）。以後の更新は GitHub 側で行う。
親 Issue 1 件と Sub-Issue 8 件。
Sub-Issue がすべて Close したら、ロードマップ §3.5「マルチシンセ対応の受け入れ条件」を満たす構成にしている。
資料の整理は `docs/pc3a8_program_mode.md`。

順番: P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8（P1〜P3 は実機の準備、P4〜P6 はコード、P7〜P8 は実測と検証）

---

## 親 Issue: FEAT: PC3A8 / V.A.S.T. Adapter（Phase 5）

## 1. 概要

- [ ] 目的: KRONOS で作った SoundSpec・解析・比較・試行履歴をそのまま使い、PC3A8 用のレシピ（手動設定の手順）を作れるようにする
- [ ] 背景: PC3A8 はユーザーサンプルを読み込めず（Musician's Guide 本文 E-1）、パラメータを書き換える SysEx の形式も公開されていない（本文 A-1 には SysEx の送受信可とだけある）。このため当面は手動レシピで進め、自動化（Phase 6 相当）は対象外とする
- [ ] ロードマップ: Phase 5（作業 1〜6、成果物 `adapters/pc3a8/`・`data/pc3a8_parameters/`・`docs/pc3a8_setup.md`・比較レポート）、§3.5 の受け入れ条件 6 項目、§5.4（PC3A8Adapter の Capability）、§5.5（拡張性のテスト）

## 2. 具体的な作業内容

- [ ] Sub-Issue P1〜P8 を順に完了する

## 3. 受け入れ条件

- [ ] KRONOS で作成済みの `SoundSpec` を改変せずに PC3A8 のレシピ生成に入力できる（P5）
- [ ] PC3A8 の V.A.S.T. / KVA の制約に沿ったレシピと手動設定手順が作れる（P4, P5）
- [ ] 波形サンプルの取り込みを PC3A8 に誤提案せず、代替策または対応不可を説明できる（P6）
- [ ] PC3A8 の録音を、KRONOS と同じ共通比較エンジンで分析できる（P2, P8）
- [ ] PC3A8 を追加しても Core に機種別の分岐が増えず、KRONOS Adapter の動作も壊れない（P5）
- [ ] 機種ごとのレシピと録音を別々に保存し、共通の参照音と SoundSpec に紐づけられる（P8）

## 4. テスト項目

- [ ] CI: 全テスト（import 境界・Adapter 契約を含む）が通る
- [ ] 手動: P8 の 1 周の検証が記録されている

---

## P1. TASK: PC3A8 の安全方針とテスト用領域を決める

## 1. 概要

- [ ] 目的: PC3A8 で作業を始める前に、保存先・バックアップ・やってはいけない操作を決める
- [ ] 背景: PC3A8 では、メモリ上の Program と同じ ID に保存すると元の Program が完全に消える（本文 5-4）。Master モードの Reset はユーザーのオブジェクトをすべて消す（本文 11-1）。Program 999（NewLyr のひな形）と Setup 126（既定の Control Setup）は変更してはいけない（本文 6-52, 6-56）
- [ ] ロードマップ: Phase 0 の安全運用（KRONOS で作った `docs/safety.md` の PC3A8 版）、§3.6 非目標

## 2. 具体的な作業内容

- [ ] `docs/safety.md` に PC3A8 の節を追加する（守ること・テスト用の領域・バックアップ・やってはいけない操作）
- [ ] ユーザー: Storage モードで本体のデータを USB メモリに保存し、PC にもコピーする（本文 13 章）
- [ ] ユーザー: テスト用の Program ID を決める（User Bank、1025 以降の空き ID。本文 5-2）
- [ ] 禁止する操作を明記する: Master モードの Reset、Program 999・Setup 126 の変更、テスト用以外の ID への保存、OS の更新
- [ ] このツールが PC3A8 に送る MIDI を明記する（Note On/Off・All Notes Off だけ。Program Change と SysEx は送らない）
- [ ] CLAUDE.md の「禁止事項」と「公式資料」に PC3A8 を追記する（文案をユーザーに確認してから）

## 3. 受け入れ条件

- [ ] `docs/safety.md` に PC3A8 の節があり、テスト用の ID と決めた日が記入されている
- [ ] ユーザーがバックアップを取り、チェックリストに記録している
- [ ] CLAUDE.md に PC3A8 の資料の場所と禁止事項がある

## 4. テスト項目

- [ ] 手動: 文書の内容をユーザーが確認する
- [ ] CI: 既存テストが通る（Markdown の変更のみ）

---

## P2. TASK: PC3A8 の MIDI・録音経路を確認し、機種ごとの接続設定を持てるようにする

## 1. 概要

- [ ] 目的: PC3A8 にノートを送り、出力を録音して解析できるようにする
- [ ] 背景: PC3A8 には USB オーディオがなく、Main 出力（1/4 TRS バランス）をオーディオインターフェースで録る（本文 2-2, A-2）。MIDI は USB MIDI か 5 ピン MIDI（本文 10-2）。今の `config/local.yaml` は接続先を 1 つしか持てない
- [ ] ロードマップ: Phase 5 作業 4（「録音機器・IF 接続は機種設定で変更し、比較エンジンは再実装しない」）、§5.1 設計原則 5

## 2. 具体的な作業内容

- [ ] `config/local.yaml` に機種ごとの接続設定（MIDI ポート・チャンネル・録音デバイス・入力チャンネル）を持てるようにする。今の設定（KRONOS）はそのまま読めるようにする
- [ ] `capture` / `midi-probe` / `calibrate` に機種を選ぶオプション（例: `--synth pc3a8`）を追加する
- [ ] ユーザー: PC3A8 の Main L/R を UR22mkII の入力につなぐ（KRONOS とのつなぎ替え手順を決める）
- [ ] ユーザー: MIDI の接続方法（USB / 5 ピン）と、PC3A8 の受信チャンネルを確認する
- [ ] ユーザー: `midi-probe` で音が鳴ること、`capture` → `analyze` で解析できることを確認する
- [ ] `docs/pc3a8_setup.md` に接続構成と確認手順を書く

## 3. 受け入れ条件

- [ ] 設定を書き換えずに、オプションで KRONOS と PC3A8 を切り替えられる
- [ ] PC3A8 の 1 音を録音し、KRONOS と同じ `analyze` で解析できる
- [ ] 既存の KRONOS 用の設定ファイルがそのまま動く

## 4. テスト項目

- [ ] ユニット: 機種ごとの設定の読み込み・既定値・旧形式の互換・存在しない機種のエラー
- [ ] ユニット: CLI の `--synth` で正しい設定が選ばれる（偽の MIDI ポート・録音デバイスで確認）
- [ ] 手動（ユーザー）: PC3A8 で midi-probe・capture・analyze
- [ ] CI: 全テストが通る

---

## P3. TASK: PC3A8 の基準音 Program（KVA）を作る

## 1. 概要

- [ ] 目的: キャリブレーションとレシピの出発点にする、単純な KVA の Program を作る（KRONOS の U-CC000「AL-1 BASIC SOUND」に当たる）
- [ ] 背景: KVA の最小構成は、Keymap 999 Silence・AMPENV User・ALG に発振器（本文 6-53）。999 Silence なら鍵ごとの音量差がない（本文 6-58）
- [ ] ロードマップ: Phase 5 作業 1（Program 編集手順の整理）、作業 5 の準備

## 2. 具体的な作業内容

- [ ] 基準音の設定案を作る: 例として発振器 SAW、その後ろに LOPASS、エフェクトなし、モノフォニックはオフ。値は P4 の実機確認のあとに決める
- [ ] ユーザー: テスト用 ID に基準音を作って保存する（P1 で決めた ID。保存先の ID を声に出して確認する）
- [ ] ユーザー: 各ページの値を読み上げ、`docs/safety.md` のテスト用領域の表に記録する
- [ ] `capture` → `analyze` で基準音を録り、ピッチ・エンベロープ・明るさが想定どおりか確かめる

## 3. 受け入れ条件

- [ ] 基準音の全設定が `docs/safety.md` に記録されている
- [ ] 基準音の録音を解析し、ピッチ（C4）・サステイン・リリースが検出できる

## 4. テスト項目

- [ ] 手動（ユーザー）: 基準音の作成と保存、ID の確認
- [ ] 手動: 録音の解析結果に問題（クリップ・途切れ・SNR）がない

---

## P4. TASK: PC3A8 のパラメータ表（KVA・フィルター・AMPENV）を作る

## 1. 概要

- [ ] 目的: レシピで使うパラメータを、公式資料の出典つきでデータにする（`data/pc3a8_parameters/`）
- [ ] 背景: AMPENV（本文 6-43）・PITCH / AMP（本文 6-29）・KVA 発振器（本文 6-54〜6-58）はマニュアルに範囲がある。DSP 機能（LOPASS など）の一覧と LP Frq の単位・範囲は載っていないので、実機の画面で確認する必要がある
- [ ] ロードマップ: Phase 5 作業 1、成果物 `data/pc3a8_parameters/`。CLAUDE.md「公式資料で確認していない値を生成しない」

## 2. 具体的な作業内容

- [ ] KRONOS の表（`data/kronos_parameters/al1.json`）と同じ形式で、PC3A8 の表を作る。ページ・項目名・範囲・単位・役割（roles）・出典（本文ページ）を入れる
- [ ] 対象: 発振器の種類（ブロック数つき）、発振器の音程（〜Pch）、フィルターブロックとその機能パラメータ、AMPENV（Attack 1〜3 / Decay / Release 1〜3 の Time と Level）、ENV2 とその割り当て（DSPMOD の Src1 / Depth）、AMP の Level と VelTrk
- [ ] 秒・% など物理単位の値を扱えるようにする（KRONOS の 0〜99 の整数との違い）
- [ ] ユーザー: マニュアルにない項目（フィルター機能の一覧、LP Frq / LP Res の単位と範囲、発振器ブロックを置けるアルゴリズムの番号）を実機の画面で読み、報告する
- [ ] 実機で確認できなかった項目は `verified: false`（要確認）にし、レシピでは使わない
- [ ] `docs/` に PC3A8 のパラメータ表の説明を追加する

## 3. 受け入れ条件

- [ ] すべての項目に出典（本文ページ、または「実機の画面で確認」と確認日）がある
- [ ] 確認していない値は表に入っていない（または `verified: false`）

## 4. テスト項目

- [ ] ユニット: 表の読み込み・スキーマ検証（範囲・単位・役割・重複 ID）
- [ ] ユニット: KRONOS の表の読み込みが変わらない
- [ ] CI: 全テストが通る

---

## P5. TASK: PC3A8Adapter を実装する（レシピと手動設定の手順）

## 1. 概要

- [ ] 目的: 既存の SoundSpec から PC3A8 用の PatchRecipe と、本体での設定手順を作る
- [ ] 背景: 役割（roles）でパラメータを引く仕組みは、今は `adapters/kronos2/` の中にある。Adapter どうしは import できないので、共有する部分の置き場所を決める必要がある
- [ ] ロードマップ: Phase 5 作業 2・6、§5.4、§5.5、CLAUDE.md 依存ルール

## 2. 具体的な作業内容

- [ ] 役割の仕組みのうち機種によらない部分を Core（または `adapters/base`）に移すか、PC3A8 側に別に持つかを決める（移す場合は KRONOS の動作が変わらないことをテストで確かめる）
- [ ] `adapters/pc3a8/` に Adapter を作る: Capabilities（`user_sample_import: unsupported`、`midi_notes: supported`、`parameter_read` / `parameter_write: unverified`）、`create_recipe`、`manual_instructions`
- [ ] SoundSpec → KVA のレシピ: 波形 → 発振器、明るさ → フィルター、エンベロープ → AMPENV（秒・%）、フィルターの時間変化 → ENV2 + DSPMOD
- [ ] 手順書: Program 編集の順番（KEYMAP 999 Silence → ALG → DSPCTL / DSPMOD → AMPENV）と、各項目のページ名
- [ ] `registry.py` に登録し、`tests/adapter_contract/test_contract.py` の `ADAPTERS` に追加する
- [ ] ParameterCatalog / AdjustmentAdvisor を実装するかを決める（キャリブレーションと比較からの調整提案に必要）

## 3. 受け入れ条件

- [ ] KRONOS 用に作った SoundSpec を、変更せずに PC3A8 のレシピ生成に渡せる
- [ ] Core に機種名・機種別の分岐が増えていない
- [ ] KRONOS Adapter のテストがすべて通る（PC3A8 の資料なしで実行できる）

## 4. テスト項目

- [ ] 契約テスト: PC3A8Adapter が全契約を満たし、SoundSpec を変更しない
- [ ] ユニット: 代表的な SoundSpec（リード・ベース・プラック）から、範囲内の値のレシピができる
- [ ] ユニット: 手順書に要確認の項目が出ない
- [ ] import 境界テスト: `adapters/pc3a8` が `adapters/kronos2` を import しない
- [ ] CI: 全テストが通る

---

## P6. TASK: サンプル取り込み非対応の代替提案を実装する

## 1. 概要

- [ ] 目的: 参照音にサンプルの取り込みが向いている場合でも、PC3A8 には取り込みを提案せず、KVA や ROM の Keymap による代替、または「対応できない」を説明する
- [ ] 背景: "The PC3A does not load samples"（本文 E-1）。KRONOS では Phase 4 で波形の取り込みを予定している
- [ ] ロードマップ: §3.5 受け入れ条件 3、§5.4、§5.5「サンプル取り込み非対応機種に WAV インポート手順を提案しない」

## 2. 具体的な作業内容

- [ ] Capability が `unsupported` のときの代替案の出し方を決める（Core は Capability だけを見る）
- [ ] PC3A8 の代替案: 近い波形の KVA 発振器、複数 Layer の重ね合わせ、ROM の Keymap（名前は実機で確認したものだけ）
- [ ] 代替が難しい音（複雑な倍音構成など）は、レシピに「再現の限界」として書く

## 3. 受け入れ条件

- [ ] PC3A8 のレシピ・手順書に、サンプルの取り込み・WAV のインポートが出てこない
- [ ] 代替案か「対応できない」の説明が必ず付く

## 4. テスト項目

- [ ] ユニット: 取り込みが向く SoundSpec を渡しても、PC3A8 では取り込みを提案しない
- [ ] 契約テスト: `user_sample_import: unsupported` の Adapter 全般で同じことを確かめる（FakeAdapter を含む）
- [ ] CI: 全テストが通る

---

## P7. TASK: PC3A8 のキャリブレーション曲線を測る

## 1. 概要

- [ ] 目的: 設定値と実際の音（時間・明るさ・音量）の対応を測り、レシピの値を逆引きできるようにする
- [ ] 背景: PC3A8 の設定は秒・dB などの物理単位だが、AMPENV のアタックは指数カーブ（本文 6-44）で、KRONOS でも表の時間と測った時間はずれた。測って確かめる
- [ ] ロードマップ: Phase 5（実装計画「キャリブレーションを同じ仕組みで実施」）、`data/kronos_calibration/` と同じ仕組み

## 2. 具体的な作業内容

- [ ] `calibrate` を PC3A8 で使えるようにする（`CALIBRATION_DIRS` に追加、P2 の `--synth`）
- [ ] 測る曲線: AMPENV Attack 1 Time → attack_time、Decay Time → decay_time、Decay Level → sustain_level、Release 1 Time → release_time、フィルターの LP Frq → brightness
- [ ] ユーザー: 基準音（P3）を呼び出し、1 つのパラメータだけを変えて録音する（測り終えたら保存せずに戻す）
- [ ] 曲線を `data/pc3a8_calibration/` に保存する

## 3. 受け入れ条件

- [ ] 上の 5 本の曲線があり、条件・測定日・参照音が記録されている
- [ ] 曲線から逆引きした値で、基準音のレシピが再現できる

## 4. テスト項目

- [ ] ユニット: 物理単位（秒・%）のパラメータ値で曲線の作成・逆引きができる
- [ ] ユニット: KRONOS の曲線の読み込みが変わらない
- [ ] 手動（ユーザー）: 実機での測定
- [ ] CI: 全テストが通る

---

## P8. TASK: 同じ SoundSpec で PC3A8 の 1 周を検証し、ドキュメントにまとめる

## 1. 概要

- [ ] 目的: KRONOS で作った SoundSpec から、PC3A8 でレシピ → 手動設定 → 録音 → 比較 → 改善を 1 周させる
- [ ] 背景: Phase 5 の完了条件は「既存の SoundSpec から PC3A8 固有の適切なレシピを生成でき、実機で 1 音を制作・録音して共通比較処理を再利用できる」
- [ ] ロードマップ: Phase 5 作業 5、§3.5 受け入れ条件 4・6、成果物「比較レポート」

## 2. 具体的な作業内容

- [ ] 試行の保存を機種ごとに分け、同じ参照音・SoundSpec に紐づける（`trial` の保存先・メタデータ）
- [ ] ユーザー: KRONOS で使った参照音の SoundSpec から PC3A8 のレシピを作り、手順書どおりに設定して録音する
- [ ] `compare` で比較し、提案に沿って 1 回以上改善する
- [ ] 比較レポートを保存し、KRONOS の結果と並べて考察する
- [ ] `docs/pc3a8_setup.md`、README、ロードマップの Phase 5 を更新する

## 3. 受け入れ条件

- [ ] 1 つの参照音について、KRONOS と PC3A8 の試行が別々に保存され、同じ SoundSpec に紐づいている
- [ ] PC3A8 の比較レポートがある（比較の処理は KRONOS と共通）
- [ ] ドキュメントだけで、PC3A8 の接続から 1 周までを再現できる

## 4. テスト項目

- [ ] ユニット: 機種ごとの試行の保存・一覧・紐づけ
- [ ] 手動（ユーザー）: 1 周の実施と記録
- [ ] CI: 全テストが通る
