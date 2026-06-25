# SP Subliminal Generator

独立的 sub 音频生成工具。现在包含两种本地使用方式：

- 网页版本：用户上传背景音频，再上传或录制肯定句人声，浏览器直接混音并导出 WAV。
- 本地命令行版本：使用 Python 脚本生成音频。

网页版本也接入了 Openverse 和 Internet Archive 开放音频搜索，并在搜索失败时提供 Archive / Wikimedia Commons 外部搜索入口。这些平台包含 Creative Commons、公有领域和其他开放条目，但具体作品授权仍需在作品页核对。

## 初始化环境

只有本地命令行版本需要这一步；如果只预览网页，可以跳过。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

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

## 本地命令行生成音频

```bash
python generate_sub.py \
  --self-name "你的名字" \
  --sp-name "对方名字" \
  --minutes 10 \
  --voice Tingting \
  --name my_sp_sub
```

输出会在：

```text
outputs/my_sp_sub.wav
outputs/my_sp_sub_affirmations.txt
```

## 常用参数

```bash
--voice-volume 0.04
--bed-volume 0.24
--custom-line "我自然地被珍惜。"
--affirmations-file my_lines.txt
--seed 11
```

默认肯定句会尽量聚焦在自我价值、放松、健康互相靠近，而不是控制对方。
