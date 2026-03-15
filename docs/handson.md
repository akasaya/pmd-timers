# ハンズオン — pmd-timers を一から作る

対象読者: Pythonはある程度書ける、PyQt6/GUIは初めて

---

## 1. はじめに

このチュートリアルでは、**pmd-timers** と同等のデスクトップポモドーロタイマーアプリを一から作ります。

**完成形のイメージ**

- 常に画面の最前面に小さく浮いているタイマーウィジェット（200×80px 程度）
- タイトルバーなし・背景半透明の丸角ウィンドウ
- マウスを乗せると操作ボタンがフェードイン
- ドラッグで好きな位置に移動でき、位置は次回起動時も記憶される
- 作業→短休憩→作業→長休憩のサイクルを自動管理
- セッション履歴をJSONで保存し、統計ダッシュボードで確認できる
- PyInstallerで単一の .exe にパッケージング可能

チュートリアルは8つのステップで構成されています。各ステップは独立して動作するコードから始め、少しずつ機能を積み上げていきます。

---

## 2. 環境セットアップ

Python 3.12 と必要なパッケージをインストールします。

```bash
# Python 3.12 がインストール済みか確認
python --version   # Python 3.12.x であること

# 仮想環境を作成・有効化
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# パッケージをインストール
pip install PyQt6>=6.7.0 PyQt6-Qt6-Charts>=6.7.0 plyer>=2.1.0
```

インストールを確認します。

```python
# check_install.py
import PyQt6.QtWidgets
print("PyQt6 OK")
try:
    import PyQt6.QtCharts
    print("QtCharts OK")
except ImportError:
    print("QtCharts なし（テキストフォールバックで動作します）")
```

```bash
python check_install.py
```

---

## 3. Step 1: PyQt6の基本 — 最小限のウィンドウを作る

まず「ウィンドウが1つ出る」だけのコードを書きます。

```python
# step1_hello.py
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

# 1. QApplication を作る（必ず最初）
app = QApplication(sys.argv)

# 2. ウィンドウ（QWidget）を作って表示
window = QWidget()
window.setWindowTitle("Hello PyQt6")
window.resize(300, 100)

label = QLabel("Hello, PyQt6!", window)
label.move(80, 35)

window.show()

# 3. イベントループに入る
sys.exit(app.exec())
```

```bash
python step1_hello.py
```

### QApplication とは

`QApplication` はアプリ全体を管理するシングルトンです。ウィンドウを作る前に必ず1つ作る必要があります。`sys.argv` を渡すのは、Qt がコマンドライン引数（`-style`, `-platform` など）を解析できるようにするためです。

### イベントループとは

`app.exec()` を呼ぶとプログラムはここで「ブロック」します。この間 Qt は内部のイベントキューを監視し続け、マウスクリックやキーボード入力、タイマー発火といったイベントが来るたびに対応する関数を呼び出します。`window.show()` だけでは画面は出ますが、イベントループに入らないと即座に終了してしまいます。

---

## 4. Step 2: フレームレス・常時最前面ウィンドウ

OS標準のタイトルバーを消し、常に最前面に表示します。

```python
# step2_frameless.py
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


class FloatingWidget(QWidget):
    def __init__(self):
        super().__init__()

        # ── ウィンドウフラグの設定 ──
        flags = (
            Qt.WindowType.FramelessWindowHint    # タイトルバーなし
            | Qt.WindowType.WindowStaysOnTopHint # 常に最前面
            | Qt.WindowType.Tool                 # タスクバーに出ない
        )
        self.setWindowFlags(flags)

        # 背景を透明にする
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(200, 80)

        layout = QVBoxLayout(self)
        label = QLabel("25:00", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(label)

    def paintEvent(self, event):
        """背景を自分で描く（透明ウィンドウには必須）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # アンチエイリアス
        # 半透明の濃いグレーで丸角矩形を描く
        painter.setBrush(QColor(20, 20, 20, 200))  # R, G, B, Alpha(0-255)
        painter.setPen(Qt.PenStyle.NoPen)           # 枠線なし
        painter.drawRoundedRect(self.rect(), 8, 8)  # 角丸8px


app = QApplication(sys.argv)
widget = FloatingWidget()
widget.show()
sys.exit(app.exec())
```

### ポイント解説

