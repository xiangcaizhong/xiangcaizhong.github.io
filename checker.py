#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本 - 使用 aligo 库
"""
import os
from aligo import Aligo

def main():
    # 从 GitHub Secrets 读取 refresh_token
    refresh_token = os.environ.get("ALIYUN_REFRESH_TOKEN", "")
    if not refresh_token:
        print("错误: 未设置 ALIYUN_REFRESH_TOKEN 环境变量")
        return

    try:
        ali = Aligo(refresh_token=refresh_token)
    except Exception as e:
        print(f"初始化 Aligo 失败，请检查 refresh_token 是否有效: {e}")
        return

    input_file = "alishare_list.txt"
    valid_lines = []
    invalid_lines = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        return

    print(f"开始检测 {len(lines)} 个分享链接...")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 3:
            print(f"⚠️ 格式错误: {line}")
            valid_lines.append(line)
            continue

        path, share_id, share_pwd = parts[0], parts[1], parts[2]
        try:
            share_token = ali.get_share_token(share_id=share_id, share_pwd=share_pwd)
            if share_token.share_token:
                valid_lines.append(line)
                print(f"✅ 有效: {path}")
            else:
                invalid_lines.append(line)
                print(f"❌ 失效: {path}")
        except Exception as e:
            invalid_lines.append(line)
            print(f"❌ 检测出错: {path} - {e}")

    # 更新原文件
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines))

    with open("invalid_links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(invalid_lines))

    print(f"\n检测完成！有效链接: {len(valid_lines)}，失效链接: {len(invalid_lines)}")

if __name__ == "__main__":
    main()
