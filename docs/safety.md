# 実機の安全運用（KRONOS 2）

このツールは「分析と提案」を中心にしており、実機に対して行うのは **ノートを鳴らすことだけ**。
音色・設定の書き換えは人が本体で行う。

## 守ること

| 項目 | ルール |
| --- | --- |
| OS | System 3.1.3 のまま。アップデートファイルは適用しない |
| バックアップ | 作業を始める前に、下のチェックリストでバックアップを取る |
| 音作りの場所 | 下で決めたテスト用 Program だけを使う。既存の Program・Combination・Set List を上書きしない |
| Global 設定 | 変更しない（MIDI チャンネルなどは本体の設定に PC 側を合わせる） |
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

`synth-ai midi-probe` と `synth-ai capture` が送るのは次の 3 種類だけ（コードで制限している。
`src/synth_ai/infrastructure/midi/sender.py`）。

| メッセージ | 用途 |
| --- | --- |
| Note On | 1 音鳴らす |
| Note Off | 鳴らした音を止める |
| Control Change 123（All Notes Off） | 終了時・エラー時に必ず送り、音の鳴りっぱなしを防ぐ |

SysEx・プログラムチェンジ・その他のコントロールチェンジは送らない。パラメータの自動書き換え（Phase 6）は、
読み取りの検証・バックアップ・明示的な承認の仕組みができるまで実装しない。

## 音量の安全

- 録音の前に、モニタースピーカー・ヘッドホンの音量を下げておく
- `capture` はピークが -1 dBFS を超えるとクリップの恐れとして警告する（`config/local.yaml` で変更可）
- 録音ファイルの先頭・末尾には 5 ms のフェードを付け、クリックノイズを防ぐ

## 音が鳴りっぱなしになったら

1. `Ctrl+C` でコマンドを止める（終了処理で All Notes Off が送られる）
2. それでも止まらなければ、本体の音量を下げてから USB を抜く、または本体のパネル操作で止める

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
