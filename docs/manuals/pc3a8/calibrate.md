# PC3A8: キャリブレーション曲線を測る

## 目的

基準音 1025 の 1 つのパラメータだけを数段階に変えて録音し、「設定値 → 実際の音（時間・音量・明るさ）」の曲線を作ります。
レシピは、この曲線から目標の音に合う値を逆引きします。曲線は `data/pc3a8_calibration/` に保存されます。

## 前提

- `docs/pc3a8_setup.md` の接続で、`devices -s pc3a8` に MIDI 出力ポートと録音デバイスの `*` が付く
- Effect モードの Master Cmpr. が **Out**（`docs/pc3a8_setup.md` の「マスターエフェクト」）
- モニターの音量と UR22mkII の入力ゲインを、基準音の録音（ピーク −10 dBFS 前後）と同じにしている
- **編集した値は保存しない**。測り終えたら必ず「保存しますか」で **No** を選ぶ

## 手順

1. Program モードで **1025 KVA BASIC SAW** を選ぶ
2. **Edit** を押して Program Editor に入り、測るパラメータのページを開く（下の表）。ボタンが見当たらなければ **more** で切り替える（本文 6-12）
3. PC で測定のコマンドを実行する（下の表）。コマンドは値ごとに「〜を 0.02 s にして Enter」と案内する
4. 案内された値に本体のパラメータを合わせ、Enter を押す。ツールが C4 を鳴らして録音・解析し、測った値を表示する
   - Enter: 採用 / r: 録り直し / s: この値は使わない
5. すべての値を測ると曲線が保存される
6. **Exit** を押し、「保存しますか」で **No** を選ぶ（本文 5-3）。次のパラメータは 1 からやり直す（前の変更を残さない）

| 測るもの | ページ（本文） | 変える項目 | コマンド |
| --- | --- | --- | --- |
| アタック | AMPENV（6-43） | Att1 の Time | `uv run synth-ai calibrate kva.ampenv.att1.time -s pc3a8 --conditions "1025 KVA BASIC SAW"` |
| ディケイ | AMPENV（6-43） | Dec1 の Time | `uv run synth-ai calibrate kva.ampenv.decay.time -s pc3a8 --conditions "1025 KVA BASIC SAW"` |
| サステイン | AMPENV（6-43） | Dec1 の Level | `uv run synth-ai calibrate kva.ampenv.decay.level -s pc3a8 --conditions "1025 KVA BASIC SAW"` |
| リリース | AMPENV（6-43〜6-44） | Rel1 の Time | `uv run synth-ai calibrate kva.ampenv.rel1.time -s pc3a8 --conditions "1025 KVA BASIC SAW"` |
| 明るさ | DSPCTL（6-29, 6-55〜6-56） | 左の列で LP Frq を選ぶ（▶ は押さない） | `uv run synth-ai calibrate kva.dspctl.lp_frq -s pc3a8 --conditions "1025 KVA BASIC SAW"` |

測る値は `data/pc3a8_parameters/kva.json` の `calibration_values` です（本体で選べる値）。

- 時間: Att1 は 0〜0.8 秒、Dec1・Rel1 は 0.02〜1.6 秒
- Dec1 の Level: 10〜100%
- LP Frq は 1 クリックで半音ずつ変わる。画面の音名で合わせる

| 値（Hz） | 131 | 262 | 523 | 1047 | 2093 | 4186 | 8372 | 16744 | 25088 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 音名 | C 3 | C 4 | C 5 | C 6 | C 7 | C 8 | C 9 | C 10 | G 10（最大） |

## 確認

- 曲線の最後に「注意: 値を上げても特徴が一方向に変わっていません」が出ていない（出たらその曲線は逆引きに使われない）
- `data/pc3a8_calibration/` に `<パラメータ ID>__<特徴>.json` ができている
- Exit の後、1025 を選び直すといつもの音（基準音）が鳴る

## 元に戻す

- 測定中に変えた値は、Exit で **No** を選べばすべて捨てられる。Program を選び直しても捨てられる（本文 6-3）
- 途中でやめたいときは、ツールの案内に `q` を入力する。測れた点が 2 つ以上あれば、その分で曲線を作る

## 注意

- **Yes（保存）を押さない**。押してしまったら、`docs/safety.md` の「基準音 1025 の設定」の値に戻して保存し直す
- 1 回の測定で変えるのは 1 項目だけ。ほかの項目は基準音のまま
- 画面の表示が表の値と違う（例: Hz の数字が 1 違う）ときは、その表示をメモして知らせる。曲線の値を直す
- 録音のたびに「クリップ」「S/N が低い」などの注意が出たら、ゲインを見直して `r` で録り直す

## 出典

- Musician's Guide 本文 5-3（保存の確認）、6-3（Program の切り替え）、6-12（ソフトボタン）、
  6-29（DSPCTL）、6-43〜6-44（AMPENV）、6-55〜6-56（LOPASS の LP Frq）
- 値の刻み: `docs/pc3a8_parameter_table.md`（実機で確認、2026-11-14）
