#!/usr/bin/env python3
import os
import re
import requests

# 115分享信息API（从浏览器抓包获取）
SHARE_INFO_API = "https://115cdn.com/api/share/shareinfo"

def get_cid_from_share(share_code, password, cookie):
    """从分享链接获取文件夹CID"""
    params = {
        "share_code": share_code,
        "receive_code": password
    }
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(SHARE_INFO_API, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        if data.get("state"):
            # 根据API返回调整字段名
            cid = data["data"].get("share_id") or data["data"].get("file_id") or data["data"].get("pick_code")
            if cid:
                return str(cid)
        print(f"API返回错误: {data}")
        return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def parse_line(line):
    """解析115.txt的每一行"""
    line = line.strip()
    if not line:
        return None
    
    # 分割序号+目录 和 URL
    parts = re.split(r'\s+', line, maxsplit=1)
    if len(parts) != 2:
        print(f"格式错误（缺少URL）: {line}")
        return None
    
    title_part, url = parts[0], parts[1]
    
    # 提取分享码
    share_code_match = re.search(r'/s/([a-zA-Z0-9]+)', url)
    if not share_code_match:
        print(f"无法提取分享码: {url}")
        return None
    share_code = share_code_match.group(1)
    
    # 提取密码
    password_match = re.search(r'password=([^&]+)', url)
    if not password_match:
        print(f"无法提取密码: {url}")
        return None
    password = password_match.group(1)
    
    return title_part, share_code, password

def main():
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("错误: 环境变量 COOKIE_115 未设置")
        return
    
    source_file = "115.txt"
    target_file = "115share_list.txt"
    
    if not os.path.exists(source_file):
        print("错误: 115.txt 不存在")
        return
    
    new_lines = []
    with open(source_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            parsed = parse_line(line)
            if not parsed:
                continue
            
            title_part, share_code, password = parsed
            cid = get_cid_from_share(share_code, password, cookie)
            
            if not cid:
                print(f"跳过第{line_num}行: 获取CID失败")
                continue
            
            new_line = f"{title_part} {share_code} {cid} {password}\n"
            new_lines.append(new_line)
            print(f"已处理: {title_part} -> CID: {cid}")
    
    if new_lines:
        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"成功写入 {target_file}，共 {len(new_lines)} 条记录")
    else:
        print("没有生成任何有效记录")

if __name__ == "__main__":
    main()
