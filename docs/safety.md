# 実機の安全運用

対象は 2 台。KRONOS 2 はこのすぐ下から、Kurzweil PC3A8 は末尾の「[PC3A8](#pc3a8)」の章に書く。
「音量の安全」「音が鳴りっぱなしになったら」は両方に共通する。

KRONOS 2 について、このツールは「分析と提案」を中心にしている。実機に対して行うのは次の 3 つだけ。

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

## PC3A8

出典は Kurzweil PC3A Musician's Guide（V3）。ページは本文ページ（例: 本文 5-4）。
構造の整理は `docs/pc3a8_program_mode.md`。

PC3A8 では、このツールは**ノートを鳴らす**（Note On / Off）ことと、キャリブレーションの CC モードで
**決めた CC 番号を送る**（下の「このツールが送る MIDI」）ことだけを行う。

- パラメータを読み書きする SysEx の形式は公開されていない。マニュアルの MIDI Implementation Chart には、SysEx を送受信できることだけが書かれている（本文 A-1）。このため状態の読み取りも書き込みもしない
- 音色の設定は、ツールが出す手順書に従って人が本体で行う

### 守ること

| 項目 | ルール |
| --- | --- |
| OS | 今のバージョンのまま。アップデートファイルは適用しない（作業開始時にバージョンを下の表に記録する） |
| バックアップ | 作業を始める前に、下のチェックリストでバックアップを取る |
| 音作りの場所 | 下で決めたテスト用の Program ID だけを使う。ほかの ID には保存しない |
| 保存 | 手順は `docs/manuals/pc3a8/save_program.md`。保存先の ID を声に出して確認してから Save する。**メモリ上の Program と同じ ID に保存すると、元の Program は完全に消える**（本文 5-4） |
| Program の切り替え | 保存していない編集は、Program を切り替えると警告なしで失われる（本文 6-3）。編集中は切り替えない |
| エフェクト | 比較用の録音はドライ（エフェクトなし）で行う |

### やってはいけない操作

| 操作 | 理由 | 出典 |
| --- | --- | --- |
| Master モードの **Reset**（作業中・ツールからは使わない） | ユーザーが作ったオブジェクトがすべて消え、工場出荷時に戻る。下の「元に戻す方法」の最後の手段として、人が判断して行うときだけ使う | 本文 11-1, 11-17 |
| Bootloader の **Format Flash** | オブジェクトだけでなく OS も消える | 本文 B-3 |
| Bootloader の **System Update**（.KUF の適用） | OS の更新にあたる | 本文 B-2 |
| **Program 999 Default Program** の変更 | NewLyr（新しい Layer）のひな形になっている | 本文 6-52 |
| **Setup 126 Internal Voices** の上書き | 既定の Control Setup。Program モードのコントローラー設定のもとになる | 本文 6-9〜6-11, 6-56 |
| テスト用以外の ID への保存・削除 | 既存の音色を失う。ROM の ID に保存した場合は、新しいほうを消せば ROM が戻る（本文 5-4）が、それにも頼らない | 本文 5-2, 5-4 |
| Storage モードでの読み込み（LOAD）のうち、既存を消す・上書きする方式（OvFill・Overwrt） | OvFill は読み込む前に、選んだバンク（または Everything）を消去する。Overwrt は同じ ID の既存オブジェクトを上書きする | 本文 13-11〜13-12 |

### テスト用の領域

作業を始める前に記入する。ROM の音色を編集して保存すると、User Bank の空き ID（1025 から）が提案される（本文 5-2, 5-4）。

- OS バージョン: `OS 2.41.24383` / オブジェクト `2.31.2`（Master モード › OBJECT で確認。本文 11-13）
- テスト用の Program ID: `1025〜`（User Bank の先頭から順に使う。使う番号を増やしたら下の表に追記する）
- 決めた日: `2026-11-14`（この時点で User Bank は未使用）

| ID | 名前 | 内容 |
| --- | --- | --- |
| 1025 | KVA BASIC SAW | キャリブレーションの基準の音（2026-11-14 作成）。Program 999 Default Program を編集して保存。下の「基準音 1025 の設定」 |
| 1026 | KVA CC CAL | **CC キャリブレーション用**（#34）。1025 を元に、LP Frq を G 1（49 Hz）、DSPMOD の LP Frq の Src1 を CC 14、Depth を +10800 ct にする。作り方は `docs/manuals/pc3a8/calibrate_cc.md` |
| 1027 | KVA ENVCTL CAL | **CC キャリブレーション用**（#37）。**CC 15 を送らなくなったため、いまは使えない**（#40）。1025 を元に、AMPENV の Rel1 Time を 1.60 s、ENVCTL の Release の Source を CC 15、Depth を 50.000x にする。作り方は `docs/manuals/pc3a8/calibrate_cc.md` |
| 1028 | KVA ENV2 CAL | **CC キャリブレーション用**（#40）。1025 を元に、LP Frq を G 1（49 Hz）、DSPMOD の LP Frq の Src2 を ENV2・DptCtl を CC 14・MinDepth 0 ct・MaxDepth 10800 ct、ENV2 を Att1 0 s・100% / Dec1 0.40 s・100%、AMPENV の Decay Level を 100% にする。作り方は `docs/manuals/pc3a8/calibrate_cc.md` |

#### 基準音 1025 の設定

ユーザーが本体で設定し、読み上げた値（2026-11-14）。作り方は `docs/manuals/pc3a8/build_base_program.md`。

| ページ | 項目 | 値 | 出典 |
| --- | --- | --- | --- |
| KEYMAP | Keymap | 999 Silence | 本文 6-53 |
| ALG | Algorithm | 1（ブロック: SAW → LOPASS → NONE） | 本文 6-22〜6-23 |
| DSPCTL | Saw Pch | 0 ST、KeyTrk 100 ct/key | 本文 6-53 |
| DSPCTL | LP Frq（LOPASS） | G 10 25088 Hz（最大。ホイールをそれ以上回しても変わらない） | 実機の画面で確認 |
| DSPCTL | Level | −6 dB、KeyTrk 0.00 dB/key、**VelTrk 0 dB**（999 の 35 dB から変更） | 本文 6-29 |
| AMPENV | モード | User | 本文 6-42 |
| AMPENV | Attack 1 / 2 / 3 | 0 s・100% / 0 s・0% / 0 s・0%（時間 0 の Attack 2・3 は音に影響しない） | 本文 6-43 |
| AMPENV | Decay | 0.10 s・75% | 本文 6-43 |
| AMPENV | Release 1 / 2 / 3 | 0.06 s・0% / 0 s・0% / 0 s（User） | 本文 6-43〜6-44 |
| AMPENV | Loop | Off（回数 Inf） | 本文 6-44 |
| COMMON | Monophonic | Off | 本文 6-35 |
| PROGFX | Insert / Aux 1 / Aux 2 | 0 None / 0 None / 0 None | 本文 6-47 |

- Release 1 の時間は 0.02 秒刻みで、予定の 0.05 秒にはできなかったので 0.06 秒にした
- 解析結果（2026-11-14、C4・ベロシティ 100、`assets/test/pc3a8_1025_c4.wav`）:
  - ピッチ: C4 +0.2 セント（確信度 0.94）
  - 倍音: 1/n の比（2 次 −6.0 dB、3 次 −9.5 dB、4 次 −12.0 dB …）で、ノコギリ波どおり
  - 明るさ: 重心は基音の 13.2 倍。発音中ほぼ変わらない（×1.02）
  - 包絡: アタック 8.5 ms、ディケイ 95 ms、**サステイン −7.9 dB**、リリース 21 ms
  - その他: ピーク −9.6 dBFS、S/N 67 dB 以上、解析上の注意なし
- AMPENV の Level 75% は、振幅の比なら −2.5 dB のはずだが、測ると −7.9 dB だった。%と dB の対応はマニュアルにないので、
  #22 のキャリブレーションで測る
- マスターエフェクトの状態は `docs/pc3a8_setup.md` の「マスターエフェクト」

キャリブレーションでは基準音を呼び出してから 1 つのパラメータだけを変え、測り終えたら保存せずに戻す
（基準音を上書きしない）。

### バックアップのチェックリスト

手順は `docs/manuals/pc3a8/backup.md`。Storage モードの STORE ページで、ユーザーが作った・編集したオブジェクトを USB メモリに .P3A ファイルとして保存する
（本文 13-6〜13-7）。ROM の音色は保存対象にならない（保存する必要もない）。

2026-11-14 時点: ユーザーが作ったオブジェクトはない（User Bank 未使用、ユーザー確認）ので、保存するものはない。
テスト用の Program を作ったあとや、Reset の前には、次の手順で保存する。

- [ ] 本体背面の USB Storage ポートに USB メモリを挿した（本文 13-2）
- [ ] STORE ページで Object Type に「All types」、Range/Bank に「Everything」を選んで保存した
- [ ] 同じページで Master ファイル（Master モード・MIDI モードの設定）も保存した（本文 13-7）
- [ ] 保存した .P3A ファイルを PC にもコピーした
- [ ] 保存日と内容をメモした

### このツールが送る MIDI

送るのは次の 4 種類だけ（`src/synth_ai/infrastructure/midi/sender.py` で制限している）。

| メッセージ | 使う場面 |
| --- | --- |
| Note On / Note Off | 鳴らす（`midi-probe`・`capture`・`calibrate`） |
| All Notes Off（CC 123） | 鳴らし終わり・中断のとき |
| **CC 14**（値 0〜127） | `calibrate` の CC モードだけ（下の「CC を送る条件」） |

- **Program Change は送らない**。PC3A8 は Program Change を受信する（本文 A-1）ので、送ると選択中の Program が切り替わり、保存していない編集が失われる
- **SysEx は送らない**
- **上の表にない CC は送らない**（バンク切り替えの 0・32、音量の 7、データ入力の 6・38・98〜101、チャンネルモードの 120〜127 など）。sender は、許可した番号以外の CC を拒否する
- 音色は、人が本体でテスト用の ID を選んでおく

#### CC を送る条件（2026-11-14 にユーザーが承認、#34）

CC は Program のパラメータの制御元（Src1・Source など）に割り当てた番号を送ると、演奏中にそのパラメータが動く（本文 10-11）。
保存された値は変わらない。

1. 番号は **CC 14** だけ。本体のコントローラーの既定の割り当てにない番号（本文 7-21〜7-22、10-13）
   - **CC 15 は送らない**（2026-11-14 に外した、#40）。マニュアルでは未使用の番号だが、実機では CC 15 が**本体全体の音程**を動かした（CC 0 で −2 半音、64 付近で正しい音程、127 で +2 半音。どの Program でも同じ）。ツールが測定のあとに CC 15 を 0 に戻したため、電源を入れ直すまで、すべての Program が 2 半音低く鳴った。何が CC 15 を受け取っているかは**要確認**
2. チャンネルは `config/local.yaml` の `channel`（Program モードで選んでいるチャンネル）だけ
3. 送るのは `calibrate` の CC モードで、人が本体で**キャリブレーション用のテスト Program**（下の表の「CC キャリブレーション用」）を選んでいると確かめたあとだけ。ツールは選んでいる Program を読めないので、コマンドの最初に人が確かめる
4. 測り終えたら（中断したときも）、送った CC を **0**（効果なし）に戻す
5. 測定のあとも保存しない（Exit で No）

### 録音の前に

- 音色を選ぶ・編集する作業はすべて人が本体で行う。ツールは鳴らして録るだけ
- 編集中の音を録るときは、Program を切り替えずに録音する（切り替えると編集が消える）
- 録音が終わったら、残したい編集だけをテスト用の ID に保存する

### 元に戻す方法

手順は `docs/manuals/pc3a8/recover.md`。影響の小さい順に試す。上の段で戻るなら、下の段は使わない。

| 状況 | 戻し方 | 消えるもの | 出典 |
| --- | --- | --- | --- |
| 編集中の音がおかしくなった | Program Editor で Storage ボタン（Compare）を押して編集前の音と比べる。Exit で「保存しますか」に No を選ぶか、Program を選び直すと、編集は捨てられる | 保存していない編集 | 本文 5-3, 6-3, 6-13 |
| テスト用の Program を保存し間違えた | テスト用の ID の Program を消す（Program Editor の Delete、または Master モード › OBJECT › Delete で 1 つずつ選ぶ）。記録した設定から作り直す | 消した Program | 本文 6-52, 11-13〜11-14 |
| ROM の ID に誤って保存した | その ID の新しい Program を消すと、ROM の音色が戻る | 消した Program | 本文 5-2, 5-4 |
| 全体を工場出荷時に戻したい（最後の手段） | 先に上の「バックアップのチェックリスト」で保存する。Master モードで **Reset** を押し、確認に Yes。必要なら Storage モードの LOAD でバックアップを読み込む（本体が空なので、既存を消す方式は使わなくてよい） | **すべてのユーザーオブジェクトと設定**（全パラメータが既定値に戻る） | 本文 11-17, 13-9〜13-12 |
| 起動しない・Reset できない | Exit を押しながら電源を入れて Bootloader に入り、**System Reset**（ユーザーオブジェクトを消して工場出荷時に戻す）。Format Flash は使わない | Reset と同じ | 本文 B-1〜B-2 |

Reset と System Reset は、人が本体で判断して行う。このツールからは行わない（そもそも PC3A8 には Note 以外を送らない）。
