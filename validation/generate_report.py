#!/usr/bin/env python3
"""
FireSing 技术验证报告生成器
读取所有 V1-V8 结果, 生成综合验证报告
"""

import json
import os
import sys
from datetime import datetime


def load_result(path):
    """加载验证结果"""
    if not os.path.exists(path):
        return {"test": os.path.basename(path), "status": "NOT_RUN"}
    with open(path, "r") as f:
        return json.load(f)


def generate_report():
    results_dir = "validation/results"
    report_path = "validation/VALIDATION_REPORT.md"

    tests = [
        ("V1", "UVR5 人声分离", "v1_result.json"),
        ("V2", "Whisper 歌词对齐", "v2_result.json"),
        ("V3", "RVC 逐句音色转换", "v3_result.json"),
        ("V4", "音色切换自然度", "v4_result.json"),
        ("V5", "合唱检测与合成", "v5_result.json"),
        ("V6", "独白处理", "v6_result.json"),
        ("V7", "视频生成", "v7_result.json"),
        ("V8", "端到端管线", "v8_result.json"),
    ]

    report_lines = [
        f"# FireSing 技术验证报告",
        f"",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## 验证环境",
        f"",
        f"| 组件 | 规格 |",
        f"|------|------|",
        f"| GPU | AutoDL RTX 4090D (24GB VRAM) |",
        f"| CPU | (AutoDL 默认) |",
        f"| OS | Ubuntu (AutoDL) |",
        f"| Python | 3.10+ |",
        f"| PyTorch | 2.x + CUDA 12.1 |",
        f"",
        f"## 验证总览",
        f"",
    ]

    # 加载所有结果
    all_results = {}
    for test_id, test_name, filename in tests:
        all_results[test_id] = load_result(os.path.join(results_dir, filename))

    # 总览表
    report_lines.append(f"| # | 验证项 | 状态 | 耗时 | 关键发现 |")
    report_lines.append(f"|---|--------|------|------|----------|")

    total_time = 0
    pass_count = 0
    fail_count = 0
    skip_count = 0

    for test_id, test_name, filename in tests:
        r = all_results[test_id]
        status = r.get("status", "NOT_RUN")
        time_s = r.get("processing_time_s", r.get("total_time_s", "—"))

        if isinstance(time_s, (int, float)):
            total_time += time_s
            time_str = f"{time_s}s"
        else:
            time_str = str(time_s)

        status_icon = {
            "PASS": "PASS",
            "FAIL": "**FAIL**",
            "FALLBACK": "PASS (fallback)",
            "SKIP": "SKIP",
            "NOT_RUN": "NOT RUN",
        }.get(status, status)

        notes = r.get("notes", r.get("error", "—"))
        if notes and len(notes) > 60:
            notes = notes[:57] + "..."

        report_lines.append(f"| {test_id} | {test_name} | {status_icon} | {time_str} | {notes} |")

        if status == "PASS" or status == "FALLBACK":
            pass_count += 1
        elif status == "FAIL":
            fail_count += 1
        else:
            skip_count += 1

    report_lines.append(f"")
    report_lines.append(f"**通过: {pass_count} / 失败: {fail_count} / 未运行: {skip_count}**")
    if total_time > 0:
        report_lines.append(f"**端到端总耗时: {total_time:.1f}s**")

    # 详细结果
    report_lines.append(f"")
    report_lines.append(f"## 详细结果")
    report_lines.append(f"")

    for test_id, test_name, filename in tests:
        r = all_results[test_id]
        status = r.get("status", "NOT_RUN")

        report_lines.append(f"### {test_id}: {test_name}")
        report_lines.append(f"")
        report_lines.append(f"**状态: {status}**")
        report_lines.append(f"")

        # 输出关键指标
        key_fields = [
            "processing_time_s", "total_conversion_time_s", "avg_per_line_s",
            "total_segments", "voice_models_used", "input_size_mb",
            "avg_centroid_diff_hz", "intro_duration_s",
            "video_file_size_mb", "generation_time_s",
        ]

        metrics = {}
        for field in key_fields:
            if field in r:
                metrics[field] = r[field]

        if metrics:
            report_lines.append(f"| 指标 | 值 |")
            report_lines.append(f"|------|-----|")
            for k, v in metrics.items():
                report_lines.append(f"| {k} | {v} |")
            report_lines.append(f"")

        if "error" in r:
            report_lines.append(f"**错误: {r['error']}**")
            report_lines.append(f"")

        notes = r.get("notes", "")
        if notes:
            report_lines.append(f"> {notes}")
            report_lines.append(f"")

        report_lines.append(f"---")
        report_lines.append(f"")

    # 风险评估
    report_lines.append(f"## 风险评估")
    report_lines.append(f"")

    risks = []

    # 检查各环节风险
    if all_results["V1"].get("status") != "PASS":
        risks.append(("- 人声分离", "高", "UVR5 质量直接影响后续所有步骤"))
    if all_results["V2"].get("status") != "PASS":
        risks.append(("- 歌词对齐", "高", "时间戳不准会导致音色切换错位"))
    if all_results["V3"].get("status") != "PASS":
        risks.append(("- RVC 转换", "高", "音色转换质量是核心功能"))
    if all_results["V4"].get("status") != "PASS":
        risks.append(("- 音色切换", "中", "交叉淡化参数需要调试"))
    if all_results["V5"].get("status") != "PASS":
        risks.append(("- 合唱检测", "中", "可以用手动标注回退"))
    if all_results.get("V8", {}).get("performance_target", {}).get("on_target") is False:
        risks.append(("- 性能", "中", f"端到端耗时超标: {all_results['V8'].get('total_time_s', '?')}s > 180s"))

    if risks:
        report_lines.append(f"| 风险项 | 等级 | 说明 |")
        report_lines.append(f"|--------|------|------|")
        for risk, level, desc in risks:
            report_lines.append(f"| {risk} | {level} | {desc} |")
    else:
        report_lines.append(f"所有验证项通过, 无高风险项。")

    report_lines.append(f"")
    report_lines.append(f"## 结论")
    report_lines.append(f"")

    if fail_count == 0 and pass_count == len(tests):
        report_lines.append(f"所有技术验证通过。建议进入正式开发阶段。")
    elif fail_count > 0:
        report_lines.append(f"有 {fail_count} 项验证失败。需要解决上述问题后重新验证。")
    else:
        report_lines.append(f"部分验证未运行。完成所有验证后重新生成报告。")

    # 写入报告
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"[Report] {report_path}")
    print(f"[Summary] PASS: {pass_count}, FAIL: {fail_count}, SKIP: {skip_count}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(generate_report())
