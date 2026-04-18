#!/usr/bin/env python3
"""
115分享链接CID自动提取工具 - 使用 /webapi/share/snap (GET)
"""
import os
import re
import requests
import json
import time

def get_cid_from_share(share_url, password, cookie):
    """通过 snap API 获取分享文件夹的 CID"""
    
    # 提取分享码
    share_code_match = re.search(r'/s/([a-zA-Z0-9]+)', share_url)
    if not share_code_match:
        print(f"❌ 无法提取分享码: {share_url}")
        return None
    share_code = share_code_match.group(1)
    
    print(f"📁 分享码: {share_code}")
    print(f"🔑 密码: {password}")
    
    # 使用 GET 方法，参数拼接到 URL
    snap_url = "https://115cdn.com/webapi/share/snap"
    params = {
        "share_code": share_code,
        "receive_code": password,   # 注意参数名是 receive_code
        "cid": 0,
        "limit": 1
    }
    
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://115cdn.com/s/{share_code}?password={password}"
    }
    
    try:
        print(f"🌐 调用API: {snap_url}")
        resp = requests.get(snap_url, params=params, headers=headers, timeout=15)
        print(f"📡 响应状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"📡 API返回: {json.dumps(data, ensure_ascii=False)[:200]}")
            
            if data.get("state") == True:
                file_list = data.get("data", {}).get("list", [])
                if file_list and len(file_list) > 0:
                    cid = str(file_list[0].get("cid"))
                    if cid and cid != "0":
                        print(f"✅ 成功获取CID: {cid}")
                        return cid
                    else:
                        print(f"⚠️ 获取到的CID为0")
                else:
                    print(f"⚠️ list为空")
            else:
                error_msg = data.get("error", "未知错误")
                print(f"❌ API返回错误: {error_msg}")
        else:
            print(f"❌ HTTP错误: {resp.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None

def parse_line(line):
    """解析115.txt的每一行"""
    line = line.strip()
    if not line:
        return None
    
    parts = re.split(r'\s+', line, maxsplit=1)
    if len(parts) != 2:
        print(f"❌ 格式错误（缺少URL）: {line}")
        return None
    
    title_part, url = parts[0], parts[1]
    
    password_match = re.search(r'password=([^&]+)', url)
    if not password_match:
        print(f"❌ 无法提取密码: {url}")
        return None
    password = password_match.group(1)
    
    return title_part, url, password

def main():
    print("=" * 60)
    print("115分享链接CID自动提取工具 (snap API - GET)")
    print("=" * 60)
    
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("❌ 错误: 环境变量 COOKIE_115 未设置")
        return
    
    source_file = "115.txt"
    target_file = "115share_list.txt"
    
    if not os.path.exists(source_file):
        print(f"❌ 错误: {source_file} 不存在")
        return
    
    print(f"\n📖 读取 {source_file}...")
    
    new_lines = []
    with open(source_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        print(f"\n{'='*50}")
        print(f"处理第{line_num}行:")
        
        parsed = parse_line(line)
        if not parsed:
            continue
        
        title_part, share_url, password = parsed
        display_url = re.sub(r'password=[^&]+', 'password=***', share_url)
        print(f"📝 标题: {title_part}")
        print(f"🔗 链接: {display_url}")
        
        cid = get_cid_from_share(share_url, password, cookie)
        
        if not cid:
            print(f"❌ 跳过第{line_num}行")
            continue
        
        share_match = re.search(r'/s/([a-zA-Z0-9]+)', share_url)
        share_code = share_match.group(1) if share_match else "unknown"
        
        new_line = f"{title_part} {share_code} {cid} {password}\n"
        new_lines.append(new_line)
        print(f"✅ 已处理: {title_part}")
        
        time.sleep(1)
    
    if new_lines:
        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        print(f"\n{'='*60}")
        print(f"✅ 成功！已生成 {target_file}")
        print(f"📊 共处理 {len(new_lines)} 条记录")
        print("\n生成的内容:")
        for line in new_lines:
            print(f"  {line.strip()}")
    else:
        print("\n❌ 没有生成任何有效记录")

if __name__ == "__main__":
    main()
