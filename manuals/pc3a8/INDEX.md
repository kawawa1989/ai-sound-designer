# pc3a8 資料インデックス

`scripts/convert_manuals.py` で自動生成。手で編集しない。

- 調べるときは、まずこの表で章を絞り、`text/` 以下を grep する。
- 各ページの先頭に `<!-- page: PDF p.N 本文p.M -->` がある。出典は本文ページで書く（マニュアル内の「→ p.xxx」も本文ページ）。
- 図・表・画面写真は抽出されないので、必要なら元PDFの該当 PDF ページを Read する。
- `text/` と元PDFは著作物のため git 管理外。無ければ `uv run python scripts/convert_manuals.py manuals/pc3a8` で再生成する。

### Kurzweil_PC3A8_Getting_Started Manual

- 元PDF: `Kurzweil_PC3A8_Getting_Started Manual.pdf`（23ページ）

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [Kurzweil_PC3A8_Getting_Started_Manual.md](text/Kurzweil_PC3A8_Getting_Started_Manual/Kurzweil_PC3A8_Getting_Started_Manual.md) | p1-23 | 1–23 |  |

### Kurzweil_PC3A_Musicians_Guide

- 元PDF: `Kurzweil_PC3A_Musicians_Guide.pdf`（425ページ）
- 本文ページ番号は「章-ページ」（例: 6-45、付録は A-3）。各ページの余白の番号を読んだもの

| ファイル | 章 | PDFページ | 本文ページ |
|---|---|---|---|
| [00-前付け目次.md](text/Kurzweil_PC3A_Musicians_Guide/00-前付け目次.md) | 前付け・目次 | 1–18 |  |
| [01-Chapter_1_Introduction.md](text/Kurzweil_PC3A_Musicians_Guide/01-Chapter_1_Introduction.md) | Chapter 1 Introduction | 19–23 | 1-1–1-5 |
| [02-Chapter_2_Startup.md](text/Kurzweil_PC3A_Musicians_Guide/02-Chapter_2_Startup.md) | Chapter 2 Startup | 24–33 | 2-1–2-10 |
| [03-Chapter_3_User_Interface_Basics.md](text/Kurzweil_PC3A_Musicians_Guide/03-Chapter_3_User_Interface_Basics.md) | Chapter 3 User Interface Basics | 34–45 | 3-1–3-12 |
| [04-Chapter_4_The_Operating_Modes.md](text/Kurzweil_PC3A_Musicians_Guide/04-Chapter_4_The_Operating_Modes.md) | Chapter 4 The Operating Modes | 46–48 | 4-1–4-3 |
| [05-Chapter_5_Editing_Conventions.md](text/Kurzweil_PC3A_Musicians_Guide/05-Chapter_5_Editing_Conventions.md) | Chapter 5 Editing Conventions | 49–55 | 5-1–5-7 |
| [06-Chapter_6_Program_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/06-Chapter_6_Program_Mode.md) | Chapter 6 Program Mode | 56–126 | 6-1–6-71 |
| [07-Chapter_7_Setup_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/07-Chapter_7_Setup_Mode.md) | Chapter 7 Setup Mode | 127–196 | 7-1–7-70 |
| [08-Chapter_8_Quick_Access_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/08-Chapter_8_Quick_Access_Mode.md) | Chapter 8 Quick Access Mode | 197–199 | 8-1–8-3 |
| [09-Chapter_9_Effects_and_Effect_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/09-Chapter_9_Effects_and_Effect_Mode.md) | Chapter 9 Effects and Effect Mode | 200–225 | 9-1–9-26 |
| [10-Chapter_10_MIDI_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/10-Chapter_10_MIDI_Mode.md) | Chapter 10 MIDI Mode | 226–243 | 10-1–10-18 |
| [11-Chapter_11_Master_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/11-Chapter_11_Master_Mode.md) | Chapter 11 Master Mode | 244–261 | 11-1–11-18 |
| [12-Chapter_12_Song_Mode_and_the_Song_Editor.md](text/Kurzweil_PC3A_Musicians_Guide/12-Chapter_12_Song_Mode_and_the_Song_Editor.md) | Chapter 12 Song Mode and the Song Editor | 262–294 | 12-1–12-33 |
| [13-Chapter_13_Storage_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/13-Chapter_13_Storage_Mode.md) | Chapter 13 Storage Mode | 295–309 | 13-1–13-15 |
| [14-Chapter_14_Keymap_and_Sample_Editing.md](text/Kurzweil_PC3A_Musicians_Guide/14-Chapter_14_Keymap_and_Sample_Editing.md) | Chapter 14 Keymap and Sample Editing | 310–322 | 14-1–14-13 |
| [15-Chapter_15_Tutorial_Song_Mode.md](text/Kurzweil_PC3A_Musicians_Guide/15-Chapter_15_Tutorial_Song_Mode.md) | Chapter 15 Tutorial: Song Mode | 323–338 | 15-1–15-16 |
| [16-Appendix_A_Specifications.md](text/Kurzweil_PC3A_Musicians_Guide/16-Appendix_A_Specifications.md) | Appendix A Specifications | 339–340 | A-1–A-2 |
| [17-Appendix_B_PC3A_Bootloader.md](text/Kurzweil_PC3A_Musicians_Guide/17-Appendix_B_PC3A_Bootloader.md) | Appendix B PC3A Bootloader | 341–343 | B-1–B-3 |
| [18-Appendix_C_Changing_PC3A_Voltage.md](text/Kurzweil_PC3A_Musicians_Guide/18-Appendix_C_Changing_PC3A_Voltage.md) | Appendix C Changing PC3A Voltage | 344–347 | C-1–C-4 |
| [19-Appendix_D_PC3A_Objects_V_2.31.2.md](text/Kurzweil_PC3A_Musicians_Guide/19-Appendix_D_PC3A_Objects_V_2.31.2.md) | Appendix D PC3A Objects (V 2.31.2) | 348–414 | D-1–D-67 |
| [20-Appendix_E_PC3A_Legacy_File_Conversion.md](text/Kurzweil_PC3A_Musicians_Guide/20-Appendix_E_PC3A_Legacy_File_Conversion.md) | Appendix E PC3A Legacy File Conversion | 415–415 | E-1–E-1 |
| [21-Index.md](text/Kurzweil_PC3A_Musicians_Guide/21-Index.md) | Index | 416–425 |  |
