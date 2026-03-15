# コードリファレンス — pmd-timers

対象読者: Python中級者（PyQt6/GUI未経験）

---

## 1. アーキテクチャ概要

pmd-timers は3層アーキテクチャで構成されています。上位層は下位層に依存しますが、逆方向の依存はありません。

```
┌─────────────────────────────────────────────────────────┐
│                        ui/ 層                           │
│  TimerWidget  │  DashboardWindow  │  SettingsDialog     │
│              SessionBarChart                            │
│  ─────────────────────────────────────────────────────  │
│  表示・入力を担当。ビジネスロジックは一切持たない。        │
└──────────────────────┬──────────────────────────────────┘
                       │ シグナル/コールバック
┌──────────────────────▼──────────────────────────────────┐
│                    services/ 層                         │
│   HistoryService  │  DashboardViewModel                 │
│   SettingsService │  NotificationService                │
│  ─────────────────────────────────────────────────────  │
│  永続化・集計・通知など「アプリのロジック」を担当。        │
└──────────────────────┬──────────────────────────────────┘
                       │ データクラス / シグナル
┌──────────────────────▼──────────────────────────────────┐
│                     engine/ 層                          │
│        session.py  │  timer_engine.py                   │
│  ─────────────────────────────────────────────────────  │
│  純粋なドメインロジック。                                 │
│  session.py はデータクラスのみ（Qt依存なし）。            │
│  timer_engine.py は状態機械＋Qtタイマー。                │
└─────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    main.py                              │
│  全層のインスタンスを生成し、シグナルを配線する。          │
└─────────────────────────────────────────────────────────┘
```

**なぜこの構造か**

- `engine/session.py` はPure Pythonなので、Qt環境なしにユニットテストできます。
- `TimerEngine` は `QObject` を継承してシグナルを持ちますが、UIの知識を持ちません。
- `ui/` 層はエンジンへの参照を持たず、コールバック（ラムダ）経由で操作します。これにより各層を独立してテスト・交換できます。

---

## 2. engine/ レイヤー

### 2-1. session.py — データクラスと列挙型

`session.py` はQtを一切インポートしない純粋なPythonモジュールです。アプリ全体で使うデータ型とバリデーションロジックを集約しています。

#### 列挙型

| クラス | 値 | 用途 |
|---|---|---|
| `Phase` | IDLE / WORKING / SHORT_BREAK / LONG_BREAK / PAUSED | タイマーの「現在の状態」。`TimerEngine` が管理する。 |
| `SessionType` | WORK / SHORT_BREAK / LONG_BREAK | セッション記録の種別。`Phase` と似ているが IDLE・PAUSED は存在しない。 |
| `SessionStatus` | COMPLETED / INTERRUPTED / SKIPPED | セッションが正常終了したか中断されたかを記録する。 |

`Phase` と `SessionType` を分けている理由: `Phase` はリアルタイムな状態機械の「今この瞬間」を表し、`SessionType` はすでに始まったセッションの「記録上の種類」を表します。IDLEやPAUSEDというセッションは記録しないため、別の型が必要です。

#### TimerSession — セッション1件の記録

```python
@dataclass
class TimerSession:
    type: SessionType
    date: str                   # "YYYY-MM-DD"
    start_time: str             # ISO8601 形式
    scheduled_duration_sec: int # 予定秒数（設定値から算出）
    session_index: int          # サイクル内の何番目か（1〜N）
    cycle_number: int           # 何サイクル目か（リセットごとに+1）
    id: str                     # UUID4（デフォルトで自動生成）
    end_time: Optional[str]     # 終了時刻（完了・中断時に記録）
    actual_duration_sec: int    # 実際に経過した秒数
    status: SessionStatus       # デフォルトは INTERRUPTED
```

`to_dict()` / `from_dict()` でJSONへの直列化・復元が可能です。デフォルトの `status` を `INTERRUPTED` にしている理由は、途中でプロセスが落ちた場合でもファイルに書き込んだセッションが「完了」扱いにならないようにするためです。

#### TimerState — エンジン内部の可変状態