**`FramelessWindowHint`**: OS のウィンドウデコレーション（タイトルバー、リサイズハンドルなど）を完全に除去します。ドラッグ移動や閉じるボタンも自前で実装する必要があります。

**`WA_TranslucentBackground`**: Qtにウィジェットの背景を透明にするよう指示します。ただしこれだけでは「何も描かれていない領域が透明になる」だけです。`paintEvent` をオーバーライドして自分で背景を描かないと、ウィジェット全体が透明になってしまいます。

**`paintEvent`**: ウィジェットの描画が必要になるたびに Qt が自動的に呼び出します（ウィンドウが重なって隠れた後に表示されたときなど）。`QPainter` オブジェクトを通じて図形・テキスト・画像を描画できます。`QColor(R, G, B, A)` の第4引数アルファが透明度です（0=透明、255=不透明）。

---

## 5. Step 3: タイマーエンジン（状態機械）

ポモドーロタイマーのロジックを `QObject` として実装します。

```python
# step3_engine.py
import sys
from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget


class TimerEngine(QObject):
    """ポモドーロタイマーの状態機械"""

    # シグナル定義: 発火時に送るデータの型を指定する
    tick = pyqtSignal(int)         # 毎秒カウントダウン値を送る
    finished = pyqtSignal()        # タイマー終了を通知

    def __init__(self, duration_sec: int, parent=None):
        super().__init__(parent)
        self._duration = duration_sec
        self._remaining = duration_sec
        self._running = False

        # QTimer: 指定間隔でシグナルを発火するタイマー
        self._timer = QTimer(self)
        self._timer.setInterval(1000)          # 1000ms = 1秒
        self._timer.timeout.connect(self._on_tick)  # スロットに接続

    def start(self):
        self._running = True
        self._timer.start()

    def pause(self):
        self._running = False
        self._timer.stop()

    def reset(self):
        self._timer.stop()
        self._remaining = self._duration
        self._running = False
        self.tick.emit(self._remaining)  # UIを初期値に戻す

    def _on_tick(self):
        """QTimer の timeout シグナルに接続されたスロット"""
        if self._remaining > 0:
            self._remaining -= 1
            self.tick.emit(self._remaining)
        if self._remaining == 0:
            self._timer.stop()
            self.finished.emit()


class TimerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Step 3: タイマー")
        self.resize(200, 150)

        self._engine = TimerEngine(duration_sec=10)  # テスト用に10秒

        # シグナルをスロット（メソッド）に接続
        self._engine.tick.connect(self._on_tick)
        self._engine.finished.connect(self._on_finished)

        layout = QVBoxLayout(self)
        self._label = QLabel("00:10", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._btn = QPushButton("スタート", self)
        self._btn.clicked.connect(self._toggle)
        layout.addWidget(self._label)
        layout.addWidget(self._btn)

        self._running = False

    def _toggle(self):
        if self._running:
            self._engine.pause()
            self._btn.setText("再開")
            self._running = False
        else:
            self._engine.start()
            self._btn.setText("一時停止")
            self._running = True

    def _on_tick(self, remaining: int):
        m, s = divmod(remaining, 60)
        self._label.setText(f"{m:02d}:{s:02d}")

    def _on_finished(self):
        self._label.setText("完了!")
        self._btn.setText("リセット")
        self._running = False


app = QApplication(sys.argv)
window = TimerWindow()
window.show()
sys.exit(app.exec())
```

### QObject とシグナル/スロットの仕組み

PyQt6 のシグナル/スロットは、オブジェクト間を疎結合にするための仕組みです。

```
送信側 (TimerEngine)              受信側 (TimerWindow)
  self.tick.emit(30)   ────────▶  _on_tick(30) が呼ばれる
```

`pyqtSignal(int)` は「整数を1つ送るシグナル」の定義です。クラス変数として定義しますが、インスタンスメソッド内で `self.tick.emit(値)` として発火します。

**`connect()` で接続する先**は「スロット」と呼ばれる関数です。Pythonの普通のメソッドや、ラムダ関数も使えます。

```python
engine.tick.connect(widget.update_time)    # メソッド
engine.tick.connect(lambda sec: print(sec)) # ラムダ
```

**なぜシグナル/スロットを使うか**: 直接 `widget.update_time(sec)` と呼べば済む場面でも、シグナルを使うと送信側が受信側の存在を知らなくて済みます。エンジンはUIが何個あるかを気にせず、あとから受信者を追加・削除できます。

