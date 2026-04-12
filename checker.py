#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（精确版）
通过解析页面内嵌的 JSON 数据判断分享是否真正有效
"""

import requests
import re
import json
import sys
import time

def is_share_valid(share_id: str) -> tuple[bool, str]:
    """
    返回 (是否有效, 详情)
    """
    url = f"https://www.aliyundrive.com/s/{share_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"

        html = resp.text

        # 1. 先快速检查明显的失效关键词（兜底）
        quick_invalid = ["分享已失效", "你来晚了", "文件已被删除", "分享链接无效"]
        for kw in quick_invalid:
            if kw in html:
                return False, f"页面提示: {kw}"

        # 2. 尝试提取 window.__INITIAL_STATE__ 中的 JSON 数据
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if not match:
            # 可能页面需要密码，尝试查找其他特征
            if "请输入提取码" in html or "提取码" in html:
                return True, "需要提取码（链接本身有效）"
            return False, "无法解析页面状态"

        try:
            state = json.loads(match.group(1))
        except json.JSONDecodeError:
            return False, "JSON 解析失败"

        # 3. 检查分享信息中的错误码
        share_info = state.get("shareInfo", {})
        error_code = share_info.get("errorCode")
        error_msg = share_info.get("errorMsg", "")

        if error_code:
            # 常见错误码：ShareLink.Forbidden, ShareLink.NotFound 等
            return False, f"API错误: {error_code} - {error_msg}"

        # 4. 检查文件列表是否存在且非空（如果有 fileList 字段）
        file_list = state.get("fileList", [])
        if isinstance(file_list, list) and len(file_list) > 0:
            return True, f"有效，包含 {len(file_list)} 个文件/文件夹"

        # 5. 如果是需要密码的分享，fileList 可能为空，但 shareInfo 中会有 pwdRequired 字段
        if share_info.get("pwdRequired") is True:
            return True, "需要提取码（链接本身有效）"

        # 6. 最后兜底：没有错误且页面包含阿里云盘特征，认为有效
        if "阿里云盘" in html and len(html) > 5000:
            return True, "页面正常（无法确定文件列表）"

        return False, "分享可能已空或不可访问"

    except requests.exceptions.Timeout:
        return False, "请求超时"
    except Exception as e:
        return False, f"异常: {str(e)}"

def main():
    input_file = "alishare_list.txt"
    valid_lines = []
    invalid_lines = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        sys.exit(1)

    print(f"开始检测 {len(lines)} 个分享链接...\n")

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            valid_lines.append(line)
            continue

        parts = line.split()
        if len(parts) < 2:
            print(f"⚠️ 格式错误（至少需要路径和分享ID）: {line}")
            valid_lines.append(line)
            continue

        path = parts[0]
        share_id = parts[1]
        # 第三段凭证忽略

        ok, detail = is_share_valid(share_id)
        if ok:
            valid_lines.append(line)
            print(f"✅ 有效: {path} — {detail}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path} — {detail}")

        time.sleep(0.5)  # 避免请求过快

    # 更新原文件
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines))
        if valid_lines and valid_lines[-1] != "":
            f.write("\n")

    with open("invalid_links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(invalid_lines))

    print(f"\n检测完成！有效: {len(valid_lines)}，失效: {len(invalid_lines)}")
    sys.exit(0)

if __name__ == "__main__":
    main()
