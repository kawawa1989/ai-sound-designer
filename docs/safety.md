# 実機の安全運用（KRONOS 2）

このツールは「分析と提案」を中心にしている。実機に対して行うのは次の 3 つだけ。

1. **ノートを鳴らす**（Note On / Off）
2. **状態を読み取る**（SysEx。モード・選択中の音色・音色の設定値）
3. **テスト用 Program のエディット中の値を変える**（SysEx の Parameter Change。下の条件をすべて満たすときだけ）

本体への保存（Write）・Global 設定の変更は、ツールからは行わない。保存が必要なときは人が本体で行う。

## 守ること

| 項目 | ルール |
| --- | --- |
| OS | System 3.1.3 のまま。アップデートファイルは適用しない |
| バックアップ | 作業を始める前に、下のチェックリストでバックアップを取る |
| 音作りの場所 | 下で決めたテスト用 Program だけを使う。既存の Program・Combination・Set List を上書きしない |
| Global 設定 | ツールからは変更しない（MIDI チャンネルなどは本体の設定に PC 側を合わせる）。例外は下の「Enable Exclusive」だけで、人が一時的に変え、保存しない |
| パラメータの自動変更 | 下の「SysEx の扱い」の条件をすべて満たすときだけ。変更はエディット中の値だけで、ツールは保存しない |
| 保存 | テスト用 Program に Write するときは、保存先の番号を声に出して確認する |
| エフェクト | 比較用の録音はドライ（エフェクトなし）で行う |

## テスト用の領域

作業を始める前に記入する。

- テスト用 Bank: `USER-CC`
- テスト用 Program 番号: `U-CC000`〜（使う番号を増やしたらここに追記する）
- 決めた日: `2026-10-25`

| 番号 | 名前 | 内容 |
| --- | --- | --- |
| U-CC000 | AL-1 BASIC SOUND | キャリブレーションの基準の音。AL-1、OSC1 Saw（Level 99、他の音源は 0）、Filter Single / Low Pass / Resonance 0 / EG Intensity 0 / Keyboard Track Intensity to A 0、Amp EG Level 0/99/75/75・Time 00/00/30/20、IFX・MFX・TFX すべてオフ |

キャリブレーションでは U-CC000 を呼び出してから 1 つのパラメータだけを変え、測り終えたら保存せずに戻す
（基準の音を上書きしない）。

## バックアップのチェックリスト

- [ ] 本体のデータ（Program / Combination / Set List / Global など）を外部メディアに保存した
- [ ] ユーザーサンプル・マルチサンプルを使っている場合、その関連データも保存した
- [ ] 保存したメディアを PC にもコピーした
- [ ] 保存日と内容をメモした（保存の操作は公式マニュアルに従う）

## このツールが送る MIDI

### ノート（`midi-probe`・`capture`・`calibrate`）

次の 3 種類だけ（コードで制限している。`src/synth_ai/infrastructure/midi/sender.py`）。

| メッセージ | 用途 |
| --- | --- |
| Note On | 1 音鳴らす |
| Note Off | 鳴らした音を止める |
| Control Change 123（All Notes Off） | 終了時・エラー時に必ず送り、音の鳴りっぱなしを防ぐ |

プログラムチェンジ・その他のコントロールチェンジは送らない。

### SysEx の扱い

KORG の SysEx 仕様（`manuals/kronos/text/txt/KRONOS_MIDI_SysEx.txt`、Version 1.26）のうち、
**下の「使う」表にあるものだけ**を使う。それ以外のファンクションはコードで拒否する（Issue #5 で実装）。
送り先は KRONOS 宛て（ヘッダー `F0 42 3g 68`、`g` は Global の MIDI チャンネル）だけ。

**使う（読み取り）**: 本体の状態を変えない。

| 送る | 受け取る | 用途 |
| --- | --- | --- |
| 12 Mode Request | 42 Mode Data | 今のモードが Program モードか確かめる |
| 32 Current Performance Id Request | 33 Current Performance Id | 選択中の Program の番号を確かめる |
| 74 Current Object Dump Request | 75 Current Object Dump | 選択中の Program の設定値を読み取る（書き込み前の保存・書き込み後の確認） |
| — | 24 Reply | エラーの応答を受け取る |

**使う（書き込み）**: エディット中の値だけを変える。本体には保存されない。

| 送る | 用途 |
| --- | --- |
| 43 Parameter Change (integer) | パラメータ表で書き込みを許可したパラメータの値を変える |

