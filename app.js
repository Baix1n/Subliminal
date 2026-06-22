const form = document.querySelector("#generatorForm");
const statusEl = document.querySelector("#systemStatus");
const messageEl = document.querySelector("#message");
const submitButton = document.querySelector("#submitButton");
const recommendButton = document.querySelector("#recommendButton");
const musicSuggestButton = document.querySelector("#musicSuggestButton");
const musicSearchButton = document.querySelector("#musicSearchButton");
const frequencyNoiseButton = document.querySelector("#frequencyNoiseButton");
const fillDefaultTextButton = document.querySelector("#fillDefaultTextButton");
const clearTextButton = document.querySelector("#clearTextButton");
const speakButton = document.querySelector("#speakButton");
const cancelSpeakButton = document.querySelector("#cancelSpeakButton");
const ttsVoiceSelect = document.querySelector("#ttsVoice");
const recordButton = document.querySelector("#recordButton");
const stopButton = document.querySelector("#stopButton");
const audioPlayer = document.querySelector("#audioPlayer");
const voicePreview = document.querySelector("#voicePreview");
const audioLink = document.querySelector("#audioLink");
const textLink = document.querySelector("#textLink");
const outputTitle = document.querySelector("#outputTitle");
const recommendationText = document.querySelector("#recommendationText");
const musicResults = document.querySelector("#musicResults");
const recorderStatus = document.querySelector("#recorderStatus");
const spField = document.querySelector("#spField");
const intentNote = document.querySelector("#intentNote");
const canvas = document.querySelector("#waveCanvas");
const ctx = canvas.getContext("2d");
const AudioContextClass = window.AudioContext || window.webkitAudioContext;

let recordedVoiceBlob = null;
let mediaRecorder = null;
let recordedChunks = [];
let activeAudioUrl = null;
let activeTextUrl = null;
let selectedLibraryMusicBlob = null;
let selectedLibraryNoiseBlob = null;
let selectedLibraryMusicName = "";
let selectedLibraryNoiseName = "";

const rangeBindings = [
  ["minutes", "minutesOut"],
  ["voiceVolume", "voiceVolumeOut"],
  ["voiceLayers", "voiceLayersOut"],
  ["musicVolume", "musicVolumeOut"],
  ["noiseVolume", "noiseVolumeOut"],
  ["fadeSeconds", "fadeOut"],
  ["toneVolume", "toneVolumeOut"],
  ["ttsRate", "ttsRateOut"],
  ["ttsPitch", "ttsPitchOut"],
];

const frequencyThemes = [
  {
    label: "爱情关系",
    frequencies: [528, 639],
    keywords: ["爱", "爱情", "喜欢", "关系", "恋爱", "复合", "亲密", "吸引", "靠近", "联系", "互动", "珍惜", "选择", "sp"],
  },
  {
    label: "自信价值",
    frequencies: [396, 528],
    keywords: ["自信", "价值", "魅力", "漂亮", "美", "被看见", "被欣赏", "值得", "安全感", "稳定"],
  },
  {
    label: "平静睡眠",
    frequencies: [174, 432],
    keywords: ["平静", "放松", "睡眠", "安心", "安全", "疗愈", "稳定", "不焦虑", "释怀", "冷静"],
  },
  {
    label: "沟通表达",
    frequencies: [639, 741],
    keywords: ["沟通", "表达", "消息", "聊天", "联系", "诚实", "清晰", "回应", "开口", "说话"],
  },
  {
    label: "行动显化",
    frequencies: [285, 852],
    keywords: ["显化", "实现", "机会", "行动", "改变", "靠近", "自然发生", "顺利", "同步", "吸引"],
  },
  {
    label: "金钱丰盛",
    frequencies: [285, 528, 852],
    keywords: ["钱", "金钱", "财富", "富", "丰盛", "收入", "存款", "中奖", "好运", "财运", "工作", "事业", "offer", "薪水", "赚钱"],
  },
  {
    label: "学业专注",
    frequencies: [396, 432, 741],
    keywords: ["学习", "学业", "考试", "成绩", "分数", "绩点", "gpa", "专注", "记忆", "理解", "作业", "论文", "录取", "学校", "大学"],
  },
  {
    label: "直觉灵感",
    frequencies: [741, 852],
    keywords: ["直觉", "灵感", "清醒", "看清", "觉察", "内在", "自由", "释放"],
  },
];

