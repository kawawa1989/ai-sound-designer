# PC3A8 のパラメータ表

`data/pc3a8_parameters/kva.json` は、PC3A8 のレシピで使うパラメータの一覧です。範囲・単位・役割・出典を書いています。
読み込みと検証は `src/synth_ai/adapters/pc3a8/parameters.py` で行います。

- 出典は Kurzweil PC3A Musician's Guide（V3）の本文ページ（例: `Musician's Guide 本文 6-43`）です
- マニュアルにない値は、実機の画面で読み、`source_ref` に「実機の画面で確認（日付）」と書きます
- 公式資料にも実機にもない値は書きません。分からないものは `verified: false` にし、`notes` に「要確認」と書きます

## KRONOS の表との違い

| 項目 | KRONOS（`al1.json`） | PC3A8（`kva.json`） |
| --- | --- | --- |
| 値 | 0〜99 などの目盛り（整数） | 秒・%・dB・Hz・セントの物理単位（小数） |
| 音源・フィルター | エンジンの固定の項目（OSC1 Waveform など） | アルゴリズムのブロックに置く機能（SAW、LOPASS など） |
| 前提 | エンジン（AL-1） | 基準音の配置（`layout`: Program 1025、Keymap 999 Silence、Algorithm 1、SAW → LOPASS → NONE） |
| 範囲が分からない項目 | 書かない | `verified: false` で、`min` / `max` を空にできる |

役割（`roles`）と選択肢のタグは、KRONOS の表と同じ名前を使います（例: `amp_eg_release`、`saw`）。
共通の語彙にするかどうかは #20 で決めます。

## 項目

| フィールド | 内容 |
| --- | --- |
| `id` | 表の中で一意な ID（例: `kva.ampenv.decay.time`） |
| `page` / `section` / `name` | Program Editor のページ名（ソフトボタン名）、ページ内の位置、本体の表示どおりの名前 |
| `kind` | `float` / `int` / `choice` |
| `min` / `max` / `step` / `unit` | 範囲・刻み・単位。`verified: true` の数値の項目は `min` と `max` が必須 |
| `default` | Program 999 Default Program での値 |
| `base_value` | 基準音 1025 での値 |
| `steps_per_octave` | 周波数の値の 1 段が何分の 1 オクターブか（半音刻みなら 12） |
| `choices` | 選択肢（本体の表示どおり）とタグ |
| `roles` | レシピでの役割 |
| `source_ref` / `verified` / `notes` | 出典、確かめたかどうか、補足 |

`verified: false` の項目と、範囲が分からない項目は、レシピに使いません（`ParameterDef.usable`）。

## 刻みが一定でない値

AMPENV の時間は、値によって刻みが変わります。`values`（個別の値）と `step_ranges`（一定の刻みの区間）で、
本体で選べる値を書きます。`ParameterDef.clamp` は、その中でいちばん近い値に丸めます。
書いた区間より外の値は丸めません。

```json
"values": [0, 0.002, 0.005, 0.01],
"step_ranges": [
  {"start": 0.02, "end": 2.0, "step": 0.02},
  {"start": 2.0, "end": 5.0, "step": 0.04},
  {"start": 5.0, "end": 10.0, "step": 0.1},
  {"start": 10.0, "end": 15.0, "step": 0.5}
]
```

実機で確かめた範囲だけを書きます。上の例は AMPENV の Att1 Time で 15.0 秒まで確かめたものです。

## 実機で確かめた値（2026-11-14）

手順は `docs/manuals/pc3a8/read_parameter_values.md`。

| ID | 確かめた値 |
| --- | --- |
| `kva.alg.block1` | ブロック 1 の一覧にある発振器は SAW、SQUARE、SINE、SINE+、RES NOISE、SHAPED SAW、PWM。TRI はない |
| `kva.dspctl.lp_frq` | 16 Hz（C 0）〜25088 Hz（G 10）、1 クリックで半音 |
| `kva.dspctl.saw_pch` | −120〜60 ST |
| `kva.dspmod.lp_frq.src1` | 一覧に ENV2 がある |
| `kva.dspmod.lp_frq.depth` | −10800〜10800 ct |
| `kva.env2.att1.level` / `kva.env2.decay.level` | −100〜100% |
| `kva.ampenv.att1.time` | 刻み: 0, 0.002, 0.005, 0.01, 0.02 → 2.00 まで 0.02 → 5.00 まで 0.04 → 10.0 まで 0.10 → 0.5（15.0 まで確認） |

## 要確認の項目

- AMPENV の Decay・Release 1 と ENV2 の時間の刻み。Att1 と同じと思われるが、確かめていない（Release 1 は 0.05 付近が 0.02 刻みであることだけ確認。表では Att1 と同じ刻みを使う）
- 時間の 15 秒より上の刻み
- ブロック 1 の一覧にあるフィルター（2POLE LOWPASS など）の機能パラメータ。2 ブロックのフィルターを使えばレゾナンスを設定できる可能性があるが、基準音の配置（ブロック 2 は 1 スロット）では使っていない
