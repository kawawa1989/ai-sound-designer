# PC3A8 の接続と録音

PC3A8 を PC から鳴らし、その音を録音・解析するための接続と設定です。安全上の決まりは `docs/safety.md` の「PC3A8」、
Program の構造は `docs/pc3a8_program_mode.md` にまとめています。
出典は Kurzweil PC3A Musician's Guide（V3）の本文ページです。

## 接続

| 経路 | つなぎ方 | 出典 |
| --- | --- | --- |
| 音声 | PC3A8 の **Main L / R**（1/4 インチ TRS バランス出力）→ UR22mkII の IN 1 / 2。PC3A8 に USB オーディオはない | 本文 2-2, A-2 |
| MIDI（どちらか） | **A. USB**: PC3A8 の USB Computer ポート → Mac。USB MIDI 機器として認識される | 本文 2-3, 2-6 |
| | **B. 5 ピン**: UR22mkII の MIDI OUT → PC3A8 の MIDI IN | 本文 2-3 |

- USB MIDI と 5 ピン MIDI は同時に使える。両方の信号は 1 つの 16 チャンネルの流れにまとめられる（本文 2-3）
- Storage モードで USB Temporary Drive を選んでいる間は、USB MIDI が使えない（本文 2-3, 2-6）
- KRONOS とオーディオインターフェースを共有する場合は、音声ケーブル（と 5 ピン MIDI）をつなぎ替える。つなぎ替える前に両方の本体の音量を下げる

## PC3A8 の MIDI 受信

MIDI モードの RECEIVE ページで確かめる（本文 10-5〜10-6）。値は変えずに見るだけでよい。

| 項目 | 既定値 | 意味 |
| --- | --- | --- |
| MIDI Mode | Multi | 有効なすべてのチャンネルで受信する。チャンネルごとに別の Program が鳴る |
| Basic Channel | 1 | |

Multi では、**Program モードで選んでいるチャンネル**（画面右上に表示。Chan/Layer ボタンで切り替え。本文 6-3）に
テスト用の Program を割り当て、`config/local.yaml` の `channel` をそのチャンネルに合わせる。

## 設定（config/local.yaml）

`synths:` の下に `pc3a8` を追加する。書かなかった項目（録音デバイスなど）は、先頭の設定（KRONOS と同じ UR22mkII）を使う。

```yaml
synth: kronos2          # 既定の機種（--synth を付けないときに使う）
midi:
  output_port: UR22mkII
  channel: 1
capture:
  input_device: UR22mkII
  # ...
synths:
  pc3a8:
    midi:
      output_port: PC3A # A. USB の場合（ポート名は「Kurzweil PC3A」）。B. 5 ピンなら UR22mkII
      channel: 1        # Program モードで選んでいるチャンネル
```

コマンドに `--synth pc3a8`（`-s pc3a8`）を付けると、PC3A8 の設定を使う。

```bash
uv run synth-ai devices -s pc3a8
```

## 確認の手順

1. `docs/safety.md` の「PC3A8」を確認し、テスト用の Program（ID 1025〜）か、音の確認に使う ROM の Program を選ぶ（ROM の Program は鳴らすだけで、編集・保存しない）
2. モニターの音量と UR22mkII の入力ゲインを下げておく
3. `devices -s pc3a8` で、MIDI 出力ポートと録音デバイスに `*` が付くことを確認する
4. `midi-probe` で 1 音鳴らす

   ```bash
   uv run synth-ai midi-probe -s pc3a8 --note C4
   ```

5. `capture` で録音し、`analyze` で解析する

   ```bash
   uv run synth-ai capture -s pc3a8 assets/test/pc3a8_c4.wav --note C4
   ```

   ```bash
   uv run synth-ai analyze assets/test/pc3a8_c4.wav -o runs/pc3a8_c4
   ```

## 実機での確認結果

