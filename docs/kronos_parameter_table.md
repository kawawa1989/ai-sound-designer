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
| `filter_eg_intensity` | フィルター EG がカットオフを動かす量 |
| `filter_eg_attack` / `_decay` / `_sustain` / `_release` | フィルター EG の各段 |
| `amp_eg_attack` / `_decay` / `_sustain` / `_release` | アンプ EG の各段 |

選択肢のタグ: `saw` `square` `pulse` `triangle` `sine` `noise` `lowpass` `highpass` `bandpass`

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
対応の目安:

| 役割 | 測る特徴（feature） |
| --- | --- |
| `filter_cutoff` | `brightness_end`（フィルター EG を効かせない状態で測る） |
| `filter_eg_intensity` | `brightness_change` |
| `filter_eg_decay` | `brightness_decay_time` |
| `amp_eg_attack` | `attack_time` |
| `amp_eg_decay` | `decay_time` |
| `amp_eg_sustain` | `sustain_level` |
| `amp_eg_release` | `release_time` |
| `noise_level` | `noisiness` |

測定手順: テスト用 Program で対象パラメータだけを数段階変え、それぞれ録音して
`synth-ai analyze` にかけ、`synth-ai spec` の定量目標から値を読み取る（自動化は Sprint 4 以降）。
曲線は単調（値を上げると特徴が一方向に変わる）である必要がある。単調でない曲線は逆引きに使われない。
