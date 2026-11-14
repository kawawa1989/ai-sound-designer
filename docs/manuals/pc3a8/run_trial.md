# PC3A8: レシピどおりに設定して録音・比較する

## 目的

参照音のレシピを本体に設定し、PC から鳴らして録音して、参照音と比べます。比較の提案に沿って直し、録り直して近づけます。
結果は試行として `runs/<参照音>/trials/pc3a8/<番号>/` に保存されます。

## 前提

- `docs/pc3a8_setup.md` の接続で、`devices -s pc3a8` に MIDI 出力ポートと録音デバイスの `*` が付く
- 参照音を `analyze` してある（`runs/<参照音>/analysis.json`）
- Effect モードの Master Cmpr. が **Out**
- 曲線（`data/pc3a8_calibration/`）がある。ない項目は、レシピに値でなく目標だけが出る

## 手順

1. レシピを作る

   ```bash
   uv run synth-ai recipe runs/<参照音> -s pc3a8
   ```

   手順書は `runs/<参照音>/recipes/pc3a8/recipe.md`。
2. Program モードで **1025 KVA BASIC SAW** を選び、**Edit** で Program Editor に入る
3. `recipe.md` の「手順」を上から順に設定する。ページは ALG → DSPCTL → DSPMOD → ENV2 → AMPENV の順（本文 6-12）
   - DSPCTL・DSPMOD は左の列で機能（LP Frq など）を選び、▶ で右のサブページ（Src1・Depth など）に移る（本文 6-29〜6-31）
   - LP Frq は画面の音名で合わせる（例: 87 Hz は F 2）
   - 「本体で選べるいちばん近い値」とある値は、ホイールで最も近い値にする
4. **設定した値を読み返す**（下の「確認」の表）。基準音のままの項目があると、比較の結果が原因と違う方向を指す
5. 録音して比べる（Program は切り替えない）

   ```bash
   uv run synth-ai capture -s pc3a8 --run runs/<参照音>
   ```

   参照音と同じ音程で鳴らし、比較レポートを表示する
6. レポートの「次の調整案」と「主な違い」を見て、本体の値を 1〜2 項目直し、5 に戻る
7. 聴いた評価を記録する（近さと好みは別々に）

   ```bash
   uv run synth-ai trial note runs/<参照音> <試行番号> -s pc3a8 --closeness 4 --preference 3 --memo "…" --change "ENV2 Dec1 Level 100→0%"
   ```

8. 一覧で確かめる

   ```bash
   uv run synth-ai trial list runs/<参照音> -s pc3a8
   ```

9. 終わったら、残す音はテスト用の空き ID（1026 以降）に保存し、`docs/safety.md` の表に追記する。残さないなら Exit で **No**（本文 5-2〜5-4）

## 確認

設定後に、次の項目が `recipe.md` の値になっているか読み返す。

| ページ | 項目 | 基準音 1025 のままだと起きること |
| --- | --- | --- |
| DSPCTL | LP Frq | 25088 Hz のままだと、ずっと明るい |
| DSPMOD | LP Frq › Src1 / Depth | OFF のままだと、明るさが時間で変わらない |
| ENV2 | Att1・Dec1 の Time と Level | **Dec1 Level が 100% のままだと ENV2 が下がらず、カットオフが開いたまま**（2026-11-14 に実際に起きた） |
| AMPENV | Dec1 Time・Level、Rel1 Time | Rel1 が 0.06 s のままだと、リリースが 20 ms 前後になる |

明るさが時間で変わらない（レポートで「明るさの変化」が 1.0 前後）ときは、DSPMOD の Depth を一時的に 0 にして弾いてみる。
音がこもれば、ENV2 が下がっていない（ENV2 の Level を見直す）。確かめたら Depth を戻す。

## 元に戻す

- 編集は Exit で **No** を選べばすべて捨てられる。Program を選び直しても捨てられる（本文 6-3）
- 試行の記録（`runs/<参照音>/trials/pc3a8/`）は、ツールが新しい番号で足していく。消す必要はない

## 注意

- 録音の途中で Program を切り替えない（編集が消える）
- 比較の提案は、パラメータと音の一般的な傾向か、曲線から出している。フィルターが音量も下げるような、効き方が重なる場面では外れることがある（`docs/pc3a8_trial_report.md`）
- 1 回に直す項目は少なくする（何が効いたか分かるように）

## 出典

- Musician's Guide 本文 5-2〜5-4（保存）、6-3（Program の切り替え）、6-12（ソフトボタン）、6-29〜6-31（DSPCTL / DSPMOD）、
  6-43〜6-45（AMPENV / ENV2）
- 実機で確かめた日: 2026-11-14（`docs/pc3a8_trial_report.md` の試行 001〜004）
