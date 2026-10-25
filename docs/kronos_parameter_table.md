# KRONOS パラメータ表の作り方

レシピ生成は KRONOS のパラメータ名をコードに持たず、`data/kronos_parameters/<engine>.json`
（AL-1 なら `al1.json`）を引いて手順を作る。表は**公式 Parameter Guide を見ながら人が作る**。
表にないパラメータは手順に出ない。

## ファイル形式

```json
{
  "schema_version": "1.0",
  "synth_id": "kronos2",
  "engine": "AL-1",
  "source": { "document": "KRONOS Parameter Guide", "version": "（資料の版）" },
  "parameters": [
    {
      "id": "al1.<ページ>.<カットオフの名前>",
      "page": "（本体の画面名をそのまま）",
      "tab": "（タブ名。なければ null）",
      "name": "（本体のパラメータ名をそのまま）",
      "kind": "int",
      "min": 0,
      "max": 99,
      "default": null,
      "roles": ["filter_cutoff"],
      "source_ref": "Parameter Guide p.000",
      "verified": true
    },
    {
      "id": "al1.<ページ>.<波形の名前>",
      "page": "…",
      "name": "…",
      "kind": "choice",
      "choices": [
        { "value": "（選択肢の表示名）", "tags": ["saw"] },
        { "value": "（選択肢の表示名）", "tags": ["square", "pulse"] }
      ],
      "roles": ["oscillator_waveform"],
      "source_ref": "Parameter Guide p.000",
      "verified": true
    }
  ]
}
```

| 項目 | 内容 |
| --- | --- |
| `id` | 表の中で一意な ID。キャリブレーション表からもこの ID で参照する |
| `page` / `tab` / `name` | 本体の表示どおり（レシピにそのまま表示される） |
| `kind` | `int` / `float` / `choice` |
| `min` / `max` / `step` | 数値パラメータの範囲と刻み（`choice` では不要） |
| `default` | 初期化した Program での値（分かる場合のみ） |
| `steps_per_octave` | 値 1 段が何分の 1 オクターブか（例: AL-1 の Filter A Frequency は 10、本文p.205）。×f0 で測った曲線を別の音程の参照音に使うとき、音程差のぶんだけ値をずらすのに使う |
| `calibration_source` | 同じ尺度の別パラメータの ID。自分の曲線がないとき、そのパラメータの曲線を使う（例: Amp EG の Break レベルは Sustain の曲線） |
| `choices` | 選択式の選択肢。`tags` で「どの種類の選択肢か」を示す |
| `roles` | このパラメータが担う役割（下の表）。1 つのパラメータに複数付けてよい |
| `source_ref` | 資料の該当ページ。必須 |
| `verified` | 資料と照合済みなら `true`。`false` のパラメータはレシピで「要確認」と表示される |

同じ役割を持つパラメータが複数ある場合（例: Filter A と Filter B）、**表の先頭のもの**が使われる。
レシピで使いたいほうを先に書く。

## 役割（roles）

| 役割 | 意味 |
| --- | --- |
| `oscillator_waveform` | オシレーターの波形（選択式。選択肢に波形タグを付ける） |
| `noise_level` | ノイズの量 |
| `filter_type` | フィルターの種類（選択式。`lowpass` などのタグを付ける） |
| `filter_cutoff` | カットオフ周波数 |
| `filter_resonance` | レゾナンス |
| `filter_eg_source` | カットオフを動かす EG の選択（選択式。フィルター用 EG の選択肢に `filter_eg` タグ） |
| `filter_eg_intensity` | フィルター EG がカットオフを動かす量 |
| `filter_eg_attack` / `_decay` / `_slope` / `_release` | フィルター EG の各段の時間 |
| `filter_eg_start_level` / `_attack_level` / `_break_level` / `filter_eg_sustain` | フィルター EG の各レベル |
| `amp_eg_attack` / `_decay` / `_slope` / `_release` | アンプ EG の各段の時間 |
| `amp_eg_start_level` / `_attack_level` / `_break_level` / `amp_eg_sustain` | アンプ EG の各レベル |

