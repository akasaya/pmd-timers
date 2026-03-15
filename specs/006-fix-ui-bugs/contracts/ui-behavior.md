# UI Behavior Contracts: UIバグ修正

## 透明度設定

- `window_opacity` の値域: 0.2 ≤ opacity ≤ 1.0
- 設定値 1.0 → `setWindowOpacity(1.0)` = 完全不透明
- 設定値 0.2 → `setWindowOpacity(0.2)` = 80%透明
- UIラベル: スライダー上の表記は「不透明度」とし、値が大きいほど見やすくなることを示す

## ホバー表示

- `enterEvent` 発火 → 150ms以内にボタンをフェードイン
- `leaveEvent` 発火 → 150ms待機後に `underMouse()` を確認
  - `underMouse() == True` の場合: キャンセル（マウスは子ウィジェット上）
  - `underMouse() == False` の場合: フェードアウト実行
- `hover_reveal_buttons == False` の場合: 常にボタン表示・ホバー処理なし

## テキスト視認性

- ウィジェット本体背景: `rgba(20, 20, 20, 180)` （任意の壁紙上で読める）
- テキストカラー: 白系（背景が暗いため）
- ホバー時・非ホバー時ともに背景は維持

## グラフ代替表示（Charts非インストール時）

- `CHARTS_AVAILABLE == False` の場合、テキスト形式で日別セッション数を表示
- データが0件の場合: 「記録なし」メッセージを表示
- 技術的なエラーメッセージ（モジュール名等）は表示しない
