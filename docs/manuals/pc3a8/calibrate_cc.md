# PC3A8: CC でキャリブレーション曲線を自動で測る

## 目的

値を手で変える代わりに、PC から CC（コントロールチェンジ）を送ってパラメータを動かし、曲線を自動で測ります。
いま測れるのは LP Frq（CC 14、Program 1026）、AMPENV の Rel1 Time（CC 15、Program 1027）、DSPMOD の Depth（CC 14、Program 1028）です。
Program 1028 では、ENV2 Dec1 Time も手で値を変えて測ります（ENV2 の時間は CC で動かせないため）。
手で値を合わせて Enter を押す作業（`docs/manuals/pc3a8/calibrate.md`）がなくなります。

CC は、Program のパラメータの制御元に割り当てた番号を送ると、演奏中にそのパラメータを動かします（本文 10-11）。
保存された値は変わりません。送ってよい CC と条件は `docs/safety.md` の「CC を送る条件」です。

## 前提

- `docs/pc3a8_setup.md` の接続で、`devices -s pc3a8` に MIDI 出力ポートと録音デバイスの `*` が付く
- Effect モードの Master Cmpr. が **Out**
- 測るパラメータのキャリブレーション用 Program（1026・1027・1028）を作ってある（下の手順。1 回だけ）

## キャリブレーション用 Program 1026 を作る（1 回だけ）

1. Program モードで **1025 KVA BASIC SAW** を選び、**Edit** で Program Editor に入る
2. **DSPCTL** ページで、左の列の **LP Frq** を **G 1（49 Hz）** にする（本文 6-29）
3. **DSPMOD** ページで、左の列の **LP Frq** を選び、▶ で右に移る（本文 6-30〜6-31）
   1. **Src1** を選び、数字ボタンで **14** を入力して **Enter** を押す。CC 14 が制御元になる（本文 10-11）。表示は「MIDI 14」などになる
   2. **Depth** を **10800 ct** にする
4. ほかの値は 1025 のまま変えない
5. **Save** で保存する。保存先は **1026** にし、ID を声に出して確かめる。1025 には上書きしない（本文 5-2〜5-4）
6. 名前を **KVA CC CAL** にする（名前の付け方は 1025 と同じ）

CC 14 が 0 のときカットオフは 49 Hz、最大で +10800 ct（9 オクターブ上の 25088 Hz）になる。
途中の CC は「49 Hz × 2^(10800 ct × CC/128)」で比例して動くとして扱う。マニュアルに換算は書かれていないため、
2026-11-14 の測定で CC/127 より CC/128 が合うことを確かめて決めた（`docs/pc3a8_parameter_table.md` の「CC での測定」）。

## キャリブレーション用 Program 1027 を作る（1 回だけ）

AMPENV の時間は、ENVCTL ページの Source / Depth で CC に動かせる。Depth は、制御元が最大（127）のときに
その区間の速さを何倍にするかで、0 では効かず、途中は比例する（本文 6-45〜6-46）。速さが 2 倍なら時間は半分になる。

1. Program モードで **1025 KVA BASIC SAW** を選び、**Edit** で Program Editor に入る
2. **AMPENV** ページで、**Rel1** の **Time** を **1.60 s** にする（本文 6-42〜6-43）。ほかの区間は 1025 のまま
3. **ENVCTL** ページで、**Release** の行を使う（本文 6-45〜6-46）
   1. **Source** を選び、数字ボタンで **15** を入力して **Enter** を押す。CC 15 が制御元になる（本文 10-11）
   2. **Depth** を **50.000x**（最大）にする
   3. Adjust・Key tracking は **1.000x** のまま（1 以外だと、時間がその分だけ変わる）
   4. ほかの値は 1025 のまま変えない
5. **Save** で保存する。保存先は **1027** にし、ID を声に出して確かめる。1025・1026 には上書きしない（本文 5-2〜5-4）
6. 名前を **KVA ENVCTL CAL** にする

