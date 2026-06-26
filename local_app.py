#!/usr/bin/env python3
import http.server
import json
import queue
import re
import shutil
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

PRODUCTION_PRESETS = {
    "清晰可辨": {"voice_layers": 3, "voice_volume": 0.055, "voice_speed": 1, "voice_stereo_width": 0.35, "layer_spacing": 0.42, "music_volume": 0.72, "noise_volume": 0.18, "fade_seconds": 6, "tone_volume": 0},
    "轻度掩蔽": {"voice_layers": 12, "voice_volume": 0.04, "voice_speed": 1.1, "voice_stereo_width": 0.75, "layer_spacing": 0.23, "music_volume": 0.8, "noise_volume": 0.35, "fade_seconds": 8, "tone_volume": 0},
    "高密度叠层": {"voice_layers": 10000, "voice_volume": 0.02, "voice_speed": 1.15, "voice_stereo_width": 1, "layer_spacing": 0.09, "music_volume": 0.78, "noise_volume": 0.4, "fade_seconds": 8, "tone_volume": 0},
    "睡眠低声": {"voice_layers": 80, "voice_volume": 0.018, "voice_speed": 0.85, "voice_stereo_width": 0.55, "layer_spacing": 0.5, "music_volume": 0.55, "noise_volume": 0.45, "fade_seconds": 12, "tone_volume": 0},
    "快速纹理": {"voice_layers": 300, "voice_volume": 0.018, "voice_speed": 1.5, "voice_stereo_width": 1, "layer_spacing": 0.06, "music_volume": 0.76, "noise_volume": 0.34, "fade_seconds": 6, "tone_volume": 0},
}


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
        self.goal_files = []
        self.manifest_state_path = Path.cwd() / "manifest_board.json"
        self.affirmation_state_path = Path.cwd() / "affirmation_practice.json"
        self.gratitude_state_path = Path.cwd() / "gratitude_journal.json"
        self.affirmation_lines = []
        self.affirmation_index = 0
        self.affirmation_clicks = {}
        self.gratitude_entries = {}

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
            "voice_speed": tk.StringVar(value="1.00"),
            "voice_stereo_width": tk.StringVar(value="1.00"),
            "layer_spacing": tk.StringVar(value="0.37"),
            "music_volume": tk.StringVar(value="0.8"),
            "noise_volume": tk.StringVar(value="0.35"),
            "fade_seconds": tk.StringVar(value="6"),
            "custom_frequencies": tk.StringVar(value=""),
            "tone_volume": tk.StringVar(value="0"),
            "sample_rate": tk.StringVar(value="44100"),
            "production_preset": tk.StringVar(value="手动调整"),
            "daily_intention": tk.StringVar(value=""),
            "embodied_feeling": tk.StringVar(value=""),
            "gratitude_date": tk.StringVar(value=time.strftime("%Y-%m-%d")),
            "library_query": tk.StringVar(value="romantic ambient"),
            "library_type": tk.StringVar(value="music"),
        }
        self.frequency_vars = {value: tk.BooleanVar(value=False) for value, _ in PRESET_FREQUENCIES}
        self.value_entries = {}
        self.scales = {}

        self.configure_style()
        self.build_ui()
        self.load_manifest_state(silent=True)
        self.load_affirmation_state(silent=True)
        self.load_gratitude_state(silent=True)
        self.sync_intent()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
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
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="\u672c\u5730 Subliminal \u663e\u5316\u52a9\u624b", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="\u5236\u4f5c\u5de5\u4f5c\u53f0\u7ba1\u7406\u97f3\u9891\u3001\u9891\u7387\u548c\u7d20\u6750\uff1b\u80af\u5b9a\u8bed\u3001\u611f\u6069\u65e5\u8bb0\u548c\u613f\u671b\u677f\u4fdd\u6301\u72ec\u7acb\u6a21\u5757\u3002").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Button(header, text="\u6253\u5f00\u7f51\u9875\u7248", command=self.open_web_version).grid(row=0, column=1, rowspan=2, sticky="e")

        tabs = ttk.Notebook(root)
        tabs.grid(row=1, column=0, sticky="nsew")
        self.build_workbench_tab(tabs)
        self.build_affirmation_tab(tabs)
        self.build_gratitude_tab(tabs)
        self.build_vision_tab(tabs)

    def build_workbench_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="\u5236\u4f5c\u5de5\u4f5c\u53f0")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        files = ttk.LabelFrame(frame, text="\u97f3\u9891\u6587\u4ef6", style="Section.TLabelframe")
        files.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        files.columnconfigure(1, weight=1)
        self.file_row(files, 0, "\u4eba\u58f0 WAV\uff08\u5fc5\u586b\uff09", "voice_file", self.pick_wav)
        self.file_row(files, 1, "\u80cc\u666f\u97f3\u4e50 WAV", "music_file", self.pick_wav)
        self.file_row(files, 2, "\u767d\u566a\u97f3 / \u9891\u7387\u97f3 WAV", "noise_file", self.pick_wav)
        self.file_row(files, 3, "\u8f93\u51fa\u6587\u4ef6\u5939", "output_dir", self.pick_folder)

        left = ttk.Frame(frame, padding=(0, 0, 8, 0))
        right = ttk.Frame(frame, padding=(8, 0, 0, 0))
        left.grid(row=1, column=0, sticky="nsew")
        right.grid(row=1, column=1, sticky="nsew")
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        main_params = ttk.LabelFrame(left, text="\u6df7\u97f3\u53c2\u6570", style="Section.TLabelframe")
        main_params.grid(row=0, column=0, sticky="ew")
        main_params.columnconfigure(1, weight=1)
        ttk.Label(main_params, text="\u5236\u4f5c\u65b9\u5f0f").grid(row=0, column=0, sticky="w", padx=12, pady=8)
        preset_box = ttk.Combobox(main_params, textvariable=self.vars["production_preset"], values=("\u624b\u52a8\u8c03\u6574", *PRODUCTION_PRESETS.keys()), state="readonly")
        preset_box.grid(row=0, column=1, columnspan=2, sticky="ew", padx=8, pady=8)
        preset_box.bind("<<ComboboxSelected>>", lambda _event: self.apply_production_preset())
        self.slider(main_params, 1, "\u65f6\u957f", "minutes", 1, 60, 1, " \u5206\u949f", as_int=True)
        self.slider(main_params, 2, "\u4eba\u58f0\u5c42\u6570", "voice_layers", 1, 50000, 1, " \u5c42", as_int=True)
        self.slider(main_params, 3, "\u4eba\u58f0\u97f3\u91cf", "voice_volume", 0, 0.16, 0.001, "", precision=3)
        self.slider(main_params, 4, "\u4eba\u58f0\u500d\u901f", "voice_speed", 0.5, 2, 0.05, " x", precision=2)
        self.slider(main_params, 5, "\u58f0\u50cf\u5bbd\u5ea6", "voice_stereo_width", 0, 1, 0.05, "", precision=2)
        self.slider(main_params, 6, "\u5c42\u95f4\u9519\u4f4d", "layer_spacing", 0.03, 0.8, 0.01, " \u79d2", precision=2)
        self.slider(main_params, 7, "\u97f3\u4e50\u97f3\u91cf", "music_volume", 0, 1, 0.01, "", precision=2)
        self.slider(main_params, 8, "\u767d\u566a\u97f3\u97f3\u91cf", "noise_volume", 0, 1, 0.01, "", precision=2)
        self.slider(main_params, 9, "\u6de1\u5165\u6de1\u51fa", "fade_seconds", 0, 30, 1, " \u79d2", as_int=True)

        presets = ttk.LabelFrame(left, text="\u5c42\u6570\u9884\u8bbe", style="Section.TLabelframe")
        presets.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        presets.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(presets, text="\u6e05\u6670 3 \u5c42", command=lambda: self.apply_preset(3, 0.055)).grid(row=0, column=0, sticky="ew", padx=8, pady=10)
        ttk.Button(presets, text="\u9ad8\u5bc6\u5ea6 100 \u5c42", command=lambda: self.apply_preset(100, 0.035)).grid(row=0, column=1, sticky="ew", padx=8, pady=10)
        ttk.Button(presets, text="\u4e0a\u4e07\u5c42 10000", command=lambda: self.apply_preset(10000, 0.02)).grid(row=0, column=2, sticky="ew", padx=8, pady=10)

        workbench_tabs = ttk.Notebook(right)
        workbench_tabs.grid(row=0, column=0, sticky="nsew")
        self.build_output_tab(workbench_tabs)
        self.build_frequency_tab(workbench_tabs)
        self.build_library_tab(workbench_tabs)

    def build_output_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="\u8f93\u51fa / \u751f\u6210")
        frame.columnconfigure(0, weight=1)

        output = ttk.LabelFrame(frame, text="\u8f93\u51fa", style="Section.TLabelframe")
        output.grid(row=0, column=0, sticky="ew")
        output.columnconfigure(1, weight=1)
        self.entry(output, 0, "\u6587\u4ef6\u540d", "name")
        self.sample_rate(output, 1)

        actions = ttk.LabelFrame(frame, text="\u751f\u6210", style="Section.TLabelframe")
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(actions, mode="determinate", maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        self.generate_button = ttk.Button(actions, text="\u751f\u6210 WAV", style="Generate.TButton", command=self.start_generate)
        self.generate_button.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.status = tk.StringVar(value="\u8bf7\u5148\u9009\u62e9\u4eba\u58f0 WAV \u6587\u4ef6\u3002\u4e0a\u4e07\u5c42\u5efa\u8bae\u4eba\u58f0\u97f3\u91cf\u4ece 0.01 \u5230 0.03 \u8bd5\u3002")
        ttk.Label(actions, textvariable=self.status, wraplength=440, justify="left").grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        note = ttk.LabelFrame(frame, text="\u5de5\u4f5c\u53f0\u8bf4\u660e", style="Section.TLabelframe")
        note.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(
            note,
            text="\u8fd9\u91cc\u4e13\u95e8\u8d1f\u8d23\u97f3\u9891\u5236\u4f5c\u3002\u9891\u7387\u548c\u97f3\u4e50\u5e93\u5c5e\u4e8e\u5236\u4f5c\u7d20\u6750\uff0c\u5728\u5de5\u4f5c\u53f0\u5185\u7ef4\u62a4\uff1b\u80af\u5b9a\u8bed\u3001\u611f\u6069\u65e5\u8bb0\u548c\u613f\u671b\u677f\u4f1a\u5728\u751f\u6210\u65f6\u4e00\u8d77\u5199\u5165\u5bfc\u51fa\u8bb0\u5f55\u3002",
            wraplength=440,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=12)

        prompt = ttk.LabelFrame(frame, text="\u5f55\u97f3\u63d0\u793a / \u6807\u6ce8\u7a3f", style="Section.TLabelframe")
        prompt.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        prompt.columnconfigure(0, weight=1)
        prompt.rowconfigure(0, weight=1)
        self.recording_prompt_text = tk.Text(prompt, height=7, wrap="word", undo=True)
        self.recording_prompt_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        prompt_buttons = ttk.Frame(prompt)
        prompt_buttons.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(prompt_buttons, text="\u4ece\u80af\u5b9a\u8bed\u586b\u5165", command=self.fill_recording_prompt_from_affirmations).pack(side="left")
        ttk.Button(prompt_buttons, text="\u4fdd\u5b58\u6807\u6ce8\u7a3f", command=self.save_affirmation_state).pack(side="left", padx=(8, 0))

    def build_gratitude_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="\u611f\u6069\u65e5\u8bb0")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        top = ttk.LabelFrame(frame, text="\u4eca\u65e5\u80fd\u91cf", style="Section.TLabelframe")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        top.columnconfigure(1, weight=1)
        self.entry(top, 0, "\u65e5\u671f", "gratitude_date")
        self.entry(top, 1, "\u4eca\u65e5\u610f\u56fe", "daily_intention")
        self.entry(top, 2, "\u5df2\u62e5\u6709\u611f\u53d7", "embodied_feeling")

        calendar_box = ttk.LabelFrame(frame, text="\u65e5\u5386", style="Section.TLabelframe")
        calendar_box.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        calendar_box.rowconfigure(0, weight=1)
        self.gratitude_date_list = tk.Listbox(calendar_box, width=18, height=14)
        self.gratitude_date_list.grid(row=0, column=0, sticky="ns", padx=8, pady=8)
        self.gratitude_date_list.bind("<<ListboxSelect>>", self.on_gratitude_date_selected)
        ttk.Button(calendar_box, text="\u4eca\u5929", command=self.select_today_gratitude).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        gratitude = ttk.LabelFrame(frame, text="\u611f\u6069\u65e5\u8bb0", style="Section.TLabelframe")
        gratitude.grid(row=1, column=1, sticky="nsew")
        gratitude.columnconfigure(0, weight=1)
        gratitude.rowconfigure(0, weight=1)
        self.gratitude_text = tk.Text(gratitude, height=16, wrap="word", undo=True)
        self.gratitude_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.gratitude_text.insert("1.0", "\u4eca\u5929\u6211\u611f\u8c22\uff1a\n\u6211\u5df2\u7ecf\u62e5\u6709\uff1a\n\u8ba9\u6211\u5b89\u5fc3\u7684\u662f\uff1a")
        gratitude_buttons = ttk.Frame(gratitude)
        gratitude_buttons.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(gratitude_buttons, text="\u4fdd\u5b58\u4eca\u65e5", command=self.save_gratitude_entry).pack(side="left")
        ttk.Button(gratitude_buttons, text="\u8bfb\u53d6\u65e5\u671f", command=self.load_selected_gratitude_entry).pack(side="left", padx=(8, 0))

    def build_vision_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="\u613f\u671b\u677f")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        goal = ttk.LabelFrame(frame, text="\u613f\u671b\u677f / \u76ee\u6807\u786e\u8ba4", style="Section.TLabelframe")
        goal.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        goal.columnconfigure(0, weight=1)
        goal.rowconfigure(1, weight=1)
        ttk.Label(goal, text="\u628a\u76ee\u6807\u5199\u5177\u4f53\uff0c\u4e5f\u53ef\u4ee5\u4e0a\u4f20\u7167\u7247\u3001\u622a\u56fe\u3001PDF \u6216\u5176\u4ed6\u6587\u4ef6\u4f5c\u4e3a\u76ee\u6807\u6750\u6599\u3002", wraplength=760, justify="left").grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        self.goal_text = tk.Text(goal, height=8, wrap="word", undo=True)
        self.goal_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        files = ttk.LabelFrame(frame, text="\u76ee\u6807\u7167\u7247 / \u6587\u4ef6", style="Section.TLabelframe")
        files.grid(row=1, column=0, sticky="nsew")
        files.columnconfigure(0, weight=1)
        files.rowconfigure(0, weight=1)
        self.goal_file_list = tk.Listbox(files, height=5)
        self.goal_file_list.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        controls = ttk.Frame(files)
        controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(controls, text="\u6dfb\u52a0\u7167\u7247", command=self.add_goal_photos).pack(side="left")
        ttk.Button(controls, text="\u6dfb\u52a0\u6587\u4ef6", command=self.add_goal_files).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="\u79fb\u9664\u9009\u4e2d", command=self.remove_goal_file).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="\u6253\u5f00\u9009\u4e2d", command=self.open_goal_file).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="\u4fdd\u5b58\u613f\u671b\u677f", command=self.save_manifest_state).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="\u8bfb\u53d6\u613f\u671b\u677f", command=lambda: self.load_manifest_state(silent=False)).pack(side="left", padx=(8, 0))

    def build_affirmation_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="\u80af\u5b9a\u8bed\u7ec3\u4e60")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(9, weight=1)
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

        practice = ttk.LabelFrame(frame, text="\u9010\u53e5\u7ec3\u4e60", style="Section.TLabelframe")
        practice.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 4))
        practice.columnconfigure(0, weight=1)
        self.current_affirmation = tk.StringVar(value="\u70b9\u51fb\u5f00\u59cb\u7ec3\u4e60")
        self.current_affirmation_count = tk.StringVar(value="\u5f53\u524d\u53e5 0 \u6b21")
        self.total_affirmation_count = tk.StringVar(value="\u603b\u8ba1 0 \u6b21")
        ttk.Label(practice, textvariable=self.current_affirmation, wraplength=760, justify="left", font=("", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="ew", padx=8, pady=(8, 4))
        ttk.Label(practice, textvariable=self.current_affirmation_count).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(practice, textvariable=self.total_affirmation_count).grid(row=1, column=1, sticky="w", padx=8, pady=(0, 8))
        ttk.Button(practice, text="\u4e0b\u4e00\u53e5", command=self.next_affirmation).grid(row=1, column=2, sticky="e", padx=8, pady=(0, 8))
        ttk.Button(practice, text="\u8bb0\u4e00\u6b21", command=self.count_current_affirmation).grid(row=1, column=3, sticky="e", padx=8, pady=(0, 8))

        ttk.Label(frame, text="肯定句模式").grid(row=5, column=0, sticky="w", padx=8, pady=8)
        mode_row = ttk.Frame(frame)
        mode_row.grid(row=5, column=1, sticky="ew", padx=8, pady=8)
        ttk.Radiobutton(mode_row, text="默认 + 自定义", variable=self.vars["affirmation_mode"], value="default").pack(side="left")
        ttk.Radiobutton(mode_row, text="只用自定义", variable=self.vars["affirmation_mode"], value="custom").pack(side="left", padx=(16, 0))
        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 8))
        ttk.Button(buttons, text="填入默认文案", command=self.fill_default_text).pack(side="left")
        ttk.Button(buttons, text="清空文案", command=self.clear_text).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="预览最终文案", command=self.preview_affirmations).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="\u4fdd\u5b58\u80af\u5b9a\u8bed", command=self.save_affirmation_state).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="\u91cd\u7f6e\u7edf\u8ba1", command=self.reset_affirmation_counts).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="\u5237\u65b0\u7ec3\u4e60\u5217\u8868", command=self.refresh_affirmation_practice).pack(side="left", padx=(8, 0))
        self.custom_text = tk.Text(frame, height=12, wrap="word", undo=True)
        self.custom_text.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)

    def build_frequency_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="\u9891\u7387")
        frame.columnconfigure(0, weight=1)
        grid = ttk.LabelFrame(frame, text="频率选择", style="Section.TLabelframe")
        grid.grid(row=0, column=0, sticky="ew")
        for index, (value, label) in enumerate(PRESET_FREQUENCIES):
            row, col = divmod(index, 2)
            ttk.Checkbutton(grid, text=f"{value} Hz  {label}", variable=self.frequency_vars[value], command=self.ensure_tone_volume).grid(row=row, column=col, sticky="w", padx=12, pady=8)
        custom = ttk.LabelFrame(frame, text="自定义频率", style="Section.TLabelframe")
        custom.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        custom.columnconfigure(1, weight=1)
        self.entry(custom, 0, "频率 Hz", "custom_frequencies")
        self.vars["custom_frequencies"].trace_add("write", lambda *_args: self.ensure_tone_volume() if self.vars["custom_frequencies"].get().strip() else None)
        self.slider(custom, 1, "频率音量", "tone_volume", 0, 0.05, 0.001, "", precision=3)
        tools = ttk.Frame(frame)
        tools.grid(row=2, column=0, sticky="ew", pady=12)
        ttk.Button(tools, text="分析文案并推荐", command=self.apply_recommended_frequencies).pack(side="left")
        ttk.Button(tools, text="清空频率", command=self.clear_frequencies).pack(side="left", padx=(8, 0))
        self.recommendation = tk.StringVar(value="推荐会根据文案关键词匹配主题频率；想加入频率音时再把频率音量调到 0.003-0.01。")
        ttk.Label(frame, textvariable=self.recommendation, wraplength=430, justify="left").grid(row=3, column=0, sticky="ew")

    def build_library_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="\u97f3\u4e50\u5e93 / \u5f55\u97f3")
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

    def apply_production_preset(self):
        preset = PRODUCTION_PRESETS.get(self.vars["production_preset"].get())
        if not preset:
            return
        for key, value in preset.items():
            scale = self.scales.get(key)
            if scale:
                scale.set(value)
            else:
                self.vars[key].set(str(value))
        self.status.set("已应用制作方式预设，可以继续微调。")

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
        text = self.export_text() or "当前没有肯定句文案或显化记录。"
        top = tk.Toplevel(self)
        top.title("最终导出文案")
        top.geometry("560x420")
        box = tk.Text(top, wrap="word")
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", text)
        box.configure(state="disabled")

    def fill_recording_prompt_from_affirmations(self):
        text = self.affirmation_text().strip()
        if not text:
            self.status.set("\u8fd8\u6ca1\u6709\u53ef\u586b\u5165\u7684\u80af\u5b9a\u8bed\u3002")
            return
        self.recording_prompt_text.delete("1.0", "end")
        self.recording_prompt_text.insert("1.0", text)
        self.status.set("\u5df2\u628a\u80af\u5b9a\u8bed\u586b\u5165\u5de5\u4f5c\u53f0\u5f55\u97f3\u63d0\u793a\u3002")

    def refresh_affirmation_practice(self):
        self.affirmation_lines = [
            line.strip()
            for line in self.affirmation_text().splitlines()
            if line.strip()
        ]
        if not self.affirmation_lines:
            self.affirmation_index = 0
            self.current_affirmation.set("\u8fd8\u6ca1\u6709\u80af\u5b9a\u8bed")
            self.current_affirmation_count.set("\u5f53\u524d\u53e5 0 \u6b21")
            self.total_affirmation_count.set("\u603b\u8ba1 0 \u6b21")
            return
        self.affirmation_index %= len(self.affirmation_lines)
        self.show_current_affirmation()

    def show_current_affirmation(self):
        if not self.affirmation_lines:
            self.refresh_affirmation_practice()
            return
        line = self.affirmation_lines[self.affirmation_index]
        current_count = self.affirmation_clicks.get(line, 0)
        total = sum(self.affirmation_clicks.values())
        self.current_affirmation.set(line)
        self.current_affirmation_count.set(f"\u5f53\u524d\u53e5 {current_count} \u6b21")
        self.total_affirmation_count.set(f"\u603b\u8ba1 {total} \u6b21")

    def next_affirmation(self):
        self.refresh_affirmation_practice()
        if not self.affirmation_lines:
            return
        self.affirmation_index = (self.affirmation_index + 1) % len(self.affirmation_lines)
        self.show_current_affirmation()
        self.save_affirmation_state(silent=True)

    def count_current_affirmation(self):
        self.refresh_affirmation_practice()
        if not self.affirmation_lines:
            return
        line = self.affirmation_lines[self.affirmation_index]
        self.affirmation_clicks[line] = self.affirmation_clicks.get(line, 0) + 1
        self.show_current_affirmation()
        self.save_affirmation_state(silent=True)

    def reset_affirmation_counts(self):
        self.affirmation_clicks = {}
        self.show_current_affirmation()
        self.save_affirmation_state(silent=True)
        self.status.set("\u80af\u5b9a\u8bed\u7edf\u8ba1\u5df2\u91cd\u7f6e\u3002")

    def save_affirmation_state(self, silent=False):
        data = {
            "intent_mode": self.vars["intent_mode"].get(),
            "affirmation_mode": self.vars["affirmation_mode"].get(),
            "self_name": self.vars["self_name"].get(),
            "sp_name": self.vars["sp_name"].get(),
            "custom_text": self.custom_text.get("1.0", "end").strip(),
            "recording_prompt": self.recording_prompt_text.get("1.0", "end").strip(),
            "affirmation_index": self.affirmation_index,
            "affirmation_clicks": self.affirmation_clicks,
        }
        self.affirmation_state_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if not silent:
            self.status.set("\u80af\u5b9a\u8bed\u5df2\u4fdd\u5b58\u3002")

    def load_affirmation_state(self, silent=False):
        if not self.affirmation_state_path.exists():
            self.refresh_affirmation_practice()
            return
        try:
            data = json.loads(self.affirmation_state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            if not silent:
                messagebox.showerror("\u8bfb\u53d6\u5931\u8d25", str(exc))
            return
        for key in ("intent_mode", "affirmation_mode", "self_name", "sp_name"):
            if key in data:
                self.vars[key].set(data[key])
        self.custom_text.delete("1.0", "end")
        self.custom_text.insert("1.0", data.get("custom_text", ""))
        self.recording_prompt_text.delete("1.0", "end")
        self.recording_prompt_text.insert("1.0", data.get("recording_prompt", ""))
        self.affirmation_index = int(data.get("affirmation_index", 0) or 0)
        self.affirmation_clicks = {
            str(key): int(value)
            for key, value in data.get("affirmation_clicks", {}).items()
        }
        self.refresh_affirmation_practice()
        if not silent:
            self.status.set("\u80af\u5b9a\u8bed\u5df2\u8bfb\u53d6\u3002")

    def gratitude_date(self):
        value = self.vars["gratitude_date"].get().strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        today = time.strftime("%Y-%m-%d")
        self.vars["gratitude_date"].set(today)
        return today

    def save_gratitude_entry(self, silent=False):
        date_key = self.gratitude_date()
        self.gratitude_entries[date_key] = {
            "daily_intention": self.vars["daily_intention"].get(),
            "embodied_feeling": self.vars["embodied_feeling"].get(),
            "gratitude": self.gratitude_text.get("1.0", "end").strip(),
        }
        self.gratitude_state_path.write_text(
            json.dumps({"entries": self.gratitude_entries}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.refresh_gratitude_calendar()
        if not silent:
            self.status.set(f"{date_key} \u611f\u6069\u65e5\u8bb0\u5df2\u4fdd\u5b58\u3002")

    def load_gratitude_state(self, silent=False):
        if self.gratitude_state_path.exists():
            try:
                data = json.loads(self.gratitude_state_path.read_text(encoding="utf-8"))
                self.gratitude_entries = data.get("entries", {})
            except Exception as exc:
                if not silent:
                    messagebox.showerror("\u8bfb\u53d6\u5931\u8d25", str(exc))
        self.refresh_gratitude_calendar()
        self.load_gratitude_entry(self.gratitude_date(), silent=True)

    def refresh_gratitude_calendar(self):
        if not hasattr(self, "gratitude_date_list"):
            return
        self.gratitude_date_list.delete(0, "end")
        dates = sorted(set(self.gratitude_entries.keys()) | {time.strftime("%Y-%m-%d")}, reverse=True)
        for date_key in dates:
            self.gratitude_date_list.insert("end", date_key)

    def load_gratitude_entry(self, date_key, silent=False):
        entry = self.gratitude_entries.get(date_key)
        self.vars["gratitude_date"].set(date_key)
        if not entry:
            if not silent:
                self.status.set(f"{date_key} \u8fd8\u6ca1\u6709\u611f\u6069\u65e5\u8bb0\u3002")
            return
        self.vars["daily_intention"].set(entry.get("daily_intention", ""))
        self.vars["embodied_feeling"].set(entry.get("embodied_feeling", ""))
        self.gratitude_text.delete("1.0", "end")
        self.gratitude_text.insert("1.0", entry.get("gratitude", ""))
        if not silent:
            self.status.set(f"\u5df2\u8bfb\u53d6 {date_key} \u7684\u611f\u6069\u65e5\u8bb0\u3002")

    def load_selected_gratitude_entry(self):
        selection = self.gratitude_date_list.curselection()
        if not selection:
            self.load_gratitude_entry(self.gratitude_date())
            return
        self.load_gratitude_entry(self.gratitude_date_list.get(selection[0]))

    def on_gratitude_date_selected(self, _event=None):
        selection = self.gratitude_date_list.curselection()
        if selection:
            self.load_gratitude_entry(self.gratitude_date_list.get(selection[0]), silent=True)

    def select_today_gratitude(self):
        self.load_gratitude_entry(time.strftime("%Y-%m-%d"))

    def manifest_text(self):
        sections = []
        intention = self.vars["daily_intention"].get().strip()
        if intention:
            sections.append("【今日意图】\n" + intention)
        feeling = self.vars["embodied_feeling"].get().strip()
        if feeling:
            sections.append("【已拥有感受】\n" + feeling)
        gratitude = self.gratitude_text.get("1.0", "end").strip()
        if gratitude:
            sections.append("【感恩日记】\n" + gratitude)
        goal = self.goal_text.get("1.0", "end").strip()
        if goal:
            sections.append("【愿望板 / 目标确认】\n" + goal)
        if self.goal_files:
            files = "\n".join(str(path) for path in self.goal_files)
            sections.append("【目标附件】\n" + files)
        return "\n\n".join(sections)

    def export_text(self):
        return "\n\n".join(part for part in [self.affirmation_text(), self.manifest_text()] if part)

    def add_goal_photos(self):
        paths = filedialog.askopenfilenames(
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.gif;*.bmp"),
                ("All files", "*.*"),
            ]
        )
        self.add_goal_paths(paths)

    def add_goal_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("All files", "*.*")])
        self.add_goal_paths(paths)

    def add_goal_paths(self, paths):
        existing = {str(path) for path in self.goal_files}
        for raw in paths:
            path = Path(raw)
            if str(path) in existing:
                continue
            self.goal_files.append(path)
            self.goal_file_list.insert("end", path.name)
        if paths:
            self.status.set("已添加目标材料。")

    def remove_goal_file(self):
        selection = list(self.goal_file_list.curselection())
        for index in reversed(selection):
            self.goal_file_list.delete(index)
            del self.goal_files[index]

    def open_goal_file(self):
        selection = self.goal_file_list.curselection()
        if not selection:
            self.status.set("请先选择一个目标材料。")
            return
        webbrowser.open(self.goal_files[selection[0]].resolve().as_uri())

    def save_manifest_state(self):
        data = {
            "daily_intention": self.vars["daily_intention"].get(),
            "embodied_feeling": self.vars["embodied_feeling"].get(),
            "gratitude": self.gratitude_text.get("1.0", "end").strip(),
            "goal": self.goal_text.get("1.0", "end").strip(),
            "goal_files": [str(path) for path in self.goal_files],
        }
        self.manifest_state_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.status.set("\u613f\u671b\u677f\u5df2\u4fdd\u5b58\u3002")

    def load_manifest_state(self, silent=False):
        if not self.manifest_state_path.exists():
            if not silent:
                self.status.set("\u8fd8\u6ca1\u6709\u4fdd\u5b58\u8fc7\u613f\u671b\u677f\u3002")
            return
        try:
            data = json.loads(self.manifest_state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            if not silent:
                messagebox.showerror("\u8bfb\u53d6\u5931\u8d25", str(exc))
            return

        self.vars["daily_intention"].set(data.get("daily_intention", ""))
        self.vars["embodied_feeling"].set(data.get("embodied_feeling", ""))
        self.gratitude_text.delete("1.0", "end")
        self.gratitude_text.insert("1.0", data.get("gratitude", ""))
        self.goal_text.delete("1.0", "end")
        self.goal_text.insert("1.0", data.get("goal", ""))
        self.goal_files = [Path(path) for path in data.get("goal_files", [])]
        self.goal_file_list.delete(0, "end")
        for path in self.goal_files:
            self.goal_file_list.insert("end", path.name)
        if not silent:
            self.status.set("\u613f\u671b\u677f\u5df2\u8bfb\u53d6\u3002")

    def on_close(self):
        try:
            self.save_manifest_state()
            self.save_affirmation_state(silent=True)
            self.save_gratitude_entry(silent=True)
        except Exception:
            pass
        self.destroy()

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
        self.ensure_tone_volume()
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

    def ensure_tone_volume(self):
        if float(self.vars["tone_volume"].get() or 0) > 0:
            return
        scale = self.scales.get("tone_volume")
        if scale:
            scale.set(0.006)
        else:
            self.vars["tone_volume"].set("0.006")

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
            voice_speed=float(self.vars["voice_speed"].get()),
            voice_stereo_width=float(self.vars["voice_stereo_width"].get()),
            layer_spacing=float(self.vars["layer_spacing"].get()),
            music_volume=float(self.vars["music_volume"].get()),
            noise_volume=float(self.vars["noise_volume"].get()),
            fade_seconds=float(self.vars["fade_seconds"].get()),
            frequencies=self.selected_frequencies(),
            tone_volume=float(self.vars["tone_volume"].get()),
            sample_rate=int(self.vars["sample_rate"].get()),
            chunk_seconds=10,
            affirmations_text=self.export_text(),
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
            self.export_manifest_assets(args)
            self.events.put(("done", output))
        except Exception as exc:
            self.events.put(("error", exc))

    def export_manifest_assets(self, args):
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        self.save_manifest_state()
        self.save_affirmation_state(silent=True)
        self.save_gratitude_entry(silent=True)
        manifest_text = self.manifest_text()
        if manifest_text:
            (output_dir / f"{args.name}_manifest_journal.txt").write_text(manifest_text.rstrip() + "\n", encoding="utf-8")
        if not self.goal_files:
            return
        assets_dir = output_dir / f"{args.name}_assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for source in self.goal_files:
            if not source.exists() or not source.is_file():
                continue
            target = assets_dir / source.name
            counter = 2
            while target.exists():
                target = assets_dir / f"{source.stem}_{counter}{source.suffix}"
                counter += 1
            shutil.copy2(source, target)

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
