from __future__ import annotations

import random
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import keyboard
import mss
import numpy as np
import pyautogui
import pyperclip
import tkinter as tk
from tkinter import ttk

try:
    import winsound  # Windows-only
except Exception:
    winsound = None

SCRIPT_DIR = Path(__file__).resolve().parent
TEXT_FILE = SCRIPT_DIR / "metinim.txt"

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}
FOLDER_CONFIG: Dict[str, Optional[str]] = {
    "Folder_Type_A": None,  # Click only
    "Folder_Type_Y": "y",   # Click and send 'y'
}

pyautogui.PAUSE = 0


@dataclass(frozen=True)
class TemplateConfig:
    path: Path
    folder: str
    post_key: Optional[str]


def discover_templates() -> List[TemplateConfig]:
    templates: List[TemplateConfig] = []
    for folder, post_key in FOLDER_CONFIG.items():
        folder_path = SCRIPT_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        for file in sorted(folder_path.iterdir()):
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
                templates.append(TemplateConfig(file, folder, post_key))
    return templates


def load_text_lines(path: Path) -> List[str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[warn] Text file not found: {path}")
        return []
    except UnicodeDecodeError:
        raw = path.read_text(encoding="utf-8-sig")
    lines = [line.rstrip("\r").lstrip("\ufeff") for line in raw.splitlines()]
    if not lines:
        print(f"[info] Text file is empty: {path}")
    return lines


def type_text_lines(
    lines: List[str],
    stop_event: threading.Event,
    typing_cancel: threading.Event,
) -> bool:
    for idx, line in enumerate(lines, start=1):
        if stop_event.is_set() or typing_cancel.is_set():
            print(f"[info] Text playback interrupted at line {idx}.")
            return False
        text = line
        if text:
            try:
                keyboard.write(text, delay=0.02)  # ~20ms per char
            except Exception as e:
                print(f"[warn] keyboard.write failed: {e}")
                return False
        try:
            keyboard.send("ctrl+j")
        except Exception as e:
            print(f"[warn] keyboard.send('ctrl+j') failed: {e}")
            return False
        time.sleep(random.uniform(0.015, 0.2))
    return True


def get_monitors() -> List[Dict[str, int]]:
    with mss.mss() as sct:
        monitors = [
            {
                "left": m["left"],
                "top": m["top"],
                "width": m["width"],
                "height": m["height"],
            }
            for m in sct.monitors[1:]
        ]
    return monitors


def point_monitor_index(x: int, y: int, monitors: List[Dict[str, int]]) -> int:
    for idx, m in enumerate(monitors, start=1):
        if (
            x >= m["left"]
            and y >= m["top"]
            and x < m["left"] + m["width"]
            and y < m["top"] + m["height"]
        ):
            return idx
    return 0


def _load_templates(
    templates: List[TemplateConfig],
) -> List[Tuple[TemplateConfig, np.ndarray, Tuple[int, int]]]:
    loaded: List[Tuple[TemplateConfig, np.ndarray, Tuple[int, int]]] = []
    for config in templates:
        try:
            tpl = cv2.imread(str(config.path), cv2.IMREAD_COLOR)
            if tpl is None:
                print(f"[warn] Could not read image: {config.path}")
                continue
            h, w = tpl.shape[:2]
            loaded.append((config, tpl, (w, h)))
        except Exception as e:
            print(f"[warn] Error reading image '{config.path}': {e}")
    return loaded


def _send_post_key(action: str) -> None:
    try:
        keyboard.send(action)
        print(f"[key] Sent '{action}'")
    except Exception as e:
        print(f"[warn] Failed to send '{action}': {e}")


def find_and_click(
    templates: List[TemplateConfig],
    threshold: float,
    retry_ms: int,
    timeout_ms: int,
) -> Optional[TemplateConfig]:
    if not templates:
        print("[info] No templates available to search.")
        return None

    print(
        f"[info] Searching {len(templates)} template(s) "
        f"threshold={threshold}, retry={retry_ms}ms, timeout={timeout_ms}ms"
    )

    loaded = _load_templates(templates)
    if not loaded:
        print("[error] No valid images to search. Aborting search.")
        return None

    start = time.monotonic()
    with mss.mss() as sct:
        monitors = [m for m in sct.monitors[1:]]
        if not monitors:
            print("[error] No physical monitors detected.")
            return None

        while (time.monotonic() - start) * 1000 < timeout_ms:
            best_val: float = -1.0
            best_loc: Optional[Tuple[int, int]] = None
            best_tpl_size: Optional[Tuple[int, int]] = None
            best_monitor: Optional[Dict[str, int]] = None
            best_template: Optional[TemplateConfig] = None

            for mon in monitors:
                try:
                    frame = np.array(sct.grab(mon))
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                except Exception as e:
                    print(f"[warn] Screen grab failed for monitor {mon}: {e}")
                    continue

                for cfg, tpl, (tw, th) in loaded:
                    try:
                        res = cv2.matchTemplate(frame_bgr, tpl, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    except Exception as e:
                        print(f"[warn] matchTemplate failed for {cfg.path.name}: {e}")
                        continue

                    if max_val > best_val:
                        best_val = max_val
                        best_loc = max_loc
                        best_tpl_size = (tw, th)
                        best_monitor = mon
                        best_template = cfg

            if (
                best_template
                and best_loc
                and best_tpl_size
                and best_monitor
                and best_val >= threshold
            ):
                gx = int(best_monitor["left"] + best_loc[0] + best_tpl_size[0] / 2)
                gy = int(best_monitor["top"] + best_loc[1] + best_tpl_size[1] / 2)
                monitor_index = next(
                    (
                        idx
                        for idx, mon in enumerate(monitors, start=1)
                        if mon is best_monitor
                    ),
                    0,
                )
                print(
                    f"[match] {best_template.path.name} (folder={best_template.folder}) "
                    f"monitor#{monitor_index} score={best_val:.3f} center=({gx},{gy})"
                )
                try:
                    pyautogui.moveTo(gx, gy)
                    pyautogui.click()
                    print(f"[click] Clicked at ({gx},{gy})")
                    if best_template.post_key:
                        time.sleep(0.1)
                        _send_post_key(best_template.post_key)
                except Exception as e:
                    print(f"[warn] pyautogui interaction failed: {e}")
                return best_template

            time.sleep(max(0.0, retry_ms / 1000.0))

    print("[debug] No image matched within timeout.")
    return None


class Hud:
    def __init__(self, root: tk.Tk, monitors: List[Dict[str, int]]) -> None:
        self.root = root
        self.monitors = monitors
        self.win: Optional[tk.Toplevel] = None
        self.label: Optional[tk.Label] = None
        self.job: Optional[str] = None

    def show(self) -> None:
        if self.win is not None:
            return
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.attributes("-alpha", 0.9)
        except Exception:
            pass

        frame = ttk.Frame(self.win, padding=(8, 6))
        frame.pack(fill=tk.BOTH, expand=True)
        self.label = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg="#222222",
            fg="#f0f0f0",
            padx=8,
            pady=4,
        )
        self.label.pack()
        self._update()

    def hide(self) -> None:
        if self.job is not None:
            try:
                self.root.after_cancel(self.job)
            except Exception:
                pass
            self.job = None
        if self.win is not None:
            try:
                self.win.destroy()
            except Exception:
                pass
            self.win = None
            self.label = None

    def _update(self) -> None:
        try:
            pos = pyautogui.position()
            x, y = int(pos.x), int(pos.y)
        except Exception:
            x, y = 0, 0
        mon_idx = point_monitor_index(x, y, self.monitors)
        if self.label and self.win:
            self.label.config(text=f"X: {x}  Y: {y}  Mon: {mon_idx}")
            mon = (
                self.monitors[mon_idx - 1]
                if 1 <= mon_idx <= len(self.monitors)
                else None
            )
            if mon:
                self.win.update_idletasks()
                ww = self.win.winfo_width()
                wh = self.win.winfo_height()
                nx = mon["left"] + mon["width"] - ww - 20
                ny = mon["top"] + 20
                try:
                    self.win.geometry(f"{ww}x{wh}+{nx}+{ny}")
                except Exception:
                    pass
        self.job = self.root.after(30, self._update)


def show_toast(
    root: tk.Tk,
    monitors: List[Dict[str, int]],
    text: str,
    duration_ms: int = 800,
    bg: str = "#333333",
    fg: str = "#ffffff",
    wraplength: int = 460,
) -> None:
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    try:
        win.attributes("-alpha", 0.92)
    except Exception:
        pass
    frame = ttk.Frame(win, padding=(8, 6))
    frame.pack(fill=tk.BOTH, expand=True)
    label = tk.Label(
        frame,
        text=text,
        font=("Segoe UI", 10, "bold"),
        bg=bg,
        fg=fg,
        padx=10,
        pady=6,
        wraplength=wraplength,
        justify="left",
    )
    label.pack()

    try:
        pos = pyautogui.position()
        x, y = int(pos.x), int(pos.y)
    except Exception:
        x, y = 0, 0
    idx = point_monitor_index(x, y, monitors)
    mon = monitors[idx - 1] if 1 <= idx <= len(monitors) else monitors[0]
    win.update_idletasks()
    ww = win.winfo_width()
    wh = win.winfo_height()
    nx = mon["left"] + mon["width"] - ww - 20
    ny = mon["top"] + 20
    try:
        win.geometry(f"{ww}x{wh}+{nx}+{ny}")
    except Exception:
        pass

    def _destroy() -> None:
        try:
            win.destroy()
        except Exception:
            pass

    root.after(duration_ms, _destroy)


def _alert_not_found(root: tk.Tk, monitors: List[Dict[str, int]]) -> None:
    show_toast(
        root,
        monitors,
        "Eşleşme bulunamadı.",
        duration_ms=1500,
        bg="#bb2222",
        fg="#ffffff",
    )
    if winsound:
        try:
            winsound.Beep(800, 250)
        except Exception:
            try:
                winsound.MessageBeep()
            except Exception:
                pass
    else:
        sys.stdout.write("\a")
        sys.stdout.flush()


def _show_start_instructions(root: tk.Tk, monitors: List[Dict[str, int]]) -> None:
    msg = (
        "Kısayollar: F8 = HUD, Ctrl+Shift+C = Koordinat kopyala, F9 = metinim.txt yaz, "
        "ESC = çıkış.\n"
        "Görsel eşleşmesi bulunduğunda ilgili klasör için tanımlanan tuş gönderilir ve 3 sn beklenir."
    )
    show_toast(root, monitors, msg, duration_ms=9000, wraplength=520)


def main() -> None:
    threshold: float = 0.85
    retry_ms: int = 120
    timeout_ms: int = 6000

    monitors = get_monitors()
    if not monitors:
        print("[error] No monitors detected via MSS.")
        return

    root = tk.Tk()
    root.withdraw()

    hud = Hud(root, monitors)

    stop_event = threading.Event()
    typing_cancel_event = threading.Event()
    typing_lock = threading.Lock()

    def notify(text: str, **kwargs: object) -> None:
        root.after(0, lambda: show_toast(root, monitors, text, **kwargs))

    def _runner() -> None:
        first_run = True
        while not stop_event.is_set():
            templates = discover_templates()
            if not templates:
                if first_run:
                    notify(
                        "Folder_Type_A ve Folder_Type_Y klasörlerine görseller ekleyin.",
                        duration_ms=2000,
                        bg="#bb2222",
                    )
                time.sleep(0.5)
                first_run = False
                continue
            match = find_and_click(templates, threshold, retry_ms, timeout_ms)
            if match:
                print("[cooldown] Sleeping 3.0s after match.")
                t_end = time.monotonic() + 3.0
                while time.monotonic() < t_end and not stop_event.is_set():
                    time.sleep(0.05)
            else:
                if first_run:
                    _alert_not_found(root, monitors)
                time.sleep(0.05)
            first_run = False

    worker = threading.Thread(target=_runner, name="finder", daemon=True)
    worker.start()

    def _copy_coords() -> None:
        try:
            pos = pyautogui.position()
            x, y = int(pos.x), int(pos.y)
            pyperclip.copy(f"{x},{y}")
            notify(f"Copied: {x},{y}")
        except Exception as e:
            notify(f"Copy failed: {e}", bg="#bb2222")

    def _start_text_writer() -> None:
        if typing_lock.locked():
            notify("Metin yazımı zaten devam ediyor.", duration_ms=1200)
            return

        def _worker() -> None:
            with typing_lock:
                typing_cancel_event.clear()
                lines = load_text_lines(TEXT_FILE)
                if not lines:
                    notify("metinim.txt bulunamadı veya boş.", bg="#bb2222", duration_ms=1800)
                    return
                notify("Metin yazımı başlatıldı.", duration_ms=1200)
                completed = type_text_lines(lines, stop_event, typing_cancel_event)
                if completed and not stop_event.is_set():
                    notify("Metin yazımı tamamlandı.", duration_ms=1200)
                else:
                    notify("Metin yazımı durduruldu.", bg="#bb2222", duration_ms=1600)

        threading.Thread(target=_worker, name="text-writer", daemon=True).start()

    keyboard.on_press_key("f8", lambda _: root.after(0, hud.show))
    keyboard.on_release_key("f8", lambda _: root.after(0, hud.hide))
    keyboard.add_hotkey("ctrl+shift+c", lambda: root.after(0, _copy_coords))
    keyboard.add_hotkey("f9", lambda: root.after(0, _start_text_writer))

    def _on_exit() -> None:
        typing_cancel_event.set()
        try:
            hud.hide()
        finally:
            try:
                stop_event.set()
            except Exception:
                pass
            try:
                root.quit()
            except Exception:
                pass
            try:
                root.destroy()
            except Exception:
                pass
            try:
                keyboard.unhook_all()
            except Exception:
                pass

    keyboard.add_hotkey("esc", _on_exit)

    _show_start_instructions(root, monitors)
    print("Ready. Continuous search running.")
    print("F8: HUD | Ctrl+Shift+C: copy mouse coords | F9: type metinim.txt | ESC: exit")

    try:
        root.mainloop()
    except KeyboardInterrupt:
        _on_exit()


if __name__ == "__main__":
    main()
