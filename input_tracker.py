import json
import queue
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from pynput import keyboard, mouse


class InputTrackerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Input Tracker")
        self.root.geometry("860x540")

        self.mouse_controller = mouse.Controller()
        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.events = []
        self.recording = False
        self.recording_start = 0.0
        self.window_hidden_for_recording = False
        self.toggle_hotkey = keyboard.Key.f8
        self.save_hotkey = keyboard.Key.f9
        self.hotkey_pressed = False
        self.save_hotkey_pressed = False

        self.position_var = tk.StringVar(value="X: 0, Y: 0")
        self.status_var = tk.StringVar(value="Status: idle")

        self._build_ui()
        self._start_listeners()
        self._schedule_tasks()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(container)
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="Mouse Pixel Position:", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        ttk.Label(top_bar, textvariable=self.position_var, font=("Consolas", 11)).pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(top_bar, textvariable=self.status_var, foreground="#0a5").pack(side=tk.LEFT)

        button_bar = ttk.Frame(container)
        button_bar.pack(fill=tk.X, pady=(12, 8))

        ttk.Button(button_bar, text="Start Recording (F8)", command=self.start_recording).pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Stop Recording (F8)", command=self.stop_recording).pack(side=tk.LEFT, padx=8)
        ttk.Button(button_bar, text="Save Log (F9)", command=self.save_log).pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=8)

        hint = (
            "Records keyboard and mouse actions while recording is active. "
            "Mouse coordinates are updated in real time. Press F8 to start/stop recording and F9 to save."
        )
        ttk.Label(container, text=hint).pack(anchor=tk.W, pady=(0, 8))

        self.log_text = tk.Text(container, wrap=tk.NONE, height=24)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        x_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.log_text.xview)
        y_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        x_scroll.pack(fill=tk.X)
        y_scroll.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")

    def _start_listeners(self) -> None:
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def _schedule_tasks(self) -> None:
        self._update_mouse_position()
        self._flush_log_queue()

    def _update_mouse_position(self) -> None:
        try:
            x, y = self.mouse_controller.position
            self.position_var.set(f"X: {x}, Y: {y}")
        finally:
            self.root.after(50, self._update_mouse_position)

    def _flush_log_queue(self) -> None:
        while not self.log_queue.empty():
            line = self.log_queue.get_nowait()
            self.log_text.insert(tk.END, line + "\n")
            self.log_text.see(tk.END)
        self.root.after(80, self._flush_log_queue)

    def _elapsed(self) -> float:
        return time.time() - self.recording_start if self.recording_start else 0.0

    def _append_event(self, device: str, action: str, detail: dict) -> None:
        if not self.recording:
            return

        event = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "elapsed_seconds": round(self._elapsed(), 3),
            "device": device,
            "action": action,
            "detail": detail,
        }
        self.events.append(event)
        self.log_queue.put(json.dumps(event, ensure_ascii=True))

    def _normalize_key(self, key) -> str:
        if isinstance(key, keyboard.KeyCode):
            return key.char or "<none>"
        return str(key)

    def _on_mouse_move(self, x: int, y: int) -> None:
        self._append_event("mouse", "move", {"x": x, "y": y})

    def _on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        self._append_event(
            "mouse",
            "click",
            {
                "x": x,
                "y": y,
                "button": str(button),
                "pressed": pressed,
            },
        )

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        self._append_event(
            "mouse",
            "scroll",
            {
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
            },
        )

    def _on_key_press(self, key) -> None:
        if key == self.toggle_hotkey:
            if not self.hotkey_pressed:
                self.hotkey_pressed = True
                self.toggle_recording()
            return
        if key == self.save_hotkey:
            if not self.save_hotkey_pressed:
                self.save_hotkey_pressed = True
                self.save_log()
            return
        self._append_event("keyboard", "press", {"key": self._normalize_key(key)})

    def _on_key_release(self, key) -> None:
        if key == self.toggle_hotkey:
            self.hotkey_pressed = False
            return
        if key == self.save_hotkey:
            self.save_hotkey_pressed = False
            return
        self._append_event("keyboard", "release", {"key": self._normalize_key(key)})

    def toggle_recording(self) -> None:
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        if self.recording:
            return
        self.events = []
        self.recording = True
        self.recording_start = time.time()
        self.status_var.set("Status: recording")
        self.log_queue.put("--- Recording started ---")
        self.root.withdraw()
        self.window_hidden_for_recording = True

    def stop_recording(self) -> None:
        if not self.recording:
            return
        self.recording = False
        if self.window_hidden_for_recording:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.window_hidden_for_recording = False
        self.status_var.set(f"Status: stopped ({len(self.events)} events)")
        self.log_queue.put("--- Recording stopped ---")

    def clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)
        self.events = []
        self.status_var.set("Status: idle")

    def save_log(self) -> None:
        if not self.events:
            messagebox.showinfo("Save Log", "No events to save.")
            return

        log_dir = Path.cwd() / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        target = log_dir / f"input_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

        lines = [json.dumps(item, ensure_ascii=True) for item in self.events]
        target.write_text("\n".join(lines), encoding="utf-8")

        messagebox.showinfo("Save Log", f"Saved {len(self.events)} events to:\n{target}")

    def _on_close(self) -> None:
        try:
            self.mouse_listener.stop()
            self.keyboard_listener.stop()
        finally:
            self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = InputTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