### QTimer の動作

`QTimer` はイベントループが動いている間だけ機能します。`start()` で起動すると、指定間隔ごとに `timeout` シグナルを発火します。`stop()` で停止します。`setSingleShot(True)` を設定すると1回だけ発火します。

---

## 6. Step 4: ホバーUI

マウスが乗ったときだけボタンをフェードインさせます。

```python
# step4_hover.py
import sys
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QApplication, QGraphicsOpacityEffect, QHBoxLayout,
    QToolButton, QVBoxLayout, QWidget, QLabel,
)


class HoverWidget(QWidget):
    def __init__(self):
        super().__init__()
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(200, 80)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        self._time_label = QLabel("25:00", self)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        layout.addWidget(self._time_label)

        # ── ボタンコンテナ（透明度エフェクト付き）──
        self._btn_container = QWidget(self)
        btn_layout = QHBoxLayout(self._btn_container)
        btn_layout.setContentsMargins(2, 0, 2, 0)
        btn_layout.setSpacing(4)

        for text in ["▶", "⏸", "⏭"]:
            btn = QToolButton(self)
            btn.setText(text)
            btn.setFixedSize(28, 22)
            btn.setStyleSheet(
                "QToolButton { background: rgba(255,255,255,40); border-radius:4px; color:white; }"
                "QToolButton:hover { background: rgba(255,255,255,80); }"
            )
            btn_layout.addWidget(btn)

        # QGraphicsOpacityEffect でウィジェット全体の不透明度を制御
        self._opacity_effect = QGraphicsOpacityEffect(self._btn_container)
        self._opacity_effect.setOpacity(0.0)  # 初期状態は完全透明
        self._btn_container.setGraphicsEffect(self._opacity_effect)
        self._btn_container.setVisible(False)  # レイアウト上のスペースも消す

        layout.addWidget(self._btn_container)

        # デバウンスタイマー（leaveEvent のガタつき防止）
        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(150)
        self._leave_timer.timeout.connect(self._on_leave_timeout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(20, 20, 20, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

    def enterEvent(self, event):
        super().enterEvent(event)
        self._leave_timer.stop()                 # フェードアウト予約をキャンセル
        self._btn_container.setVisible(True)
        self._animate_opacity(target=1.0)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # すぐにフェードアウトせず、150ms 待つ（デバウンス）
        self._leave_timer.start()

    def _on_leave_timeout(self):
        if self.underMouse():
            return   # まだマウスが内部にある
        anim = self._animate_opacity(target=0.0)
        anim.finished.connect(lambda: self._btn_container.setVisible(False))

    def _animate_opacity(self, target: float) -> QPropertyAnimation:
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(150)
        anim.setStartValue(self._opacity_effect.opacity())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        # 重要: ローカル変数のままだとGCされてアニメが止まる
        self._current_anim = anim
        return anim


app = QApplication(sys.argv)
w = HoverWidget()
w.move(100, 100)
w.show()
sys.exit(app.exec())
```

### QPropertyAnimation の仕組み

`QPropertyAnimation` は Qt プロパティ（`b"opacity"` のようにバイト列で指定）を開始値から終了値まで滑らかに変化させます。

```python
anim = QPropertyAnimation(対象オブジェクト, b"プロパティ名", parent)
anim.setDuration(150)          # アニメーション時間 (ms)
anim.setStartValue(0.0)        # 開始値
anim.setEndValue(1.0)          # 終了値
anim.setEasingCurve(...)       # 加速・減速曲線
anim.start()                   # 開始
```

`b"opacity"` の `b` はバイト列リテラルです。Qt のプロパティシステムはC++側で定義されており、バイト列で名前を渡します。

**`QGraphicsOpacityEffect`**: ウィジェット全体に透明度エフェクトをかけるクラスです。`setOpacity(0.0)` で完全透明、`setOpacity(1.0)` で完全不透明になります。`QPropertyAnimation` で `b"opacity"` プロパティをアニメーションさせることでフェード効果が得られます。

### デバウンスタイマーが必要な理由

```
ウィジェット
┌─────────────────┐
│  ボタン  ←───── マウスがここに移ると:
│  [▶][⏸][⏭]   │    親ウィジェットで leaveEvent 発火
│                 │    ボタンウィジェットで enterEvent 発火
└─────────────────┘
```

