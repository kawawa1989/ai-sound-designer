# 本体の操作手順書

本体（シンセ）で人が行う操作を、だれが読んでも同じように実行できるようにまとめた手順書です。
1 つの作業につき 1 ファイルにしています。

2026-11-14 から PC3A8 だけで進めているため、KRONOS の手順書は作っていません（KRONOS の実装は残しています）。

## 文書の分担

| 文書 | 書くこと |
| --- | --- |
| `docs/safety.md` | **ルール**。してはいけない操作、テスト用の ID、ツールが送る MIDI、元に戻す方法の一覧 |
| `docs/manuals/`（ここ） | **やり方**。ボタンを押す順番と、確かめ方 |
| `runs/<参照音>/recipes/<機種>/recipe.md` | **音色ごとの設定値**。ツールが参照音から作る |
| `docs/pc3a8_setup.md` | 接続と設定ファイル、マスターエフェクトの状態 |
| `docs/pc3a8_parameter_table.md` | パラメータ表の書き方と、キャリブレーションの結果 |

ルールと手順が食い違ったら、`docs/safety.md` を優先し、手順書を直します。

## 手順書の形

どの手順書も、次の見出しをこの順に並べます。

| 見出し | 書くこと |
| --- | --- |
| 目的 | 何のための作業か、終わると何ができるか |
| 前提 | 始める前に済ませておくこと、選んでおく Program |
| 手順 | 番号付き。ボタン名・ページ名・パラメータ名は**本体の表示どおり**に太字で書く |
| 確認 | 正しくできたかを確かめる方法 |
| 元に戻す | 間違えたときの戻し方（必要な手順だけ） |
| 注意 | してはいけないこと、間違えやすいこと |
| 出典 | マニュアルの本文ページ（例: Musician's Guide 本文 5-3）と、実機で確かめた日 |

- マニュアルにも実機にも確かめていない操作は「**要確認**」と書く
- 本文ページはマニュアルの余白の番号（PDF のページ番号ではない）。PC3A8 は「章-ページ」（例: 6-45）
- `synth_docs/` の非公式メモは出典にしない

## PC3A8

### 本体の基本

| 手順書 | 内容 |
| --- | --- |
| [program_editor.md](pc3a8/program_editor.md) | Program Editor の基本（ページの移動、more、左の列と右のサブページ） |
| [exit_and_compare.md](pc3a8/exit_and_compare.md) | 編集を保存せずに抜ける・Compare で編集前と比べる |
| [save_program.md](pc3a8/save_program.md) | 編集した Program をテスト用 ID（1025〜）に保存する（Replace しない） |
| [rename_object.md](pc3a8/rename_object.md) | 保存した Program の名前を変える（Master › OBJECT › Rename）。2026-11-14 に実機で確認 |
| [check_master_effects.md](pc3a8/check_master_effects.md) | マスターエフェクト（Effect モード › MASTER、AUXFX1 / AUXFX2）を確かめる |
| [backup.md](pc3a8/backup.md) | ユーザーオブジェクトを USB メモリにバックアップする（Storage › STORE） |
| [recover.md](pc3a8/recover.md) | 元に戻す（Compare → 1 つの削除 → Reset → Bootloader の System Reset） |
| [build_base_program.md](pc3a8/build_base_program.md) | 基準音 1025「KVA BASIC SAW」を作る |

### ツールと組み合わせる作業

| 手順書 | 内容 |
| --- | --- |
| [read_parameter_values.md](pc3a8/read_parameter_values.md) | パラメータの値と範囲を画面で読み取る |
| [calibrate.md](pc3a8/calibrate.md) | キャリブレーション曲線を手で値を変えて測る |
| [calibrate_cc.md](pc3a8/calibrate_cc.md) | CC で自動で測る（Program 1026・1027 の作り方を含む） |
| [run_trial.md](pc3a8/run_trial.md) | レシピどおりに設定して録音・比較する |
