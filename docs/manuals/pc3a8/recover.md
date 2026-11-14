# PC3A8: 元に戻す

## 目的

本体の音や状態がおかしくなったときに、**影響の小さい順に**戻します。上の段で戻るなら、下の段は使いません。
どの方法で何が消えるかの一覧は `docs/safety.md` の「元に戻す方法」です。

## 前提

- 何がおかしいかをメモしてある（どの Program で、何をしたあとか）
- 段 3・4 に進むときは、先にバックアップを取る（[backup.md](backup.md)）

## 手順

### 段 1: 編集中の音がおかしい → 編集を捨てる

1. Program Editor で **Storage**（Compare）を押し、編集前の音と比べる（本文 6-13）。もう一度押して戻る
2. **Exit** を押し、「保存しますか」で **No** を選ぶ（本文 5-3）

詳しくは [exit_and_compare.md](exit_and_compare.md)。**消えるもの: 保存していない編集だけ**

### 段 2: テスト用の Program を保存し間違えた → その 1 つを消す

1. 消す Program の ID と名前を、`docs/safety.md` の表と見比べる。**テスト用の ID 以外なら消さない**
2. 次のどちらかで消す
   - Program モードでその Program を選び、**Edit** → **Delete** を押す。一覧で目的の Program を選び、もう一度 **Delete**（本文 6-52）
   - **Master** モード → **OBJECT** → **Delete** → advanced のページで 1 つだけ選んで消す（本文 11-13〜11-14）
3. 必要なら、記録した設定から作り直す（例: [build_base_program.md](build_base_program.md)）
4. ROM の ID に保存してしまった場合も同じ。新しいほうを消すと ROM の音色が戻る（本文 5-2、5-4）

**消えるもの: 消した Program だけ**

### 段 3: 全体を工場出荷時に戻す（最後の手段）

1. [backup.md](backup.md) でバックアップを取る
2. **Master** モードで **Reset** を押す（本文 11-17）
3. 「すべて消しますか」に **Yes**。数秒で Program モードに戻る
4. 必要なら、Storage モードの **LOAD** でバックアップを読み込む（本文 13-9〜13-12）。本体が空なので、既存を消す方式（OvFill・Overwrt）は使わなくてよい

**消えるもの: すべてのユーザーオブジェクトと設定**（全パラメータが既定値に戻る）

### 段 4: 起動しない・Reset できない → Bootloader の System Reset

1. 電源を切る
2. **Exit** を押したまま電源を入れる。「Initializing Scanner」と出ている間、押し続ける（本文 B-1）
3. Bootloader のメニューで **System Reset** を押す（本文 B-1〜B-2）
4. 終わったら **Run PC3A** で起動する（本文 B-1）

**消えるもの: 段 3 と同じ**

## 確認

- 段 1・2: Program を選び直すと、記録どおりの音が鳴る
- 段 3・4: Program モードで工場出荷時の Program が鳴る。テスト用の ID（1025〜）は空になる（バックアップを読み込めば戻る）

## 注意

- **段 3・4 は人が判断して行う**。ツールからも、作業の途中でも使わない（`docs/safety.md`）
- Bootloader の **Format Flash** と **System Update** は使わない。OS が消える・更新される（本文 B-2〜B-3）
- 段 2 で消す前に、ID を声に出して読む

## 出典

- Musician's Guide 本文 5-2〜5-4（保存と ROM の復活）、6-13（Compare）、6-52（Program の Delete）、11-13〜11-14（OBJECT › Delete）、
  11-17（Reset）、13-9〜13-12（LOAD）、B-1〜B-3（Bootloader）
- 実機で確かめた日: 段 1 は 2026-11-14（Exit → No）。段 2〜4 は実機ではまだ試していない（**要確認**）
