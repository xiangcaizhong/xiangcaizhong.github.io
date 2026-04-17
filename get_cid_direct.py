#!/usr/bin/env python3
"""
直接通过115 API获取分享链接的CID（不依赖p115client）
用法: python get_cid_direct.py <share_code> <password>
输出: CID 或 空（失败）
"""
import os
import sys
import re
import requests
import json
import time

def get_cid(share_code, password, cookie):
    """通过模拟浏览器请求获取CID"""
    session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://115.com/",
        "Origin": "https://115.com",
        "Cookie": cookie,
        "X-Requested-With": "XMLHttpRequest"
    }
    session.headers.update(headers)
    
    # 步骤1: 先访问分享页面，获得必要的 cookie
    share_url = f"https://115.com/s/{share_code}?password={password}"
    try:
        resp = session.get(share_url, timeout=10)
        if "receive_code" in resp.text:
            print("需要验证提取码", file=sys.stderr)
    except Exception as e:
        print(f"访问分享页面失败: {e}", file=sys.stderr)
    
    time.sleep(0.5)
    
    # 步骤2: 调用分享信息接口
    api_url = "https://115.com/share/shareinfo"
    params = {
        "share_code": share_code,
        "receive_code": password
    }
    
    try:
        resp = session.get(api_url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("state") == True:
                # 成功获取分享信息
                share_data = data.get("data", {})
                # 提取 CID
                cid = share_data.get("share_id") or share_data.get("file_id") or share_data.get("pick_code")
                if cid:
                    return str(cid)
                # 如果 data 是列表（多文件分享），取第一个的 fid
                if isinstance(share_data, list) and len(share_data) > 0:
                    cid = share_data[0].get("fid") or share_data[0].get("file_id")
                    if cid:
                        return str(cid)
            else:
                # 可能 state=false 但仍有数据？尝试备用接口
                print(f"shareinfo返回: {data.get('error')}", file=sys.stderr)
        else:
            print(f"API状态码异常: {resp.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"请求shareinfo失败: {e}", file=sys.stderr)
    
    # 备用接口
    api_url2 = "https://webapi.115.com/share/shareinfo"
    try:
        resp = session.get(api_url2, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("state") == True:
                share_data = data.get("data", {})
                cid = share_data.get("share_id") or share_data.get("file_id") or share_data.get("pick_code")
                if cid:
                    return str(cid)
    except Exception as e:
        print(f"备用API失败: {e}", file=sys.stderr)
    
    return None

def main():
    if len(sys.argv) < 3:
        print("用法: python get_cid_direct.py <share_code> <password>", file=sys.stderr)
        sys.exit(1)
    
    share_code = sys.argv[1]
    password = sys.argv[2]
    cookie = os.environ.get("COOKIE_115")
    
    if not cookie:
        print("错误: 未设置 COOKIE_115 环境变量", file=sys.stderr)
        sys.exit(1)
    
    cid = get_cid(share_code, password, cookie)
    if cid:
        print(cid)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
