import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import webbrowser
from tkinter import TclError

import keyboard


class GuiLogger:
    def __init__(self, widget):
        self.widget = widget
        self.lock = threading.Lock()
        self.queue = []
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

    def write(self, s):
        if not s:
            return
        with self.lock:
            self.queue.append(s)
        try:
            self.widget.after(0, self._flush)
        except TclError:
            pass
        except Exception:
            pass

    def _flush(self):
        try:
            with self.lock:
                items = self.queue
                self.queue = []
            for s in items:
                self.widget.insert(tk.END, s)
                self.widget.see(tk.END)
        except TclError:
            pass

    def flush(self):
        pass

    def install(self):
        sys.stdout = self
        sys.stderr = self

    def restore(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr


class TriggerBotApp:
    def __init__(self, settings):
        self.settings = settings
        self.bot_thread = None
        self.capture_thread = None
        self.logger = None

        self.root = tk.Tk()
        self.root.title("CS2 TriggerBot")
        self.root.geometry("500x400")
        self.root.minsize(400, 400)
        self.root.attributes('-topmost', True)

        self.build_ui()
        self.load_ui_values()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        padx = 12
        pady = 6

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(5, weight=1)

        title = ttk.Label(self.root, text="CS2 TriggerBot", font=("Segoe UI", 14, "bold"))
        title.grid(row=0, column=0, pady=(12, 8))

        # Settings frame
        settings_frame = ttk.LabelFrame(self.root, text="Settings", padding=(10, 5))
        settings_frame.grid(row=1, column=0, sticky="ew", padx=padx, pady=pady)
        settings_frame.columnconfigure(1, weight=1)

        # Trigger key
        ttk.Label(settings_frame, text="Trigger key:").grid(row=0, column=0, sticky="w", pady=pady)
        self.trigger_key_var = tk.StringVar()
        self.trigger_key_entry = ttk.Entry(settings_frame, textvariable=self.trigger_key_var, width=14, state="readonly")
        self.trigger_key_entry.grid(row=0, column=1, sticky="w", padx=padx, pady=pady)
        self.set_key_btn = ttk.Button(settings_frame, text="Set key", command=self.start_key_capture, width=10)
        self.set_key_btn.grid(row=0, column=2, sticky="e", pady=pady)

        # Delay before click
        ttk.Label(settings_frame, text="Delay before click (s):").grid(row=1, column=0, sticky="w", pady=pady)
        delay_frame = ttk.Frame(settings_frame)
        delay_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=padx, pady=pady)
        self.delay_min_var = tk.StringVar()
        self.delay_max_var = tk.StringVar()
        ttk.Entry(delay_frame, textvariable=self.delay_min_var, width=8).pack(side="left")
        ttk.Label(delay_frame, text=" - ").pack(side="left")
        ttk.Entry(delay_frame, textvariable=self.delay_max_var, width=8).pack(side="left")

        # Hold time
        ttk.Label(settings_frame, text="Hold time (s):").grid(row=2, column=0, sticky="w", pady=pady)
        hold_frame = ttk.Frame(settings_frame)
        hold_frame.grid(row=2, column=1, columnspan=2, sticky="w", padx=padx, pady=pady)
        self.hold_min_var = tk.StringVar()
        self.hold_max_var = tk.StringVar()
        ttk.Entry(hold_frame, textvariable=self.hold_min_var, width=8).pack(side="left")
        ttk.Label(hold_frame, text=" - ").pack(side="left")
        ttk.Entry(hold_frame, textvariable=self.hold_max_var, width=8).pack(side="left")

        # Checkboxes
        self.check_team_var = tk.BooleanVar()
        self.enabled_var = tk.BooleanVar()

        cb_frame = ttk.Frame(settings_frame)
        cb_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=pady)
        ttk.Checkbutton(
            cb_frame, text="Check enemy team", variable=self.check_team_var, command=self.save_checkboxes
        ).pack(side="left", padx=(0, 10))
        ttk.Checkbutton(
            cb_frame, text="Enabled", variable=self.enabled_var, command=self.save_checkboxes
        ).pack(side="left")

        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, foreground="green")
        self.status_label.grid(row=2, column=0, pady=(4, 0))

        # Info
        info = ttk.Label(self.root, text="Changes are saved automatically.", font=("Segoe UI", 8), foreground="gray")
        info.grid(row=3, column=0, pady=(0, 6))

        # Logs
        logs_label = ttk.Label(self.root, text="Logs", font=("Segoe UI", 10, "bold"))
        logs_label.grid(row=4, column=0, sticky="w", padx=padx, pady=(8, 0))

        self.log_widget = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state="normal", height=10)
        self.log_widget.grid(row=5, column=0, sticky="nsew", padx=padx, pady=(0, 6))
        self.log_widget.config(font=("Consolas", 9))

        self.logger = GuiLogger(self.log_widget)

        # About button
        about_btn = ttk.Button(self.root, text="About", command=self.show_about)
        about_btn.grid(row=6, column=0, sticky="e", padx=padx, pady=(0, 12))

        self.bind_entries()

    def bind_entries(self):
        for var in (self.delay_min_var, self.delay_max_var, self.hold_min_var, self.hold_max_var):
            var.trace_add("write", lambda *args, v=var: self.save_numbers(v))

    def load_ui_values(self):
        cfg = self.settings.get()
        self.trigger_key_var.set(cfg.trigger_key)
        self.delay_min_var.set(str(cfg.delay_min))
        self.delay_max_var.set(str(cfg.delay_max))
        self.hold_min_var.set(str(cfg.hold_min))
        self.hold_max_var.set(str(cfg.hold_max))
        self.check_team_var.set(cfg.check_team)
        self.enabled_var.set(cfg.enabled)

    def save_numbers(self, changed_var=None):
        try:
            delay_min = float(self.delay_min_var.get())
            delay_max = float(self.delay_max_var.get())
            hold_min = float(self.hold_min_var.get())
            hold_max = float(self.hold_max_var.get())

            if delay_min < 0 or delay_max < 0 or hold_min < 0 or hold_max < 0:
                return
            if delay_min > delay_max or hold_min > hold_max:
                return

            self.settings.set(
                delay_min=delay_min,
                delay_max=delay_max,
                hold_min=hold_min,
                hold_max=hold_max
            )
            self.settings.save()
            self.status_var.set("Saved")
            self.status_label.configure(foreground="green")
        except ValueError:
            pass

    def save_checkboxes(self):
        self.settings.set(
            check_team=self.check_team_var.get(),
            enabled=self.enabled_var.get()
        )
        self.settings.save()
        self.status_var.set("Saved")
        self.status_label.configure(foreground="green")

    def start_key_capture(self):
        if self.capture_thread and self.capture_thread.is_alive():
            return
        self.trigger_key_var.set("Press a key...")
        self.set_key_btn.configure(state="disabled")
        self.capture_thread = threading.Thread(target=self.capture_key, daemon=True)
        self.capture_thread.start()

    def capture_key(self):
        try:
            event = keyboard.read_event(suppress=False)
            if event.event_type == keyboard.KEY_DOWN:
                key = event.name
                if key:
                    key = key.lower()
                    self.settings.set(trigger_key=key)
                    self.settings.save()
                    self.root.after(0, lambda: self.trigger_key_var.set(key))
                    self.root.after(0, lambda: self.status_var.set(f"Trigger key set to: {key}"))
                    self.root.after(0, lambda: self.status_label.configure(foreground="green"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
            self.root.after(0, lambda: self.status_label.configure(foreground="red"))
        finally:
            self.root.after(0, lambda: self.set_key_btn.configure(state="normal"))

    def install_logger(self):
        if self.logger:
            self.logger.install()

    def uninstall_logger(self):
        if self.logger:
            self.logger.restore()

    def set_bot_thread(self, bot_thread):
        self.bot_thread = bot_thread

    def on_close(self):
        if self.bot_thread:
            self.bot_thread.running = False
        self.uninstall_logger()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    def show_about(self):
        about = tk.Toplevel(self.root)
        about.title("About")
        about.geometry("360x180")
        about.resizable(False, False)
        about.attributes('-topmost', True)
        about.transient(self.root)

        ttk.Label(about, text="CS2 TriggerBot", font=("Segoe UI", 12, "bold")).pack(pady=(16, 8))
        ttk.Label(about, text="Original code by im-razvan").pack()

        link = ttk.Label(
            about,
            text="https://github.com/im-razvan/CS2_TriggerBot/",
            foreground="blue",
            cursor="hand2"
        )
        link.pack(pady=(6, 12))
        link.bind("<Button-1>", self._open_github)

    def _open_github(self, event=None):
        try:
            webbrowser.open("https://github.com/im-razvan/CS2_TriggerBot/")
        except Exception as e:
            self.status_var.set(f"Failed to open link: {e}")
            self.status_label.configure(foreground="red")

        ttk.Button(about, text="Close", command=about.destroy).pack(pady=(0, 12))
