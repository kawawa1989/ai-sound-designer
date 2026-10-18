# kronos 資料インデックス

`scripts/convert_manuals.py` で自動生成。手で編集しない。

- 調べるときは、まずこの表で章を絞り、`text/` 以下を grep する。
- 各ページの先頭に `<!-- page: PDF p.N 本文p.M -->` がある。出典は本文ページで書く（マニュアル内の「→ p.xxx」も本文ページ）。
- 図・表・画面写真は抽出されないので、必要なら元PDFの該当 PDF ページを Read する。
- `text/` と元PDFは著作物のため git 管理外。無ければ `uv run python scripts/convert_manuals.py manuals/kronos` で再生成する。

### KRONOS_ExternalSetup

- 元PDF: `KRONOS_ExternalSetup.pdf`（7ページ）

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [KRONOS_ExternalSetup.md](text/KRONOS_ExternalSetup/KRONOS_ExternalSetup.md) | KRONOS_ExternalSetup | 1–7 |  |

### KRONOS_Operation_Guide

- 元PDF: `KRONOS_Operation_Guide.pdf`（314ページ）
- 本文ページ番号 = PDFページ番号 - 6

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [00-前付け目次.md](text/KRONOS_Operation_Guide/00-前付け目次.md) | 前付け・目次 | 1–6 |  |
| [01-はじめに.md](text/KRONOS_Operation_Guide/01-はじめに.md) | はじめに | 7–38 | 1–32 |
| [02-プログラムの演奏とエディット.md](text/KRONOS_Operation_Guide/02-プログラムの演奏とエディット.md) | プログラムの演奏とエディット | 39–74 | 33–68 |
| [03-コンビネーションの演奏とエディット.md](text/KRONOS_Operation_Guide/03-コンビネーションの演奏とエディット.md) | コンビネーションの演奏とエディット | 75–92 | 69–86 |
| [04-ソングの制作_Sequencer_モード.md](text/KRONOS_Operation_Guide/04-ソングの制作_Sequencer_モード.md) | ソングの制作（ Sequencer モード） | 93–138 | 87–132 |
| [05-セットリスト.md](text/KRONOS_Operation_Guide/05-セットリスト.md) | セット・リスト | 139–152 | 133–146 |
| [06-サンプリング_オープンサンプリングシステム.md](text/KRONOS_Operation_Guide/06-サンプリング_オープンサンプリングシステム.md) | サンプリング（オープン・サンプリング・システム） | 153–188 | 147–182 |
| [07-KRONOS_全体に関する設定.md](text/KRONOS_Operation_Guide/07-KRONOS_全体に関する設定.md) | KRONOS 全体に関する設定 | 189–216 | 183–210 |
| [08-CD_の作成.md](text/KRONOS_Operation_Guide/08-CD_の作成.md) | CD の作成 | 217–236 | 211–230 |
| [09-エフェクトの設定.md](text/KRONOS_Operation_Guide/09-エフェクトの設定.md) | エフェクトの設定 | 237–252 | 231–246 |
| [10-KARMA_機能.md](text/KRONOS_Operation_Guide/10-KARMA_機能.md) | KARMA 機能 | 253–274 | 247–268 |
| [11-ドラムトラック機能.md](text/KRONOS_Operation_Guide/11-ドラムトラック機能.md) | ドラムトラック機能 | 275–284 | 269–278 |
| [12-付_録.md](text/KRONOS_Operation_Guide/12-付_録.md) | 付 録 | 285–314 | 279–308 |

節（本文ページ）:

- **はじめに**: 各部の名称と機能 (p.1), 基礎知識 (p.14), セットアップ (p.21), アップデート情報 (p.27)
- **プログラムの演奏とエディット**: プログラムの演奏 (p.33), プログラムの簡易エディット (p.45), クイック・レイヤー / スプリット機能 (p.49), プログラムの詳細なエディット (p.54)
- **コンビネーションの演奏とエディット**: コンビネーションの演奏 (p.69), コンビネーションの簡単なエディット (p.72), クイック・レイヤー / スプリット機能 (p.74), コンビネーションの詳細なエディット (p.78)
- **ソングの制作（ Sequencer モード）**: ソングのプレイバック（再生） (p.89), MIDI トラック・レコーディング (p.93), オーディオ・レコーディング (p.108), ソング編集（エディット） (p.123), RPPR の作成とレコーディング方法 (p.125), Sequencer モードでのサンプリング (p.129), ソングを保存する (p.129), Sequencer モードでの注意とその他の機能 (p.130)
- **セット・リスト**: サウンドの選択と演奏 (p.134), セット・リストの作成 (p.137), スムーズ・サウンド・トランジション（ SST ） (p.145)
- **サンプリング（オープン・サンプリング・システム）**: サンプリングの準備 (p.150), Sampling モードでのサンプリングとエディット (p.155), Program, Combination モードでのサンプリング (p.170), Sequencer モードでのサンプリング (p.174), Banks ） (p.177)
- **KRONOS 全体に関する設定**: グローバル・セッティング (p.184), サンプル・データを自動的にロードする (p.191), FTP 経由でコンピューターに接続する (p.195), ウェーブ・シーケンスのエディット (p.196), ドラムキットのエディット (p.206)
- **CD の作成**: データの保存 (p.211), データのロード (p.220), オーディオ CD の作成、再生 (p.227), その他の Disk モードの機能 (p.229)
- **エフェクトの設定**: エフェクトの入出力 (p.232), ルーティングとエフェクト設定 (p.235), エフェクトの詳細なエディット (p.243)
- **KARMA 機能**: KARMA 機能を使って演奏する (p.250), する (p.253), KARMA 機能の設定 (p.256), Sequencer モードでの KARMA 機能の設定 (p.265), KARMA 機能の同期について (p.267)
- **ドラムトラック機能**: ドラムトラック機能を使って演奏する (p.270), ドラムトラック機能の設定 (p.273), ドラムトラック・パターンの作成方法 (p.277)
- **付 録**: 故障とお思いになる前に (p.279), 各種メッセージ (p.289), ディスク、メディア情報 (p.299)

### KRONOS_Parameter_Guide

- 元PDF: `KRONOS_Parameter_Guide.pdf`（1164ページ）
- 本文ページ番号 = PDFページ番号 - 12

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [00-前付け目次.md](text/KRONOS_Parameter_Guide/00-前付け目次.md) | 前付け・目次 | 1–12 |  |
| [01-Program_モード_HD-1.md](text/KRONOS_Parameter_Guide/01-Program_モード_HD-1.md) | Program モード : HD-1 | 13–182 | 1–170 |
| [02-Program_モード_EXi.md](text/KRONOS_Parameter_Guide/02-Program_モード_EXi.md) | Program モード : EXi | 183–200 | 171–188 |
| [03-EXi_AL-1_Analog_Synthesizer.md](text/KRONOS_Parameter_Guide/03-EXi_AL-1_Analog_Synthesizer.md) | EXi: AL-1 Analog Synthesizer | 201–242 | 189–230 |
| [04-EXi_CX-3_Tonewheel_Organ.md](text/KRONOS_Parameter_Guide/04-EXi_CX-3_Tonewheel_Organ.md) | EXi: CX-3 Tonewheel Organ | 243–268 | 231–256 |
| [05-EXi_STR-1_Plucked_String.md](text/KRONOS_Parameter_Guide/05-EXi_STR-1_Plucked_String.md) | EXi: STR-1 Plucked String | 269–314 | 257–302 |
| [06-EXi_MS-20EX.md](text/KRONOS_Parameter_Guide/06-EXi_MS-20EX.md) | EXi: MS-20EX | 315–342 | 303–330 |
| [07-EXi_PolysixEX.md](text/KRONOS_Parameter_Guide/07-EXi_PolysixEX.md) | EXi: PolysixEX | 343–356 | 331–344 |
| [08-EXi_MOD-7_Waveshaping_VPM_Synthesizer.md](text/KRONOS_Parameter_Guide/08-EXi_MOD-7_Waveshaping_VPM_Synthesizer.md) | EXi: MOD-7 Waveshaping VPM Synthesizer | 357–408 | 345–396 |
| [09-EXi_SGX-2_Premium_Piano.md](text/KRONOS_Parameter_Guide/09-EXi_SGX-2_Premium_Piano.md) | EXi: SGX-2 Premium Piano | 409–418 | 397–406 |
| [10-EXi_EP-1_MDS_Electric_Piano.md](text/KRONOS_Parameter_Guide/10-EXi_EP-1_MDS_Electric_Piano.md) | EXi: EP-1 MDS Electric Piano | 419–436 | 407–424 |
| [11-Combination_モード.md](text/KRONOS_Parameter_Guide/11-Combination_モード.md) | Combination モード | 437–540 | 425–528 |
| [12-Sequencer_モード.md](text/KRONOS_Parameter_Guide/12-Sequencer_モード.md) | Sequencer モード | 541–692 | 529–680 |
| [13-Set_List_モード.md](text/KRONOS_Parameter_Guide/13-Set_List_モード.md) | Set List モード | 693–704 | 681–692 |
| [14-Sampling_モード.md](text/KRONOS_Parameter_Guide/14-Sampling_モード.md) | Sampling モード | 705–776 | 693–764 |
| [15-Global_モード.md](text/KRONOS_Parameter_Guide/15-Global_モード.md) | Global モード | 777–838 | 765–826 |
| [16-Disk_モード.md](text/KRONOS_Parameter_Guide/16-Disk_モード.md) | Disk モード | 839–880 | 827–868 |
| [17-Effect_Guide.md](text/KRONOS_Parameter_Guide/17-Effect_Guide.md) | Effect Guide | 881–1032 | 869–1020 |
| [18-KARMA_GE_Guide.md](text/KRONOS_Parameter_Guide/18-KARMA_GE_Guide.md) | KARMA GE Guide | 1033–1098 | 1021–1086 |
| [19-付_録.md](text/KRONOS_Parameter_Guide/19-付_録.md) | 付 録 | 1099–1164 | 1087–1152 |