- 確認日: `2026-11-14`
- MIDI の接続: 5 ピン（Mac ← USB → UR22mkII の MIDI OUT → PC3A8 の MIDI IN）。ポートは `Steinberg UR22mkII`
  - USB も試した。PC3A8 の USB Computer ポートを Mac につなぐと `Kurzweil PC3A` として認識された。録音には UR22mkII の USB も要るので、USB ケーブルが 2 本あるときの選択肢とする
- 受信チャンネル: 1（`midi-probe -s pc3a8` で C4 が鳴った）
- 録音: UR22mkII の IN 1/2、48 kHz・2 ch。ピーク −10.5 dBFS（クリップなし）
- 解析結果: ピッチ C4 +4.4 セント（確信度 0.93）、S/N 69 dB 以上。
  左右の相関が 0.28 と低く `wide_stereo` の注意が出た。選んでいた Program のエフェクト（コーラス・リバーブなど）か
  ステレオ音源によるものと考えられる。比較用の録音は、テスト用の Program（#18）でエフェクトを切って行う

### マスターエフェクト（Effect モード）

Program モードの音には、Effect モードのマスターエフェクト（コンプレッサーと EQ）が掛かる（本文 9-8）。
2026-11-14 に読み取った状態（変更はしていない）:

| 項目 | 値 | 測定への影響 |
| --- | --- | --- |
| Master FX | Master FX Enabled（Order: Compressor ⇒ EQ） | |
| Master Cmpr. | **In/Out: Out**（Ratio 3.0:1、Threshold −28.0 dB、MakeUp 0.0 dB、Atk 0.0 ms、Rel 100 ms。3 帯域とも同じ） | Out なので掛かっていない |
| Master EQ | In/Out: In。Bass / Treb / Mid1〜3 の Gain と OutGain がすべて 0.0 dB | 素通し |
| AUXFX1 / AUXFX2 | Override: No | Program 側のエフェクト設定がそのまま使われる |

- 今の状態では、マスターエフェクトは音を変えない。このため Master FX は Enabled のまま測る
- **コンプレッサーを In にすると、−28 dB を超える音が 3:1 で圧縮され、音量とエンベロープの測定がずれる**。
  キャリブレーションの前に Out のままか確かめる
- Effect モードの設定は、マスターテーブルを保存すると電源を切っても残る（本文 9-4）

### 経路の違い（USB と 5 ピン）

このツールは Note On/Off・All Notes Off しか送らないので、どちらでも同じように動く。違いは次のとおり。

| 項目 | USB | 5 ピン（UR22mkII 経由） |
| --- | --- | --- |
| 録音のノイズ | 音声と USB の 2 経路でつながるため、グラウンドループのノイズが出ることがある | MIDI は電気的に絶縁されていて、ノイズが乗りにくい |
| ケーブル | USB が 2 本（PC3A8 と UR22mkII） | USB は 1 本 |
| KRONOS との切り替え | MIDI のつなぎ替えは不要 | UR22mkII の MIDI OUT を差し替える |
| ファイル転送 | Storage モードの仮想ドライブで Mac に保存できる（本文 2-6）。その間は USB MIDI が止まる | できない（USB メモリを使う） |

- 1 回目の `devices -s pc3a8` は、USB をつなぎ替えた直後に macOS の MIDI 初期化エラー（RtMidiError −304）で止まった。もう一度実行すると正常に動いた

## 1 周の流れ（レシピ → 設定 → 録音 → 比較 → 改善）

接続ができたら、次の順に進める。2026-11-14 に参照音 1 つで 1 周した記録は `docs/pc3a8_trial_report.md`。

1. 参照音を解析する: `uv run synth-ai analyze <参照.wav> -o runs/<名前>`
2. PC3A8 のレシピを作る: `uv run synth-ai recipe runs/<名前> -s pc3a8`
3. 本体で設定し、録音・比較する: `docs/manuals/pc3a8/run_trial.md`
4. 必要ならキャリブレーション曲線を測り直す: `docs/manuals/pc3a8/calibrate.md`