マウスがボタンに移動するたびに親ウィジェットで `leaveEvent` が発火します。デバウンス（150ms待機）なしだとボタンが点滅します。150ms後に `underMouse()` を確認し、まだマウスがウィジェット内にあればフェードアウトをキャンセルします。

---

## 7. Step 5: ドラッグ移動

タイトルバーがないため、ドラッグ移動を自前で実装します。

```python
# step5_drag.py
import sys
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


class DraggableWidget(QWidget):
    def __init__(self):
        super().__init__()
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(200, 80)

        layout = QVBoxLayout(self)
        label = QLabel("ドラッグして移動", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white;")
        layout.addWidget(label)

        self._drag_start: QPoint | None = None  # ドラッグ開始時のオフセット

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(20, 20, 20, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # グローバル座標（スクリーン全体基準）からウィジェット左上を引く
            # = 「ウィジェット内でクリックした位置」のオフセット
            self._drag_start = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start and event.buttons() & Qt.MouseButton.LeftButton:
            # 現在のグローバル座標からオフセットを引くと新しいウィジェット位置になる
            new_pos = event.globalPosition().toPoint() - self._drag_start
            clamped = self._clamp_to_screen(new_pos)
            self.move(clamped)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            # ここで位置を設定ファイルに保存するとよい
        super().mouseReleaseEvent(event)

    def _clamp_to_screen(self, pos: QPoint) -> QPoint:
        """ウィジェットが画面外に出ないよう座標を制限する"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return pos
        rect = screen.availableGeometry()
        x = max(rect.left(), min(pos.x(), rect.right() - self.width()))
        y = max(rect.top(), min(pos.y(), rect.bottom() - self.height()))
        return QPoint(x, y)


app = QApplication(sys.argv)
w = DraggableWidget()
w.move(200, 200)
w.show()
sys.exit(app.exec())
```

### ドラッグの計算

```
クリック時のグローバル座標: (500, 300)
ウィジェット左上のグローバル座標: (480, 290)
オフセット = (500-480, 300-290) = (20, 10)   ← _drag_start に保存

マウス移動後のグローバル座標: (600, 350)
新しいウィジェット位置 = (600-20, 350-10) = (580, 340)   ← ここに move()
```

このオフセット計算により、クリックした位置がウィジェット内のどこであっても、マウスとの相対位置が保たれたままドラッグできます。

### 画面端クランプ

`screen.availableGeometry()` はタスクバーを除いた使用可能な画面領域です。`max(left, min(pos, right - width))` でウィジェットが画面端からはみ出さないよう制限します。

---

## 8. Step 6: データの永続化

セッション履歴をJSONファイルに保存・読み込みします。

```python
# step6_history.py
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


def get_history_dir() -> Path:
    """OSに応じた適切な保存先ディレクトリを返す"""
    if sys.platform == "win32":
        # %APPDATA%\pmd-timers\history\ (例: C:\Users\user\AppData\Roaming\...)
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        # XDG Base Directory 仕様に従う (Linux)
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    history_dir = base / "pmd-timers" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)  # 初回起動時に作成
    return history_dir


@dataclass
class SessionRecord:
    date: str
    type: str          # "work" / "short_break" / "long_break"
    status: str        # "completed" / "interrupted"
    duration_sec: int


def save_session(session: SessionRecord) -> None:
    """セッションを当日のJSONファイルに追記保存する"""
    history_dir = get_history_dir()
    path = history_dir / f"{session.date}.json"

    # 既存ファイルを読み込む（なければ空の辞書）
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"date": session.date, "sessions": []}

    # セッションを追加
    data["sessions"].append({
        "type": session.type,
        "status": session.status,
        "duration_sec": session.duration_sec,
    })

    # アトミック書き込み（書き込み中のクラッシュでデータが壊れないよう一時ファイル経由）
    import tempfile, shutil
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8",
                                     dir=path.parent, suffix=".tmp") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
    shutil.move(tmp.name, path)

    print(f"保存: {path}")


def load_today() -> list[dict]:
    """今日のセッション一覧を返す"""
    history_dir = get_history_dir()
    today = date.today().isoformat()
    path = history_dir / f"{today}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sessions", [])


# 動作確認
if __name__ == "__main__":
    today = date.today().isoformat()
    save_session(SessionRecord(date=today, type="work", status="completed", duration_sec=1500))
    save_session(SessionRecord(date=today, type="short_break", status="completed", duration_sec=300))
    sessions = load_today()
    print(f"今日のセッション: {len(sessions)} 件")
    for s in sessions:
        print(f"  {s['type']} - {s['status']} ({s['duration_sec']}秒)")
```