```python
@dataclass
class TimerState:
    phase: Phase = Phase.IDLE
    pre_pause_phase: Optional[Phase] = None  # 一時停止前のフェーズを記憶
    remaining_sec: int = 0
    current_session_index: int = 1
    daily_completed_count: int = 0
    is_sleep_paused: bool = False
    sleep_start_time: Optional[datetime] = None
```

`pre_pause_phase` がある理由: 一時停止（PAUSED）から再開する際、「作業中だったか休憩中だったか」を覚えておく必要があるためです。

#### 設定クラス群

設定は責務ごとに4つのデータクラスに分割され、`AppSettings` に集約されています。

```
AppSettings
├── TimerSettings      # 作業・休憩時間、セッション数など
├── BehaviorSettings   # 自動開始など
├── NotificationSettings # 通知音・デスクトップ通知
└── WidgetDisplaySettings # 不透明度・位置・サイズなど
```

各クラスの `validate()` メソッドは、範囲外の値が設定ファイルから読み込まれた場合に早期にエラーを発生させます。`AppSettings.to_dict()` / `from_dict()` でJSONへの一括変換が可能です。

#### DailyRecord — 1日分の集計

`DailyRecord` は1日単位のファイル（`YYYY-MM-DD.json`）に対応するデータクラスです。`add_session()` を呼ぶたびに各カウンタが自動集計されます。

---

### 2-2. timer_engine.py — 状態機械

`TimerEngine` は `QObject` を継承したポモドーロタイマーの心臓部です。外部からは `start()` / `pause()` / `resume()` / `reset()` / `skip()` という5つのAPIで操作します。

#### シグナル定義

```python
class TimerEngine(QObject):
    tick = pyqtSignal(int)                  # 毎秒: remaining_sec
    phase_changed = pyqtSignal(str, int)    # フェーズ変化時: phase.value, session_index
    session_completed = pyqtSignal(object)  # セッション完了/中断時: TimerSession
    daily_count_updated = pyqtSignal(int)   # 本日完了数が変化: completed_count
```

`phase_changed` が `Phase` オブジェクトではなく `str`（`phase.value`）を送る理由: シグナルに独自クラスを乗せるとPyQt6の型チェックが厳しくなる場合があるためです。受信側で `Phase(phase_val)` と変換して使います。

#### 状態遷移図

```
         start()
  ┌──── IDLE ─────────────────────────────────────────┐
  │      │                                             │
  │      ▼                                             │
  │   WORKING ──── pause() ──── PAUSED                 │
  │      │                        │                   │
  │      │ (タイムアップ)          │ start()/resume()   │
  │      ▼                        │                   │
  │  [セッション数 < N?]           │                   │
  │   YES ──▶ SHORT_BREAK ◀───────┘                   │
  │   NO  ──▶ LONG_BREAK  ◀───────┘                   │
  │      │                                             │
  │      │ (タイムアップ)                               │
  │      ▼                                             │
  │   [auto_start?]                                    │
  │   YES ──▶ WORKING (次のセッション)                  │
  │   NO  ──▶ IDLE                                     │
  │                                                    │
  └── reset() で常に IDLE へ戻る ─────────────────────┘

  ※ skip() は現フェーズから強制的に _advance_phase() を呼ぶ
  ※ LONG_BREAK 後は current_session_index が 1 にリセットされ、
    cycle_number が +1 される
```

#### 内部フロー: 1秒ごとの処理

```
QTimer(1000ms) → _on_tick()
  └─ remaining_sec -= 1
  └─ actual_duration_sec += 1
  └─ tick シグナル emit
  └─ remaining_sec == 0 なら:
       _qt_timer.stop()
       → _on_phase_complete()
            └─ _finalize_session(COMPLETED)
            └─ _advance_phase()
```

`_finalize_session()` はセッションに `end_time` と `status` をセットしてから `session_completed` シグナルを emit します。シグナルを emit した後に `self._current_session = None` をクリアするのではなく、その**前**に `None` を代入している点に注意してください。これはシグナルハンドラが再入してもセッションが二重に完了しないようにするためです。