CC 15 が 0 のとき Rel1 は 1.60 s、CC が上がると速くなる。途中の CC は「1.60 s ÷ 50^(CC/128)」として扱う。
マニュアルは途中の値を「比例する（scaled）」とだけ書いているが、2026-11-14 の測定で、倍率は CC に正比例（1 + 49 × CC/128 倍）ではなく
指数的に効くことを確かめた（`docs/pc3a8_parameter_table.md` の「ENVCTL で Rel1 を測る」）。

注意: 時間が 0 の区間には効かない（0 に何を掛けても 0、本文 6-46）。Rel1 を 0 にしない。

## キャリブレーション用 Program 1028 を作る（1 回だけ）

DSPMOD の **Src2** は、深さを **MinDepth** から **MaxDepth** の間で、**DptCtl** に選んだ制御元で動かせる（本文 6-26、6-31）。
Src2 を ENV2、DptCtl を CC 14 にすると、ENV2 が掛かったまま Depth だけを CC で動かせる。

1. Program モードで **1025 KVA BASIC SAW** を選び、**Edit** で Program Editor に入る
2. **DSPCTL** ページで、左の列の **LP Frq** を **G 1（49 Hz）** にする（本文 6-29）
3. **DSPMOD** ページで、左の列の **LP Frq** を選び、▶ で右に移る（本文 6-30〜6-31）
   1. **Src1** は **OFF** のまま
   2. **Src2** を **ENV2** にする
   3. **DptCtl** を選び、数字ボタンで **14** を入力して **Enter** を押す（CC 14 が制御元になる。本文 10-11）。CC 14 を選べなければ止めて知らせる（**要確認**）
   4. **MinDepth** を **0 ct**、**MaxDepth** を **10800 ct** にする
4. **ENV2** ページで、**Att1** を **0 s・100%**、**Dec1** を **0.40 s・100%** にする（本文 6-44〜6-45）。Dec1 Level が 100% なので ENV2 は 100% のまま下がらない
5. **AMPENV** ページで、**Decay** の **Level** を **100%** にする（音量を下げず、明るさだけを見るため。本文 6-43）
6. ほかの値は 1025 のまま変えない
7. **Save** で **1028** に保存し、名前を **KVA ENV2 CAL** にする（[save_program.md](save_program.md)）

CC 14 が 0 のとき Depth は 0 ct（カットオフは 49 Hz のまま）、CC が上がると「10800 ct × CC/128」で深くなると仮定して測る。
ENV2 が 100% のときに Depth の分だけカットオフが上がるなら、LP Frq の曲線と同じ明るさになる。

### ENV2 Dec1 Time を測る（手動）

ENV2 の時間は CC で動かせない（ENVCTL は AMPENV だけに効く。本文 6-45）ので、`calibrate.md` と同じく手で値を変えて測る。

1. Program モードで **1028 KVA ENV2 CAL** を選び、**Edit** で Program Editor に入る
2. 保存しないまま、次のように変える
   - **DSPMOD** で、左の列の **LP Frq** を選び ▶ で右に移る（Saw Pch ではない）。**Src1** を **ENV2**、**Depth** を **7200 ct**、**Src2** を **OFF**
   - **ENV2** の **Dec1 Level** を **0%**（ENV2 が下がるようにする）
3. C4 を弾き、明るく始まってこもっていく音になっているか確かめる。変わらなければ測らない
4. PC で実行する

   ```bash
   uv run synth-ai calibrate kva.env2.decay.time -s pc3a8 --hold 5 --conditions "1028 KVA ENV2 CAL（Src1 ENV2・Depth 7200 ct、Src2 OFF、ENV2 Dec1 Level 0%）"
   ```

5. ツールの指示に合わせて、**ENV2** の **Dec1 Time** を 0.10 / 0.20 / 0.40 / 0.80 / 1.60 / 3.20 s に変え、**Enter だけ**を押す（y は入れない）
6. 終わったら **Exit** で **No**（1028 は保存しない）