節（本文ページ）:

- **Program モード : HD-1**: 0–1: Main (p.2), Quick Layer (p.7), Quick Split (p.10), 0–2: Performance Meters (p.12), 0–6: KARMA GE (p.14), 0–7: Controller View/Effect (p.18), 0–8: Audio Input/Sampling (p.19), 0–9: Control Surface (p.26), 1–1: Program Basic (p.39), 1–3: Drum Track (p.45), 1–5: Vector Control (p.49), 1–6: Vector Envelope (p.53), 1–8: Set Up Controllers (p.56), 1–9: Pads (p.57), 2–1: OSC1 Basic (p.59), 2–2: OSC1 Pitch (p.65), 2–5: OSC2 Basic (p.67), 2–6: OSC2 Pitch (p.67), 2–9: Pitch EG (p.68), 3–1: Filter1 (p.71), 3–2: Filter1 Modulation (p.74), 3–3: Filter1 LFO Modulation (p.78), 3–4: Filter1 EG (p.80), 3–5: Filter2 (p.83), 3–6: Filter2 Modulation (p.83), 3–7: Filter2 LFO Modulation (p.83), 3–8: Filter2 EG (p.83), 4–1: Amp1/Driver1 (p.84), 4–2: Amp1 Modulation (p.86), 4–3: Amp1 EG (p.89), 4–5: Amp2/Driver2 (p.91), 4–6: Amp2 Modulation (p.92), 4–7: Amp2 EG (p.92), 4–9: EQ (p.93), 5–1: OSC1 LFO1 (p.94), 5–2: OSC1 LFO2 (p.97), 5–5: OSC2 LFO1 (p.97), 5–6: OSC2 LFO2 (p.97), 5–9: Common LFO (p.98), 6–1: OSC1 AMS Mixer (p.100), 6–5: OSC 2 AMS Mix (p.106), 6–9: Common Keyboard Track (p.107), 7–1: GE Setup/Key Zones (p.109), 7–2: MIDI Filter/CC Offset (p.111), 7–3: Module Parameters-Control (p.114), 7–4: Module Parameters-Trigger (p.119), 7–5: GE Real-Time Parameters/Scenes (p.122), 7–6: Perf Real-Time Parameters (p.125), 7–7: Dynamic MIDI (p.129), 7–8: Random Seeds (p.131), 7–9: Name/Note Map (p.134), 8–1: Routing (p.136), 8–5: Insert FX (p.139), 8–6: Track View (p.142), 8–7: IFX 1–12 (p.143), 8–9: Common FX LFO (p.145), 9–1: Routing (p.147), 9–2: MFX1 (p.150), 9–3: MFX2, 9–4: TFX1, 9–5: TFX2 (p.150)
- **Program モード : EXi**: 0–1: Main (p.171), 0–2: Performance Meters (p.172), 0–6: KARMA GE (p.172), 0–7: Controller View/Effect (p.173), 0–8: Audio Input/Sampling (p.173), 0–9: Control Surface (p.173), 4–1: Program Basic (p.174), 4–2: EXi Audio Input (p.179), 4–3: Drum Track (p.180), 4–5: Vector Control (p.180), 4–6: Vector Envelope (p.180), 4–8: Set Up Controllers (p.180), 4–9: Pads (p.181), 5–1: Common Step Sequencer (p.182), 5–2: Common LFO (p.185), 5–3: Common Keyboard Track (p.185)
- **EXi: AL-1 Analog Synthesizer**: 0–1: Main (p.190), 4–1: OSC Basic (p.192), 4–2: Sub/Noise/Ring Mod (p.195), 4–3: Mixer (p.197), 4–4: Pitch Common (p.199), 4–5: Pitch EG/Mod (p.201), 5–1: Basic (p.203), 5–2: Multi Filter (p.206), 5–3: Filter Modulation (p.208), 5–4: Filter LFO Mod (p.210), 6–1: Amp/Driver (p.211), 6–2: Amp Modulation (p.213), 6–3: Amp EG (p.215), 7–1: EG 1 (Filter) (p.217), 7–2: EG 2 (Pitch) (p.220), 7–3: EG 3 (p.220), 7–4: EG 4 (p.220), 8–1: Step Sequencer (p.221), 8–2: LFO 1 (p.224), 8–3: LFO 2 (p.226), 8–4: LFO 3 (p.226), 8–5: LFO 4 (p.226), 9–1: AMS Mixer (p.227), トーン・アジャスト機能 (p.228)
- **EXi: CX-3 Tonewheel Organ**: 0–1: Main (p.233), 4–1: Basic (p.236), 4–2: Controllers (p.238), 5–1: Keyboard Split (p.240), 5–2: Drawbars (p.241), 5–3: EX Drawbars (p.243), 6–1: Percussion (p.244), 6–2: EX Percussion (p.246), 7–1: Amp/Vibrato/Chorus (p.247), 7–2: Rotary Speaker (p.250), 9–1: AMS Mixer (p.253), トーン・アジャスト機能 (p.254), コルグ Combo Organ CX-3 との相違点 (p.255)
- **EXi: STR-1 Plucked String**: 0–1: Main (p.259), 4–1: Pluck and Noise (p.261), 4–2: PCM Oscillator (p.263), 4–3: PCM Oscillator Pitch (p.266), 4–4: Excitation Mixer (p.269), 4–5: String Main (p.271), 4–6: Damping and Dispersion (p.274), 4–7: String Pitch (p.276), 4–8: Pickups and Feedback (p.279), 4–9: Mixer (p.281), 5–1: Basic (p.283), 5–2: Multi Filter (p.286), 5–3: Filter Mod (p.288), 5–4: Filter LFO Mod (p.290), 6–1: Amp (p.291), 6–2: Amp Modulation (p.293), 6–3: Amp EG (p.295), 7–1: EG 1 (Filter) (p.297), 7–2: EG 2 (Pitch) (p.297), 7–3: EG 3 (p.297), 7–4: EG 4 (p.297), 8–1: LFO 1 (p.297), 8–2: LFO 2 (p.297), 8–3: LFO 3 (p.297), 8–4: LFO 4 (p.297), 9–1: AMS Mixers 1–2 (p.298), 9–2: AMS Mixers 3–4 (p.298), 9–9: String Track (p.298), トーン・アジャスト機能 (p.300)
- **EXi: MS-20EX**: ディスプレイ上のノブとパラメーター・ディテール・エリア (p.304), 0–1: Main (p.305), 4-1: Oscillators & Filters (p.307), 5–1: MG, EG, & Modulation (p.311), 目 次 Program P6: Patch Panel (p.315), 6–1: Patch Panel (p.315), 7–1: EG 3 (p.325), 7–2: EG 4 (p.325), 7–3: EG 5 (p.325), 7–4: EG 6 (p.325), 8–1: LFO 1 (p.325), 8–2: LFO 2 (p.325), 8–3: LFO 3 (p.325), 8–4: LFO 4 (p.325), 9–1: AMS Mixers 1–2 (p.326), 9–2: AMS Mixers 3–4 (p.326), トーン・アジャスト機能 (p.327)
- **EXi: PolysixEX**: ディスプレイ上のノブとパラメーター・ディテール・エリア (p.332), 0–1: Main (p.333), 4–1: Patch Panel (p.335), 5–1: Modulation & Arpeggiator (p.339), 7–1: EG 2 (p.341), 7–2: EG 3 (p.341), 8–1: LFO 1 (p.341), 8–2: LFO 2 (p.341), 9–1: AMS Mixers 1–2 (p.342), 9–2: AMS Mixers 3–4 (p.342), トーン・アジャスト機能 (p.343)
- **EXi: MOD-7 Waveshaping VPM Synthesizer**: オシレーターと減算合成 (p.350), VPM (FM) (p.351), フィルターと VPM (p.353), PCM を VPM モジュレーターとして使う (p.354), ウェーブシェーピング (p.355), リング・モジュレーション (p.357), 0–1: Main (p.358), 4–1: Patch Panel (p.360), 5–1: Osc Main (p.364), 5–2: PCM Osc (p.368), 5–3: PCM Mod (p.370), 5–4: VPM Osc 1 (p.373), 5–5: VPM Osc 2 (p.383), 5–6: VPM Osc 3 (p.383), 5–7: VPM Osc 4 (p.383), 5–8: VPM Osc 5 (p.383), 5–9: VPM Osc 6 (p.383), 6–1: Basic (p.384), 6–2 ： Multi Filter (p.384), 6–3 ： Filter Modulation (p.384), 6–4 ： Filter LFO Modulation (p.384), 7–1: Mixers 1–3 (p.385), 7–2: Output Mixer (p.387), 7–3: Amp (p.388), 7–4: Amp Mod (Amp Modulation) (p.388), 7–5: Amp EG (p.388), 8–1: EG1 (p.389), 8–2: EG 2 (p.392), 8–3: EG 3 (p.392), 8–4: EG 4 (p.392), 8–5: EG 5 (p.392), 8–6: EG 6 (p.392), 8–7: EG 7 (p.392), 8–8: EG 8 (p.392), 8–9: EG 9 (p.392), 9-1: Step Sequencer (p.393), 9-2: LFO 1 (p.393), 9-3: LFO 2 (p.393), 9-4: LFO 3 (p.393), 9-5: LFO 4 (p.393), 9-6: AMS Mixers 1-2 (p.393), 9-7: AMS Mixers 3-4 (p.393), 9-8: AMS Mixers 5-6 (p.393), 9-9: AMS Mixers 7-8 (p.393), トーン・アジャスト機能 (p.394)
- **EXi: SGX-2 Premium Piano**: 0–1: Main (p.398), 4–1: Main (p.400), 5–1: String Resonance/Una Corda (p.402), 目 次トーン・アジャスト機能 (p.404)
- **EXi: EP-1 MDS Electric Piano**: ディスプレイ上のノブ、スライダー、スイッチとパラメーター・ディテール (p.408), 0–1: Main (p.409), P4–1: Basic (p.411), P4–2: Oscillator (p.413), Common (p.415), Tine EP (p.416), Reed EP (p.418), Insert Effects (p.419), トーン・アジャスト機能 (p.423)
- **Combination モード**: 0–1: Program Select/Mixer (p.425), Quick Layer (p.432), Quick Split (p.435), 0–2: Performance Meters (p.437), 0–6: KARMA GE (p.438), 0–7: Controller View/Effect (p.441), 0–8: Audio Input/Sampling (p.442), 0–9: Control Surface (p.444), 1–1: Timbre EQ (p.455), 1–3: DrumTrack (p.457), 1–5: Vector Volume Control (p.459), 1–6: Vector CC Control (p.462), 1–7: Vector Envelope (p.465), 1–8: Set Up Controllers (p.468), 1–9: Pads (p.469), 2–1: MIDI (p.471), 2–2: OSC (p.472), 2–3: Pitch (p.474), 2–4: Delay (p.476), 2–5: Wave Sequence/KARMA (p.477), 2–6: EXi Audio Input (p.479), 3–1: MIDI Filter1 (p.480), 3–2: MIDI Filter2 (p.482), 3–3: MIDI Filter3 (p.483), 3–5: Keyboard Zones (p.484), 3–6: Velocity Zones (p.486), 7–1: GE Setup/Key Zones (p.488), 7–2: MIDI Filter/CC Offset (p.492), 7–3: Module Parameters-Control (p.494), 7–4: Module Parameters-Trigger (p.495), 7–5: GE Real-Time Parameters/Scenes (p.497), 7–6: Perf Real-Time Parameters (p.501), 7–7: Dynamic MIDI (p.503), 7–8: Random Seeds (p.504), 7–9: Name/Note Map (p.506), 8–1: Routing1 (p.508), 8–2: Routing2 (p.511), 8–5: Insert FX (p.512), 8–6: Track View (p.513), 8–7: IFX 1–12 (p.514), 8–9: Common FX LFO (p.516), 9–1: Routing (p.517), 9–2: MFX1 (p.518), 9–3: MFX2, 9–4: TFX1, 9–5: TFX2 (p.519)
- **Sequencer モード**: シーケンサー概要 (p.529), MIDI シーケンサー部 (p.529), 設定パラメーター／演奏データ (p.531), Auto Song Setup (p.532), 0–1: MIDI Track Prog Select/Mixer (p.533), 0–2: Audio Track Mixer (p.539), 0–3: MIDI Track Loop (p.544), 0–4: Performance Meters (p.545), 0–5: Preferences (p.546), 0–6: KARMA GE (p.550), 0–7: Controller View/Effect (p.552), 0–8: Audio In/Sampling (p.553), 0–9: Control Surface (p.555), 1–1: MIDI Track EQ (p.567), 1–2: Audio Track EQ (p.569), 1–3: DrumTrack (p.570), 1–5: Vector Volume Control (p.572), 1–6: Vector CC Control (p.575), 1–7: Vector Envelope (p.578), 1–8: Set Up Controllers (p.581), 1–9: Pads (p.582), 2–1: MIDI (p.584), 2–2: OSC (p.586), 2–3: Pitch (p.588), 2–4: Delay (p.590), 2–5: Wave Sequence/KARMA (p.591), 2–6: EXi Audio Input (p.593), 2–7: Audio Track Delay (p.594), 3–1: MIDI Filter1 (p.595), 3–2: MIDI Filter2 (p.597), 3–3: MIDI Filter3 (p.598), 3–5: Keyboard Zones (p.599), 3–6: Velocity Zones (p.601), 目 次 Sequencer P4: Track Edit (p.603), 4–1: Track Edit (p.603), 4–2: MIDI Track Name (p.605), 4–3: AUDIO Track Name (p.606), 5–1: Pattern Edit (p.607), 5–2: Pattern Name (p.609), 5–3: RPPR Setup (p.610), 7–1: GE Setup/Key Zones (p.614), 7–2: MIDI Filter/CC Offset (p.618), 7–3: Module Parameters-Control (p.619), 7–4: Module Parameters-Trigger (p.620), 7–5: GE Real-Time Parameters/Scenes (p.621), 7–6: Perf Real-Time Parameters (p.623), 7–7: Dynamic MIDI (p.624), 7–8: Random Seeds (p.625), 7–9: Name/Note Map (p.626), 8–1: MIDI Routing1 (p.628), 8–2: MIDI Routing2 (p.630), 8–3: Audio Routing1 (p.632), 8–4: Audio Routing2 (p.634), 8–5: Insert FX (p.635), 8–6: Track View (p.637), 8–7: IFX 1–12 (p.638), 8–9: Common FX LFO (p.640), 9–1: Routing (p.641), 9–2: MFX1 (p.642), 9–3: MFX2, 9–4: TFX1, 9–5: TFX2 (p.643)
- **Set List モード**: セット・リスト概要 (p.681), 0–1: Play (p.682), 1–1: Edit (p.686)
- **Sampling モード**: サンプリング概要 (p.693), RAM メモリーまたはディスクへのサンプリング (p.693), サンプリングの特長 (p.694), 0–1: Recording (p.696), 0–8: Audio Input (p.702), 0–9: Control Surface (p.708), 1–1: Sample Edit (p.715), 2–1: Loop Edit (p.718), 3–1: Multisample Edit (p.721), 4–1: EQ (p.723), 4–8: Set Up Controllers (p.725), 4–9: Pads (p.727), 5–1: Ripping (p.728), 8–1: Routing (p.730), 8–5: Insert FX (p.732), 8–6: Track View (p.734), 8–7: IFX 1–12 (p.735), 8–9: Common FX LFO (p.736), 9–1: Routing (p.737), 9–2: MFX1 (p.739), 9–3: MFX2, 9–4: TFX1, 9–5: TFX2 (p.740)
- **Global モード**: 0–1: Basic (p.765), 0–2: Audio Input (p.772), 0–3: KSC Auto-Load (p.775), 0–4: Sample Management (p.778), 0–5: Network (p.780), 1–1: MIDI (p.783), 1–2: External 1 (p.789), 1–3: External 2 (p.791), 2–1: Controller (p.792), 2–2: User Scale (p.794), 2–3: Function Assign (p.795), 3–1: Program Category (p.797), 3–2: Combi Category (p.798), 3–3: KARMA Category (p.798), 4–1: Sequence Parameters (p.799), 4–2: Step Parameters (p.803), 5–1: Sample Setup (p.807), 5–2: Sample Parameters (p.810), 5–3: Voice Assign/Mixer (p.812), 6–1: Options Info (p.814), 目 次 Global: Page Menu Command (p.816)
- **Disk モード**: 0–1: Load (p.829), 0–2: Save (p.831), 0–3: Utility (p.832), 0–9: Media Information (p.833), 1–1: Make Audio CD (p.834), 1–2: Play Audio CD (p.836), 1–9: Media Information (p.837)
- **Effect Guide**: エフェクト概要 (p.869), 1. 各モードでのエフェクトについて (p.870), 2. ダイナミック・モジュレーション（ Dmod ） (p.871), 3. Common FX LFO (p.871), 4. FX Control Bus (p.871), 5. エフェクトの入出力について (p.874), インサート・エフェクト (p.875), 1. イン／アウト（ In/Out ） (p.875), 2. ルーティング（ Routing ） (p.876), 3. ミキサー（ Mixer ） (p.883), ル (p.885), マスター・エフェクト（ MFX1, 2 ） (p.886), 1. イン／アウト（ In/Out ） (p.886), 2. ルーティング（ Routing ） (p.887), 3. ミキサー（ Mixer ） (p.890),  (p.890), トータル・エフェクト（ TFX1, 2 ） (p.891), 1. イン／アウト（ In/Out ） (p.891), 2. ルーティング（ Routing ） (p.891), 3. ミキサー（ Mixer ） (p.892), 4. トータル・エフェクトの MIDI によるコントロール (p.892), 000: NoEffect (p.897), 001: Stereo Dyna Compressor (p.897), 002: Stereo Compressor (p.898), 003: Stereo Expander (p.900), 004: St. Multiband Compressor (p.901), 005: Stereo Limiter (p.903), 006: Multiband Limiter (p.904), 007: Stereo Multiband Limiter (p.905), 008: Stereo Mastering Limiter (p.905), 009: Stereo Gate (p.906), 010: Stereo Noise Reduction (p.907), 4. マスター・エフェクトの MIDI によるコントロール 011: Stereo Parametric 4EQ (p.908), 012: Stereo Graphic 7EQ (p.909), 013: Stereo Master 3EQ (p.910), 014: Stereo Exciter/Enhancer (p.910), 015: Stereo Isolator (p.911), 016: Stereo Wah/Auto Wah (p.912), 017: St. Vintage/Custom Wah (p.913), 018: Stereo Random Filter (p.914), 019: Stereo Multi Mode Filter (p.915), 020: Stereo Sub Oscillator (p.916), 021: Talking Modulator (p.917), 022: Stereo Decimator (p.918), 023: Stereo Analog Record (p.919), 024: Stereo Wave Shaper (p.920), 025: Piano Body/Damper (p.921), 026: Vocoder (p.922), 027: OD/Hi-Gain Wah (p.923), 028: OD/Hyper-Gain Wah (p.924), 029: Stereo Guitar Cabinet (p.924), 030: Guitar AmpModel+P4EQ (p.925), 031: Guitar Amp Model +Cabinet (p.926), 032: Stereo Bass Cabinet (p.927), 033: Bass Amp Model (p.927), 034: Bass Amp Model +Cabinet (p.928), 035: Bass Amp TubeDrive +Cab (p.929), 036: Tube PreAmp Modeling (p.929), 037: St. Tube PreAmp Modeling (p.929), 038: Mic Modeling +PreAmp (p.930), 039: St. Mic Modeling +PreAmp (p.930), 040: Stereo Chorus (p.931), 041: Stereo Harmonic Chorus (p.932), 042: St. Bi-phase Modulation (p.932), 043: Multitap Cho/Delay 4Taps (p.933), 044: Multitap Cho/Delay 6Taps (p.934), 045: Bi Chorus (p.935), 046: Ensemble (p.936), 047: Polysix Ensemble (p.936), 048: Stereo Flanger (p.937), 049: Stereo Random Flanger (p.937), 050: Stereo Envelope Flanger (p.938), 051: Stereo Phaser (p.939), 052: Stereo Random Phaser (p.940), 053: Stereo Envelope Phaser (p.940), 054: Bi Phaser (p.941), 055: Stereo Vibrato (p.942), 056: Stereo Auto Fade Mod (p.943), 057: 2-Voice Resonator (p.944), 058: Doppler (p.945), 059: Scratch (p.946), 060: Grain Shifter (p.947), 061: Stereo Tremolo (p.947), 062: Stereo Envelope Tremolo (p.948), 063: Stereo Auto Pan (p.949), 064: Stereo Phaser+Tremolo (p.950), 065: Stereo Ring Modulator (p.951), 066: Stereo Frequency Shifter (p.952), 067: Detune (p.952), 068: Pitch Shifter (p.953), 069: Stereo Pitch Shifter (p.954), 070: Pitch Shifter BPM (p.954), 071: Stereo Pitch Shifter BPM (p.955), 072: Pitch Shift Mod (p.956), 073: Organ Vibrato/Chorus (p.957), 074: Rotary Speaker (p.958), 075: Rotary Speaker Pro OD (p.959), 076: Rotary Speaker Pro CX (p.960), 077: L/C/R Delay (p.962), 078: L/C/R Long Delay (p.962), 079: Stereo/Cross Delay (p.963), 080: Stereo/Cross Long Delay (p.963), 081: Stereo Multitap Delay (p.964), 082: Stereo Modulation Delay (p.965), 083: Stereo Dynamic Delay (p.966), 084: Stereo Auto Panning Delay (p.967), 085: Tape Echo (p.968), 086: Multiband Mod. Delay (p.969), 087: Reverse Delay (p.971), 088: Hold Delay (p.972), 089: Auto Reverse (p.973), 090: Sequence BPM Delay (p.973), 091: L/C/R BPM Delay (p.974), 092: L/C/R BPM Long Delay (p.974), 093: Stereo BPM Delay (p.975), 094: Stereo BPM Long Delay (p.975), 095: Stereo BPM Multitap Delay (p.976), 096: Stereo BPM Mod. Delay (p.977), 097: St. BPM Auto Panning Dly (p.978), 098: Tape Echo BPM (p.979), 099: Reverse BPM Delay (p.980), 100: O-verb (p.981), 101: Reverb Hall (p.981), 102: Reverb Smooth Hall (p.981), 103: Reverb Wet Plate (p.981), 104: Reverb Dry Plate (p.982), 105: Reverb Room (p.982), 106: Reverb Bright Room (p.982), 107: Early Reflections (p.983), 108: Early Reflections Hi Dens (p.983), 109: P4EQ - Exciter (p.984), 110: P4EQ - Wah (p.984), 111: P4EQ - Chorus/Flanger (p.985), 112: P4EQ - Phaser (p.985), 113: P4EQ - Multitap Delay (p.986), 114: Comp - Wah (p.986), 115: Comp - Amp Sim (p.987), 116: Comp - OD/Hi Gain (p.987), 117: Comp - P4EQ (p.988), 118: Comp - Chorus/Flanger (p.988), 119: Comp - Phaser (p.989), 120: Comp - Multitap Delay (p.989), 121: Limiter - P4EQ (p.990), 122: Limiter - Chorus/Flanger (p.990), 123: Limiter - Phaser (p.991), 124: Limiter - Multitap Delay (p.991), 125: Exciter - Comp (p.992), 126: Exciter - Limiter (p.992), 127: Exciter - Chorus/Flanger (p.993), 128: Exciter - Phaser (p.993), 129: Exciter - Multitap Delay (p.994), 130: OD/Hi Gain - Amp Sim (p.994), 131: OD/Hi Gain - Cho/Flanger (p.995), 132: OD/Hi Gain - Phaser (p.995), 133: OD/Hi Gain - Multitap Dly (p.996), 134: Wah - Amp Sim (p.996), 135: Decimator - Amp Sim (p.997), 136: Decimator - Comp (p.997), 137: Amp Sim - Tremolo (p.998), 138: Cho/Flanger - Multitap Dly (p.998), 139: Phaser - Chorus/Flanger (p.999), 140: Reverb - Gate (p.1000), 141: P4EQ // P4EQ (p.1002), 142: P4EQ // Comp (p.1002), 143: P4EQ // Limiter (p.1003), 144: P4EQ // Exciter (p.1003), 145: P4EQ // OD/Hi Gain (p.1003), 146: P4EQ // Wah (p.1003), 147: P4EQ // Chorus/Flanger (p.1003), 148: P4EQ // Phaser (p.1003), 149: P4EQ // Multitap BPM Dly (p.1004), 150: Comp // Comp (p.1004), 151: Comp // Limiter (p.1004), 152: Comp // Exciter (p.1004), 153: Comp // OD/Hi Gain (p.1004), 154: Comp // Wah (p.1004), 155: Comp // Chorus/Flanger (p.1005), 156: Comp // Phaser (p.1005), 157: Comp // Multitap BPM Dly (p.1005), 158: Limiter // Limiter (p.1005), 159: Limiter // Exciter (p.1005), 160: Limiter // OD/Hi Gain (p.1005), 161: Limiter // Wah (p.1006), 162: Limiter // Chorus/Flanger (p.1006), 163: Limiter // Phaser (p.1006), 164: Limiter // Mtap BPM Dly (p.1006), 165: Exciter // Exciter (p.1006), 166: Exciter // OD/Hi Gain (p.1006), 167: Exciter // Wah (p.1007), 168: Exciter // Chorus/Flanger (p.1007), 169: Exciter // Phaser (p.1007), 170: Exciter // Mtap BPM Dly (p.1007), 171: OD/Hi Gain // OD/Hi Gain (p.1007), 172: OD/Hi Gain // Wah (p.1007), 173: OD/Hi Gain // Cho/Flanger (p.1008), 174: OD/Hi Gain // Phaser (p.1008), 175: OD/Hi Gain // Mt BPM Dly (p.1008), 176:Wah // Wah (p.1008), 177: Wah // Chorus/Flanger (p.1008), 178: Wah // Phaser (p.1008), 179: Wah // Multitap BPM Dly (p.1009), 180: Cho/Flange // Cho/Flanger (p.1009), 181: Cho/Flange // Phaser (p.1009), 182: Cho/Flange // Mt BPM Dly (p.1009), 183: Phaser // Phaser (p.1009), 184: Phaser // Mtap BPM Dly (p.1009), 185: Mt.BPM Dly // Mt.BPM Dly (p.1010), 目 次 Vintage (p.1011), 186: Small Phase (p.1011), 187: Orange Phase (p.1011), 188: Black Phase (p.1012), 189: Vintage Chorus (p.1012), 190: Black Chorus (p.1013), 191: EP Chorus (p.1013), 192: Vintage Flanger (p.1014), 193: Red Comp (p.1014), 194: Vox Wah (p.1015), 195: Stereo EP Cabinet (p.1016), 196: Rotary Speaker Amp Model (p.1016), 197: Rotary Speaker Pro CX Custom (p.1018)
- **KARMA GE Guide**: GE ガイドについて (p.1021), 概要 (p.1023), KARMA 機能について (p.1023), KARMA Architecture (Diagram) (p.1024), GE Global Parameters (p.1025), 概要 (p.1028), Parameters (p.1028), 概要 (p.1032), フェイズ・パターンについて (p.1032), General Parameters (p.1032), Phase Specific Parameters (p.1034), End Loop Parameters (p.1035), Pattern Parameters (p.1035), 概要 (p.1037), リズム・パターンについて (p.1037), Global Parameters (p.1037), Pattern Grid & Associated Parameters (p.1038), Random Weighting Parameters - Pools (p.1038), Random Weighting Parameters - Ties (p.1039), Associated Parameters (p.1040), Template Parameters (p.1040), 概要 (p.1041), Pattern Grid & Associated Parameters (p.1041), Associated Parameters (p.1041), Random Weighting Parameters - Pools (p.1042), Random Weighting Parameters – Ties (p.1043), Associated Parameters (p.1043), 概要 (p.1044), インデックス・パターンについて (p.1044), Pattern Grid & Associated Parameters (p.1044), Associated Parameters (p.1044), Random Weighting Parameters (p.1045), Associated Parameters (p.1045), 概要 (p.1047), クラスター・パターンについて (p.1047), Pattern Grid & Associated Parameters (p.1047), Random Weighting Parameters (p.1047), Associated Parameters (p.1048), 概要 (p.1049), ベロシティ・パターンについて (p.1049), Global Parameters (p.1049), Pattern Grid & Associated Parameters (p.1050), Random Weighting Parameters - Pools (p.1050), Associated Parameters (p.1050), 概要 (p.1052), CC 、ベンド、ピッチ・パターンについて (p.1052), Pattern Grid & Associated Parameters (p.1052), Associated Parameters (p.1052), Random Weighting Parameters (p.1053), Global Parameters (p.1053), Associated Parameters (p.1054), 概要 (p.1055), ウェーブ・シーケンス・パターンについて (p.1055), Global Parameters (p.1055), Pattern Grid & Associated Parameters (p.1056), Random Weighting Parameters (p.1057), Associated Parameters (p.1057), 概要 (p.1058), エンベロープについて (p.1058), Parameters (p.1058), Level Combinations (p.1061), Time Combinations (p.1061), 概要 (p.1062), General Parameters (p.1062), Range Parameters (p.1064), GE Mode=Real-Time Parameters (p.1065), 概要 (p.1067), General Parameters (p.1067), GE Mode=Real-Time Parameters (p.1069), 概要 (p.1071), ドラム・パターンについて (p.1071), Pattern Editing Grid & Associated Parameters (p.1071), Associated Parameters (p.1071), Random Weighting Parameters - Pools (p.1073), Random Weighting Parameters − Rests (p.1073), Associated Parameters (p.1074), 概要 (p.1077), General Parameters (p.1077), Duration Parameters (p.1078), Repeat Parameters (p.1079), Bend Parameters (p.1079), 付 録 (p.1081), オート・ベンドについて (p.1081), Random Weighting Curves (p.1083)
- **付 録**: 概要 (p.1087), AMS List (p.1089), Alternate Modulation の設定 (p.1098), 概要 (p.1102), Dmod List (p.1103), コントローラー・アサイン (p.1105), SW1/2 Assign (p.1105), Realtime Knobs 5–8 Assign (p.1106), Foot Switch Assign (p.1107), Foot Pedal Assign (p.1108), Dynamic MIDI Sources (p.1109), Dynamic MIDI Destinations (p.1111), 本機コントローラー操作時の MIDI 送信 (p.1116), コントロール・チェンジ送受信時の本機の動作 (p.1118), MIDI について (p.1123), MIDI 機器 / コンピューターとの接続 (p.1123), USB MIDI コントローラー (p.1124), 本機が送受信する MIDI メッセージ (p.1125), コルグ・フォーマットのファイルについて (p.1137), OASYS.SNG ファイルの互換性 (p.1142), 本機のパケットライト・サポート (p.1142), コルグでの GPL および LGPL ソフトウェアの使用について (p.1144), AKAI Program ファイルについて (p.1144), SoundFont 2.0 ファイルについて (p.1144), システム・アップデート (p.1145), アクセサリー・ディスクを使ったシステムおよびファクトリー・サウンドの復旧 (p.1146)