const defaultAffirmationsByMode = {
  general: [
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
  sp: [
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
  money: [
    "{selfName}允许自己接住更多机会和资源。",
    "{selfName}值得拥有稳定、丰盛、持续增长的收入。",
    "金钱以清晰、健康、安心的方式流向{selfName}。",
    "{selfName}越来越会选择高价值机会。",
    "{selfName}的能力被看见，付出得到合理回报。",
    "{selfName}对财富、工作和未来越来越有安全感。",
  ],
  study: [
    "{selfName}学习时越来越专注、清醒、稳定。",
    "{selfName}理解知识很快，也记得牢。",
    "{selfName}在考试和作业中发挥自然、顺利。",
    "{selfName}每天都在靠近理想成绩。",
    "{selfName}相信自己的节奏，也愿意持续行动。",
    "{selfName}被适合自己的学校、机会和结果支持。",
  ],
};

const intentNotes = {
  general: "通用模式不会指向特定对象，适合自信、关系、状态稳定类 sub。",
  sp: "SP 模式会使用特定对象名字，适合做关系、联系、复合或吸引主题。",
  money: "金钱 / 事业模式适合丰盛、机会、事业、offer、收入和财运主题。",
  study: "学业 / 考试模式适合学习专注、成绩、考试、录取、论文和 GPA 主题。",
};

for (const [name, outputId] of rangeBindings) {
  const input = form.elements[name];
  const output = document.querySelector(`#${outputId}`);
  const sync = () => {
    output.value = input.value;
  };
  input.addEventListener("input", sync);
  sync();
}

function setBusy(isBusy) {
  submitButton.disabled = isBusy;
  recordButton.disabled = isBusy;
  statusEl.textContent = isBusy ? "Working" : "Ready";
}

function setMessage(text, kind = "") {
  messageEl.textContent = text;
  messageEl.className = `message ${kind}`.trim();
}

function setRecorderStatus(text, kind = "") {
  recorderStatus.textContent = `录音状态：${text}`;
  recorderStatus.className = `recorder-status ${kind}`.trim();
}

function revokeActiveUrls() {
  if (activeAudioUrl) URL.revokeObjectURL(activeAudioUrl);
  if (activeTextUrl) URL.revokeObjectURL(activeTextUrl);
  activeAudioUrl = null;
  activeTextUrl = null;
}

function safeFileName(value) {
  return (value || "sp_sub").replace(/[^0-9A-Za-z_-]+/g, "_").replace(/^_+|_+$/g, "") || "sp_sub";
}

function getAffirmationText() {
  const intentMode = form.elements.intentMode.value;
  const defaults = defaultAffirmationsByMode[intentMode] || defaultAffirmationsByMode.general;
  const customLines = form.elements.customLines.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const mode = form.elements.affirmationMode.value;
  const lines = mode === "custom" ? customLines : defaults.concat(customLines);
  const selfName = form.elements.selfName.value.trim() || "我";
  const spName = form.elements.spName.value.trim() || "SP";
  return lines
    .map((line) => line.replaceAll("{selfName}", selfName).replaceAll("{spName}", spName))
    .join("\n");
}

function syncIntentMode() {
  const isSp = form.elements.intentMode.value === "sp";
  spField.classList.toggle("hidden", !isSp);
  intentNote.textContent = intentNotes[form.elements.intentMode.value] || intentNotes.general;
}

function renderedDefaultAffirmations() {
  const intentMode = form.elements.intentMode.value;
  const selfName = form.elements.selfName.value.trim() || "我";
  const spName = form.elements.spName.value.trim() || "SP";
  return (defaultAffirmationsByMode[intentMode] || defaultAffirmationsByMode.general)
    .map((line) => line.replaceAll("{selfName}", selfName).replaceAll("{spName}", spName))
    .join("\n");
}

function populateTtsVoices() {
  if (!("speechSynthesis" in window)) {
    ttsVoiceSelect.innerHTML = "<option>当前浏览器不支持</option>";
    speakButton.disabled = true;
    cancelSpeakButton.disabled = true;
    return;
  }

  const voices = window.speechSynthesis.getVoices();
  ttsVoiceSelect.textContent = "";

  const preferred = voices
    .map((voice, index) => ({ voice, index }))
    .sort((a, b) => {
      const aZh = /^zh|Chinese|Mandarin|Tingting|Meijia|Sinji/i.test(`${a.voice.lang} ${a.voice.name}`) ? 0 : 1;
      const bZh = /^zh|Chinese|Mandarin|Tingting|Meijia|Sinji/i.test(`${b.voice.lang} ${b.voice.name}`) ? 0 : 1;
      return aZh - bZh || a.voice.name.localeCompare(b.voice.name);
    });

  for (const { voice, index } of preferred) {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${voice.name} (${voice.lang || "unknown"})`;
    ttsVoiceSelect.append(option);
  }

  if (!preferred.length) {
    const option = document.createElement("option");
    option.textContent = "默认系统声音";
    ttsVoiceSelect.append(option);
  }
}

function speakAffirmations() {
  if (!("speechSynthesis" in window)) {
    setMessage("当前浏览器不支持 AI 朗读。", "error");
    return;
  }

  window.speechSynthesis.cancel();
  const text = getAffirmationText();
  if (!text.trim()) {
    setMessage("请先填写肯定句文案。", "error");
    return;
  }

  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  const selectedVoice = voices[Number(ttsVoiceSelect.value)];
  if (selectedVoice) utterance.voice = selectedVoice;
  utterance.rate = Number(form.elements.ttsRate.value);
  utterance.pitch = Number(form.elements.ttsPitch.value);
  utterance.volume = 1;
  utterance.onstart = () => setMessage("正在试听 AI 配音。", "success");
  utterance.onend = () => setMessage("AI 配音试听结束。", "success");
  utterance.onerror = () => setMessage("AI 配音朗读失败，可以换一个声音试试。", "error");
  window.speechSynthesis.speak(utterance);
}

async function readArrayBuffer(fileOrBlob) {
  if (!fileOrBlob) throw new Error("请选择音频文件。");
  return await fileOrBlob.arrayBuffer();
}

function mixLoopedChannel(buffer, frameIndex, channelIndex) {
  const channel = buffer.getChannelData(Math.min(channelIndex, buffer.numberOfChannels - 1));
  return channel[frameIndex % channel.length] || 0;
}

function softClip(value) {
  return Math.tanh(value * 0.95) / Math.tanh(0.95);
}

function getSelectedFrequencies() {
  const presetValues = [...document.querySelectorAll('input[name="presetFrequency"]:checked')]
    .map((input) => Number(input.value));
  const customValues = form.elements.customFrequencies.value
    .split(/[,\s，、]+/)
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isFinite(value) && value > 0 && value <= 20000);
  return [...new Set(presetValues.concat(customValues))];
}

function recommendMusicQuery() {
  const text = getAffirmationText().toLowerCase();
  const rules = [
    { query: "romantic ambient", keywords: ["爱", "爱情", "喜欢", "恋爱", "复合", "亲密", "关系", "sp"] },
    { query: "calm meditation", keywords: ["平静", "放松", "安心", "睡眠", "疗愈", "安全"] },
    { query: "soft piano", keywords: ["温柔", "珍惜", "被爱", "靠近", "自然", "舒服"] },
    { query: "confidence upbeat ambient", keywords: ["自信", "魅力", "价值", "漂亮", "被欣赏"] },
    { query: "deep focus ambient", keywords: ["显化", "实现", "机会", "行动", "清晰", "稳定"] },
    { query: "abundance success ambient", keywords: ["钱", "金钱", "财富", "丰盛", "收入", "财运", "工作", "事业", "offer", "赚钱"] },
    { query: "study focus ambient", keywords: ["学习", "学业", "考试", "成绩", "专注", "记忆", "论文", "学校", "gpa"] },
  ];
  const best = rules
    .map((rule) => ({
      ...rule,
      score: rule.keywords.filter((keyword) => text.includes(keyword)).length,
    }))
    .sort((a, b) => b.score - a.score)[0];
  return best && best.score > 0 ? best.query : "ambient meditation";
}

function setLibraryMessage(text, kind = "") {
  musicResults.textContent = "";
  const message = document.createElement("p");
  message.className = `library-message ${kind}`.trim();
  message.textContent = text;
  musicResults.append(message);
}

function appendExternalSearchLinks(query) {
  const actions = document.createElement("div");
  actions.className = "music-actions";

  const archiveLink = document.createElement("a");
  archiveLink.className = "ghost-button small";
  archiveLink.href = `https://archive.org/search?query=${encodeURIComponent(query)}&and%5B%5D=mediatype%3A%22audio%22`;
  archiveLink.target = "_blank";
  archiveLink.rel = "noreferrer";
  archiveLink.textContent = "Archive 搜索";

  const commonsLink = document.createElement("a");
  commonsLink.className = "ghost-button small";
  commonsLink.href = `https://commons.wikimedia.org/w/index.php?search=${encodeURIComponent(`${query} audio`)}&title=Special:MediaSearch&type=audio`;
  commonsLink.target = "_blank";
  commonsLink.rel = "noreferrer";
  commonsLink.textContent = "Commons 搜索";

  actions.append(archiveLink, commonsLink);
  musicResults.append(actions);
}

function compactLicense(result) {
  if (result.provider === "Internet Archive") return result.license || "Archive item";
  const license = result.license || "unknown";
  const version = result.license_version ? ` ${result.license_version}` : "";
  return `${license.toUpperCase()}${version}`;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 9000) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}

function renderMusicResults(results) {
  musicResults.textContent = "";
  if (!results.length) {
    setLibraryMessage("没有搜到合适结果，可以换一个关键词。");
    return;
  }

  for (const result of results) {
    const item = document.createElement("article");
    item.className = "music-result";

    const title = document.createElement("h3");
    title.textContent = result.title || "Untitled";

    const meta = document.createElement("p");
    meta.textContent = `${result.creator || "Unknown creator"} · ${compactLicense(result)} · ${result.provider || result.source || "Openverse"}`;

    const player = document.createElement("audio");
    player.controls = true;
    player.src = result.url;

    const actions = document.createElement("div");
    actions.className = "music-actions";

    const useButton = document.createElement("button");
    useButton.type = "button";
    useButton.className = "ghost-button small";
    useButton.textContent = form.elements.libraryType.value === "noise" ? "用作白噪音" : "用作音乐";
    useButton.addEventListener("click", () => useLibraryTrack(result, useButton));

    const sourceLink = document.createElement("a");
    sourceLink.className = "ghost-button small";
    sourceLink.href = result.foreign_landing_url || result.url;
    sourceLink.target = "_blank";
    sourceLink.rel = "noreferrer";
    sourceLink.textContent = "作品页";

    actions.append(useButton, sourceLink);
    item.append(title, meta, player, actions);
    musicResults.append(item);
  }
}

async function searchOpenverseMusic() {
  const query = form.elements.musicQuery.value.trim() || recommendMusicQuery();
  form.elements.musicQuery.value = query;
  setLibraryMessage("正在搜索开放音乐库...");

  const results = [];
  const errors = [];

  try {
    results.push(...await searchOpenverse(query));
  } catch (error) {
    errors.push("Openverse");
  }

  try {
    results.push(...await searchInternetArchive(query));
  } catch (error) {
    errors.push("Internet Archive");
  }

  if (results.length) {
    renderMusicResults(results.slice(0, 10));
    if (errors.length) setMessage(`${errors.join(" / ")} 暂时无响应，已显示其他来源结果。`);
    return;
  }

  setLibraryMessage("两个音乐源都没搜到。可以换关键词，比如 rain white noise、528 hz meditation、ambient drone。", "error");
  appendExternalSearchLinks(query);
}

async function searchOpenverse(query) {
  const params = new URLSearchParams({
    q: query,
    page_size: "5",
    license: "cc0,pdm,by,by-sa",
  });
  const response = await fetchWithTimeout(`https://api.openverse.org/v1/audio/?${params.toString()}`);
  if (!response.ok) throw new Error(`Openverse returned ${response.status}`);
  const data = await response.json();
  return (data.results || []).map((result) => ({ ...result, provider: "Openverse" }));
}

async function searchInternetArchive(query) {
  const searchParams = new URLSearchParams();
  searchParams.set("q", `mediatype:audio AND (${query})`);
  searchParams.append("fl[]", "identifier");
  searchParams.append("fl[]", "title");
  searchParams.append("fl[]", "creator");
  searchParams.set("rows", "8");
  searchParams.set("page", "1");
  searchParams.set("output", "json");

  const response = await fetchWithTimeout(`https://archive.org/advancedsearch.php?${searchParams.toString()}`);
  if (!response.ok) throw new Error(`Internet Archive returned ${response.status}`);
  const data = await response.json();
  const docs = data.response?.docs || [];
  const enriched = await Promise.all(docs.slice(0, 5).map(buildInternetArchiveResult));
  return enriched.filter(Boolean);
}

async function buildInternetArchiveResult(doc) {
  if (!doc.identifier) return null;
  try {
    const response = await fetchWithTimeout(`https://archive.org/metadata/${encodeURIComponent(doc.identifier)}`, {}, 7000);
    if (!response.ok) return null;
    const data = await response.json();
    const files = data.files || [];
    const audioFile = files.find((file) => {
      const name = file.name || "";
      const format = `${file.format || ""} ${file.source || ""}`;
      return /\.(mp3|ogg|oga|m4a|wav)$/i.test(name) || /MP3|Ogg|VBR|WAVE|MPEG/i.test(format);
    });
    if (!audioFile?.name) return null;
    const fileName = audioFile.name.split("/").map(encodeURIComponent).join("/");
    return {
      title: doc.title || data.metadata?.title || doc.identifier,
      creator: doc.creator || data.metadata?.creator || "Internet Archive",
      license: data.metadata?.licenseurl ? "license linked on item page" : "check item page",
      provider: "Internet Archive",
      source: "Internet Archive",
      url: `https://archive.org/download/${encodeURIComponent(doc.identifier)}/${fileName}`,
      foreign_landing_url: `https://archive.org/details/${encodeURIComponent(doc.identifier)}`,
    };
  } catch (error) {
    return null;
  }
}

async function useLibraryTrack(result, button) {
  button.disabled = true;
  button.textContent = "载入中";
  try {
    const response = await fetchWithTimeout(result.url, {}, 12000);
    if (!response.ok) throw new Error("无法下载这首音频。");
    const blob = await response.blob();
    const title = result.title || "Library track";
    if (form.elements.libraryType.value === "noise") {
      selectedLibraryNoiseBlob = blob;
      selectedLibraryNoiseName = title;
      form.elements.noiseFile.value = "";
      setMessage(`已选择白噪音 / 频率音：${selectedLibraryNoiseName}`, "success");
    } else {
      selectedLibraryMusicBlob = blob;
      selectedLibraryMusicName = title;
      form.elements.musicFile.value = "";
      setMessage(`已选择音乐：${selectedLibraryMusicName}`, "success");
    }
    button.textContent = "已选择";
  } catch (error) {
    button.textContent = form.elements.libraryType.value === "noise" ? "用作白噪音" : "用作音乐";
    setMessage("这首音频不允许浏览器直接混音，请从作品页下载后上传。", "error");
  } finally {
    button.disabled = false;
  }
}

function suggestMusicKeyword() {
  const query = recommendMusicQuery();
  form.elements.musicQuery.value = query;
  setLibraryMessage(`推荐关键词：${query}`);
}

function suggestFrequencyNoiseKeyword() {
  const selected = getSelectedFrequencies();
  const fallback = analyzeFrequencyKeywords().recommended;
  const frequency = selected[0] || fallback[0] || 528;
  const query = `${frequency} Hz`;
  form.elements.libraryType.value = "noise";
  form.elements.musicQuery.value = query;
  setLibraryMessage(`频率搜索词：${query}`);
}

function analyzeFrequencyKeywords() {
  const text = `${getAffirmationText()}\n${form.elements.selfName.value}\n${form.elements.spName.value}`.toLowerCase();
  const scores = frequencyThemes.map((theme) => {
    const hits = theme.keywords.filter((keyword) => text.includes(keyword.toLowerCase()));
    return { ...theme, hits, score: hits.length };
  }).filter((theme) => theme.score > 0);

  scores.sort((a, b) => b.score - a.score);
  const topThemes = scores.slice(0, 3);
  const recommended = [...new Set(topThemes.flatMap((theme) => theme.frequencies))].slice(0, 4);
  return { topThemes, recommended: recommended.length ? recommended : [432, 528, 639] };
}

function applyRecommendedFrequencies() {
  const { topThemes, recommended } = analyzeFrequencyKeywords();
  const recommendedSet = new Set(recommended.map(String));
  document.querySelectorAll('input[name="presetFrequency"]').forEach((input) => {
    input.checked = recommendedSet.has(input.value);
  });

  const themeText = topThemes.length
    ? topThemes.map((theme) => `${theme.label}(${theme.hits.slice(0, 3).join("、")})`).join(" / ")
    : "未匹配到明显主题，使用通用组合";
  recommendationText.textContent = `推荐：${recommended.join(" / ")} Hz。匹配：${themeText}。`;
  setMessage("已根据文案推荐频率。", "success");
}

function frequencySample(frequencies, frameIndex, sampleRate) {
  if (!frequencies.length) return 0;
  let tone = 0;
  for (const frequency of frequencies) {
    tone += Math.sin((2 * Math.PI * frequency * frameIndex) / sampleRate);
  }
  return tone / frequencies.length;
}

function buildLayeredVoiceLoops(buffer, sampleRate, layerCount, maxFrames) {
  const loopFrames = Math.max(1, Math.min(Math.ceil(buffer.duration * sampleRate), maxFrames));
  const source = new Float32Array(loopFrames);
  const left = new Float32Array(loopFrames);
  const right = new Float32Array(loopFrames);

  for (let i = 0; i < loopFrames; i += 1) {
    const sourceIndex = Math.floor((i * buffer.sampleRate) / sampleRate);
    source[i] = mixLoopedChannel(buffer, sourceIndex, 0);
  }

  for (let layer = 0; layer < layerCount; layer += 1) {
    const offsetSeconds = (layer * 0.37) + ((layer % 3) * 0.11);
    const offsetFrames = Math.floor(offsetSeconds * sampleRate) % loopFrames;
    const pan = layerCount === 1 ? 0 : (layer / (layerCount - 1)) * 2 - 1;
    const leftGain = Math.sqrt((1 - pan) / 2);
    const rightGain = Math.sqrt((1 + pan) / 2);

    for (let i = 0; i < loopFrames; i += 1) {
      const value = source[(i + offsetFrames) % loopFrames];
      left[i] += value * leftGain;
      right[i] += value * rightGain;
    }
  }

  const normalizer = Math.sqrt(layerCount);
  for (let i = 0; i < loopFrames; i += 1) {
    left[i] /= normalizer;
    right[i] /= normalizer;
  }

  return { left, right, frames: loopFrames };
}

function encodeWav(left, right, sampleRate) {
  const frames = left.length;
  const bytesPerSample = 2;
  const blockAlign = 2 * bytesPerSample;
  const buffer = new ArrayBuffer(44 + frames * blockAlign);
  const view = new DataView(buffer);

  function writeString(offset, value) {
    for (let i = 0; i < value.length; i += 1) {
      view.setUint8(offset + i, value.charCodeAt(i));
    }
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + frames * blockAlign, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 2, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, frames * blockAlign, true);

  let offset = 44;
  for (let i = 0; i < frames; i += 1) {
    const l = Math.max(-1, Math.min(1, left[i]));
    const r = Math.max(-1, Math.min(1, right[i]));
    view.setInt16(offset, l < 0 ? l * 0x8000 : l * 0x7fff, true);
    view.setInt16(offset + 2, r < 0 ? r * 0x8000 : r * 0x7fff, true);
    offset += 4;
  }

  return new Blob([buffer], { type: "audio/wav" });
}

async function generateInBrowser() {
  const musicFile = form.elements.musicFile.files[0] || selectedLibraryMusicBlob;
  const noiseFile = form.elements.noiseFile.files[0] || selectedLibraryNoiseBlob;
  const voiceFile = form.elements.voiceFile.files[0] || recordedVoiceBlob;
  if (!musicFile && !noiseFile) throw new Error("请先选择音乐或白噪音音频。");
  if (!voiceFile) throw new Error("请上传或录制肯定句人声。");
  if (!AudioContextClass) throw new Error("当前浏览器不支持 Web Audio。");

  const audioContext = new AudioContextClass();
  const [musicBuffer, noiseBuffer, voiceBuffer] = await Promise.all([
    musicFile ? readArrayBuffer(musicFile).then((data) => audioContext.decodeAudioData(data)) : null,
    noiseFile ? readArrayBuffer(noiseFile).then((data) => audioContext.decodeAudioData(data)) : null,
    readArrayBuffer(voiceFile).then((data) => audioContext.decodeAudioData(data)),
  ]);

  const sampleRate = 44100;
  const minutes = Number(form.elements.minutes.value);
  const totalFrames = Math.floor(minutes * 60 * sampleRate);
  const musicVolume = Number(form.elements.musicVolume.value);
  const noiseVolume = Number(form.elements.noiseVolume.value);
  const voiceVolume = Number(form.elements.voiceVolume.value);
  const voiceLayers = Number(form.elements.voiceLayers.value);
  const toneVolume = Number(form.elements.toneVolume.value);
  const frequencies = getSelectedFrequencies();
  const fadeFrames = Math.floor(Number(form.elements.fadeSeconds.value) * sampleRate);
  const voiceLoops = buildLayeredVoiceLoops(voiceBuffer, sampleRate, voiceLayers, totalFrames);
  const left = new Float32Array(totalFrames);
  const right = new Float32Array(totalFrames);

  for (let i = 0; i < totalFrames; i += 1) {
    let fade = 1;
    if (fadeFrames > 0) {
      fade = Math.min(1, i / fadeFrames, (totalFrames - i) / fadeFrames);
    }

    let musicL = 0;
    let musicR = 0;
    if (musicBuffer) {
      const musicIndex = Math.floor((i * musicBuffer.sampleRate) / sampleRate);
      musicL = mixLoopedChannel(musicBuffer, musicIndex, 0);
      musicR = musicBuffer.numberOfChannels > 1 ? mixLoopedChannel(musicBuffer, musicIndex, 1) : musicL;
    }

    let noiseL = 0;
    let noiseR = 0;
    if (noiseBuffer) {
      const noiseIndex = Math.floor((i * noiseBuffer.sampleRate) / sampleRate);
      noiseL = mixLoopedChannel(noiseBuffer, noiseIndex, 0);
      noiseR = noiseBuffer.numberOfChannels > 1 ? mixLoopedChannel(noiseBuffer, noiseIndex, 1) : noiseL;
    }

    const voiceLoopIndex = i % voiceLoops.frames;
    const voiceL = voiceLoops.left[voiceLoopIndex];
    const voiceR = voiceLoops.right[voiceLoopIndex];
    const tone = frequencySample(frequencies, i, sampleRate) * toneVolume;
    left[i] = softClip((musicL * musicVolume + noiseL * noiseVolume + voiceL * voiceVolume + tone) * fade * 0.86);
    right[i] = softClip((musicR * musicVolume + noiseR * noiseVolume + voiceR * voiceVolume + tone) * fade * 0.86);
  }

  await audioContext.close();
  return encodeWav(left, right, sampleRate);
}

function enableResult(wavBlob) {
  revokeActiveUrls();
  const name = safeFileName(form.elements.name.value);
  activeAudioUrl = URL.createObjectURL(wavBlob);
  const textBlob = new Blob([getAffirmationText() + "\n"], { type: "text/plain;charset=utf-8" });
  activeTextUrl = URL.createObjectURL(textBlob);

  audioPlayer.src = activeAudioUrl;
  audioLink.href = activeAudioUrl;
  audioLink.download = `${name}.wav`;
  textLink.href = activeTextUrl;
  textLink.download = `${name}_affirmations.txt`;
  audioLink.classList.remove("disabled");
  textLink.classList.remove("disabled");
  outputTitle.textContent = "已生成";
}

recordButton.addEventListener("click", async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    setRecorderStatus("当前打开方式不支持麦克风，请用 http://127.0.0.1:8765 或 GitHub Pages 打开。", "error");
    setMessage("当前浏览器没有开放麦克风录音接口。", "error");
    return;
  }

  setRecorderStatus("正在请求麦克风权限...");
  setMessage("正在请求麦克风权限；如果没有弹窗，请检查浏览器地址栏权限。");
  recordButton.disabled = true;

  try {
    const permissionTimer = window.setTimeout(() => {
      setRecorderStatus("还在等待权限；如果没看到弹窗，请改用 localhost 打开页面。", "error");
    }, 5000);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    window.clearTimeout(permissionTimer);

    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) recordedChunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", () => {
      recordedVoiceBlob = new Blob(recordedChunks, { type: mediaRecorder.mimeType });
      voicePreview.src = URL.createObjectURL(recordedVoiceBlob);
      stream.getTracks().forEach((track) => track.stop());
      setRecorderStatus("录音已完成", "success");
      setMessage("录音已准备好，可以生成。", "success");
    });
    mediaRecorder.start();
    recordButton.disabled = true;
    stopButton.disabled = false;
    statusEl.textContent = "Recording";
    setRecorderStatus("正在录音", "recording");
    setMessage("正在录制肯定句人声...");
  } catch (error) {
    recordButton.disabled = false;
    stopButton.disabled = true;
    statusEl.textContent = "Ready";
    setRecorderStatus("录音未开始", "error");
    setMessage(error.message || "无法访问麦克风。", "error");
  }
});

