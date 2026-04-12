#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（增强版）
"""

import requests
import sys
import os
import json

def check_share_validity(share_id: str, share_pwd: str) -> tuple[bool, str]:
    """
    检测分享链接是否有效
    返回 (是否有效, 详情信息)
    """
    # 第一步：获取 share_token
    token_url = "https://api.aliyundrive.com/adrive/v2/share_link/get_share_token"
    token_payload = {"share_id": share_id, "share_pwd": share_pwd}
    
    try:
        resp = requests.post(token_url, json=token_payload, timeout=10)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        
        data = resp.json()
        share_token = data.get("share_token")
        if not share_token:
            return False, f"无 share_token: {data}"
        
        # 第二步：获取分享信息（更可靠的方式）
        info_url = "https://api.aliyundrive.com/adrive/v2/share_link/get_share_info"
        headers = {"Authorization": f"Bearer {share_token}"}
        info_payload = {"share_id": share_id}
        
        info_resp = requests.post(info_url, json=info_payload, headers=headers, timeout=10)
        if info_resp.status_code == 200:
            info_data = info_resp.json()
            # 检查是否包含有效内容
            if "name" in info_data or "file_name" in info_data:
                return True, "有效"
            else:
                return False, f"无有效内容: {info_data}"
        else:
            return False, f"get_share_info 返回 {info_resp.status_code}: {info_resp.text[:100]}"
    except Exception as e:
        return False, f"异常: {str(e)}"

def main():
    refresh_token = os.environ.get("ALIYUN_REFRESH_TOKEN", "")
    if not refresh_token:
        print("错误: 未设置 ALIYUN_REFRESH_TOKEN")
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
        if len(parts) < 3:
            print(f"⚠️ 格式错误: {line[:50]}")
            valid_lines.append(line)  # 保留格式错误的行
            continue
        
        path, share_id, share_pwd = parts[0], parts[1], parts[2]
        ok, detail = check_share_validity(share_id, share_pwd)
        if ok:
            valid_lines.append(line)
            print(f"✅ 有效: {path}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path} ({detail})")
    
    # 更新原文件
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines))
        if valid_lines and valid_lines[-1] != "":
            f.write("\n")
    
    with open("invalid_links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(invalid_lines))
    
    print(f"\n检测完成！有效: {len(valid_lines)}，失效: {len(invalid_lines)}")
    
    if invalid_lines:
        print(f"已清理 {len(invalid_lines)} 个失效链接")
    sys.exit(0)  # 始终返回成功，避免 Actions 报错

if __name__ == "__main__":
    main()
