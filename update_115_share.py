#!/usr/bin/env python3
"""
从115.txt读取分享链接，自动获取CID，生成115share_list.txt
"""
import os
import re
import sys
import subprocess
from pathlib import Path

def get_cid_via_script(share_code: str, password: str) -> str:
    """
    调用独立脚本获取CID
    """
    script_path = Path(__file__).parent / ".github" / "scripts" / "get_cid_from_share.py"
    
    if not script_path.exists():
        print(f"错误: 找不到 {script_path}")
        return None
    
    # 调用脚本
    result = subprocess.run(
        [sys.executable, str(script_path), share_code, password],
        capture_output=True,
        text=True,
        env={**os.environ, "COOKIE_115": os.environ.get("COOKIE_115", "")}
    )
    
    if result.returncode == 0:
        cid = result.stdout.strip()
        if cid and cid.isdigit():
            return cid
        # 可能是其他格式的ID
        return cid
    
    # 输出错误信息
    if result.stderr:
        print(f"  错误: {result.stderr.strip()}")
    return None

def parse_line(line: str):
    """
    解析115.txt的每一行
    格式: 序号、目录    https://115cdn.com/s/分享码?password=密码
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    
    # 分割标题和URL（用空白符分割）
    parts = re.split(r'\s+', line, maxsplit=1)
    if len(parts) != 2:
        print(f"格式错误（需要标题和URL）: {line}")
        return None
    
    title_part, url = parts[0], parts[1]
    
    # 提取分享码
    share_match = re.search(r'/s/([a-zA-Z0-9]+)', url)
    if not share_match:
        print(f"无法提取分享码: {url}")
        return None
    share_code = share_match.group(1)
    
    # 提取密码
    pwd_match = re.search(r'password=([^&]+)', url)
    if not pwd_match:
        print(f"无法提取密码: {url}")
        return None
    password = pwd_match.group(1)
    
    return title_part, share_code, password

def main():
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("❌ 错误: 环境变量 COOKIE_115 未设置")
        print("请在 GitHub Secrets 中设置 COOKIE_115")
        return
    
    source_file = "115.txt"
    target_file = "115share_list.txt"
    
    if not os.path.exists(source_file):
        print(f"❌ 错误: {source_file} 不存在")
        # 创建示例文件
        with open(source_file, "w", encoding="utf-8") as f:
            f.write("# 格式：序号、目录    分享链接\n")
            f.write("# 示例：\n")
            f.write("3、学习机计划/电视剧    https://115cdn.com/s/swf94vk3nqq?password=l224\n")
        print(f"✅ 已创建示例 {source_file}，请编辑后重新运行")
        return
    
    print("=" * 60)
    print("开始处理分享链接")
    print("=" * 60)
    print(f"Cookie 状态: {'已设置' if cookie else '未设置'}")
    print()
    
    new_lines = []
    failed_lines = []
    
    with open(source_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            parsed = parse_line(line)
            if not parsed:
                continue
            
            title_part, share_code, password = parsed
            print(f"[{line_num}] {title_part}")
            print(f"    分享码: {share_code}")
            print(f"    密码: {password}")
            
            # 获取CID
            print(f"    正在获取CID...")
            cid = get_cid_via_script(share_code, password)
            
            if cid:
                new_line = f"{title_part} {share_code} {cid} {password}\n"
                new_lines.append(new_line)
                print(f"    ✅ CID: {cid}")
            else:
                failed_lines.append((line_num, title_part))
                print(f"    ❌ 获取CID失败")
            print()
    
    # 写入结果
    if new_lines:
        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        print("=" * 60)
        print(f"✅ 成功生成 {target_file}")
        print(f"   成功: {len(new_lines)} 条")
        print(f"   失败: {len(failed_lines)} 条")
        
        if new_lines:
            print("\n生成的内容预览:")
            for line in new_lines[:5]:
                print(f"  {line.strip()}")
        
        if failed_lines:
            print(f"\n失败的行:")
            for line_num, title in failed_lines:
                print(f"  第{line_num}行: {title}")
    else:
        print("=" * 60)
        print("❌ 没有生成任何记录")
        print("\n可能的原因:")
        print("1. 115.txt 中没有有效的分享链接")
        print("2. 分享链接已失效或密码错误")
        print("3. Cookie 可能已过期")
        print("\n建议:")
        print("1. 检查 115.txt 格式是否正确")
        print("2. 在浏览器中测试分享链接是否能正常访问")
        print("3. 重新获取 Cookie 并更新 GitHub Secret")

if __name__ == "__main__":
    main()
