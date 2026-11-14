# PC3A8: 基準音 1025「KVA BASIC SAW」を作る

## 目的

キャリブレーションとレシピの出発点になる基準音を作ります。KVA のノコギリ波 1 つと LOPASS だけの、単純な音です。
ふだんは作り直す必要はありません。消えたとき（[recover.md](recover.md) の段 2〜4 のあと）に使います。

設定値の一覧は `docs/safety.md` の「基準音 1025 の設定」です。値はこの手順書と同じで、食い違ったら safety.md が正です。

## 前提

- 1025 が空いている（Program モードで 1025 を選んで、何もないか、消してよいものか確かめる）
- モニターの音量を下げている（ALG を変えると音が大きく変わることがある。本文 6-22）

## 手順

1. Program モードで **999 Default Program** を選び、**Edit** で Program Editor に入る（本文 6-52）。999 は保存しない（ひな形として使うだけ）
2. **KEYMAP** ページで **Keymap** を **999 Silence** にする（本文 6-53）
3. **ALG** ページで **Algorithm** を **1** にし、ブロックを左から **SAW** → **LOPASS** → **NONE** にする（本文 6-22〜6-23、6-54）
   - ブロックを選び、Alpha Wheel で機能を回して選ぶ（本文 6-54）
4. **DSPCTL** ページで、次の値にする（本文 6-29、6-53）

   | 左の列 | 値 |
   | --- | --- |
   | Saw Pch | 0 ST（サブページの KeyTrk 100 ct/key） |
   | LP Frq | G 10 25088 Hz（最大。それ以上回しても変わらない） |
   | Level | −6 dB（サブページの KeyTrk 0.00 dB/key、**VelTrk 0 dB**） |

   999 では Level の VelTrk が 35 dB なので、0 dB に変える（ベロシティで音量が変わらないようにする）
5. **AMPENV** ページで、モードを **User** にし、次の値にする（本文 6-42〜6-44）

   | 区間 | Time・Level |
   | --- | --- |
   | Attack 1 / 2 / 3 | 0 s・100% / 0 s・0% / 0 s・0% |
   | Decay | 0.10 s・75% |
   | Release 1 / 2 / 3 | 0.06 s・0% / 0 s・0% / 0 s |
   | Loop | Off |

6. **COMMON** ページで **Monophonic** を **Off** にする（本文 6-35）
7. **PROGFX** ページで **Insert**・**Aux 1**・**Aux 2** を **0 None** にする（本文 6-47）
8. [save_program.md](save_program.md) の手順で、**1025** に **KVA BASIC SAW** の名前で保存する

## 確認

1. Program モードで 1025 を選ぶ
2. PC で `uv run synth-ai capture assets/test/pc3a8_1025_check.wav -s pc3a8 --note C4` を実行し、`analyze` する（`docs/pc3a8_setup.md`）
3. `docs/safety.md` の「解析結果」と比べる: ピッチ C4 ±数セント、倍音が 1/n の比、サステイン −7.9 dB 前後、リリース 20 ms 前後

## 元に戻す

- 保存前なら Exit で **No**（[exit_and_compare.md](exit_and_compare.md)）
- 値を間違えて保存したら、1025 を Edit で開いて直し、同じ 1025 に保存し直す（メモリの Program なので、同じ ID が提案される。本文 5-4）

## 注意

- **999 Default Program を保存しない**（NewLyr のひな形。本文 6-52、`docs/safety.md`）
- 1025 を作り直したら、キャリブレーション曲線（`data/pc3a8_calibration/`）が今の 1025 で測ったものと合うか、1〜2 点測り直して確かめる
- 1026・1027（CC キャリブレーション用）は 1025 を元に作るので、1025 を作り直したら作り直す（[calibrate_cc.md](calibrate_cc.md)）

## 出典

- Musician's Guide 本文 5-4（保存）、6-22〜6-23（ALG）、6-29（DSPCTL）、6-35（COMMON）、6-42〜6-44（AMPENV）、6-47（PROGFX）、
  6-52（Program 999）、6-53〜6-54（KVA の最小の設定、オシレーターの選び方）
- 実機で確かめた日: 2026-11-14（この値で作って読み上げた。`docs/safety.md` の「基準音 1025 の設定」）
- 作るときに押したボタンの順番は記録していない。上の順番はマニュアルの手順から書いた（**要確認**）
