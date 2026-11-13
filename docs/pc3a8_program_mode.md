# PC3A8 の Program 構造（Chapter 6 の整理）

PC3A8 Adapter（ロードマップ Phase 5）を作るために、公式マニュアルから必要なことだけを抜き出した。

- 出典: Kurzweil PC3A Musician's Guide（V3、©2014 Young Chang）。`manuals/pc3a8/INDEX.md` から引く
- ページは本文ページ（「章-ページ」形式。例: 本文 6-42）
- 「要確認」と書いた項目は、マニュアルに記載がない。実機の画面で確かめるまで、値を決めつけない
- `synth_docs/` のコミュニティ調査ノートは参考にしただけで、出典にはしていない

## 1. 構造

| 単位 | 内容 | 出典 |
| --- | --- | --- |
| VAST Program | 1〜32 の Layer。各 Layer は Keymap（ROM のサンプル）か KVA 発振器を音源にする | 本文 6-4 |
| KB3 Program | オルガン専用の別方式。Layer もアルゴリズムもない。**このプロジェクトでは使わない** | 本文 6-4 |
| Layer | Keymap とアルゴリズム（DSP の配線）の組。発音数の単位（1 Layer で 128 ボイスのうち 1 つを使う） | 本文 6-4 |
| 信号の流れ | Keymap → アルゴリズム（先頭が PITCH、末尾が AMP）→ エフェクト → 出力 | 本文 6-4, 6-23 |
| Setup | 最大 16 の Program を並べたもの。このプロジェクトでは Program モードだけを使う | 本文 6-4 |

**ユーザーサンプルは読み込めない**: "The PC3A does not load samples"（本文 E-1）。
`user_sample_import` は `unsupported` とする。KRONOS で波形を取り込む提案（Phase 4）は PC3A8 には出さない。

## 2. KVA 発振器（KRONOS の AL-1 に当たる）

ROM のサンプルではなく、DSP で波形を作る発振器（本文 6-53）。
アナログ・シンセのような基本の音作りには、次の 3 点を設定する（本文 6-53 "Minimal Settings"）。

1. KEYMAP ページ: Keymap を **999 Silence** にする
2. AMPENV ページ: エンベロープを **User** にする
3. ALG ページ: アルゴリズムを選び、ブロックに発振器を割り当てる

- **999 Silence を使う理由**: Keymap に設定された鍵ごとの最大音量が発振器にも掛かる。999 Silence は全鍵で同じなので、鍵によって音量が変わらない（本文 6-58）
- **音程**: KVA の音程は発振器ごとの「〜Pch」（例: Saw Pch）で決まる。DSPCTL 左上の Pitch は Keymap 用で、KVA には効かない（本文 6-53〜6-54）
- **発振器は 22 種類**: 11 種類がエイリアスなし、11 種類がエイリアスありで、エイリアスなしが推奨（本文 6-54）。ブロックの大きさが合うアルゴリズムを選んでから割り当てる

エイリアスなし（推奨）:

| ブロック数 | 発振器 | 固有のパラメータ（本文 6-57〜6-58） |
| --- | --- | --- |
| 1 | LPNOIZ（ノイズ + ローパス） | Noiz Frq（カットオフ） |
| 2 | SINE, SINE+, SAW, RES NOISE（ノイズ + レゾナンス付きローパス）, SQUARE | SINE+: Sin+ Pch / Sine+ Am、RES NOISE: Noiz Frq / Noiz Q |
| 3 | PWM | PWM Wid（1〜99、50 で矩形波） |
| 4 | SYNC SAW, SUPER SAW, TRIPLE SAW | SyncOff、Detune（0〜50 セント） |
| 8 | SYNC SQUARE（master / slave、4 ブロックずつ 2 Layer） | Syncoff。Cascade が必要（本文 6-55） |

エイリアスあり（非推奨）:

| ブロック数 | 発振器 |
| --- | --- |
| 1 | SINE, SAW, TRI, SQUARE, NOISE, SINE+, SAW+, NOISE+, SW+SHP（ノコギリ波 + シェイパー。基本的な FM に使える） |
| 2 | SHAPED SAW（Shape 0 でノコギリ波、127 で正弦波）, PWM |

- 表は本文 6-54 の元 PDF を目視して確認した（テキスト抽出では表組みが崩れる）
- **三角波（TRI）はエイリアスありの 1 ブロック版しかない**
- 発振器を複数置くと、最後の発振器の音だけが聞こえる。前の発振器を MIX ブロックへ回すアルゴリズムか、入力を加工する発振器を使う場合は例外（本文 6-54）
- 例として挙がっている Program: 1019 VA1NakedPWMPoly（KVA の最小構成、本文 6-53）

## 3. アルゴリズムと DSP

| 項目 | 内容 | 出典 |
| --- | --- | --- |
| アルゴリズム | 1〜28 と、Cascade 用の 101〜131（101 は 1 の Cascade 版）。ユーザー定義もできる（Dynamic VAST） | 本文 6-22, 6-28 |
| ブロック | DSP 機能 1 つが 1〜4 スロットを使い、スロット数だけ「機能パラメータ」を持つ | 本文 6-23 |
| DSPCTL | 機能パラメータの基準値、Fine Adjust、KeyTrk（C4 が 0 点）、VelTrk | 本文 6-24〜6-25, 6-29 |
| DSPMOD | Src1 + Depth、Src2 + DptCtl + MinDepth / MaxDepth | 本文 6-25〜6-26, 6-30〜6-31 |
| 単位 | **実際の単位**で設定する（音程は ST / ct、音量は dB） | 本文 6-25 |
| PITCH（先頭ブロック） | Pitch −128〜127 ST、Fine ±100 ct、Hz ±10.00、KeyTrk ±2400 ct/key、VelTrk ±7200 ct | 本文 6-29 |
| AMP（末尾ブロック） | Level −96〜24 dB（既定 −6）、KeyTrk ±2.00 dB/key、VelTrk ±96 dB（既定 35） | 本文 6-29 |
| Cascade | Alt Input で、別の Layer の出力をこの Layer の DSP に通す | 本文 6-27〜6-28 |

