#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（稳定版）
仅使用 get_share_token 验证，成功率最高
"""

import os
import sys
import time
from aligo import Aligo

def main():
    refresh_token = os.environ.get("ALIYUN_REFRESH_TOKEN")
    if not refresh_token:
        print("错误: 未设置 ALIYUN_REFRESH_TOKEN")
        sys.exit(1)

    try:
        ali = Aligo(refresh_token=refresh_token)
    except Exception as e:
        print(f"登录失败: {e}")
        sys.exit(1)

    input_file = "alishare_list.txt"
    valid_lines = []
    invalid_lines = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 找不到 {input_file}")
        sys.exit(1)

    print(f"开始检测 {len(lines)} 个分享链接...\n")

    for line in lines:
        line = line.strip()
        if not line:
            valid_lines.append(line)
            continue

        parts = line.split()
        if len(parts) < 2:
            print(f"⚠️ 格式错误: {line}")
            valid_lines.append(line)
            continue

        path = parts[0]
        share_id = parts[1]
        extra_pwd = parts[2] if len(parts) >= 3 else None

        passwords_to_try = [""]
        if extra_pwd:
            passwords_to_try.append(extra_pwd)

        success = False
        for pwd in passwords_to_try:
            try:
                share_token_resp = ali.get_share_token(share_id=share_id, share_pwd=pwd)
                if share_token_resp and share_token_resp.share_token:
                    success = True
                    break
            except Exception:
                continue

        if success:
            valid_lines.append(line)
            print(f"✅ 有效: {path}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path}")

        time.sleep(0.2)   # 缩短间隔，减少等待

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