### OS別パス解決の理由

各OSには「アプリがデータを保存すべき場所」の慣習があります。

| OS | パス |
|---|---|
| Windows | `%APPDATA%\pmd-timers\history\` |
| macOS | `~/Library/Application Support/pmd-timers/history/` |
| Linux | `~/.config/pmd-timers/history/` |

`Path.mkdir(parents=True, exist_ok=True)` は親ディレクトリも含めて再帰的に作成します。すでに存在してもエラーになりません。

### JSON設計のポイント

- `ensure_ascii=False`: 日本語などのUnicode文字をエスケープせずそのまま書き込みます
- `indent=2`: 人間が読みやすいよう2スペースインデントで整形します
- 1日1ファイル方式にすることで、特定日のデータだけを高速に読み書きできます

---

## 9. Step 7: 統計ダッシュボード

HistoryServiceからデータを集計してViewModelに変換し、別ウィンドウで表示します。

```python
# step7_dashboard.py
import sys
from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QApplication, QGroupBox, QLabel, QListWidget,
    QPushButton, QVBoxLayout, QWidget,
)


class SimpleHistoryService:
    """簡略版 HistoryService（step6の実装を使う場合はそちらに置き換える）"""
    def get_today_count(self) -> int:
        # 実際はJSONファイルを読む
        return 3  # ダミー

    def get_week_counts(self) -> list[tuple[str, int]]:
        # (日付ラベル, セッション数) のリスト
        today = date.today()
        result = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            label = f"{d.month}/{d.day}"
            count = [2, 4, 3, 0, 5, 3, 2][i]  # ダミーデータ
            result.append((label, count))
        return result


class DashboardWindow(QWidget):
    def __init__(self, history_svc: SimpleHistoryService):
        super().__init__()
        self.setWindowTitle("統計ダッシュボード")
        self.resize(400, 350)
        self._svc = history_svc
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 今日のサマリー
        today_group = QGroupBox("本日の記録")
        today_layout = QVBoxLayout()
        self._today_label = QLabel("", self)
        today_layout.addWidget(self._today_label)
        today_group.setLayout(today_layout)
        layout.addWidget(today_group)

        # 過去7日の簡易グラフ（テキストバー）
        week_group = QGroupBox("過去7日")
        week_layout = QVBoxLayout()
        self._week_list = QListWidget()
        week_layout.addWidget(self._week_list)
        week_group.setLayout(week_layout)
        layout.addWidget(week_group)

        refresh_btn = QPushButton("更新")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        self.refresh()

    def refresh(self):
        """データを再取得して表示を更新する"""
        count = self._svc.get_today_count()
        self._today_label.setText(f"完了セッション: {count} 件")

        self._week_list.clear()
        week_data = self._svc.get_week_counts()
        max_count = max((c for _, c in week_data), default=1)
        for label, count in week_data:
            bar = "█" * int(count / max_count * 10)
            self._week_list.addItem(f"{label:5s} {bar:<10s} {count}")


# ── メインウィンドウからダッシュボードを開く例 ──

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("メイン")
        self.resize(200, 100)
        self._svc = SimpleHistoryService()
        self._dashboard = None  # 遅延生成

        layout = QVBoxLayout(self)
        btn = QPushButton("統計を開く", self)
        btn.clicked.connect(self._open_dashboard)
        layout.addWidget(btn)

    def _open_dashboard(self):
        if self._dashboard is None or not self._dashboard.isVisible():
            # 初回、または閉じられていたら新規作成
            self._dashboard = DashboardWindow(self._svc)
            self._dashboard.show()
        else:
            # すでに開いていたら前面に出す
            self._dashboard.raise_()
            self._dashboard.activateWindow()


app = QApplication(sys.argv)
main_win = MainWindow()
main_win.show()
sys.exit(app.exec())
```

### ViewModelパターンとは

**ViewModel** は「ビュー（UI）のために加工されたデータを提供するオブジェクト」です。直接 `HistoryService` を UI で使うと、UIコードの中に「秒を時間:分に変換する」「日付ラベルを作る」といったロジックが混在します。ViewModelにそれらを集めることで、UIは `get_today_stats()` を呼ぶだけで済みます。

```
HistoryService（生データ）
    └── DashboardViewModel（加工・集計）
            └── DashboardWindow（表示するだけ）