---

## 3. services/ レイヤー

### 3-1. HistoryService — JSON永続化

`HistoryService` はセッション履歴を1日1ファイルのJSONで管理するサービスです。`QObject` を継承しているため、`session_recorded` シグナルを発火してUIに更新を知らせることができます。

#### ファイルパス解決

```python
def _get_history_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", ...))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "pmd-timers" / "history"
```

各OSの標準的なアプリデータ保存場所に従います。`history_dir.mkdir(parents=True, exist_ok=True)` で起動時に自動作成されます。

#### 主要メソッド

| メソッド | 説明 |
|---|---|
| `record_session(session)` | セッションを当日のJSONに追記・保存し、`session_recorded` を emit |
| `load_daily(date_str)` | `YYYY-MM-DD.json` を読んで `DailyRecord` を返す。存在しなければ `None` |
| `load_period(start, end)` | 期間内の日付をイテレートして `DailyRecord` のリストを返す |
| `get_streak()` | 今日から遡って連続達成日数を数える（90日上限） |
| `cleanup(keep_days=90)` | 90日より古いJSONを削除して返り値に削除数を返す |

`record_session()` は既存レコードを `load_daily()` で読み込み、`add_session()` で集計してから上書き保存します。ファイルが存在しない場合は新しい `DailyRecord` を作成します。

---

### 3-2. DashboardViewModel — 集計ロジック

`DashboardViewModel` はHistoryServiceから取得したデータをUIに適した形式に変換します。GUIのViewModelパターンをシンプルに実装したものです。

#### 提供するデータ型

```python
@dataclass
class TodayStats:
    completed_count: int
    interrupted_count: int
    total_work_time_str: str  # "2時間30分" のような文字列
    short_breaks: int
    long_breaks: int
    current_streak_days: int

@dataclass
class DailyCount:
    date: str
    label: str   # "3/15" のような表示用ラベル
    count: int   # その日の完了セッション数

@dataclass
class PeriodStats:
    daily_counts: list[DailyCount]  # グラフ用
    total_completed: int
    best_day_date: str | None
    best_day_count: int
```

#### get_period_stats() の設計

`Period.THIS_WEEK` は「過去7日間」（今日を含む）、`Period.THIS_MONTH` は「今月1日から今日まで」です。データがない日も `DailyCount(count=0)` として含めるため、グラフが連続して表示されます（歯抜けにならない）。

`_cache` フィールドはあるものの、現在は `refresh()` で毎回クリアされています。将来的なパフォーマンス最適化のための足がかりです。

---

## 4. ui/ レイヤー

### 4-1. TimerWidget — フレームレス常時最前面ウィジェット

`TimerWidget` はポモドーロタイマーのメインウィンドウです。OS標準のウィンドウ枠を持たず、常に最前面に表示されます。

#### ウィンドウフラグの組み合わせ

```python
flags = (
    Qt.WindowType.FramelessWindowHint   # タイトルバー・枠なし
    | Qt.WindowType.WindowStaysOnTopHint # 常に最前面
    | Qt.WindowType.Tool                 # タスクバーに表示しない
)
self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 背景を透明に
```

`WA_TranslucentBackground` を設定すると、ウィジェットの背景がOSによって透明化されます。ただし単純に何も描かなければ透明になるだけなので、`paintEvent` で丸角矩形を自分で描画します。

#### paintEvent による背景描画

```python
def paintEvent(self, event) -> None:
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    opacity = self._settings.ui.window_opacity
    bg_alpha = min(255, round(_BG_BASE_ALPHA / max(opacity, 0.2)))
    painter.setBrush(QColor(20, 20, 20, bg_alpha))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(self.rect(), 8, 8)
```

`setWindowOpacity()` はウィジェット全体（テキストを含む）を一律に半透明化します。そのためウィンドウ透明度が低いほど背景のアルファを逆補正し、テキストが読みやすい濃さを保ちます。

#### ホバーUI（enterEvent / leaveEvent）