### KRONOS_Quick_Start

- 元PDF: `KRONOS_Quick_Start.pdf`（29ページ）

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [KRONOS_Quick_Start.md](text/KRONOS_Quick_Start/KRONOS_Quick_Start.md) | p1-29 | 1–29 |  |

### KRONOS_Update_and_Restore

- 元PDF: `KRONOS_Update_and_Restore.pdf`（3ページ）

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [KRONOS_Update_and_Restore.md](text/KRONOS_Update_and_Restore/KRONOS_Update_and_Restore.md) | KRONOS_Update_and_Restore | 1–3 |  |

### KRONOS_VoiceNameList

- 元PDF: `KRONOS_VoiceNameList.pdf`（270ページ）
- 本文ページ番号 = PDFページ番号 - 0

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [00-前付け目次.md](text/KRONOS_VoiceNameList/00-前付け目次.md) | 前付け・目次 | 1–2 | 1–2 |
| [01-000_Preload_Set_List.md](text/KRONOS_VoiceNameList/01-000_Preload_Set_List.md) | 000: Preload Set List | 3–3 | 3–3 |
| [02-INT-A.md](text/KRONOS_VoiceNameList/02-INT-A.md) | INT-A | 4–4 | 4–4 |
| [03-INT-B.md](text/KRONOS_VoiceNameList/03-INT-B.md) | INT-B | 5–5 | 5–5 |
| [04-INT-C.md](text/KRONOS_VoiceNameList/04-INT-C.md) | INT-C | 6–6 | 6–6 |
| [05-INT-D.md](text/KRONOS_VoiceNameList/05-INT-D.md) | INT-D | 7–7 | 7–7 |
| [06-Bank_INT-A_EXi.md](text/KRONOS_VoiceNameList/06-Bank_INT-A_EXi.md) | Bank INT-A [EXi] | 8–8 | 8–8 |
| [07-Bank_INT-B_HD-1.md](text/KRONOS_VoiceNameList/07-Bank_INT-B_HD-1.md) | Bank INT-B [HD-1] | 9–9 | 9–9 |
| [08-Bank_INT-C_EXi.md](text/KRONOS_VoiceNameList/08-Bank_INT-C_EXi.md) | Bank INT-C [EXi] | 10–10 | 10–10 |
| [09-Bank_INT-D_EXi.md](text/KRONOS_VoiceNameList/09-Bank_INT-D_EXi.md) | Bank INT-D [EXi] | 11–11 | 11–11 |
| [10-Bank_INT-E_EXi.md](text/KRONOS_VoiceNameList/10-Bank_INT-E_EXi.md) | Bank INT-E [EXi] | 12–12 | 12–12 |
| [11-Bank_INT-F_EXi.md](text/KRONOS_VoiceNameList/11-Bank_INT-F_EXi.md) | Bank INT-F [EXi] | 13–13 | 13–13 |
| [12-Bank_USER-A_EXi.md](text/KRONOS_VoiceNameList/12-Bank_USER-A_EXi.md) | Bank USER-A [EXi] | 14–14 | 14–14 |
| [13-Bank_USER-B_EXi.md](text/KRONOS_VoiceNameList/13-Bank_USER-B_EXi.md) | Bank USER-B [EXi] | 15–15 | 15–15 |
| [14-Bank_USER-C_HD-1.md](text/KRONOS_VoiceNameList/14-Bank_USER-C_HD-1.md) | Bank USER-C [HD-1] | 16–16 | 16–16 |
| [15-Bank_USER-D_HD-1.md](text/KRONOS_VoiceNameList/15-Bank_USER-D_HD-1.md) | Bank USER-D [HD-1] | 17–17 | 17–17 |
| [16-Bank_USER-E_HD-1.md](text/KRONOS_VoiceNameList/16-Bank_USER-E_HD-1.md) | Bank USER-E [HD-1] | 18–18 | 18–18 |
| [17-Bank_USER-F_HD-1.md](text/KRONOS_VoiceNameList/17-Bank_USER-F_HD-1.md) | Bank USER-F [HD-1] | 19–19 | 19–19 |
| [18-Bank_USER-AA_HD-1.md](text/KRONOS_VoiceNameList/18-Bank_USER-AA_HD-1.md) | Bank USER-AA [HD-1] | 20–20 | 20–20 |
| [19-Bank_USER-BB_HD-1.md](text/KRONOS_VoiceNameList/19-Bank_USER-BB_HD-1.md) | Bank USER-BB [HD-1] | 21–21 | 21–21 |
| [20-Bank_GM_g_1_g_9_g_d.md](text/KRONOS_VoiceNameList/20-Bank_GM_g_1_g_9_g_d.md) | Bank GM / g(1)…g(9) / g(d) | 22–23 | 22–23 |
| [21-INT00_Trance_kit.md](text/KRONOS_VoiceNameList/21-INT00_Trance_kit.md) | INT00: Trance kit | 24–25 | 24–25 |
| [22-INT01_House_Kit.md](text/KRONOS_VoiceNameList/22-INT01_House_Kit.md) | INT01: House Kit | 26–27 | 26–27 |
| [23-INT02_Hard_House_Kit.md](text/KRONOS_VoiceNameList/23-INT02_Hard_House_Kit.md) | INT02: Hard House Kit | 28–29 | 28–29 |
| [24-INT03_Psycho_Chill_Kit.md](text/KRONOS_VoiceNameList/24-INT03_Psycho_Chill_Kit.md) | INT03: Psycho/Chill Kit | 30–31 | 30–31 |
| [25-INT04_Hip_Hop_Kit.md](text/KRONOS_VoiceNameList/25-INT04_Hip_Hop_Kit.md) | INT04: Hip Hop Kit | 32–33 | 32–33 |
| [26-INT05_Mashed_Kit.md](text/KRONOS_VoiceNameList/26-INT05_Mashed_Kit.md) | INT05: Mashed Kit | 34–35 | 34–35 |
| [27-INT06_Tricki_kit.md](text/KRONOS_VoiceNameList/27-INT06_Tricki_kit.md) | INT06: Tricki kit | 36–37 | 36–37 |
| [28-INT07_Electro_Rock_Kit.md](text/KRONOS_VoiceNameList/28-INT07_Electro_Rock_Kit.md) | INT07: Electro Rock Kit | 38–39 | 38–39 |
| [29-INT08_Nu_Style_Kit.md](text/KRONOS_VoiceNameList/29-INT08_Nu_Style_Kit.md) | INT08: Nu Style Kit | 40–41 | 40–41 |
| [30-INT09_Insane_FX_Kit.md](text/KRONOS_VoiceNameList/30-INT09_Insane_FX_Kit.md) | INT09: Insane FX Kit | 42–43 | 42–43 |
| [31-INT10_DrumnBass_Kit.md](text/KRONOS_VoiceNameList/31-INT10_DrumnBass_Kit.md) | INT10: Drum'n'Bass Kit | 44–45 | 44–45 |
| [32-INT11_Studio_StandardKit_Mono.md](text/KRONOS_VoiceNameList/32-INT11_Studio_StandardKit_Mono.md) | INT11: Studio StandardKit (Mono) | 46–47 | 46–47 |
| [33-INT12_Acoustic_Pop_Kit_Mono.md](text/KRONOS_VoiceNameList/33-INT12_Acoustic_Pop_Kit_Mono.md) | INT12: Acoustic Pop Kit (Mono) | 48–49 | 48–49 |
| [34-INT13_Wild_Rock_Kit_Mono.md](text/KRONOS_VoiceNameList/34-INT13_Wild_Rock_Kit_Mono.md) | INT13: Wild Rock Kit (Mono) | 50–51 | 50–51 |
| [35-INT14_New_Processed_Kit_Mono.md](text/KRONOS_VoiceNameList/35-INT14_New_Processed_Kit_Mono.md) | INT14: New Processed Kit (Mono) | 52–53 | 52–53 |
| [36-INT15_Jazz_Brush_Kit_Mono.md](text/KRONOS_VoiceNameList/36-INT15_Jazz_Brush_Kit_Mono.md) | INT15: Jazz/Brush Kit (Mono) | 54–55 | 54–55 |
| [37-INT16_Funk_Kit_Mono.md](text/KRONOS_VoiceNameList/37-INT16_Funk_Kit_Mono.md) | INT16: Funk Kit (Mono) | 56–57 | 56–57 |
| [38-INT17_Orch._Ethnic_Kit_Mono.md](text/KRONOS_VoiceNameList/38-INT17_Orch._Ethnic_Kit_Mono.md) | INT17: Orch./Ethnic Kit (Mono) | 58–58 | 58–58 |
| [39-INT18_Original_Perc_Kit_Mono.md](text/KRONOS_VoiceNameList/39-INT18_Original_Perc_Kit_Mono.md) | INT18: Original Perc Kit (Mono) | 59–60 | 59–60 |
| [40-INT19_Brazilian_Perc_Kit_Mono.md](text/KRONOS_VoiceNameList/40-INT19_Brazilian_Perc_Kit_Mono.md) | INT19: Brazilian Perc Kit (Mono) | 61–62 | 61–62 |
| [41-INT20_Cuban_Perc._Kit_Mono.md](text/KRONOS_VoiceNameList/41-INT20_Cuban_Perc._Kit_Mono.md) | INT20: Cuban Perc. Kit (Mono) | 63–64 | 63–64 |
| [42-INT21_Studio_Standard_Kit.md](text/KRONOS_VoiceNameList/42-INT21_Studio_Standard_Kit.md) | INT21: Studio Standard Kit | 65–66 | 65–66 |
| [43-INT22_Acoustic_Pop_Kit.md](text/KRONOS_VoiceNameList/43-INT22_Acoustic_Pop_Kit.md) | INT22: Acoustic Pop Kit | 67–68 | 67–68 |
| [44-INT23_Wild_Rock_Kit.md](text/KRONOS_VoiceNameList/44-INT23_Wild_Rock_Kit.md) | INT23: Wild Rock Kit | 69–70 | 69–70 |
| [45-INT24_New_Processed_Kit.md](text/KRONOS_VoiceNameList/45-INT24_New_Processed_Kit.md) | INT24: New Processed Kit | 71–72 | 71–72 |
| [46-INT25_Jazz_Brush_Kit.md](text/KRONOS_VoiceNameList/46-INT25_Jazz_Brush_Kit.md) | INT25: Jazz/Brush Kit | 73–74 | 73–74 |
| [47-INT26_Funk_Kit.md](text/KRONOS_VoiceNameList/47-INT26_Funk_Kit.md) | INT26: Funk Kit | 75–76 | 75–76 |
| [48-INT27_Orch._Ethnic_Kit.md](text/KRONOS_VoiceNameList/48-INT27_Orch._Ethnic_Kit.md) | INT27: Orch./Ethnic Kit | 77–77 | 77–77 |
| [49-INT28_Original_Perc._Kit.md](text/KRONOS_VoiceNameList/49-INT28_Original_Perc._Kit.md) | INT28: Original Perc. Kit | 78–79 | 78–79 |
| [50-INT29_Brazilian_Perc._Kit.md](text/KRONOS_VoiceNameList/50-INT29_Brazilian_Perc._Kit.md) | INT29: Brazilian Perc. Kit | 80–81 | 80–81 |
| [51-INT30_Cuban_Perc._Kit.md](text/KRONOS_VoiceNameList/51-INT30_Cuban_Perc._Kit.md) | INT30: Cuban Perc. Kit | 82–83 | 82–83 |
| [52-INT31_Conga_Variation_Kit.md](text/KRONOS_VoiceNameList/52-INT31_Conga_Variation_Kit.md) | INT31: Conga Variation Kit | 84–85 | 84–85 |
| [53-INT32_Misc._Perc._Kit.md](text/KRONOS_VoiceNameList/53-INT32_Misc._Perc._Kit.md) | INT32: Misc. Perc. Kit | 86–87 | 86–87 |
| [54-INT33_Rap_Gospel_Hits.md](text/KRONOS_VoiceNameList/54-INT33_Rap_Gospel_Hits.md) | INT33: Rap/Gospel Hits | 88–88 | 88–88 |
| [55-INT34_DJ_Set.md](text/KRONOS_VoiceNameList/55-INT34_DJ_Set.md) | INT34: DJ Set | 89–89 | 89–89 |
| [56-INT35_Industry_VocoderSet.md](text/KRONOS_VoiceNameList/56-INT35_Industry_VocoderSet.md) | INT35: Industry/VocoderSet | 90–90 | 90–90 |
| [57-INT36_Vinyl_Loop_Kit.md](text/KRONOS_VoiceNameList/57-INT36_Vinyl_Loop_Kit.md) | INT36: Vinyl Loop Kit | 91–92 | 91–92 |
| [58-INT37_BD_SD_Catalog_Kit_1.md](text/KRONOS_VoiceNameList/58-INT37_BD_SD_Catalog_Kit_1.md) | INT37: BD/SD Catalog Kit 1 | 93–95 | 93–95 |
| [59-INT38_BD_SD_Catalog_Kit_2.md](text/KRONOS_VoiceNameList/59-INT38_BD_SD_Catalog_Kit_2.md) | INT38: BD/SD Catalog Kit 2 | 96–97 | 96–97 |
| [60-INT39_Cymbal_Catalog_Kit.md](text/KRONOS_VoiceNameList/60-INT39_Cymbal_Catalog_Kit.md) | INT39: Cymbal Catalog Kit | 98–99 | 98–99 |
| [61-U-A00_JazzAmbi_Kit_Dry.md](text/KRONOS_VoiceNameList/61-U-A00_JazzAmbi_Kit_Dry.md) | U-A00: JazzAmbi Kit Dry | 100–102 | 100–102 |
| [62-U-A01_JazzAmbi_Kit_Amb1.md](text/KRONOS_VoiceNameList/62-U-A01_JazzAmbi_Kit_Amb1.md) | U-A01: JazzAmbi Kit Amb1 | 103–105 | 103–105 |
| [63-U-A02_JazzAmbi_Kit_Amb2.md](text/KRONOS_VoiceNameList/63-U-A02_JazzAmbi_Kit_Amb2.md) | U-A02: JazzAmbi Kit Amb2 | 106–108 | 106–108 |
| [64-U-A03_JazzAmbi_Kit_Amb3.md](text/KRONOS_VoiceNameList/64-U-A03_JazzAmbi_Kit_Amb3.md) | U-A03: JazzAmbi Kit Amb3 | 109–111 | 109–111 |
| [65-U-A04_RockAmbi_Kit_SnOn_Dry.md](text/KRONOS_VoiceNameList/65-U-A04_RockAmbi_Kit_SnOn_Dry.md) | U-A04: RockAmbi Kit SnOn Dry | 112–114 | 112–114 |
| [66-U-A05_RockAmbi_Kit_SnOn_Amb1.md](text/KRONOS_VoiceNameList/66-U-A05_RockAmbi_Kit_SnOn_Amb1.md) | U-A05: RockAmbi Kit SnOn Amb1 | 115–116 | 115–116 |
| [67-U-A06_RockAmbi_Kit_SnOn_Amb2.md](text/KRONOS_VoiceNameList/67-U-A06_RockAmbi_Kit_SnOn_Amb2.md) | U-A06: RockAmbi Kit SnOn Amb2 | 117–118 | 117–118 |
| [68-U-A07_RockAmbi_Kit_SnOn_Amb3.md](text/KRONOS_VoiceNameList/68-U-A07_RockAmbi_Kit_SnOn_Amb3.md) | U-A07: RockAmbi Kit SnOn Amb3 | 119–120 | 119–120 |
| [69-U-A08_RockAmbi_Kit_SnOff_Dry.md](text/KRONOS_VoiceNameList/69-U-A08_RockAmbi_Kit_SnOff_Dry.md) | U-A08: RockAmbi Kit SnOff Dry | 121–123 | 121–123 |
| [70-U-A09_RockAmbi_Kit_SnOff_Amb1.md](text/KRONOS_VoiceNameList/70-U-A09_RockAmbi_Kit_SnOff_Amb1.md) | U-A09: RockAmbi Kit SnOff Amb1 | 124–125 | 124–125 |
| [71-U-A10_RockAmbi_Kit_SnOff_Amb2.md](text/KRONOS_VoiceNameList/71-U-A10_RockAmbi_Kit_SnOff_Amb2.md) | U-A10: RockAmbi Kit SnOff Amb2 | 126–127 | 126–127 |
| [72-U-A11_RockAmbi_Kit_SnOff_Amb3.md](text/KRONOS_VoiceNameList/72-U-A11_RockAmbi_Kit_SnOff_Amb3.md) | U-A11: RockAmbi Kit SnOff Amb3 | 128–129 | 128–129 |
| [73-U-A12_Human_Beat_Box_Kit.md](text/KRONOS_VoiceNameList/73-U-A12_Human_Beat_Box_Kit.md) | U-A12: Human Beat Box Kit | 130–130 | 130–130 |
| [74-U-A13_Urban_Hip_Hop_Kit.md](text/KRONOS_VoiceNameList/74-U-A13_Urban_Hip_Hop_Kit.md) | U-A13: Urban Hip Hop Kit | 131–131 | 131–131 |
| [75-U-A14_RB_Kit.md](text/KRONOS_VoiceNameList/75-U-A14_RB_Kit.md) | U-A14: R&B Kit | 132–132 | 132–132 |
| [76-U-A15_NuHop_Kit.md](text/KRONOS_VoiceNameList/76-U-A15_NuHop_Kit.md) | U-A15: NuHop Kit | 133–134 | 133–134 |
| [77-U-B00_Granular_Acid_Kit.md](text/KRONOS_VoiceNameList/77-U-B00_Granular_Acid_Kit.md) | U-B00: Granular Acid Kit | 135–135 | 135–135 |
| [78-U-B01_80008_Kit.md](text/KRONOS_VoiceNameList/78-U-B01_80008_Kit.md) | U-B01: 80008 Kit | 136–136 | 136–136 |
| [79-U-B02_90009_Kit.md](text/KRONOS_VoiceNameList/79-U-B02_90009_Kit.md) | U-B02: 90009 Kit | 137–137 | 137–137 |
| [80-U-B03_Tekno_Klub_Kit.md](text/KRONOS_VoiceNameList/80-U-B03_Tekno_Klub_Kit.md) | U-B03: Tekno Klub Kit | 138–138 | 138–138 |
| [81-U-B04_Mad_Analog_Kit.md](text/KRONOS_VoiceNameList/81-U-B04_Mad_Analog_Kit.md) | U-B04: Mad Analog Kit | 139–140 | 139–140 |
| [82-U-B05_Acoustik_Freak_Kit.md](text/KRONOS_VoiceNameList/82-U-B05_Acoustik_Freak_Kit.md) | U-B05: Acoustik Freak Kit | 141–142 | 141–142 |
| [83-U-B06_Middle_East_Perc._Kit.md](text/KRONOS_VoiceNameList/83-U-B06_Middle_East_Perc._Kit.md) | U-B06: Middle East Perc. Kit | 143–144 | 143–144 |
| [84-U-B07_Cajon_Drum_Kit.md](text/KRONOS_VoiceNameList/84-U-B07_Cajon_Drum_Kit.md) | U-B07: Cajon Drum Kit | 145–146 | 145–146 |
| [85-U-B08_Djembe_Drum_Kit.md](text/KRONOS_VoiceNameList/85-U-B08_Djembe_Drum_Kit.md) | U-B08: Djembe Drum Kit | 147–148 | 147–148 |
| [86-U-B09_Darabukka9_PercKit_C.md](text/KRONOS_VoiceNameList/86-U-B09_Darabukka9_PercKit_C.md) | U-B09: Darabukka9 PercKit C | 149–150 | 149–150 |
| [87-U-B10_Darabuka10_PercKit_C.md](text/KRONOS_VoiceNameList/87-U-B10_Darabuka10_PercKit_C.md) | U-B10: Darabuka10 PercKit C | 151–152 | 151–152 |
| [88-U-B11_Darabukka_Perc._Kit_C2.md](text/KRONOS_VoiceNameList/88-U-B11_Darabukka_Perc._Kit_C2.md) | U-B11: Darabukka Perc. Kit C2 | 153–154 | 153–154 |
| [89-U-B12_Tar_Perc._Kit_C2.md](text/KRONOS_VoiceNameList/89-U-B12_Tar_Perc._Kit_C2.md) | U-B12: Tar Perc. Kit C2 | 155–156 | 155–156 |
| [90-U-B13_Daf_21_Perc._Kit_C2.md](text/KRONOS_VoiceNameList/90-U-B13_Daf_21_Perc._Kit_C2.md) | U-B13: Daf 21 Perc. Kit C2 | 157–158 | 157–158 |
| [91-U-B14_Daf_16_Perc._Kit_C2.md](text/KRONOS_VoiceNameList/91-U-B14_Daf_16_Perc._Kit_C2.md) | U-B14: Daf 16 Perc. Kit C2 | 159–160 | 159–160 |
| [92-U-B15_Bendir_14_Perc_Kit_C2.md](text/KRONOS_VoiceNameList/92-U-B15_Bendir_14_Perc_Kit_C2.md) | U-B15: Bendir 14 Perc Kit C2 | 161–162 | 161–162 |
| [93-U-C00_Doyra_15_Perc._Kit_C2.md](text/KRONOS_VoiceNameList/93-U-C00_Doyra_15_Perc._Kit_C2.md) | U-C00: Doyra 15 Perc. Kit C2 | 163–164 | 163–164 |
| [94-U-C01_Tabil_Perc._Kit_C2.md](text/KRONOS_VoiceNameList/94-U-C01_Tabil_Perc._Kit_C2.md) | U-C01: Tabil Perc. Kit C2 | 165–166 | 165–166 |
| [95-U-C02_Rek_Perc._Kit_1_C2.md](text/KRONOS_VoiceNameList/95-U-C02_Rek_Perc._Kit_1_C2.md) | U-C02: Rek Perc. Kit 1 C2 | 167–168 | 167–168 |
| [96-U-C03_Rek_Perc._Kit_2_Eg_C2.md](text/KRONOS_VoiceNameList/96-U-C03_Rek_Perc._Kit_2_Eg_C2.md) | U-C03: Rek Perc. Kit 2 Eg C2 | 169–170 | 169–170 |
| [97-U-C04_Sagat_Perc_Kit_1_Eg_C2.md](text/KRONOS_VoiceNameList/97-U-C04_Sagat_Perc_Kit_1_Eg_C2.md) | U-C04: Sagat Perc Kit 1 Eg C2 | 171–172 | 171–172 |
| [98-U-C05_Sagat_Perc._Kit_2_C2.md](text/KRONOS_VoiceNameList/98-U-C05_Sagat_Perc._Kit_2_C2.md) | U-C05: Sagat Perc. Kit 2 C2 | 173–174 | 173–174 |
| [99-GM0_STANDARD.md](text/KRONOS_VoiceNameList/99-GM0_STANDARD.md) | GM0: STANDARD | 175–175 | 175–175 |
| [100-GM1_ROOM.md](text/KRONOS_VoiceNameList/100-GM1_ROOM.md) | GM1: ROOM | 176–176 | 176–176 |
| [101-GM2_POWER.md](text/KRONOS_VoiceNameList/101-GM2_POWER.md) | GM2: POWER | 177–177 | 177–177 |
| [102-GM3_ELECTRONIC.md](text/KRONOS_VoiceNameList/102-GM3_ELECTRONIC.md) | GM3: ELECTRONIC | 178–178 | 178–178 |
| [103-GM4_ANALOG.md](text/KRONOS_VoiceNameList/103-GM4_ANALOG.md) | GM4: ANALOG | 179–179 | 179–179 |
| [104-GM5_JAZZ.md](text/KRONOS_VoiceNameList/104-GM5_JAZZ.md) | GM5: JAZZ | 180–180 | 180–180 |
| [105-GM6_BRUSH.md](text/KRONOS_VoiceNameList/105-GM6_BRUSH.md) | GM6: BRUSH | 181–181 | 181–181 |
| [106-GM7_ORCHESTRA.md](text/KRONOS_VoiceNameList/106-GM7_ORCHESTRA.md) | GM7: ORCHESTRA | 182–182 | 182–182 |
| [107-GM8_SFX.md](text/KRONOS_VoiceNameList/107-GM8_SFX.md) | GM8: SFX | 183–183 | 183–183 |
| [108-Drum_Track_Patterns_Patterns_Preset.md](text/KRONOS_VoiceNameList/108-Drum_Track_Patterns_Patterns_Preset.md) | Drum Track Patterns/Patterns Preset | 184–185 | 184–185 |
| [109-Template_Songs.md](text/KRONOS_VoiceNameList/109-Template_Songs.md) | Template Songs | 186–186 | 186–186 |
| [110-ROM.md](text/KRONOS_VoiceNameList/110-ROM.md) | ROM | 187–191 | 187–191 |
| [111-EXs2_-_Concert_Grand_Piano.md](text/KRONOS_VoiceNameList/111-EXs2_-_Concert_Grand_Piano.md) | EXs2 - Concert Grand Piano | 192–192 | 192–192 |
| [112-Exs4_-_Vintage_Keyboards.md](text/KRONOS_VoiceNameList/112-Exs4_-_Vintage_Keyboards.md) | Exs4 - Vintage Keyboards | 193–193 | 193–193 |
| [113-EXs7_-_SGX-1_Japanese_C_Piano.md](text/KRONOS_VoiceNameList/113-EXs7_-_SGX-1_Japanese_C_Piano.md) | EXs7 - SGX-1 Japanese C Piano | 194–194 | 194–194 |
| [114-EXs12_-_SGX-1_Austrian_Piano.md](text/KRONOS_VoiceNameList/114-EXs12_-_SGX-1_Austrian_Piano.md) | EXs12 - SGX-1 Austrian Piano | 195–195 | 195–195 |
| [115-EXs17_-_SGX-2_Berlin_D_Piano.md](text/KRONOS_VoiceNameList/115-EXs17_-_SGX-2_Berlin_D_Piano.md) | EXs17 - SGX-2 Berlin D Piano | 196–196 | 196–196 |
| [116-EXs18_-_KORG_EXs_Collections.md](text/KRONOS_VoiceNameList/116-EXs18_-_KORG_EXs_Collections.md) | EXs18 - KORG EXs Collections | 197–197 | 197–197 |
| [117-ROM.md](text/KRONOS_VoiceNameList/117-ROM.md) | ROM | 198–202 | 198–202 |
| [118-EXs1_-_ROM_Expansion.md](text/KRONOS_VoiceNameList/118-EXs1_-_ROM_Expansion.md) | EXs1 - ROM Expansion | 203–207 | 203–207 |
| [119-EXs5_-_ROM_Expansion_2.md](text/KRONOS_VoiceNameList/119-EXs5_-_ROM_Expansion_2.md) | EXs5 - ROM Expansion 2 | 208–210 | 208–210 |
| [120-EXs8_-_Rock_Ambience_Drums.md](text/KRONOS_VoiceNameList/120-EXs8_-_Rock_Ambience_Drums.md) | EXs8 - Rock Ambience Drums | 211–214 | 211–214 |
| [121-EXs9_-_Jazz_Ambience_Drums.md](text/KRONOS_VoiceNameList/121-EXs9_-_Jazz_Ambience_Drums.md) | EXs9 - Jazz Ambience Drums | 215–222 | 215–222 |
| [122-USER-F.md](text/KRONOS_VoiceNameList/122-USER-F.md) | USER-F | 223–223 | 223–223 |
| [123-Piano_Type.md](text/KRONOS_VoiceNameList/123-Piano_Type.md) | Piano Type | 224–224 | 224–224 |
| [124-Category_Arpeggio.md](text/KRONOS_VoiceNameList/124-Category_Arpeggio.md) | Category: Arpeggio | 225–226 | 225–226 |
| [125-Category_Melodic.md](text/KRONOS_VoiceNameList/125-Category_Melodic.md) | Category: Melodic | 227–228 | 227–228 |
| [126-Category_Harmonic_Poly.md](text/KRONOS_VoiceNameList/126-Category_Harmonic_Poly.md) | Category: Harmonic (Poly) | 229–233 | 229–233 |
| [127-Category_Chord_Rhythmic.md](text/KRONOS_VoiceNameList/127-Category_Chord_Rhythmic.md) | Category: Chord Rhythmic | 234–236 | 234–236 |
| [128-Category_Strumming.md](text/KRONOS_VoiceNameList/128-Category_Strumming.md) | Category: Strumming | 237–237 | 237–237 |
| [129-Category_Pick.md](text/KRONOS_VoiceNameList/129-Category_Pick.md) | Category: Pick | 238–238 | 238–238 |
| [130-Category_Bass_Pattern.md](text/KRONOS_VoiceNameList/130-Category_Bass_Pattern.md) | Category: Bass Pattern | 239–241 | 239–241 |
| [131-Category_Gated.md](text/KRONOS_VoiceNameList/131-Category_Gated.md) | Category: Gated | 242–242 | 242–242 |
| [132-Category_Drum.md](text/KRONOS_VoiceNameList/132-Category_Drum.md) | Category: Drum | 243–252 | 243–252 |
| [133-Category_Real-Time.md](text/KRONOS_VoiceNameList/133-Category_Real-Time.md) | Category: Real-Time | 253–253 | 253–253 |
| [134-Category_Pick.md](text/KRONOS_VoiceNameList/134-Category_Pick.md) | Category: Pick | 254–254 | 254–254 |
| [135-Category_Wavesequence.md](text/KRONOS_VoiceNameList/135-Category_Wavesequence.md) | Category: Wavesequence | 255–255 | 255–255 |
| [136-KARMA_RTC_Name.md](text/KRONOS_VoiceNameList/136-KARMA_RTC_Name.md) | KARMA RTC Name | 256–257 | 256–257 |
| [137-Effect_Presets.md](text/KRONOS_VoiceNameList/137-Effect_Presets.md) | Effect Presets | 258–263 | 258–263 |
| [138-S006.md](text/KRONOS_VoiceNameList/138-S006.md) | S006 | 264–264 | 264–264 |
| [139-EXs2_Concert_Grand.PCG.md](text/KRONOS_VoiceNameList/139-EXs2_Concert_Grand.PCG.md) | EXs2 Concert Grand.PCG: | 265–265 | 265–265 |
| [140-EXs3_Brass_Woodwinds.PCG.md](text/KRONOS_VoiceNameList/140-EXs3_Brass_Woodwinds.PCG.md) | EXs3 Brass Woodwinds.PCG: | 266–266 | 266–266 |
| [141-EXs3_Brass_Woodwinds_Extra.PCG.md](text/KRONOS_VoiceNameList/141-EXs3_Brass_Woodwinds_Extra.PCG.md) | EXs3 Brass Woodwinds Extra.PCG: | 267–268 | 267–268 |
| [142-EXs4_Vintage_Keyboards.PCG.md](text/KRONOS_VoiceNameList/142-EXs4_Vintage_Keyboards.PCG.md) | EXs4 Vintage Keyboards.PCG: | 269–270 | 269–270 |

