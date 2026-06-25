#!/usr/bin/env python3
import http.server
import json
import queue
import re
import socket
import socketserver
import time
import threading
import urllib.parse
import urllib.request
import webbrowser
import wave
import tkinter as tk
from argparse import Namespace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


DEFAULT_AFFIRMATIONS = {
    "general": [
        "我很安全，我也很值得被爱。",
        "{selfName}允许自己放松下来，被真诚地选择。",
        "{selfName}的吸引力来自稳定、自然和真实的自己。",
        "我不需要追逐，我只需要回到自己的价值感。",
        "我值得拥有清晰、稳定、互相喜欢的关系。",
        "每一次沉默都不能定义我的价值。",
        "{selfName}越来越自信，越来越有魅力，越来越被珍惜。",
        "真正适合我的关系，会以健康、诚实、温柔的方式靠近我。",
        "{selfName}被看见，被欣赏，被认真对待。",
    ],
    "sp": [
        "我很安全，我也很值得被爱。",
        "{selfName}允许自己放松下来，被真诚地选择。",
        "我和{spName}之间的互动轻松、自然、舒服。",
        "{spName}在想到{selfName}时，感到温暖、安心和好奇。",
        "我不需要追逐，我只需要回到自己的价值感。",
        "我值得拥有清晰、稳定、互相喜欢的关系。",
        "每一次联系都可以自然发生，每一次沉默也不能定义我的价值。",
        "{selfName}越来越自信，越来越有魅力，越来越被珍惜。",
        "我尊重自己，也尊重{spName}的自由和感受。",
        "真正适合我的关系，会以健康、诚实、温柔的方式靠近我。",
    ],
    "money": [
        "{selfName}允许自己接住更多机会和资源。",
        "{selfName}值得拥有稳定、丰盛、持续增长的收入。",
        "金钱以清晰、健康、安心的方式流向{selfName}。",
        "{selfName}越来越会选择高价值机会。",
        "{selfName}的能力被看见，付出得到合理回报。",
        "{selfName}对财富、工作和未来越来越有安全感。",
    ],
    "study": [
        "{selfName}学习时越来越专注、清醒、稳定。",
        "{selfName}理解知识很快，也记得牢。",
        "{selfName}在考试和作业中发挥自然、顺利。",
        "{selfName}每天都在靠近理想成绩。",
        "{selfName}相信自己的节奏，也愿意持续行动。",
        "{selfName}被适合自己的学校、机会和结果支持。",
    ],
}

INTENT_NOTES = {
    "general": "通用模式不会指向特定对象，适合自信、关系、状态稳定类 sub。",
    "sp": "SP 模式会使用特定对象名字，适合做关系、联系、复合或吸引主题。",
    "money": "金钱 / 事业模式适合丰盛、机会、事业、offer、收入和财运主题。",
    "study": "学业 / 考试模式适合学习专注、成绩、考试、录取、论文和 GPA 主题。",
}

FREQUENCY_THEMES = [
    ("爱情关系", [528, 639], ["爱", "爱情", "喜欢", "关系", "恋爱", "复合", "亲密", "吸引", "靠近", "联系", "互动", "珍惜", "选择", "sp"]),
    ("自信价值", [396, 528], ["自信", "价值", "魅力", "漂亮", "美", "被看见", "被欣赏", "值得", "安全感", "稳定"]),
    ("平静睡眠", [174, 432], ["平静", "放松", "睡眠", "安心", "安全", "疗愈", "稳定", "不焦虑", "释怀", "冷静"]),
    ("沟通表达", [639, 741], ["沟通", "表达", "消息", "聊天", "联系", "诚实", "清晰", "回应", "开口", "说话"]),
    ("行动显化", [285, 852], ["显化", "实现", "机会", "行动", "改变", "靠近", "自然发生", "顺利", "同步", "吸引"]),
    ("金钱丰盛", [285, 528, 852], ["钱", "金钱", "财富", "富", "丰盛", "收入", "存款", "中奖", "好运", "财运", "工作", "事业", "offer", "薪水", "赚钱"]),
    ("学业专注", [396, 432, 741], ["学习", "学业", "考试", "成绩", "分数", "绩点", "gpa", "专注", "记忆", "理解", "作业", "论文", "录取", "学校", "大学"]),
    ("直觉灵感", [741, 852], ["直觉", "灵感", "清醒", "看清", "觉察", "内在", "自由", "释放"]),
]

