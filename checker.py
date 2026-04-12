#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（优化版）
1. 使用 get_share_token 验证（与成功版本一致）
2. 对 token 成功的链接，再调用 get_share_info 确认分享信息可获取
3. 使用 requests 直接调用 API，避免 aligo 版本问题
4. 调整请求间隔为 0.5 秒，减少 429 风险
"""

import os
import sys
import time
import requests
from aligo import Aligo

def get_share_info_via_api(share_id, share_token):
    """获取分享基本信息，返回 (是否成功, 错误码或信息)"""
    url = "https://api.aliyundrive.com/v2/share_link/get_share_info"
    headers = {
        "Authorization": f"Bearer {share_token}",
        "Content-Type": "application/json",
    }
    body = {"share_id": share_id}
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "code" in data:
                # 有错误码，如 ShareLink.Forbidden, NotFound.Drive
                return False, data["code"]
            # 有效分享应包含 name 或 creator 等字段
            if "name" in data or "creator" in data:
                return True, "ok"
            else:
                return False, "no_info"
        else:
            # 非200，尝试解析错误
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

        # 尝试密码列表：空密码和第三段
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

                # 第二步：验证分享信息（get_share_info）
                ok, msg = get_share_info_via_api(share_id, share_token)
                if ok:
                    success = True
                    detail = "有效"
                    break
                else:
                    detail = f"分享信息获取失败: {msg}"
                    # 如果错误是密码相关，继续尝试下一个密码；否则直接跳出
                    if "SharePwd" in msg or "share_pwd" in msg:
                        continue
                    else:
                        # 非密码错误（如 Forbidden, NotFound），不再尝试其他密码
                        break
            except Exception as e:
                detail = str(e)
                continue

        if success:
            valid_lines.append(line)
            print(f"✅ 有效: {path}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path} — {detail}")

        # 固定间隔 0.5 秒，减少触发频率限制
        time.sleep(0.5)

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
