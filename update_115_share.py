#!/usr/bin/env python3
import os
import re
import requests
import json

def get_cid_from_share(share_url, password, cookie):
    """从分享链接获取文件夹CID"""
    
    # 从URL提取分享码
    share_code_match = re.search(r'/s/([a-zA-Z0-9]+)', share_url)
    if not share_code_match:
        print(f"无法提取分享码: {share_url}")
        return None
    share_code = share_code_match.group(1)
    
    print(f"正在处理分享码: {share_code}, 密码: {password}")
    
    # 尝试多个API接口
    apis = [
        {
            "url": "https://115.com/api/share/shareinfo",
            "params": {"share_code": share_code, "receive_code": password}
        },
        {
            "url": "https://webapi.115.com/share/shareinfo",
            "params": {"share_code": share_code, "receive_code": password}
        },
        {
            "url": "https://115cdn.com/api/share/shareinfo",
            "params": {"share_code": share_code, "receive_code": password}
        }
    ]
    
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://115.com/s/{share_code}"
    }
    
    for api in apis:
        try:
            print(f"尝试API: {api['url']}")
            resp = requests.get(api["url"], params=api["params"], headers=headers, timeout=10)
            print(f"响应状态码: {resp.status_code}")
            
            # 尝试解析JSON
            try:
                data = resp.json()
                print(f"API返回: {json.dumps(data, ensure_ascii=False)[:200]}")
                
                if data.get("state") or data.get("code") == 0:
                    # 查找CID字段
                    if "data" in data:
                        cid = data["data"].get("share_id") or data["data"].get("file_id") or data["data"].get("pick_code") or data["data"].get("cid")
                        if cid:
                            print(f"成功获取CID: {cid}")
                            return str(cid)
                    # 直接查找
                    cid = data.get("share_id") or data.get("file_id") or data.get("pick_code") or data.get("cid")
                    if cid:
                        print(f"成功获取CID: {cid}")
                        return str(cid)
            except:
                print(f"响应不是JSON格式: {resp.text[:200]}")
                
        except Exception as e:
            print(f"API请求失败: {e}")
    
    print("所有API都失败了")
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
    
    # 提取密码
    password_match = re.search(r'password=([^&]+)', url)
    if not password_match:
        print(f"无法提取密码: {url}")
        return None
    password = password_match.group(1)
    
    return title_part, url, password

def main():
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("错误: 环境变量 COOKIE_115 未设置")
        return
    
    source_file = "115.txt"
    target_file = "115share_list.txt"
    
    if not os.path.exists(source_file):
        print(f"错误: {source_file} 不存在")
        # 创建一个示例文件
        with open(source_file, "w", encoding="utf-8") as f:
            f.write("3、学习机计划/电视剧    https://115cdn.com/s/swf94vk3nqq?password=l224\n")
        print(f"已创建示例 {source_file}，请编辑后重新运行")
        return
    
    new_lines = []
    with open(source_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            parsed = parse_line(line)
            if not parsed:
                continue
            
            title_part, share_url, password = parsed
            cid = get_cid_from_share(share_url, password, cookie)
            
            if not cid:
                print(f"跳过第{line_num}行: 获取CID失败")
                continue
            
            # 提取分享码用于输出
            share_code_match = re.search(r'/s/([a-zA-Z0-9]+)', share_url)
            share_code = share_code_match.group(1) if share_code_match else "unknown"
            
            new_line = f"{title_part} {share_code} {cid} {password}\n"
            new_lines.append(new_line)
            print(f"✓ 已处理: {title_part}")
    
    if new_lines:
        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"\n成功写入 {target_file}，共 {len(new_lines)} 条记录")
        print("\n生成的内容：")
        for line in new_lines:
            print(line.strip())
    else:
        print("\n没有生成任何有效记录")
        print("请检查：")
        print("1. 115.txt 格式是否正确")
        print("2. COOKIE_115 是否有效（可能已过期）")
        print("3. 分享链接和密码是否正确")

if __name__ == "__main__":
    main()
