#!/usr/bin/env python3
"""
阿里云盘分享链接有效性检测脚本（基于网页模拟）
适用于小雅格式：路径 share_id 长凭证（凭证在检测时忽略，仅用于展示）
"""

import requests
import sys
import time

def is_share_valid(share_id: str) -> tuple[bool, str]:
    """
    通过访问分享页面判断链接是否有效
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
        # 检查 HTTP 状态码
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        
        html = resp.text
        # 判断失效的关键词
        invalid_keywords = [
            "分享已失效",
            "你来晚了",
            "文件已被删除",
            "分享链接无效",
            "不存在",
            "share_link is forbidden"
        ]
        for kw in invalid_keywords:
            if kw in html:
                return False, f"页面提示: {kw}"
        
        # 如果页面包含 "请输入提取码" 或文件列表，说明有效（或需要密码）
        if "请输入提取码" in html or "提取码" in html:
            return True, "需要提取码（但链接本身有效）"
        
        # 有时候页面会直接显示文件列表（无密码情况）
        if "file-list" in html or "drive-file" in html:
            return True, "链接有效，可直接访问"
        
        # 兜底：如果页面既无失效关键词，又包含正常结构，认为有效
        if "阿里云盘" in html and len(html) > 1000:
            return True, "页面正常（可能无需密码）"
        
        return False, "无法判断（页面内容异常）"
    
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
    
    # 礼貌控制请求频率，避免被 ban
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
        # 第三段（凭证）忽略，不使用
        
        ok, detail = is_share_valid(share_id)
        if ok:
            valid_lines.append(line)
            print(f"✅ 有效: {path} — {detail}")
        else:
            invalid_lines.append(line)
            print(f"❌ 失效: {path} — {detail}")
        
        # 每检测一个暂停 0.5 秒，避免请求过快
        time.sleep(0.5)
    
    # 更新原文件（只保留有效的）
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
