# Quickstart: フェーズ別BGM再生

## 動作確認シナリオ

### シナリオ1: 作業用BGMのループ再生

1. 設定ダイアログを開く（右クリック → 設定）
2. 「BGM設定」グループ → 作業用BGM の「参照」でWAVファイルを選択
3. 「作業中BGMを有効にする」チェックボックスをON
4. 音量スライダーを適切な値に設定（デフォルト50%）
5. 「▶」プレビューボタンで5秒間再生されることを確認
6. OK で保存
7. タイマーの▶ボタンで作業セッション開始 → BGMがループ再生される
8. タイマー終了 / スキップ → BGMが停止する

### シナリオ2: 休憩用BGMへの切り替え

1. 休憩用BGMも同様に設定（異なるファイル・音量）
2. 作業セッションを開始してBGMが再生されることを確認
3. セッション終了時に作業BGMが止まり、通知音が鳴る
4. 休憩フェーズに移行 → 休憩用BGMが自動再生される
5. 休憩終了 → 休憩BGMが止まる

### シナリオ3: 一時停止時の動作

1. 作業BGM再生中にタイマーを「⏸」で一時停止
2. BGMが停止することを確認
3. ▶ で再開 → BGMが再び最初から再生される

### シナリオ4: BGMファイルが削除された場合

1. BGMファイルを設定後、そのファイルを手動で削除
2. 作業フェーズを開始 → BGMは再生されないがアプリはクラッシュしない

---

## PyInstaller ビルドコマンド（BGM対応版）

```powershell
pyinstaller --onefile --windowed --name "PomodoroTimer" `
  --add-data "assets/sounds/notification.wav;assets/sounds" `
  --collect-all PyQt6 `
  src/main.py
```

> `--collect-all PyQt6` により QtMultimedia バックエンドプラグインが同梱され、BGMと通知音が Windows exe でも動作します。
