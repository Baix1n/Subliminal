#!/usr/bin/env python3
import queue
import threading
import tkinter as tk
from argparse import Namespace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from generate_sub import generate


class LocalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SP Subliminal Generator")
        self.geometry("720x620")
        self.minsize(680, 560)
        self.events = queue.Queue()
        self.worker = None

        self.vars = {
            "voice_file": tk.StringVar(),
            "music_file": tk.StringVar(),
            "noise_file": tk.StringVar(),
            "output_dir": tk.StringVar(value=str(Path.cwd() / "outputs")),
            "name": tk.StringVar(value="my_sub"),
            "minutes": tk.StringVar(value="10"),
            "voice_layers": tk.StringVar(value="10000"),
            "voice_volume": tk.StringVar(value="0.02"),
            "music_volume": tk.StringVar(value="0.8"),
            "noise_volume": tk.StringVar(value="0.35"),
            "fade_seconds": tk.StringVar(value="6"),
            "frequencies": tk.StringVar(value=""),
            "tone_volume": tk.StringVar(value="0"),
            "sample_rate": tk.StringVar(value="44100"),
        }

        self.build_ui()
        self.after(100, self.poll_events)

    def build_ui(self):
        pad = {"padx": 16, "pady": 8}
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        title = ttk.Label(root, text="本地高密度人声生成", font=("", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        self.file_row(root, 1, "人声 WAV", "voice_file", self.pick_wav)
        self.file_row(root, 2, "背景音乐 WAV", "music_file", self.pick_wav)
        self.file_row(root, 3, "白噪音 WAV", "noise_file", self.pick_wav)
        self.file_row(root, 4, "输出文件夹", "output_dir", self.pick_folder)

        fields = ttk.LabelFrame(root, text="参数")
        fields.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=16, pady=10)
        fields.columnconfigure(1, weight=1)
        fields.columnconfigure(3, weight=1)

        self.entry(fields, 0, 0, "文件名", "name")
        self.entry(fields, 0, 2, "时长 分钟", "minutes")
        self.entry(fields, 1, 0, "人声层数", "voice_layers")
        self.entry(fields, 1, 2, "人声音量", "voice_volume")
        self.entry(fields, 2, 0, "音乐音量", "music_volume")
        self.entry(fields, 2, 2, "白噪音音量", "noise_volume")
        self.entry(fields, 3, 0, "淡入淡出 秒", "fade_seconds")
        self.entry(fields, 3, 2, "采样率", "sample_rate")
        self.entry(fields, 4, 0, "频率 Hz", "frequencies")
        self.entry(fields, 4, 2, "频率音量", "tone_volume")

        actions = ttk.Frame(root)
        actions.grid(row=6, column=0, columnspan=3, sticky="ew", padx=16, pady=8)
        actions.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(actions, mode="determinate", maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.generate_button = ttk.Button(actions, text="生成 WAV", command=self.start_generate)
        self.generate_button.grid(row=0, column=1)

        self.status = tk.StringVar(value="请选择 WAV 文件。上万层建议人声音量从 0.01 到 0.03 试。")
        status = ttk.Label(root, textvariable=self.status, wraplength=660)
        status.grid(row=7, column=0, columnspan=3, sticky="ew", **pad)

        root.columnconfigure(1, weight=1)
        root.rowconfigure(5, weight=1)

    def file_row(self, parent, row, label, key, picker):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=16, pady=6)
        ttk.Entry(parent, textvariable=self.vars[key]).grid(row=row, column=1, sticky="ew", padx=8, pady=6)
        ttk.Button(parent, text="选择", command=lambda: picker(key)).grid(row=row, column=2, padx=16, pady=6)

    def entry(self, parent, row, col, label, key):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=12, pady=8)
        ttk.Entry(parent, textvariable=self.vars[key]).grid(row=row, column=col + 1, sticky="ew", padx=12, pady=8)

    def pick_wav(self, key):
        path = filedialog.askopenfilename(filetypes=[("WAV audio", "*.wav"), ("All files", "*.*")])
        if path:
            self.vars[key].set(path)

    def pick_folder(self, key):
        path = filedialog.askdirectory()
        if path:
            self.vars[key].set(path)

    def build_args(self):
        voice_file = self.vars["voice_file"].get().strip()
        if not voice_file:
            raise ValueError("请先选择人声 WAV 文件。")

        return Namespace(
            voice_file=voice_file,
            music_file=self.vars["music_file"].get().strip() or None,
            noise_file=self.vars["noise_file"].get().strip() or None,
            output_dir=self.vars["output_dir"].get().strip() or "outputs",
            name=self.vars["name"].get().strip() or "my_sub",
            minutes=float(self.vars["minutes"].get()),
            voice_layers=int(self.vars["voice_layers"].get()),
            voice_volume=float(self.vars["voice_volume"].get()),
            music_volume=float(self.vars["music_volume"].get()),
            noise_volume=float(self.vars["noise_volume"].get()),
            fade_seconds=float(self.vars["fade_seconds"].get()),
            frequencies=self.vars["frequencies"].get().strip(),
            tone_volume=float(self.vars["tone_volume"].get()),
            sample_rate=int(self.vars["sample_rate"].get()),
            chunk_seconds=10,
        )

    def start_generate(self):
        if self.worker and self.worker.is_alive():
            return
        try:
            args = self.build_args()
            if args.voice_layers < 1:
                raise ValueError("人声层数必须大于等于 1。")
            if args.voice_layers > 100000:
                raise ValueError("人声层数建议不超过 100000。")
        except Exception as exc:
            messagebox.showerror("参数有误", str(exc))
            return

        self.progress["value"] = 0
        self.status.set("正在生成，请稍等...")
        self.generate_button.state(["disabled"])
        self.worker = threading.Thread(target=self.run_generate, args=(args,), daemon=True)
        self.worker.start()

    def run_generate(self, args):
        try:
            output = generate(args, progress=lambda value: self.events.put(("progress", value)))
            self.events.put(("done", output))
        except Exception as exc:
            self.events.put(("error", exc))

    def poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    self.progress["value"] = payload * 100
                elif kind == "done":
                    self.generate_button.state(["!disabled"])
                    self.progress["value"] = 100
                    self.status.set(f"已生成：{payload}")
                    messagebox.showinfo("完成", f"已生成：\n{payload}")
                elif kind == "error":
                    self.generate_button.state(["!disabled"])
                    self.status.set("生成失败。")
                    messagebox.showerror("生成失败", str(payload))
        except queue.Empty:
            pass
        self.after(100, self.poll_events)


if __name__ == "__main__":
    LocalApp().mainloop()
