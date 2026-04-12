#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（API 版）
尝试密码：空字符串 → 如果失败且列表中有第三段，则尝试第三段作为密码
"""

import os
import sys
import time
from aligo import Aligo

def main():
    refresh_token = os.environ.get("ALIYUN_REFRESH_TOKEN")
    if not refresh_token:
        print("错误: 未设置 ALIYUN_REFRESH_TOKEN 环境变量")
        sys.exit(1)

    # 初始化 Aligo
    try:
        ali = Aligo(refresh_token=refresh_token)
    except Exception as e:
        print(f"登录失败，请检查 refresh_token 是否有效: {e}")
        sys.exit(1)

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

    for line in lines:
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
        # 第三段作为备选密码（如果有）
        extra_pwd = parts[2] if len(parts) >= 3 else None

        # 尝试密码列表：优先空密码，其次 extra_pwd
        passwords_to_try = [""]
        if extra_pwd:
            passwords_to_try.append(extra_pwd)

        success = False
        for pwd in passwords_to_try:
            try:
                share_token = ali.get_share_token(share_id=share_id, share_pwd=pwd)
                if share_token and share_token.share_token:
                    success = True
                    break
            except Exception as e:
                error_msg = str(e)
                # 密码错误则继续尝试下一个密码
                if "SharePwd" in error_msg or "share_pwd" in error_msg:
                    continue
                # 其他错误（如网络、权限）直接打印并跳出
                print(f"⚠️ {path} 检测异常: {error_msg}")
                break

        if success:
            valid_lines.append(line)
            print(f"✅ 有效: {path}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path}")

        time.sleep(0.3)  # 避免请求过快

    # 更新原文件（只保留有效行）
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines))
        if valid_lines and valid_lines[-1] != "":
            f.write("\n")

    # 记录失效链接
    with open("invalid_links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(invalid_lines))

    print(f"\n检测完成！有效: {len(valid_lines)}，失效: {len(invalid_lines)}")
    sys.exit(0)

if __name__ == "__main__":
    main()