```

### 別ウィンドウの開き方

```python
self._dashboard = DashboardWindow(vm)
self._dashboard.show()   # show() で別ウィンドウとして表示
```

`show()` を呼ぶだけで別ウィンドウとして表示されます。`self._dashboard` で参照を保持しないとすぐにGCされて消えてしまうため、インスタンス属性に代入します。`isVisible()` で既に開いているか確認し、二重に開かないようにします。

---

## 10. Step 8: PyInstallerでexe化

Windowsの単一実行ファイルを作成します。

```bash
# PyInstaller をインストール
pip install pyinstaller

# src ディレクトリに移動して実行
cd /path/to/pmd-timers

# ビルド
pyinstaller \
    --name PomodoroTimer \
    --onefile \
    --windowed \
    --add-data "src;src" \
    src/main.py
```

主なオプションの意味:

| オプション | 効果 |
|---|---|
| `--onefile` | すべてを1つの .exe にまとめる |
| `--windowed` | コンソールウィンドウを表示しない（GUIアプリ用） |
| `--add-data "src;src"` | `src/` ディレクトリをバンドルに含める（macOS/Linuxでは `:` 区切り） |
| `--name PomodoroTimer` | 出力ファイル名 |

ビルドが完了すると `dist/PomodoroTimer.exe` が生成されます。

### よくある問題

**ImportError: DLL load failed**: PyQt6のDLLが見つからない場合です。`--collect-all PyQt6` を追加することで全DLLをバンドルできます。

**PyQt6-Qt6-Charts が含まれない**: `--collect-all PyQt6.QtCharts` を追加します。

**アイコンを設定したい**: `--icon icon.ico` で指定できます。

### .spec ファイルの活用

`pyinstaller main.py` を一度実行すると `PomodoroTimer.spec` が生成されます。次回以降は:

```bash
pyinstaller PomodoroTimer.spec
```

で再ビルドできます。`.spec` ファイルに詳細な設定を書いておくと再現性が高まります。

---

## 11. まとめ・次のステップ

このチュートリアルで学んだ主なトピック:

| トピック | 使ったクラス/概念 |
|---|---|
| 基本ウィンドウ | `QApplication`, `QWidget`, `show()` |
| フレームレスウィンドウ | `FramelessWindowHint`, `WA_TranslucentBackground` |
| カスタム描画 | `paintEvent`, `QPainter`, `QColor` |
| タイマー | `QObject`, `QTimer`, `pyqtSignal` |
| アニメーション | `QPropertyAnimation`, `QGraphicsOpacityEffect` |
| ホバー検出 | `enterEvent`, `leaveEvent`, デバウンス |
| ドラッグ | `mousePressEvent`, `mouseMoveEvent` |
| 永続化 | `json`, `pathlib.Path`, OS別パス |
| ダッシュボード | ViewModelパターン, 複数ウィンドウ |
| パッケージング | PyInstaller |

### 次に学ぶとよいこと

- **QThread / asyncio 連携**: タイマーとは別のスレッドでネットワーク通信やファイルI/Oを行う方法
- **QSS（Qt Style Sheet）**: CSSライクな記法でウィジェットのスタイルを細かく制御する
- **QSettings**: プラットフォームに応じた設定保存（Windowsではレジストリ、macOSではplistを使う）
- **pytest-qt**: PyQt6アプリのユニットテストフレームワーク
- **Qt Designer**: GUIレイアウトをビジュアルで設計し `.ui` ファイルとして出力するツール

### コード全体を読む

このチュートリアルで作ったコードは pmd-timers の実装と対応しています。

| チュートリアル | 本実装 |
|---|---|
| `TimerEngine` | `src/engine/timer_engine.py` |
| セッションデータクラス | `src/engine/session.py` |
| `save_session()` | `src/services/history_service.py` |
| `DashboardViewModel` | `src/services/dashboard_viewmodel.py` |
| `FloatingWidget` | `src/ui/timer_widget.py` |
| `DashboardWindow` | `src/ui/dashboard_window.py` |

各ファイルの設計意図については `/home/onom/pmd-timers/docs/reference.md` を参照してください。