### KRONOS_MIDI_Implementation

- 元PDF: `MIDI Implementation/KRONOS_MIDI_Implementation.pdf`（4ページ）

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [KRONOS_MIDI_Implementation.md](text/KRONOS_MIDI_Implementation/KRONOS_MIDI_Implementation.md) | KRONOS_MIDI_Implementation | 1–4 |  |

### テキスト資料（MIDI Implementation など）

| ファイル | 先頭行 |
|---|---|
| [CombiAndSongTimbreSet.txt](text/txt/CombiAndSongTimbreSet.txt) | Combi and Song Timbre Set objects have the same structure. |
| [DrumKit.txt](text/txt/DrumKit.txt) | Drum Kit Size: 38424 byte |
| [DrumTrackPattern.txt](text/txt/DrumTrackPattern.txt) | 1 DRUM TRACK PATTERN DATA |
| [Effect.txt](text/txt/Effect.txt) | 00:No Effect |
| [Global.txt](text/txt/Global.txt) | Global Size: 24708 byte |
| [KARMA_GE_RTP.txt](text/txt/KARMA_GE_RTP.txt) | Object Version: 0 |
| [KRONOS_MIDI_SysEx.txt](text/txt/KRONOS_MIDI_SysEx.txt) | KORG Proprietary System Exclusive Messages For KRONOS Version 1.26 (Aug 21, 2014 |
| [Prog_EXi.txt](text/txt/Prog_EXi.txt) | 0:Off |
| [Prog_EXi_Common.txt](text/txt/Prog_EXi_Common.txt) | EXi Program Size: 4960 byte |
| [Prog_HD-1.txt](text/txt/Prog_HD-1.txt) | HD-1 Program Size: 3706 byte Version 1.01 (Jan 7, 2015) |
| [SetList.txt](text/txt/SetList.txt) | 1:SetList, Number Of Bytes = 69416 |
| [Song.txt](text/txt/Song.txt) | Song Size: 13076 byte |
| [SongControl.txt](text/txt/SongControl.txt) | Song Control Size: 5264 byte |
| [SongEvent.txt](text/txt/SongEvent.txt) | ======================================================================== |
| [WaveSequence.txt](text/txt/WaveSequence.txt) | Wave Seq Size: 2216 byte |