ボタン群は通常非表示（`setVisible(False)`）で、マウスが重なったときだけフェードインします。

```
enterEvent
  └─ _leave_timer.stop()         # 誤ったフェードアウトをキャンセル
  └─ _btn_container.setVisible(True)
  └─ QPropertyAnimation (opacity: 現在値 → 1.0)

leaveEvent
  └─ _leave_timer.start(150ms)   # デバウンス: すぐには消さない

_on_leave_timeout (150ms後)
  └─ underMouse() チェック → まだ内部なら中止
  └─ QPropertyAnimation (opacity: 現在値 → 0.0)
  └─ finished → setVisible(False)
```

**デバウンスが必要な理由**: `QWidget` の内部にある子ウィジェット（ボタンなど）にマウスが移動すると、親ウィジェットで `leaveEvent` が発火します。150msのデバウンスを挟むことで、子ウィジェット境界を通過するたびにチカチカするのを防ぎます。

**アニメーション参照を保持する理由**: `QPropertyAnimation` はローカル変数として作ると関数を抜けた瞬間にガベージコレクトされ、アニメーションが途中で止まります。`self._fade_in_anim = anim` のように属性として持つことで生存期間を保証します。

#### ドラッグ移動

```python
def mousePressEvent(self, event):
    self._drag_start = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

def mouseMoveEvent(self, event):
    new_pos = event.globalPosition().toPoint() - self._drag_start
    self.move(self._clamp_to_screen(new_pos))

def mouseReleaseEvent(self, event):
    self._drag_start = None
    self._save_position()  # 設定ファイルに位置を保存
```

`globalPosition()` はスクリーン座標、`frameGeometry().topLeft()` はウィジェットの左上のスクリーン座標です。差分を取ることで「マウスをクリックした位置からの相対距離」を `_drag_start` に保存します。`_clamp_to_screen()` で画面外に出ないよう境界を制限します。

#### コールバックパターン

`TimerWidget` はエンジンへの直接参照を持ちません。代わりに `on_start`, `on_pause` などのコールバック属性（デフォルトは何もしないラムダ）を `main.py` で上書きします。これにより `TimerWidget` はエンジンの存在を知らなくて済みます。

---

### 4-2. DashboardWindow — 統計表示

`DashboardWindow` は別ウィンドウとして開く統計ダッシュボードです。

#### _StatCard — 再利用可能なカードコンポーネント

```python
class _StatCard(QFrame):
    def __init__(self, title: str, value: str = "–", parent=None):
        ...
    def set_value(self, value: str) -> None:
        self._value.setText(value)
```

タイトルと値を縦並びにした小さなパネルです。`_` プレフィックスはモジュール外から使わないことを示すPythonの慣習です。

#### 期間フィルター

3つのチェック可能な `QPushButton` を `QButtonGroup` に追加しています。`QButtonGroup` は排他的選択（一度に1つだけON）を自動管理するため、ラジオボタン的な動作を実現できます。

#### リアルタイム更新

`main.py` でダッシュボードを開く際に:

```python
history_svc.session_recorded.connect(dashboard.refresh_stats)
```

を接続します。セッションが完了するたびに `HistoryService` が `session_recorded` を emit し、`DashboardWindow.refresh_stats()` が自動的に呼ばれます。

---

### 4-3. SessionBarChart — グラフ/テキストフォールバック

```python
try:
    from PyQt6.QtCharts import QBarCategoryAxis, QBarSet, ...
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
```

`PyQt6-Qt6-Charts` はオプション依存として扱い、インポートに失敗した場合はテキストベースの棒グラフにフォールバックします。これにより最小インストール構成でもアプリが動作します。

**テキストフォールバックの仕組み**:
`QGridLayout` に3列（日付ラベル / `█` 文字の棒 / 数値）を並べることで棒グラフを模倣します。棒の長さは `bar_len = int(dc.count / max_count * 12)` で正規化されます。

**QtChartsを使う場合のデータ更新**:
グラフを更新するたびに `removeAllSeries()` と軸の削除を行い、ゼロから再構築します。QtChartsは系列と軸の管理が密結合しているため、差分更新よりも全再構築の方がシンプルです。