stopButton.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  recordButton.disabled = false;
  stopButton.disabled = true;
  statusEl.textContent = "Ready";
  setRecorderStatus("正在保存录音...");
});

form.elements.voiceFile.addEventListener("change", () => {
  recordedVoiceBlob = null;
  const file = form.elements.voiceFile.files[0];
  voicePreview.src = file ? URL.createObjectURL(file) : "";
});

form.elements.musicFile.addEventListener("change", () => {
  if (form.elements.musicFile.files[0]) {
    selectedLibraryMusicBlob = null;
    selectedLibraryMusicName = "";
  }
});

form.elements.noiseFile.addEventListener("change", () => {
  if (form.elements.noiseFile.files[0]) {
    selectedLibraryNoiseBlob = null;
    selectedLibraryNoiseName = "";
  }
});

recommendButton.addEventListener("click", applyRecommendedFrequencies);
musicSuggestButton.addEventListener("click", suggestMusicKeyword);
musicSearchButton.addEventListener("click", searchOpenverseMusic);
frequencyNoiseButton.addEventListener("click", () => {
  suggestFrequencyNoiseKeyword();
  searchOpenverseMusic();
});
speakButton.addEventListener("click", speakAffirmations);
cancelSpeakButton.addEventListener("click", () => window.speechSynthesis?.cancel());
form.elements.intentMode.addEventListener("change", syncIntentMode);
fillDefaultTextButton.addEventListener("click", () => {
  form.elements.customLines.value = renderedDefaultAffirmations();
  form.elements.affirmationMode.value = "custom";
  setMessage("已填入当前主题的默认文案。", "success");
});
clearTextButton.addEventListener("click", () => {
  form.elements.customLines.value = "";
  setMessage("已清空自定义文案。");
});
syncIntentMode();

