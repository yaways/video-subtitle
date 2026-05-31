#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双语 cues 构建器：从 cues_en.json + bi_config.json 合并出 cues_bi.json。

配置文件 bi_config.json 只含数据（纠错/翻译/时间覆写/删条），逻辑由本脚本承载，
所有视频复用同一脚本，逐视频只需写一份配置。

用法:
  build_bi_cues.py --config bi_config.json [--cues cues_en.json] [--out cues_bi.json]

bi_config.json 格式:
  {
    "corr": {"Cloud Code": "Claude Code"},      // 英文识别纠错（顺序敏感：长/特定短语在前）
    "en_override": {},                           // 个别条整句覆写英文：{"3": "corrected en"}
    "time_override": {"7": [1.2, 5.0]},         // 个别条改时间：{"idx": [start, end]}
    "drop": [7, 8],                             // 删除的 idx 列表
    "zh": ["中文译文1", "中文译文2", ...]        // 逐条中文译文（数量必须等于 cues 数）
  }
"""
import json, argparse, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="bi_config.json 路径")
    ap.add_argument("--cues", default=None, help="cues_en.json 路径（默认与 config 同目录）")
    ap.add_argument("--out", default=None, help="输出 cues_bi.json 路径（默认与 config 同目录）")
    args = ap.parse_args()

    cfg_dir = os.path.dirname(os.path.abspath(args.config))
    cues_path = args.cues or os.path.join(cfg_dir, "cues_en.json")
    out_path = args.out or os.path.join(cfg_dir, "cues_bi.json")

    cfg = json.load(open(args.config, encoding="utf-8"))
    cues = json.load(open(cues_path, encoding="utf-8"))

    corr = cfg.get("corr", {})
    en_override = {int(k): v for k, v in cfg.get("en_override", {}).items()}
    time_override = {int(k): tuple(v) for k, v in cfg.get("time_override", {}).items()}
    drop = set(cfg.get("drop", []))
    zh = cfg.get("zh", [])

    assert len(zh) == len(cues), f"ZH {len(zh)} != cues {len(cues)}"

    out = []
    for c, z in zip(cues, zh):
        if c["idx"] in drop:
            continue
        en = en_override.get(c["idx"], c["text"])
        for a, b in corr.items():
            en = en.replace(a, b)
        start, end = time_override.get(c["idx"], (c["start"], c["end"]))
        out.append({"start": start, "end": end, "en": en.strip(), "zh": z})

    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✓ {os.path.basename(out_path)}: {len(out)} 条")


if __name__ == "__main__":
    main()
