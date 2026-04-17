#!/usr/bin/env python3
import os
import re
import requests
import json
import time

def get_cid_from_share(share_url, password, cookie):
    """通过模拟浏览器访问获取CID"""
    
    # 提取分享码
    share_code_match = re.search(r'/s/([a-zA-Z0-9]+)', share_url)
    if not share_code_match:
        print(f"无法提取分享码: {share_url}")
        return None
    share_code = share_code_match.group(1)
    
    print(f"正在处理分享码: {share_code}, 密码: {password}")
    
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://115.com/s/{share_code}",
        "Origin": "https://115.com",
        "Connection": "keep-alive"
    }
    
    # 方法1: 先访问分享页面获取token
    try:
        print("步骤1: 访问分享页面...")
        share_page_url = f"https://115.com/s/{share_code}"
        session = requests.Session()
        session.headers.update(headers)
        
        resp = session.get(share_page_url)
        print(f"页面访问状态: {resp.status_code}")
        
        # 从页面中提取一些关键信息
        if 'receive_code' in resp.text:
            print("页面包含receive_code")
        
        time.sleep(1)  # 等待一下
        
        # 方法2: 尝试使用官方API (带receive_code参数)
        print("步骤2: 尝试提交密码...")
        api_url = "https://115.com/share/shareinfo"
        params = {
            "share_code": share_code,
            "receive_code": password
        }
        
        resp = session.get(api_url, params=params)
        print(f"API状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"API返回: {json.dumps(data, ensure_ascii=False)}")
                
                if data.get("state") == True:
                    # 成功获取分享信息
                    share_data = data.get("data", {})
                    # 尝试多个可能的字段名
                    cid = (share_data.get("share_id") or 
                          share_data.get("file_id") or 
                          share_data.get("pick_code") or
                          share_data.get("cid") or
                          share_data.get("fid"))
                    
                    if cid:
                        print(f"✓ 成功获取CID: {cid}")
                        return str(cid)
                    else:
                        print(f"返回数据中没有CID字段，可用字段: {list(share_data.keys())}")
                else:
                    error_msg = data.get("error", "未知错误")
                    print(f"API返回错误: {error_msg}")
            except Exception as e:
                print(f"JSON解析失败: {e}")
        
        # 方法3: 尝试webapi接口
        print("步骤3: 尝试备用API...")
        api_url2 = "https://webapi.115.com/share/shareinfo"
        params = {
            "share_code": share_code,
            "receive_code": password
        }
        
        resp = session.get(api_url2, params=params)
        print(f"备用API状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"备用API返回: {json.dumps(data, ensure_ascii=False)}")
                
                if data.get("state") == True:
                    share_data = data.get("data", {})
                    cid = (share_data.get("share_id") or 
                          share_data.get("file_id") or 
                          share_data.get("pick_code"))
                    
                    if cid:
                        print(f"✓ 成功获取CID: {cid}")
                        return str(cid)
            except Exception as e:
                print(f"JSON解析失败: {e}")
                
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("❌ 所有方法都失败了")
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

def test_cookie(cookie):
    """测试Cookie是否有效"""
    try:
        test_url = "https://115.com/web/lixian/?ct=lixian&ac=user_info"
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(test_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            try:
                data = resp.json()
                if data.get("state") == True:
                    print("✓ Cookie有效")
                    return True
            except:
                pass
        print("❌ Cookie可能已失效")
        return False
    except Exception as e:
        print(f"测试Cookie时出错: {e}")
        return False

def main():
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("错误: 环境变量 COOKIE_115 未设置")
        return
    
    # 测试Cookie是否有效
    print("=== 测试Cookie ===")
    if not test_cookie(cookie):
        print("警告: Cookie可能无效，请重新获取并更新Secret")
    
    source_file = "115.txt"
    target_file = "115share_list.txt"
    
    if not os.path.exists(source_file):
        print(f"错误: {source_file} 不存在")
        return
    
    print("\n=== 开始处理分享链接 ===")
    new_lines = []
    with open(source_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            print(f"\n处理第{line_num}行:")
            parsed = parse_line(line)
            if not parsed:
                continue
            
            title_part, share_url, password = parsed
            cid = get_cid_from_share(share_url, password, cookie)
            
            if not cid:
                print(f"❌ 跳过第{line_num}行: 获取CID失败")
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
        print(f"\n✅ 成功写入 {target_file}，共 {len(new_lines)} 条记录")
        print("\n生成的内容：")
        for line in new_lines:
            print(f"  {line.strip()}")
    else:
        print("\n❌ 没有生成任何有效记录")
        print("\n可能的原因：")
        print("1. 分享链接已失效或密码错误")
        print("2. Cookie已过期（请重新获取）")
        print("3. 需要在浏览器中先访问一次该分享链接")
        print("\n建议：")
        print("1. 先在浏览器中打开分享链接，确认可以正常访问")
        print("2. 重新获取115的Cookie（确保登录状态）")
        print("3. 更新GitHub Secret中的COOKIE_115")

if __name__ == "__main__":
    main()