if ("speechSynthesis" in window) {
  populateTtsVoices();
  window.speechSynthesis.addEventListener("voiceschanged", populateTtsVoices);
} else {
  populateTtsVoices();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(true);
  setMessage("正在浏览器里混音...");

  try {
    const wavBlob = await generateInBrowser();
    enableResult(wavBlob);
    setMessage("音频已生成，可以播放或下载。", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setBusy(false);
  }
});

let phase = 0;

function drawWave() {
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "#17202a");
  gradient.addColorStop(0.52, "#20383b");
  gradient.addColorStop(1, "#3b2f36");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  ctx.globalAlpha = 0.24;
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 1;
  for (let x = 0; x < width; x += 34) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
  for (let y = 0; y < height; y += 34) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  const colors = ["#68d391", "#f6ad55", "#f687b3"];
  ctx.globalAlpha = 1;
  for (let band = 0; band < colors.length; band += 1) {
    ctx.beginPath();
    ctx.strokeStyle = colors[band];
    ctx.lineWidth = 3 - band * 0.45;
    const center = height * (0.42 + band * 0.08);
    for (let x = 0; x <= width; x += 4) {
      const t = x / width;
      const y =
        center +
        Math.sin(t * Math.PI * 8 + phase * (1 + band * 0.4)) * (32 - band * 5) +
        Math.sin(t * Math.PI * 23 + phase * 0.7) * 10;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  phase += 0.018;
  requestAnimationFrame(drawWave);
}

drawWave();
