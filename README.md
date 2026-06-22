# SP Subliminal Generator

独立的 sub 音频生成工具。现在包含两种模式：

- `web/`：纯静态网页，适合部署到 GitHub Pages。用户上传背景音频，再上传或录制肯定句人声，浏览器直接混音并导出 WAV。
- `generate_sub.py`：本地 macOS 命令行版本，使用 `say` 自动合成肯定句语音。

GitHub Pages 不能运行 Python 后端，也不能可靠地把浏览器 TTS 导出成音频文件，所以公开网页版本采用“上传/录制人声 + 上传背景音”的方案。

网页版本也接入了 Openverse 和 Internet Archive 开放音频搜索，并在搜索失败时提供 Archive / Wikimedia Commons 外部搜索入口。这些平台包含 Creative Commons、公有领域和其他开放条目，但具体作品授权仍需在作品页核对。

## GitHub Pages 部署

把 `sp_sub_generator/web` 里的文件放到 GitHub Pages 发布目录即可：

```text
index.html
styles.css
app.js
```

如果你的仓库专门只放这个网页，也可以把这三个文件放到仓库根目录，然后在 GitHub 仓库设置里开启 Pages。

网页端所有处理都发生在用户浏览器里，不会上传音频到服务器。

## 初始化环境

只有本地命令行自动 TTS 版本需要这一步；GitHub Pages 版本不需要安装环境。

```bash
cd "/Users/wangminghao/Downloads/CampusConnect- Prototype/sp_sub_generator"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 本地预览网页

```bash
cd "/Users/wangminghao/Downloads/CampusConnect- Prototype/sp_sub_generator/web"
python3 -m http.server 8765
```

打开：

```text
http://127.0.0.1:8765
```

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
