"""Windows上で実行する、独立した配布フォルダのビルド。"""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if sys.platform != "win32":
    raise SystemExit("WindowsのPythonで実行してください。")
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--onedir",
        "--name",
        "FocusPomodoro",
        "--icon",
        str(root / "assets/focus.ico"),
        "--paths",
        str(root),
        "--distpath",
        str(root / "dist"),
        "--workpath",
        str(root / "build/focus"),
        "--specpath",
        str(root / "build"),
        "--add-data",
        str(root / "assets/sounds/notification.wav") + ";assets/sounds",
        "--hidden-import",
        "plyer.platforms.win.notification",
        str(root / "scripts/windows_entry.py"),
    ],
    cwd=root,
    check=True,
)
