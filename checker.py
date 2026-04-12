#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本
用法: python checker.py
读取 alishare_list.txt，检测每个分享链接，将失效的写入失效文件，并更新原文件
"""

import requests
import sys
import os
from typing import List, Tuple

def extract_share_info_from_line(line: str) -> Tuple[str, str, str]:
    """从一行文本中提取路径、分享ID和密码"""
    parts = line.strip().split()
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    return "", "", ""

def check_share_validity(share_id: str, share_pwd: str, refresh_token: str) -> bool:
    """检测分享链接是否有效"""
    # 第一步：获取分享 token
    token_url = "https://api.aliyundrive.com/adrive/v2/share_link/get_share_token"
    token_payload = {"share_id": share_id, "share_pwd": share_pwd}
    
    try:
        resp = requests.post(token_url, json=token_payload, timeout=10)
        if resp.status_code != 200:
            return False
        
        data = resp.json()
        share_token = data.get("share_token")
        if not share_token:
            return False
        
        # 第二步：验证分享内容是否存在
        list_url = "https://api.aliyundrive.com/adrive/v3/share_link/get_share_by_share_token"
        list_payload = {"share_id": share_id, "share_token": share_token}
        
        list_resp = requests.post(list_url, json=list_payload, timeout=10)
        return list_resp.status_code == 200
        
    except Exception:
        return False

def main():
    # 从 GitHub Secrets 读取 refresh_token
    refresh_token = os.environ.get("ALIYUN_REFRESH_TOKEN", "")
    if not refresh_token:
        print("错误: 未设置 ALIYUN_REFRESH_TOKEN 环境变量")
        sys.exit(1)
    
    input_file = "alishare_list.txt"   # 修改为新的文件名
    valid_lines = []
    invalid_lines = []
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        sys.exit(1)
    
    print(f"开始检测 {len(lines)} 个分享链接...")
    
    for line in lines:
        line = line.strip()
        if not line:
            valid_lines.append(line)  # 保留空行
            continue
        
        path, share_id, share_pwd = extract_share_info_from_line(line)
        if not share_id:
            valid_lines.append(line)  # 格式错误的行暂时保留
            print(f"⚠️ 格式错误: {line[:50]}...")
            continue
        
        if check_share_validity(share_id, share_pwd, refresh_token):
            valid_lines.append(line)
            print(f"✅ 有效: {path}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path}")
    
    # 更新原文件（只保留有效的）
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines))
        if valid_lines and not valid_lines[-1] == "":
            f.write("\n")
    
    # 记录失效链接到单独文件
    with open("invalid_links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(invalid_lines))
    
    print(f"\n检测完成！有效链接: {len(valid_lines)}，失效链接: {len(invalid_lines)}")
    
    # 如果有失效链接，返回非零退出码，以便后续步骤可以检测到变更
    if invalid_lines:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
