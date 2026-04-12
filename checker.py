#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（增强版）
增加文件列表验证，确保不仅能获取 token，还能正常列出文件
"""

import os
import sys
import time
from aligo import Aligo

def check_share_files(ali, share_id, share_pwd):
    """尝试获取分享的文件列表，返回 (是否有效, 详情)"""
    try:
        # 第一步：获取 share_token
        share_token_resp = ali.get_share_token(share_id=share_id, share_pwd=share_pwd)
        if not share_token_resp or not share_token_resp.share_token:
            return False, "无法获取 share_token"

        share_token = share_token_resp.share_token

        # 第二步：调用文件列表接口
        url = "https://api.aliyundrive.com/v2/share_link/get_share_file_list"
        headers = {
            "Authorization": f"Bearer {share_token}",
            "Content-Type": "application/json",
        }
        body = {
            "share_id": share_id,
            "limit": 1,                     # 只取一个文件即可验证
            "order_by": "name",
            "order_direction": "ASC",
            "parent_file_id": "root",
        }
        resp = ali._post(url, headers=headers, body=body)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            # 如果 items 存在且不为空（即使为空列表，也可能是分享被清空）
            if items and len(items) > 0:
                return True, f"有 {len(items)} 个文件/文件夹"
            else:
                # 检查响应中是否有错误码
                if "code" in data and data["code"] in ("NotFound.Drive", "ShareLink.Forbidden"):
                    return False, f"API错误: {data['code']}"
                else:
                    # 空列表视为无效（分享可能已空或权限不足）
                    return False, "分享为空或无法访问文件列表"
        else:
            # 非200状态，尝试解析错误
            try:
                err = resp.json()
                code = err.get("code")
                if code in ("NotFound.Drive", "ShareLink.Forbidden"):
                    return False, f"API错误: {code}"
                else:
                    return False, f"HTTP {resp.status_code}: {err.get('message', '')}"
            except:
                return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, f"异常: {str(e)}"

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
        detail = ""
        for pwd in passwords_to_try:
            ok, msg = check_share_files(ali, share_id, pwd)
            if ok:
                success = True
                detail = msg
                break
            else:
                # 如果是密码错误，继续尝试下一个密码
                if "share_pwd" in msg.lower() or "密码" in msg:
                    continue
                # 其他错误记录，但不立即失败（可能下一个密码成功）
                detail = msg
        if success:
            valid_lines.append(line)
            print(f"✅ 有效: {path} — {detail}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path} — {detail}")

        time.sleep(0.3)  # 避免请求过快

    # 更新原文件
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