`*_start_level` `*_attack_level` `*_break_level` `*_slope` と `filter_eg_source` は、多段 EG を持つ機種向けの
任意の役割。表になければ手順から省かれ、未登録としても報告されない。
両極性のレベル（–99…+99 など）は、レシピで「効果なし」にするとき 0 に設定される。

選択肢のタグ: `saw` `square` `pulse` `triangle` `sine` `noise` `lowpass` `highpass` `bandpass` `filter_eg`

`notes` に書いた内容は、レシピの各手順の理由に「（注: …）」として表示される。
レシピで自動設定できない補足（例: Pulse を矩形波にするにはパルス幅 50）はここに書く。

役割の一覧は `src/synth_ai/adapters/kronos2/roles.py` が正。足りない役割があれば先にそこへ追加する。

## キャリブレーション表（任意・推奨）

表があればレシピは具体的な値を出せる。なければ値は空欄になり、音響上の目標（例: アタック 8 ms）だけが示される。

`data/kronos_calibration/*.json`（1 ファイル 1 曲線）:

```json
{
  "schema_version": "1.0",
  "synth_id": "kronos2",
  "parameter_id": "al1.<ページ>.<名前>",
  "feature": "attack_time",
  "unit": "ms",
  "conditions": "初期化した AL-1 / Saw / C4 / velocity 100 / 他は初期値",
  "measured_at": "2026-10-20",
  "points": [
    { "parameter_value": 0, "feature_value": 2.1 },
    { "parameter_value": 20, "feature_value": 15.0 },
    { "parameter_value": 40, "feature_value": 80.0 }
  ]
}
```

`feature` は `src/synth_ai/core/sound_spec/features.py` の名前を使う。
`reference_note` は測定した音（`calibrate` が自動で記録する）。カットオフのように ×f0 の特徴で測った曲線は、
参照音の音程が違うと `steps_per_octave × log2(参照音の f0 / 測定音の f0)` 段だけずらして使う
（例: C4 で測った曲線を C3 の参照音に使うと −10 段）。
対応の目安:

| 役割 | 測る特徴（feature） |
| --- | --- |
| `filter_cutoff` | `brightness_end`（フィルター EG を効かせない状態で測る） |
| `filter_eg_intensity` | `brightness_change` |
| `filter_eg_decay` | `brightness_decay_time` |
| `amp_eg_attack` | `attack_time` |
| `amp_eg_decay` | `decay_time` |
| `amp_eg_sustain` | `sustain_level`（絶対音量で測り、いちばん大きい値の録音を 0 dB とした差にする。アタックの段を変える必要はない） |
| `amp_eg_release` | `release_time` |
| `noise_level` | `noisiness` |

測定は `synth-ai calibrate` で対話的に行う（基準の音色は `docs/safety.md` の U-CC000）。

```bash
uv run synth-ai calibrate
```

```bash
uv run synth-ai calibrate al1.filter_a.frequency --values 0,15,30,45,60,75,90,99
```

1 つめは測れるパラメータの一覧を表示する。2 つめで測定を始めると、値ごとに
「本体でその値にして Enter」→ MIDI で発音・録音 → 解析 → 測った特徴を表示 →「Enter で採用 / r で録り直し / s で使わない」
を繰り返し、最後に `data/kronos_calibration/<パラメータ ID>__<特徴>.json` を書き出す。録音は `runs/calibration/` に残る。

- 測る特徴はパラメータ表の役割から自動で決まる（`--feature` で変更可）
- アタック・ディケイなどは押さえる時間を最低 3 秒、リリースは余韻を最低 4 秒にする
- 曲線は単調（値を上げると特徴が一方向に変わる）である必要がある。単調でない曲線は逆引きに使われない
- 測り終えたら、変えたパラメータを保存せずに基準の音色を選び直す