PRESET_FREQUENCIES = [
    (174, "放松/安定"),
    (285, "更新/机会"),
    (396, "释放/突破"),
    (432, "平静/睡眠"),
    (528, "爱/温柔"),
    (639, "关系/沟通"),
    (741, "表达/专注"),
    (852, "直觉/丰盛"),
]


class QuietServer(socketserver.TCPServer):
    allow_reuse_address = True


class LocalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SP Subliminal Generator")
        self.geometry("1080x760")
        self.minsize(960, 700)
        self.events = queue.Queue()
        self.worker = None
        self.library_worker = None
        self.recording_stream = None
        self.recording_chunks = []
        self.web_server = None
        self.library_results = []

        self.vars = {
            "voice_file": tk.StringVar(),
            "music_file": tk.StringVar(),
            "noise_file": tk.StringVar(),
            "output_dir": tk.StringVar(value=str(Path.cwd() / "outputs")),
            "name": tk.StringVar(value="manifest_track"),
            "self_name": tk.StringVar(value="我"),
            "sp_name": tk.StringVar(value="SP"),
            "intent_mode": tk.StringVar(value="general"),
            "affirmation_mode": tk.StringVar(value="default"),
            "minutes": tk.StringVar(value="10"),
            "voice_layers": tk.StringVar(value="10000"),
            "voice_volume": tk.StringVar(value="0.02"),
            "music_volume": tk.StringVar(value="0.8"),
            "noise_volume": tk.StringVar(value="0.35"),
            "fade_seconds": tk.StringVar(value="6"),
            "custom_frequencies": tk.StringVar(value=""),
            "tone_volume": tk.StringVar(value="0"),
            "sample_rate": tk.StringVar(value="44100"),
            "library_query": tk.StringVar(value="romantic ambient"),
            "library_type": tk.StringVar(value="music"),
        }
        self.frequency_vars = {value: tk.BooleanVar(value=False) for value, _ in PRESET_FREQUENCIES}
        self.value_entries = {}
        self.scales = {}

        self.configure_style()
        self.build_ui()
        self.sync_intent()
        self.after(100, self.poll_events)

    def configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("", 18, "bold"))
        style.configure("Section.TLabelframe.Label", font=("", 10, "bold"))
        style.configure("Generate.TButton", font=("", 11, "bold"), padding=(16, 8))

    def build_ui(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="本地 Subliminal 工作台", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="桌面版和网页版都是完整工作台；桌面版额外支持本地高层数生成。").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Button(header, text="打开网页版", command=self.open_web_version).grid(row=0, column=1, rowspan=2, sticky="e")

        files = ttk.LabelFrame(root, text="音频文件", style="Section.TLabelframe")
        files.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        files.columnconfigure(1, weight=1)
        self.file_row(files, 0, "人声 WAV（必填）", "voice_file", self.pick_wav)
        self.file_row(files, 1, "背景音乐 WAV", "music_file", self.pick_wav)
        self.file_row(files, 2, "白噪音 / 频率音 WAV", "noise_file", self.pick_wav)
        self.file_row(files, 3, "输出文件夹", "output_dir", self.pick_folder)

        body = ttk.PanedWindow(root, orient="horizontal")
        body.grid(row=2, column=0, sticky="nsew")
        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=1)
        body.add(right, weight=1)
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        main_params = ttk.LabelFrame(left, text="混音参数", style="Section.TLabelframe")
        main_params.grid(row=0, column=0, sticky="ew")
        main_params.columnconfigure(1, weight=1)
        self.slider(main_params, 0, "时长", "minutes", 1, 60, 1, " 分钟", as_int=True)
        self.slider(main_params, 1, "人声层数", "voice_layers", 1, 50000, 1, " 层", as_int=True)
        self.slider(main_params, 2, "人声音量", "voice_volume", 0, 0.16, 0.001, "", precision=3)
        self.slider(main_params, 3, "音乐音量", "music_volume", 0, 1, 0.01, "", precision=2)
        self.slider(main_params, 4, "白噪音音量", "noise_volume", 0, 1, 0.01, "", precision=2)
        self.slider(main_params, 5, "淡入淡出", "fade_seconds", 0, 30, 1, " 秒", as_int=True)

        presets = ttk.LabelFrame(left, text="层数预设", style="Section.TLabelframe")
        presets.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        presets.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(presets, text="清晰 3 层", command=lambda: self.apply_preset(3, 0.055)).grid(row=0, column=0, sticky="ew", padx=8, pady=10)
        ttk.Button(presets, text="高密度 100 层", command=lambda: self.apply_preset(100, 0.035)).grid(row=0, column=1, sticky="ew", padx=8, pady=10)
        ttk.Button(presets, text="上万层 10000", command=lambda: self.apply_preset(10000, 0.02)).grid(row=0, column=2, sticky="ew", padx=8, pady=10)

        output = ttk.LabelFrame(left, text="输出", style="Section.TLabelframe")
        output.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        output.columnconfigure(1, weight=1)
        self.entry(output, 0, "文件名", "name")
        self.sample_rate(output, 1)

        actions = ttk.LabelFrame(left, text="生成", style="Section.TLabelframe")
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(actions, mode="determinate", maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        self.generate_button = ttk.Button(actions, text="生成 WAV", style="Generate.TButton", command=self.start_generate)
        self.generate_button.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.status = tk.StringVar(value="请先选择人声 WAV 文件。上万层建议人声音量从 0.01 到 0.03 试。")
        ttk.Label(actions, textvariable=self.status, wraplength=440, justify="left").grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        tabs = ttk.Notebook(right)
        tabs.grid(row=0, column=0, sticky="nsew")
        self.build_affirmation_tab(tabs)
        self.build_frequency_tab(tabs)
        self.build_library_tab(tabs)

    def build_affirmation_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="主题 / 肯定句")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)
        self.entry(frame, 0, "你的名字", "self_name")
        ttk.Label(frame, text="主题模式").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        mode = ttk.Combobox(
            frame,
            textvariable=self.vars["intent_mode"],
            values=("general", "sp", "money", "study"),
            state="readonly",
        )
        mode.grid(row=1, column=1, sticky="ew", padx=8, pady=8)
        mode.bind("<<ComboboxSelected>>", lambda _event: self.sync_intent())
        self.intent_note = ttk.Label(frame, wraplength=430, justify="left")
        self.intent_note.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        self.sp_label = ttk.Label(frame, text="SP 名字")
        self.sp_entry = ttk.Entry(frame, textvariable=self.vars["sp_name"])
        self.sp_label.grid(row=3, column=0, sticky="w", padx=8, pady=8)
        self.sp_entry.grid(row=3, column=1, sticky="ew", padx=8, pady=8)
        ttk.Label(frame, text="肯定句模式").grid(row=4, column=0, sticky="w", padx=8, pady=8)
        mode_row = ttk.Frame(frame)
        mode_row.grid(row=4, column=1, sticky="ew", padx=8, pady=8)
        ttk.Radiobutton(mode_row, text="默认 + 自定义", variable=self.vars["affirmation_mode"], value="default").pack(side="left")
        ttk.Radiobutton(mode_row, text="只用自定义", variable=self.vars["affirmation_mode"], value="custom").pack(side="left", padx=(16, 0))
        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 8))
        ttk.Button(buttons, text="填入默认文案", command=self.fill_default_text).pack(side="left")
        ttk.Button(buttons, text="清空文案", command=self.clear_text).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="预览最终文案", command=self.preview_affirmations).pack(side="left", padx=(8, 0))
        self.custom_text = tk.Text(frame, height=12, wrap="word", undo=True)
        self.custom_text.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)

    def build_frequency_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="频率")
        frame.columnconfigure(0, weight=1)
        grid = ttk.LabelFrame(frame, text="频率选择", style="Section.TLabelframe")
        grid.grid(row=0, column=0, sticky="ew")
        for index, (value, label) in enumerate(PRESET_FREQUENCIES):
            row, col = divmod(index, 2)
            ttk.Checkbutton(grid, text=f"{value} Hz  {label}", variable=self.frequency_vars[value]).grid(row=row, column=col, sticky="w", padx=12, pady=8)
        custom = ttk.LabelFrame(frame, text="自定义频率", style="Section.TLabelframe")
        custom.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        custom.columnconfigure(1, weight=1)
        self.entry(custom, 0, "频率 Hz", "custom_frequencies")
        self.slider(custom, 1, "频率音量", "tone_volume", 0, 0.05, 0.001, "", precision=3)
        tools = ttk.Frame(frame)
        tools.grid(row=2, column=0, sticky="ew", pady=12)
        ttk.Button(tools, text="分析文案并推荐", command=self.apply_recommended_frequencies).pack(side="left")
        ttk.Button(tools, text="清空频率", command=self.clear_frequencies).pack(side="left", padx=(8, 0))
        self.recommendation = tk.StringVar(value="推荐会根据文案关键词匹配主题频率；想加入频率音时再把频率音量调到 0.003-0.01。")
        ttk.Label(frame, textvariable=self.recommendation, wraplength=430, justify="left").grid(row=3, column=0, sticky="ew")

    def build_library_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="音乐库 / 录音")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        recorder = ttk.LabelFrame(frame, text="录音", style="Section.TLabelframe")
        recorder.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        recorder.columnconfigure(2, weight=1)
        self.record_button = ttk.Button(recorder, text="开始录音", command=self.start_recording)
        self.record_button.grid(row=0, column=0, sticky="ew", padx=8, pady=10)
        self.stop_record_button = ttk.Button(recorder, text="停止并设为人声", command=self.stop_recording, state="disabled")
        self.stop_record_button.grid(row=0, column=1, sticky="ew", padx=8, pady=10)
        self.record_status = tk.StringVar(value="录音状态：待机")
        ttk.Label(recorder, textvariable=self.record_status).grid(row=0, column=2, sticky="w", padx=8, pady=10)

        search = ttk.LabelFrame(frame, text="开放音乐库", style="Section.TLabelframe")
        search.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text="搜索词").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(search, textvariable=self.vars["library_query"]).grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        ttk.Button(search, text="推荐关键词", command=self.suggest_library_query).grid(row=0, column=2, sticky="ew", padx=8, pady=8)
        type_row = ttk.Frame(search)
        type_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
        ttk.Radiobutton(type_row, text="音乐", variable=self.vars["library_type"], value="music").pack(side="left")
        ttk.Radiobutton(type_row, text="白噪音 / 频率音", variable=self.vars["library_type"], value="noise").pack(side="left", padx=(16, 0))
        ttk.Button(search, text="搜索 WAV 音频", command=self.start_library_search).grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 10))

        results = ttk.LabelFrame(frame, text="搜索结果", style="Section.TLabelframe")
        results.grid(row=2, column=0, sticky="nsew")
        results.columnconfigure(0, weight=1)
        results.rowconfigure(0, weight=1)
        self.library_list = tk.Listbox(results, height=8)
        self.library_list.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        scrollbar = ttk.Scrollbar(results, orient="vertical", command=self.library_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=8)
        self.library_list.configure(yscrollcommand=scrollbar.set)
        row = ttk.Frame(results)
        row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        row.columnconfigure((0, 1), weight=1)
        ttk.Button(row, text="下载并使用选中音频", command=self.start_library_download).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(row, text="打开作品页", command=self.open_selected_landing).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.library_status = tk.StringVar(value="搜索会优先返回可直接下载的 WAV 音频。使用前请核对作品页授权。")
        ttk.Label(results, textvariable=self.library_status, wraplength=430, justify="left").grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))

    def file_row(self, parent, row, label, key, picker):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=12, pady=7)
        ttk.Entry(parent, textvariable=self.vars[key]).grid(row=row, column=1, sticky="ew", padx=8, pady=7)
        ttk.Button(parent, text="选择", command=lambda: picker(key)).grid(row=row, column=2, padx=12, pady=7)

    def entry(self, parent, row, label, key):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(parent, textvariable=self.vars[key]).grid(row=row, column=1, sticky="ew", padx=8, pady=8)

    def slider(self, parent, row, label, key, from_, to, step, suffix="", as_int=False, precision=2):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=12, pady=8)
        scale = ttk.Scale(parent, from_=from_, to=to, orient="horizontal")
        scale.grid(row=row, column=1, sticky="ew", padx=8, pady=8)
        value_entry = ttk.Entry(parent, textvariable=self.vars[key], width=12, justify="right")
        value_entry.grid(row=row, column=2, sticky="e", padx=12, pady=8)
        self.value_entries[key] = value_entry

        def normalize(value):
            snapped = round(float(value) / step) * step
            snapped = max(from_, min(to, snapped))
            if as_int:
                snapped = int(round(snapped))
                return snapped, str(snapped)
            return snapped, f"{snapped:.{precision}f}"

        def set_value(value):
            _snapped, text = normalize(value)
            self.vars[key].set(text)

        def commit_entry(_event=None):
            try:
                snapped, text = normalize(self.vars[key].get())
            except ValueError:
                snapped, text = normalize(scale.get())
            self.vars[key].set(text)
            scale.set(snapped)

        if suffix:
            ttk.Label(parent, text=suffix.strip()).grid(row=row, column=3, sticky="w", padx=(0, 12), pady=8)
        else:
            ttk.Label(parent, text="").grid(row=row, column=3, sticky="w", padx=(0, 12), pady=8)
        value_entry.bind("<Return>", commit_entry)
        value_entry.bind("<FocusOut>", commit_entry)

        scale.configure(command=set_value)
        scale.set(float(self.vars[key].get()))
        commit_entry()
        self.scales[key] = scale

    def sample_rate(self, parent, row):
        ttk.Label(parent, text="采样率").grid(row=row, column=0, sticky="w", padx=8, pady=8)
        box = ttk.Combobox(parent, textvariable=self.vars["sample_rate"], values=("44100", "48000"), state="readonly")
        box.grid(row=row, column=1, sticky="ew", padx=8, pady=8)

    def apply_preset(self, layers, volume):
        self.scales["voice_layers"].set(layers)
        self.scales["voice_volume"].set(volume)
        self.status.set(f"已应用预设：{layers} 层，人声音量 {volume:.3f}。")

    def sync_intent(self):
        mode = self.vars["intent_mode"].get()
        self.intent_note.configure(text=INTENT_NOTES.get(mode, INTENT_NOTES["general"]))
        if mode == "sp":
            self.sp_label.grid()
            self.sp_entry.grid()
        else:
            self.sp_label.grid_remove()
            self.sp_entry.grid_remove()

    def rendered_default_affirmations(self):
        mode = self.vars["intent_mode"].get()
        self_name = self.vars["self_name"].get().strip() or "我"
        sp_name = self.vars["sp_name"].get().strip() or "SP"
        return "\n".join(
            line.replace("{selfName}", self_name).replace("{spName}", sp_name)
            for line in DEFAULT_AFFIRMATIONS.get(mode, DEFAULT_AFFIRMATIONS["general"])
        )

    def affirmation_text(self):
        custom = [line.strip() for line in self.custom_text.get("1.0", "end").splitlines() if line.strip()]
        defaults = self.rendered_default_affirmations().splitlines()
        lines = custom if self.vars["affirmation_mode"].get() == "custom" else defaults + custom
        return "\n".join(lines)

    def fill_default_text(self):
        self.custom_text.delete("1.0", "end")
        self.custom_text.insert("1.0", self.rendered_default_affirmations())
        self.vars["affirmation_mode"].set("custom")
        self.status.set("已填入当前主题的默认文案。")

    def clear_text(self):
        self.custom_text.delete("1.0", "end")
        self.status.set("已清空自定义文案。")

    def preview_affirmations(self):
        text = self.affirmation_text() or "当前没有肯定句文案。"
        top = tk.Toplevel(self)
        top.title("最终肯定句文案")
        top.geometry("560x420")
        box = tk.Text(top, wrap="word")
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", text)
        box.configure(state="disabled")

    def analyze_frequency_keywords(self):
        text = self.affirmation_text().lower()
        scores = []
        for label, frequencies, keywords in FREQUENCY_THEMES:
            hits = [keyword for keyword in keywords if keyword.lower() in text]
            if hits:
                scores.append((len(hits), label, frequencies, hits))
        scores.sort(reverse=True, key=lambda item: item[0])
        top = scores[:3]
        recommended = []
        for _score, _label, frequencies, _hits in top:
            for frequency in frequencies:
                if frequency not in recommended:
                    recommended.append(frequency)
        return top, recommended[:4] or [432, 528, 639]

    def apply_recommended_frequencies(self):
        top, recommended = self.analyze_frequency_keywords()
        for value, var in self.frequency_vars.items():
            var.set(value in recommended)
        if top:
            matches = " / ".join(f"{label}({', '.join(hits[:3])})" for _score, label, _freq, hits in top)
        else:
            matches = "未匹配到明显主题，使用通用组合"
        self.recommendation.set(f"推荐：{' / '.join(str(v) for v in recommended)} Hz。匹配：{matches}。")
        self.status.set("已根据文案推荐频率。")

    def clear_frequencies(self):
        for var in self.frequency_vars.values():
            var.set(False)
        self.vars["custom_frequencies"].set("")
        self.status.set("已清空频率选择。")

    def selected_frequencies(self):
        values = [str(value) for value, var in self.frequency_vars.items() if var.get()]
        custom = self.vars["custom_frequencies"].get().replace("，", ",")
        values.extend(part.strip() for part in custom.split(",") if part.strip())
        return ",".join(dict.fromkeys(values))

    def suggest_library_query(self):
        text = self.affirmation_text().lower()
        if self.vars["library_type"].get() == "noise":
            top, recommended = self.analyze_frequency_keywords()
            frequency = recommended[0] if recommended else 528
            self.vars["library_query"].set(f"{frequency} Hz white noise")
            return
        if any(keyword in text for keyword in ["爱", "爱情", "关系", "喜欢", "sp", "复合", "亲密"]):
            query = "romantic ambient"
        elif any(keyword in text for keyword in ["睡眠", "平静", "安心", "放松"]):
            query = "calm meditation"
        elif any(keyword in text for keyword in ["学习", "考试", "专注", "论文"]):
            query = "focus ambient"
        elif any(keyword in text for keyword in ["钱", "财富", "事业", "工作", "丰盛"]):
            query = "uplifting ambient"
        else:
            query = "soft ambient"
        self.vars["library_query"].set(query)

    def start_library_search(self):
        if self.library_worker and self.library_worker.is_alive():
            return
        query = self.vars["library_query"].get().strip()
        if not query:
            self.library_status.set("请先输入搜索词。")
            return
        self.library_list.delete(0, "end")
        self.library_results = []
        self.library_status.set("正在搜索开放 WAV 音频...")
        self.library_worker = threading.Thread(target=self.run_library_search, args=(query,), daemon=True)
        self.library_worker.start()

    def run_library_search(self, query):
        try:
            results = self.search_open_audio(query)
            self.events.put(("library_results", results))
        except Exception as exc:
            self.events.put(("library_error", exc))

    def search_open_audio(self, query):
        results = []
        results.extend(self.search_openverse(query))
        if len(results) < 8:
            results.extend(self.search_internet_archive(query))
        deduped = []
        seen = set()
        for result in results:
            key = result["url"]
            if key not in seen:
                seen.add(key)
                deduped.append(result)
        return deduped[:12]

    def search_openverse(self, query):
        params = urllib.parse.urlencode({"q": query, "page_size": 20})
        url = f"https://api.openverse.org/v1/audio/?{params}"
        data = self.fetch_json(url, timeout=12)
        results = []
        for item in data.get("results", []):
            audio_url = item.get("url") or ""
            if not self.is_wav_url(audio_url):
                continue
            title = item.get("title") or "Untitled"
            creator = item.get("creator") or "unknown"
            results.append({
                "title": title,
                "creator": creator,
                "source": "Openverse",
                "url": audio_url,
                "landing": item.get("foreign_landing_url") or item.get("url") or "",
            })
        return results

    def search_internet_archive(self, query):
        search = f'({query}) AND mediatype:audio'
        params = urllib.parse.urlencode({
            "q": search,
            "fl[]": ["identifier", "title", "creator"],
            "rows": 8,
            "output": "json",
        }, doseq=True)
        data = self.fetch_json(f"https://archive.org/advancedsearch.php?{params}", timeout=12)
        docs = data.get("response", {}).get("docs", [])
        results = []
        for doc in docs:
            identifier = doc.get("identifier")
            if not identifier:
                continue
            try:
                meta = self.fetch_json(f"https://archive.org/metadata/{urllib.parse.quote(identifier)}", timeout=8)
            except Exception:
                continue
            for file_info in meta.get("files", []):
                name = file_info.get("name") or ""
                if not self.is_wav_url(name):
                    continue
                results.append({
                    "title": doc.get("title") or identifier,
                    "creator": doc.get("creator") or "unknown",
                    "source": "Internet Archive",
                    "url": f"https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(name)}",
                    "landing": f"https://archive.org/details/{urllib.parse.quote(identifier)}",
                })
                break
        return results

    def fetch_json(self, url, timeout=10):
        request = urllib.request.Request(url, headers={"User-Agent": "SubliminalLocalApp/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def is_wav_url(self, value):
        path = urllib.parse.urlparse(value).path.lower()
        return path.endswith(".wav") or path.endswith(".wave")

    def start_library_download(self):
        selection = self.library_list.curselection()
        if not selection:
            self.library_status.set("请先选择一个搜索结果。")
            return
        result = self.library_results[selection[0]]
        self.library_status.set("正在下载音频...")
        threading.Thread(target=self.run_library_download, args=(result,), daemon=True).start()

    def run_library_download(self, result):
        try:
            output_dir = Path(self.vars["output_dir"].get().strip() or "outputs")
            output_dir.mkdir(parents=True, exist_ok=True)
            stem = self.safe_file_stem(result["title"]) or "library_audio"
            output = output_dir / f"{stem}.wav"
            counter = 2
            while output.exists():
                output = output_dir / f"{stem}_{counter}.wav"
                counter += 1
            request = urllib.request.Request(result["url"], headers={"User-Agent": "SubliminalLocalApp/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                output.write_bytes(response.read())
            self.events.put(("library_downloaded", output))
        except Exception as exc:
            self.events.put(("library_error", exc))

    def open_selected_landing(self):
        selection = self.library_list.curselection()
        if not selection:
            self.library_status.set("请先选择一个搜索结果。")
            return
        landing = self.library_results[selection[0]].get("landing")
        if landing:
            webbrowser.open(landing)

    def safe_file_stem(self, value):
        return re.sub(r"[^0-9A-Za-z_-]+", "_", value).strip("_")[:48]

    def start_recording(self):
        if self.recording_stream is not None:
            return
        try:
            import sounddevice as sd
        except Exception:
            messagebox.showerror("缺少录音依赖", "请先安装录音依赖：python -m pip install sounddevice")
            return

        self.recording_chunks = []

        def callback(indata, _frames, _time_info, status):
            if status:
                self.events.put(("record_status", f"录音状态：{status}"))
            self.recording_chunks.append(indata.copy())

        try:
            self.recording_stream = sd.InputStream(samplerate=44100, channels=1, dtype="float32", callback=callback)
            self.recording_stream.start()
        except Exception as exc:
            self.recording_stream = None
            messagebox.showerror("无法开始录音", str(exc))
            return

        self.record_button.configure(state="disabled")
        self.stop_record_button.configure(state="normal")
        self.record_status.set("录音状态：正在录音...")

    def stop_recording(self):
        if self.recording_stream is None:
            return
        stream = self.recording_stream
        self.recording_stream = None
        try:
            stream.stop()
            stream.close()
            output_dir = Path(self.vars["output_dir"].get().strip() or "outputs")
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / f"recorded_voice_{time.strftime('%Y%m%d_%H%M%S')}.wav"
            self.write_recording(output)
            self.vars["voice_file"].set(str(output))
            self.record_status.set(f"录音状态：已保存 {output.name}")
            self.status.set("录音已设为人声。")
        except Exception as exc:
            messagebox.showerror("录音保存失败", str(exc))
        finally:
            self.record_button.configure(state="normal")
            self.stop_record_button.configure(state="disabled")

    def write_recording(self, output):
        if not self.recording_chunks:
            raise ValueError("没有录到声音。")
        import numpy as np

        data = np.concatenate(self.recording_chunks, axis=0)
        pcm = np.clip(data[:, 0], -1, 1)
        pcm = (pcm * 32767).astype("<i2")
        with wave.open(str(output), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            wav.writeframes(pcm.tobytes())

    def pick_wav(self, key):
        path = filedialog.askopenfilename(filetypes=[("WAV audio", "*.wav"), ("All files", "*.*")])
        if path:
            self.vars[key].set(path)
            if key == "voice_file":
                self.status.set("已选择人声，可以生成或继续调整参数。")

    def pick_folder(self, key):
        path = filedialog.askdirectory()
        if path:
            self.vars[key].set(path)

    def build_args(self):
        voice_file = self.vars["voice_file"].get().strip()
        if not voice_file:
            raise ValueError("还没有人声：请先选择人声 WAV 文件，再生成音频。")

        return Namespace(
            voice_file=voice_file,
            music_file=self.vars["music_file"].get().strip() or None,
            noise_file=self.vars["noise_file"].get().strip() or None,
            output_dir=self.vars["output_dir"].get().strip() or "outputs",
            name=self.vars["name"].get().strip() or "my_sub",
            minutes=float(self.vars["minutes"].get()),
            voice_layers=int(float(self.vars["voice_layers"].get())),
            voice_volume=float(self.vars["voice_volume"].get()),
            music_volume=float(self.vars["music_volume"].get()),
            noise_volume=float(self.vars["noise_volume"].get()),
            fade_seconds=float(self.vars["fade_seconds"].get()),
            frequencies=self.selected_frequencies(),
            tone_volume=float(self.vars["tone_volume"].get()),
            sample_rate=int(self.vars["sample_rate"].get()),
            chunk_seconds=10,
            affirmations_text=self.affirmation_text(),
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
            self.status.set(str(exc))
            messagebox.showerror("参数有误", str(exc))
            return

        self.progress["value"] = 0
        self.status.set("正在生成，请稍等...")
        self.generate_button.state(["disabled"])
        self.worker = threading.Thread(target=self.run_generate, args=(args,), daemon=True)
        self.worker.start()

    def run_generate(self, args):
        try:
            from generate_sub import generate

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
                elif kind == "library_results":
                    self.library_results = payload
                    self.library_list.delete(0, "end")
                    for result in payload:
                        self.library_list.insert("end", f"[{result['source']}] {result['title']} - {result['creator']}")
                    if payload:
                        self.library_status.set(f"找到 {len(payload)} 个 WAV 结果。选择一个下载使用。")
                    else:
                        self.library_status.set("没有搜到可直接下载的 WAV 音频，可以换关键词。")
                elif kind == "library_downloaded":
                    target = "noise_file" if self.vars["library_type"].get() == "noise" else "music_file"
                    self.vars[target].set(str(payload))
                    label = "白噪音" if target == "noise_file" else "音乐"
                    self.library_status.set(f"已下载并设为{label}：{payload}")
                    self.status.set(f"已下载开放音频：{payload.name}")
                elif kind == "library_error":
                    self.library_status.set(f"音乐库操作失败：{payload}")
                elif kind == "record_status":
                    self.record_status.set(str(payload))
        except queue.Empty:
            pass
        self.after(100, self.poll_events)

    def open_search(self, query):
        webbrowser.open(f"https://openverse.org/search/audio?q={query.replace(' ', '%20')}")

    def open_web_version(self):
        if self.web_server is None:
            port = self.find_port()
            handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(*args, directory=str(Path.cwd()), **kwargs)
            self.web_server = QuietServer(("127.0.0.1", port), handler)
            threading.Thread(target=self.web_server.serve_forever, daemon=True).start()
            self.web_url = f"http://127.0.0.1:{port}/index.html"
        webbrowser.open(self.web_url)
        self.status.set("已打开网页版。")

    def find_port(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]


if __name__ == "__main__":
    LocalApp().mainloop()
