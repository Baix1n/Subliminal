# SP Subliminal Generator

独立的 sub 音频生成工具。现在包含三种本地使用方式：

- 网页版本：用户上传背景音频，再上传或录制肯定句人声，浏览器直接混音并导出 WAV。
- 本地桌面版：Windows、macOS、Linux 都可以打开一个简单窗口生成音频。
- 本地命令行版本：使用 Python 脚本生成音频，支持上万层人声叠加。

网页版本也接入了 Openverse 和 Internet Archive 开放音频搜索，并在搜索失败时提供 Archive / Wikimedia Commons 外部搜索入口。这些平台包含 Creative Commons、公有领域和其他开放条目，但具体作品授权仍需在作品页核对。

## 初始化环境

只有本地桌面版和命令行版本需要这一步；如果只预览网页，可以跳过。

需要 Python 3.10 或更新版本。推荐安装 Python 3.11 / 3.12。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows 如果没有 `python3`，可以把命令里的 `python3` 换成 `python`。安装 Python 时建议勾选 `Add python.exe to PATH`。

## 本地部署

```bash
cd Subliminal-main
python3 -m http.server 8765
```

打开：

```text
http://127.0.0.1:8765
```

网页端所有处理都发生在用户浏览器里，不会上传音频到服务器。

## 本地桌面版

Windows：

```bat
start_windows.bat
```

Windows 启动脚本会自动检查 Python 和依赖；如果启动失败，窗口会停住显示原因。

macOS / Linux：

```bash
sh start_mac_linux.sh
```

也可以直接运行：

```bash
python local_app.py
```

桌面版支持选择人声、背景音乐、白噪音 WAV 文件，并设置人声层数。上万层建议先从这些参数试起：

```text
人声层数：10000
人声音量：0.01 到 0.03
时长：先用 1 分钟测试
```

## 本地命令行生成音频

```bash
python generate_sub.py \
  --voice-file voice.wav \
  --music-file music.wav \
  --minutes 10 \
  --voice-layers 10000 \
  --voice-volume 0.02 \
  --name my_sp_sub
```

输出会在：

```text
outputs/my_sp_sub.wav
```

## 常用参数

```bash
--voice-file voice.wav
--music-file music.wav
--noise-file noise.wav
--voice-layers 10000
--voice-volume 0.02
--music-volume 0.8
--noise-volume 0.35
--frequencies 528,639
--tone-volume 0.02
```

本地版目前使用 WAV 文件。其他格式可以先用音频软件或 ffmpeg 转成 WAV。