フィルター:

- LOPASS の機能パラメータは LP Frq（カットオフ）で、VelTrk・Depth はセント単位（例: 10800 ct）（本文 6-55〜6-56）
- 2 ブロックの Lopass は LP Frq / LP Res を持つ（本文 6-24）。「4Pole Mogue LP」という機能もある（本文 6-55）
- **DSP 機能の一覧と、LP Frq の単位・範囲はマニュアルにない。要確認**（実機の DSPCTL 画面で読む）

## 4. エンベロープ

**AMPENV**（本文 6-42〜6-44）:

| 区間 | Time | Level |
| --- | --- | --- |
| Attack 1〜3 | 0〜60 秒 | 0〜100%（Attack 1 は 0% から始まる） |
| Decay（1 区間） | 0〜60 秒 | 0〜100%（0 でなければサステインになる） |
| Release 1〜3 | 0〜60 秒 | Release 1・2 は 0〜150%、Release 3 は常に 0% |
| Loop | Off / seg1F〜seg3F / seg1B〜seg3B | 回数: Inf / 1〜31 |

- **Natural / User**: 既定は Natural（サンプル固有のエンベロープ）。値を回すと User になる（本文 6-42）
- **アタックの曲線**: AMPENV のアタックは指数カーブ（終わりのほうで急に上がる）。ENV2 / ENV3 は直線（本文 6-44）
- **時間の値の扱い**: KRONOS（0〜99 の目盛り）と違い、時間は秒で指定する。ただし実際の聞こえ方とどう対応するかは、キャリブレーションで確かめる（KRONOS でも、表の時間と測った時間はずれた）

**ENV2 / ENV3**（本文 6-44〜6-45）:

- 正負の値を取れる（Release 1・2 は ±100%、Release 3 にも値を設定できる）
- 制御元として割り当てた Layer にだけ効く

**ENVCTL**（本文 6-45〜6-47）:

- AMPENV の Attack / Decay / Release の速さを倍率で変える。Adjust・KeyTrk・VelTrk・Source/Depth の範囲は 0.018〜50.000x
- **時間 0 の区間には倍率が効かない**。必要なら 0.02 秒にする（本文 6-46）
- Impact: 最初の 20 ms を ±24 dB で増減する（本文 6-47）

## 5. 保存と ID（安全に関係する点）

| 項目 | 内容 | 出典 |
| --- | --- | --- |
| ROM の Program を編集して保存 | User Bank の空き ID（**1025 から**）が提案される | 本文 5-2, 5-4 |
| ROM と同じ ID に保存 | ROM を上書きしたように見える。新しいほうを消せば ROM が戻る | 本文 5-2, 5-4 |
| メモリ上の Program と同じ ID に保存 | **元の Program は完全に消える** | 本文 5-4 |
| Program を切り替える | 保存していない編集・コントローラーの状態は警告なしで失われる | 本文 6-3 |
| Program 999 Default Program | NewLyr はこの Program の Layer をひな形にする。**変更しない** | 本文 6-52 |
| Setup 126 Internal Voices | 既定の Control Setup。**上書きしない** | 本文 6-56 |
| Compare（Storage ボタン） | 編集前の音と比べられる。現在の Program は変わらない | 本文 6-13 |
| Master モードの Reset | **ユーザーのオブジェクトをすべて消して工場出荷時に戻す。実行しない** | 本文 11-1 |

## 6. MIDI と録音経路

- **SysEx**: MIDI Implementation Chart で送信 O・受信 O\*（Manufacturer ID 07、Device ID の既定は 0、0〜127 で変更可）（本文 A-1）。ただし、パラメータを読み書きするメッセージの形式はマニュアルに**載っていない**。このため PC3A8 の `parameter_read` / `parameter_write` は `unverified` のままにする
- **Program Change**: 送受信できる（1〜999）（本文 A-1）。このツールからは送らない（`docs/safety.md` の方針と同じ）
- **音声出力**: Main / Aux のバランス出力（1/4 TRS）と S/PDIF 出力（本文 2-2〜2-3, A-2）。**USB オーディオはない**ので、KRONOS と同じくオーディオインターフェース（UR22mkII）のアナログ入力で録る
- **MIDI 接続**: USB MIDI と 5 ピン MIDI のどちらも使える（本文 10-2）。どちらを使うかは実機で決める

## 7. KRONOS（AL-1）との対応（レシピを作るときの目安）

| 役割 | KRONOS AL-1 | PC3A8（KVA） | 違い |
| --- | --- | --- | --- |
| 波形 | OSC1 Waveform | ALG の発振器ブロック（SAW / SQUARE / SINE / PWM、TRI はエイリアスあり版のみ） | PC3A8 は**正弦波を選べる** |
| フィルター | Filter A Type / Frequency / Resonance | 発振器の後ろのフィルターブロック（LOPASS など）、LP Frq / LP Res | 単位と範囲は要確認 |
| フィルターの時間変化 | Filter EG + EG Intensity | DSPMOD で LP Frq の Src1 に ENV2 を割り当て、Depth を設定 | 割り当て方式 |
| 音量エンベロープ | Amp EG（0〜99 の目盛り） | AMPENV User（秒と %） | 単位が違う。区間が多い |
| ノイズ | Mixer Noise Level | NOISE / LPNOIZ / RES NOISE ブロック | 別の発振器として置く |