**使わない**（主なもの。表にないものはすべて使わない）

| ファンクション | 使わない理由 |
| --- | --- |
| 73 Object Dump（PC から送る） | 本体のデータ（音色など）が書き換わる |
| 76 Store Bank Request | バンクを本体のストレージに保存する |
| 72 Object Dump Request / 77 Dump Bank Request | 必要以上に大きな読み取り。選択中の音色は 74 で足りる |
| 44 Parameter Change (binary)・41 / 6D / 6E / 53〜56（ほかの種類のパラメータ変更） | 対象外のデータを変える。必要になったら改めて方針を決める |
| 71 Set Current Object・4E Mode Change | 選択中の音色やモードを切り替える（テスト用以外の音色に変わる恐れ） |
| 7C Change Program Bank Type | バンクの種類を変える |
| 78 Reset Controller・7F KARMA Control | 書き込みの検証に関係しない操作 |

### 書き込みの条件（すべて満たすときだけ）

1. 本体が **Program モード**である（12 Mode Request で確認）
2. 選択中の Program が、上の「テスト用の領域」の表にある番号である（32 Current Performance Id Request で確認）
3. パラメータが **パラメータ表で書き込みを許可**されている（Issue #8 で実機検証したものだけ。それまではすべて不許可）
4. 値がパラメータ表の範囲内である
5. 書き込む前に現在値を読み取り、保存している（74 Current Object Dump Request）
6. 書き込んだ後に読み取り直し、値が反映されたことを確認する。一致しなければエラーにして元の値に戻す
7. 終了時・エラー時・中断（`Ctrl+C`）時に、変えたすべてのパラメータを元の値に戻す
8. ユーザーが承認している
   - `device set`（1 項目の変更）: 1 回ごとに、パラメータ・今の値 → 新しい値・送り先を表示して承認を求める
   - `calibrate --auto`: 開始時に、変えるパラメータと値の一覧を表示して 1 回承認を求める

ツールは本体の Write（Program の保存）を行わない。測定のあとは、Program を選び直せばエディット中の値は捨てられ、
保存されている音色に戻る。

### Global の「Enable Exclusive」

SysEx を送受信するには、Global P1: MIDI の「Enable Exclusive」（1–1c、Parameter Guide 本文p.788）が
オンである必要がある。

- オンなら何もしない
- オフなら、作業の間だけ**人が本体でオンにし、Write Global Setting は実行しない**。Global モードの変更は
  保存しなければ電源を切ると元に戻る（Operation Guide 本文p.183）
- ツールから Global 設定を変えることはしない

## 音量の安全

- 録音の前に、モニタースピーカー・ヘッドホンの音量を下げておく
- `capture` はピークが -1 dBFS を超えるとクリップの恐れとして警告する（`config/local.yaml` で変更可）
- 録音ファイルの先頭・末尾には 5 ms のフェードを付け、クリックノイズを防ぐ

## 音が鳴りっぱなしになったら

1. `Ctrl+C` でコマンドを止める（終了処理で All Notes Off が送られる）
2. それでも止まらなければ、本体の音量を下げてから USB を抜く、または本体のパネル操作で止める

## パラメータが変わったままになったら

ツールは終了・エラー・中断時に元の値へ戻すが、ケーブルが抜けた・PC が止まったなどで戻せないことがある。

1. 本体でテスト用の Program を選び直す（エディット中の値は捨てられ、保存されている音色に戻る）
2. **Write しない**（変わった値を保存してしまうため）
3. 心配なときは `synth-ai device read`（Issue #7 で追加）で値を確認する

## 初回の接続確認

```bash
uv run synth-ai devices
```

```bash
uv run synth-ai midi-probe --port KRONOS --note C4
```

```bash
uv run synth-ai capture assets/test/kronos_c4.wav --note C4
```

1. `devices` に KRONOS の MIDI 出力ポートと録音デバイスが表示されることを確認する
2. `config/local.example.yaml` を `config/local.yaml` にコピーし、`midi.output_port` と `capture.input_device` を記入する
3. テスト用 Program を選んだ状態で `midi-probe` を実行し、音が鳴ることを確認する
4. `capture` で録音し、`synth-ai analyze` で解析できることを確認する

MIDI が使えない場合は `midi.output_port` を空（null）のままにする。`capture` が合図を出すので、
それに合わせて鍵盤を弾けば同じ流れで録音・比較できる。
