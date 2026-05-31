# 双语字幕：构建工作流（纠错 + 翻译 + 时间修正 + 删条，可复现）

双语视频的「纠错 + 翻译」是你（Claude）的逐视频工件，量大（几百条）、又需要可复现、可局部返工。
**别手写 `cues_bi.json`**（条数多、JSON 易错、改一条还要对齐时间戳）。用配置文件 + 可复用脚本承载四件套，
按 `idx` 从 whisper 的 `cues_en.json` 合并出 `cues_bi.json`：

- **`corr`**：英文识别纠错表（有序 dict，**先长/特定短语、后通用**，区分大小写）。例：把误听的 `"Cloud Code"→"Claude Code"`、人名拼写统一替换。
- **`zh`**：按 `cues_en.json` 顺序的逐条中文译文（list，长度**必须等于** cues 数，脚本会 assert 卡住）。
- **`time_override`**：个别条的 `(start,end)` 覆写——**改时间不必重译**（如开场被音乐/掌声带偏的几条）。
- **`drop`**：要删除的 `idx` 列表（如音乐段的幻觉字幕条）。
- （可选）**`en_override`**：个别条整句覆写英文（CORR 的字符串替换搞不定的复杂情形）。

好处：「只修开场 6 条时间 + 删 4 条幻觉、保留其余 400+ 翻译」只动几行、可整段重跑，结果稳定。

## 流程
1. `../scripts/srt_to_cues.py --srt video_whisper.srt --cues cues_en.json` → 带 `idx` 的英文 cues。
2. 你通读 `cues_en.json`，在工作目录写出 `bi_config.json`（填 `corr`/`zh`/`time_override`/`drop`），运行 `../scripts/build_bi_cues.py --config bi_config.json` 得 `cues_bi.json`。
3. `../scripts/split_bi_cues.py` 拆行（中英都顾）→ `../scripts/bi_ass.py` 生成 ASS → ffmpeg 烧录（见 SKILL.md / burn-in-ffmpeg.md）。

## 配置文件模板（bi_config.json，按视频改 corr / zh / time_override / drop）
```json
{
  "corr": {
    "Cloud Code": "Claude Code"
  },
  "en_override": {},
  "time_override": {},
  "drop": [],
  "zh": [
    "……",
    "……"
  ]
}
```

## 配套：TIME_OVERRIDE 的时间从哪来
开场/结尾的音乐·掌声会让 whisper 把人声计时往前压（字幕偏早），中后段连续对话通常已准（见
[`transcribe-whisper.md`](transcribe-whisper.md) 的 VAD 一节）。拿准确时间的办法：
- 对开场单独跑 **VAD / 细粒度 VAD** 读出每句真实时间；或
- 用 `ffmpeg silencedetect` 找真实语音起点，对照 whisper 时间戳定位偏差。

把准确时间填进 `time_override`、把音乐段幻觉条放进 `drop`，即可**只改开场、不动其余翻译**。