---

### 4-4. SettingsDialog

`SettingsDialog` は `QDialog` のサブクラスです。`exec()` を呼ぶとモーダル（他のウィンドウを操作できなくなる）で表示されます。

- `QSpinBox`: 数値の入力フォーム（`setRange` で最小・最大値を設定）
- `QSlider`: スライダー。`valueChanged` シグナルでリアルタイムに `QLabel` を更新
- `QDialogButtonBox`: OK/キャンセルボタンを標準的に配置するウィジェット。`ResetRole` でリセットボタンも追加できる

`_apply()` は `accepted` シグナルに接続されており、OKボタン押下時に `self._settings` を直接書き換えます。`AppSettings` がデータクラスなので参照渡しの挙動となり、`SettingsDialog` の外側（`main.py`）が同じオブジェクトを参照していれば自動的に更新が反映されます。

---

## 5. main.py — シグナル配線の全体像

`main()` 関数はすべてのコンポーネントを生成し、シグナルとコールバックを配線するだけに集中しています。

```
engine.tick            → widget.update_time
engine.phase_changed   → widget.update_phase (Phase変換あり)
engine.phase_changed   → tray.update_icon_for_phase
engine.daily_count_updated → widget.update_daily_count
engine.session_completed   → history_svc.record_session  ← 永続化
history_svc.session_recorded → dashboard.refresh_stats   ← リアルタイム更新

widget.on_start   = engine.start
widget.on_pause   = lambda: engine.pause() or engine.resume()
widget.on_reset   = engine.reset
widget.on_skip    = engine.skip
widget.on_open_settings  = open_settings  (クロージャ)
widget.on_open_dashboard = open_dashboard (クロージャ)
widget.on_quit    = quit_app
```

`open_dashboard()` はクロージャです。`nonlocal dashboard` を使い、ダッシュボードが既に開いている場合は `raise_()` で前面に出します。新規作成した場合のみ `session_recorded` シグナルを接続します（二重接続を防ぐため）。

`app.setQuitOnLastWindowClosed(False)` の意味: デフォルトでは最後のウィンドウを閉じるとアプリが終了しますが、このアプリはシステムトレイから操作するため、ウィンドウを隠してもアプリが継続する必要があります。

---

## 6. 重要な設計判断

### 6-1. engine/ に Qt 依存を最小化する

`session.py` は Qt を一切インポートしません。`TimerEngine` だけが `QObject` を継承します。これにより `session.py` のデータクラスは pytest で直接テストでき、Qt のイベントループを起動する必要がありません。

### 6-2. シグナルとコールバックの使い分け

| 方向 | 手段 | 理由 |
|---|---|---|
| Engine → UI (通知) | pyqtSignal | 1対多の通知。複数の受信者（widget + tray）に同時に届く |
| UI → Engine (命令) | コールバック属性 | UIがエンジンを直接参照しないようにするため |
| Service → Service | pyqtSignal | `history_svc.session_recorded` → `dashboard.refresh_stats` の連鎖 |

### 6-3. DailyRecord の即時集計

`DailyRecord.add_session()` はセッション追加と同時にカウンタを集計します。読み込み時に毎回 `sessions` リストを走査して集計する代わりに、書き込み時点で集計済みにすることでJSONファイルが可読性のある形式になります。

### 6-4. ウィジェット位置の保存タイミング

ドラッグ終了時（`mouseReleaseEvent`）に位置を保存します。ムーブ中は保存しません。理由はパフォーマンスよりも書き込み頻度の抑制です。設定サービスが注入されていない場合（テスト時など）はメモリ上の `settings` オブジェクトだけを更新します。

### 6-5. PyInstallerとの互換性

`from __future__ import annotations` が各ファイルの先頭にあります。これはPython 3.10+で導入された「遅延評価アノテーション」をPython 3.7+で利用可能にするためです。PyInstallerでバンドルする際にも型アノテーションが評価されないため、ランタイムエラーを防ぎます。
