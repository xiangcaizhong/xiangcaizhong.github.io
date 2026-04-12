#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（混合版）
1. 使用 get_share_token 验证（与之前成功版本一致）
2. 对 token 成功的链接，再调用一次文件列表 API 确认实际可访问
3. 使用 requests 直接调用 API，避免 aligo 版本兼容问题
"""

import os
import sys
import time
import requests
from aligo import Aligo

def check_file_list_via_api(share_id, share_token):
    """直接调用阿里云盘文件列表 API，返回 (是否成功, 错误信息)"""
    url = "https://api.aliyundrive.com/v2/share_link/get_share_file_list"
    headers = {
        "Authorization": f"Bearer {share_token}",
        "Content-Type": "application/json",
    }
    body = {
        "share_id": share_id,
        "limit": 1,
        "order_by": "name",
        "order_direction": "ASC",
        "parent_file_id": "root",
    }
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # 检查是否有错误码
            if "code" in data:
                if data["code"] in ("NotFound.Drive", "ShareLink.Forbidden"):
                    return False, data["code"]
            # 有 items 且至少一个条目
            if data.get("items") and len(data["items"]) > 0:
                return True, "ok"
            else:
                # 无 items 或空列表，视为失效（分享可能为空或无法访问）
                return False, "empty_list"
        else:
            # 尝试解析错误
            try:
                err = resp.json()
                code = err.get("code")
                if code:
                    return False, code
                else:
                    return False, f"HTTP {resp.status_code}"
            except:
                return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

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

        # 尝试密码列表
        passwords_to_try = [""]
        if extra_pwd:
            passwords_to_try.append(extra_pwd)

        success = False
        detail = ""
        for pwd in passwords_to_try:
            try:
                # 第一步：获取 share_token
                share_token_resp = ali.get_share_token(share_id=share_id, share_pwd=pwd)
                if not share_token_resp or not share_token_resp.share_token:
                    continue
                share_token = share_token_resp.share_token

                # 第二步：验证文件列表（额外检查）
                ok, msg = check_file_list_via_api(share_id, share_token)
                if ok:
                    success = True
                    detail = "文件列表可访问"
                    break
                else:
                    detail = f"token有效但列表失败: {msg}"
                    # 如果列表失败，不认为有效，继续尝试下一个密码（如果有）
                    continue
            except Exception as e:
                detail = str(e)
                continue

        if success:
            valid_lines.append(line)
            print(f"✅ 有效: {path}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path} — {detail}")

        # 动态调整间隔：如果遇到 429 可适当增加，这里简单使用 0.3 秒
        time.sleep(0.3)

    # 更新文件
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
