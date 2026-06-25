# SP Subliminal Generator

独立的 sub 音频生成工具。

用户上传背景音频，再上传或录制肯定句人声，浏览器直接混音并导出 WAV。

网页版本也接入了 Openverse 和 Internet Archive 开放音频搜索，并在搜索失败时提供 Archive / Wikimedia Commons 外部搜索入口。这些平台包含 Creative Commons、公有领域和其他开放条目，但具体作品授权仍需在作品页核对。

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
