#!/usr/bin/env python3
"""
从115.txt读取分享链接，自动获取CID，生成115share_list.txt
"""
import os
import re
import sys
import subprocess
from pathlib import Path

def get_cid(share_code, password):
    """调用 get_cid_direct.py 获取 CID"""
    script_path = Path(__file__).parent / "get_cid_direct.py"
    if not script_path.exists():
        print(f"❌ 找不到 {script_path}")
        return None
    
    result = subprocess.run(
        [sys.executable, str(script_path), share_code, password],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        if result.stderr:
            print(f"   错误: {result.stderr.strip()}")
        return None

def main():
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("❌ 错误: COOKIE_115 未设置")
        return
    
    source_file = "115.txt"
    target_file = "115share_list.txt"
    
    if not os.path.exists(source_file):
        print(f"❌ {source_file} 不存在，跳过")
        return
    
    print("=" * 60)
    print("开始转换115.txt -> 115share_list.txt")
    print("=" * 60)
    
    new_lines = []
    success = 0
    failed = 0
    
    with open(source_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # 解析：标题    链接
            parts = re.split(r'\s+', line, maxsplit=1)
            if len(parts) != 2:
                print(f"⚠️ 第{line_num}行格式错误，跳过")
                failed += 1
                continue
            
            title, url = parts[0], parts[1]
            
            # 提取分享码
            share_match = re.search(r'/s/([a-zA-Z0-9]+)', url)
            if not share_match:
                print(f"⚠️ 第{line_num}行无法提取分享码")
                failed += 1
                continue
            share_code = share_match.group(1)
            
            # 提取密码
            pwd_match = re.search(r'password=([^&]+)', url)
            if not pwd_match:
                print(f"⚠️ 第{line_num}行无法提取密码")
                failed += 1
                continue
            password = pwd_match.group(1)
            
            print(f"\n📁 [{line_num}] {title}")
            print(f"   🔗 分享码: {share_code}")
            print(f"   🔑 密码: {password}")
            print(f"   ⏳ 获取CID...")
            
            cid = get_cid(share_code, password)
            
            if cid:
                new_lines.append(f"{title} {share_code} {cid} {password}\n")
                print(f"   ✅ CID: {cid}")
                success += 1
            else:
                print(f"   ❌ 获取CID失败")
                failed += 1
    
    if new_lines:
        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"\n✅ 生成完成: {success} 成功, {failed} 失败")
        print(f"📄 已写入 {target_file}")
    else:
        print("\n❌ 没有生成任何记录")

if __name__ == "__main__":
    main()
