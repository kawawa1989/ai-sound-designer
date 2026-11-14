# PC3A8: 保存した Program の名前を変える

## 目的

保存したテスト用 Program の名前を、Program Editor に入らずに変えます。
保存するときに付ける場合は [save_program.md](save_program.md) の手順 4。

## 前提

- 名前を変える Program が、テスト用の ID（`docs/safety.md` の表）に保存されている

## 手順

1. **Master** モードボタンを押す
2. **OBJECT** ソフトボタンを押す。OBJECTS ページが出る（本文 11-13）
3. **Rename** ソフトボタンを押す。ユーザーが作った・編集したオブジェクトの一覧が、種類ごとに出る（本文 11-14）
4. Alpha Wheel または **−** / **+** で、名前を変える Program を選ぶ。**ID がテスト用のものか確かめる**
5. **Rename** を押し、名前を入れる（入れ方は [save_program.md](save_program.md) の手順 4。本文 5-3）
   - ◀ / ▶ を同時に 2 回押すと、カーソルが名前の最後に移る（本文 11-14）
6. **OK** を押す
7. **Exit** で Master モードを抜ける。Program モードに戻る
8. `docs/safety.md` の表の名前を直す

## 確認

- Program モードでその ID を選ぶと、新しい名前が出る。**見るだけで、Edit は押さない**
- 音は変わっていない
- Edit を押して Program Editor に入ってしまったら、**Exit** を押す。「保存しますか」が出たら **No**（何も変えていなければ、そのまま戻る。本文 5-3）

## 元に戻す

- もう一度この手順で、元の名前に変える

## 注意

- OBJECTS ページの **Delete** を押さない（オブジェクトを消す機能。本文 11-14）
- Master モードの **Reset** を押さない（すべてのユーザーオブジェクトが消える。本文 11-17）
- 名前の変更は、Program Editor に入らなくても保存される（Rename の OK で終わり）。確かめるために Edit に入る必要はない
- 名前を変えたら、手順書（`calibrate_cc.md` など）やパラメータ表（`kva.json` の `program`）に書いた名前も直す。
  ツールは `program` の名前で「本体で 〜 を選んでいますか」と聞く

## 出典

- Musician's Guide 本文 5-3（名前の付け方、Exit ページ）、11-13（OBJECTS ページ）、11-14（Rename と Delete）、11-17（Reset）
- 実機で確かめた日: 2026-11-14（1027 を KVA ENVCTL CALX に変えてから、KVA ENVCTL CAL に戻した。手順どおりに動いた。
  確かめるときに Edit に入ってしまったが、保存せずに抜けて影響はなかった）
