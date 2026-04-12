#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（稳健版）
使用 aligo 官方方法验证文件列表
"""

import os
import sys
import time
from aligo import Aligo

def check_share_files(ali, share_id, share_pwd):
    """尝试获取分享的文件列表，返回 (是否有效, 详情)"""
    try:
        # 1. 获取 share_token
        share_token_resp = ali.get_share_token(share_id=share_id, share_pwd=share_pwd)
        if not share_token_resp or not share_token_resp.share_token:
            return False, "无法获取 share_token"

        # 2. 使用 share_token 获取文件列表（只请求第一页，limit=1）
        try:
            file_list = ali.get_share_file_list(
                share_id=share_id,
                share_token=share_token_resp.share_token,
                limit=1
            )
        except Exception as e:
            # 捕获 aligo 内部抛出的异常（例如 404, 403 等）
            error_msg = str(e)
            if "NotFound.Drive" in error_msg:
                return False, "分享关联的网盘不存在 (NotFound.Drive)"
            elif "ShareLink.Forbidden" in error_msg:
                return False, "分享已被禁止访问 (ShareLink.Forbidden)"
            else:
                return False, f"文件列表请求失败: {error_msg[:100]}"

        # 3. 检查返回的文件列表
        if file_list and hasattr(file_list, 'items') and file_list.items:
            # 有至少一个文件/文件夹
            return True, f"有 {len(file_list.items)} 个文件/文件夹"
        else:
            # 列表为空，可能分享已空或权限不足
            return False, "分享为空或无法列出文件"

    except Exception as e:
        return False, f"检测异常: {str(e)[:100]}"

def main():
    refresh_token = os.environ.get("ALIYUN_REFRESH_TOKEN")
    if not refresh_token:
        print("错误: 未设置 ALIYUN_REFRESH_TOKEN 环境变量")
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
        detail = ""
        for pwd in passwords_to_try:
            ok, msg = check_share_files(ali, share_id, pwd)
            if ok:
                success = True
                detail = msg
                break
            else:
                detail = msg
                # 如果是密码错误，继续尝试下一个
                if "share_pwd" in msg.lower() or "密码" in msg.lower():
                    continue
                else:
                    # 非密码错误（如 NotFound.Drive），不再尝试其他密码
                    break

        if success:
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