曲線は `data/pc3a8_calibration/` 直下に保存される。レシピは ENV2 Dec1 Time を LP Frq の曲線から計算するので、測り終えたら `reference/` に移す（計算の確認に使う。`docs/pc3a8_parameter_table.md`）。

注意: **Src2 の MinDepth と MaxDepth を同じ値にする方法では、ENV2 はカットオフを動かさなかった**（2026-11-14 に実機で確認。明るさが Dec1 Time によらず一定だった）。Src1 を使う。

## 手順

| 測るもの | Program | CC | コマンド |
| --- | --- | --- | --- |
| LP Frq | 1026 KVA CC CAL | 14 | `uv run synth-ai calibrate kva.dspctl.lp_frq -s pc3a8 --cc --conditions "1026 KVA CC CAL"` |
| AMPENV Rel1 Time | 1027 KVA ENVCTL CAL | 15 | **いまは使えない**（下の注意。CC 15 を送らなくなった） |
| DSPMOD Depth | 1028 KVA ENV2 CAL | 14 | `uv run synth-ai calibrate kva.dspmod.lp_frq.depth -s pc3a8 --cc --feature brightness_end --conditions "1028 KVA ENV2 CAL"` |

1. Program モードで、表の Program を選ぶ（Edit には入らなくてよい）
2. PC で表のコマンドを実行する
3. 「本体で 〜 を選んでいますか？」に **y** と答える。違う Program なら **n** で止める（何も送らない）
4. ツールが値ごとに CC を送り、C4 を鳴らして録音・解析する。人の操作は要らない（1 点 4〜6 秒ほど）
5. 終わると CC を 0 に戻し、曲線を `data/pc3a8_calibration/cc/` に保存する

## 確認

- 「注意: 値を上げても特徴が一方向に変わっていません」が出ていない
- 手動で測った曲線（`data/pc3a8_calibration/` の同じパラメータの曲線）と比べて、同じ値で特徴がほぼ同じ。
  比べた結果は `docs/pc3a8_parameter_table.md` の「CC での測定」に書く

CC の曲線は、手動の曲線と合うことを確かめるまでレシピに使わない（`cc/` に分けて保存しているのはこのため）。

## 元に戻す

- ツールは終わったとき・中断したとき（Ctrl-C）に CC を 0 に戻す。戻ったか不安なら、Program を選び直す
- 1026・1027・1028 の保存された値は変わらない。測定のあとも保存しない

## 注意

- **表の Program 以外を選んだまま実行しない**。ほかの Program でも CC 14・15 を制御元にしていれば、その音が変わる
- 送る CC は 14 だけ（sender が、許可した番号以外を送らない）
- **CC 15 は送らない**（2026-11-14、#40）。1027 の測定で、CC 15 が本体全体の音程を動かした（CC 0 で −2 半音、127 で +2 半音）。
  測定のあと CC 15 を 0 に戻したため、電源を入れ直すまで、どの Program も 2 半音低く鳴った。何が CC 15 を受け取っているかは要確認
- 測ったあとに音程がおかしいと感じたら、本体の電源を入れ直す（2026-11-14 に、これで戻ることを確かめた）
- 1026・1027・1028 を編集し直したら（LP Frq・Rel1 Time・Depth・MinDepth・MaxDepth を変えたら）、`data/pc3a8_parameters/kva.json` の `cc_calibration` も同じ値に直す

## 出典

- Musician's Guide 本文 5-2〜5-4（保存）、6-25（Src1 と Depth: 制御元が最大のとき Depth の分だけ動く）、6-29〜6-31（DSPCTL / DSPMOD）、
  6-26（Src2・DptCtl・MinDepth・MaxDepth）、6-42〜6-45（AMPENV・ENV2）、6-45〜6-46（ENVCTL: 倍率は 0.018〜50.000x、制御元が 127 で Depth 倍、0 で効かない、0 秒の区間には効かない）、
  7-21〜7-22（コントローラーの番号）、10-11（外部の CC を制御元にする）、10-13（本体のコントローラーの既定の CC）
