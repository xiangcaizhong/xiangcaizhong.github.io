#!/usr/bin/env python3
"""
从115.txt读取分享链接，自动获取CID，生成115share_list.txt
"""
import os
import re
import sys
import subprocess
from pathlib import Path

def get_cid(share_code: str, password: str) -> str:
    """调用 check_115_share.py 获取 CID"""
    script_path = Path(__file__).parent / ".github" / "scripts" / "check_115_share.py"
    
    if not script_path.exists():
        print(f"❌ 找不到脚本: {script_path}")
        return None
    
    # 调用脚本的 getcid 模式
    result = subprocess.run(
        [sys.executable, str(script_path), "getcid", share_code, password],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        cid = result.stdout.strip()
        if cid and len(cid) > 5:  # CID 应该是一个长数字
            return cid
    
    if result.stderr:
        print(f"  错误信息: {result.stderr[:200]}")
    return None

def main():
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("❌ 错误: COOKIE_115 未设置")
        return
    
    source_file = "115.txt"
    target_file = "115share_list.txt"
    
    # 检查源文件
    if not os.path.exists(source_file):
        print(f"❌ 错误: {source_file} 不存在")
        # 创建示例文件
        with open(source_file, "w", encoding="utf-8") as f:
            f.write("# 格式：序号、目录    分享链接\n")
            f.write("# 示例：\n")
            f.write("3、学习机计划/电视剧    https://115cdn.com/s/swf94vk3nqq?password=l224\n")
        print(f"✅ 已创建示例文件 {source_file}")
        print("请编辑后重新运行")
        return
    
    print("=" * 60)
    print("🤖 115分享链接自动转换工具")
    print("=" * 60)
    
    # 读取并处理每一行
    new_lines = []
    success_count = 0
    fail_count = 0
    
    with open(source_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            
            # 解析行：标题 和 URL
            parts = re.split(r'\s+', line, maxsplit=1)
            if len(parts) != 2:
                print(f"⚠️ 第{line_num}行格式错误，跳过: {line[:50]}...")
                fail_count += 1
                continue
            
            title, url = parts[0], parts[1]
            
            # 提取分享码
            share_match = re.search(r'/s/([a-zA-Z0-9]+)', url)
            if not share_match:
                print(f"⚠️ 第{line_num}行无法提取分享码，跳过")
                fail_count += 1
                continue
            share_code = share_match.group(1)
            
            # 提取密码
            pwd_match = re.search(r'password=([^&]+)', url)
            if not pwd_match:
                print(f"⚠️ 第{line_num}行无法提取密码，跳过")
                fail_count += 1
                continue
            password = pwd_match.group(1)
            
            print(f"\n📁 [{line_num}] {title}")
            print(f"   🔗 分享码: {share_code}")
            print(f"   🔑 密码: {password}")
            print(f"   ⏳ 正在获取CID...")
            
            # 获取CID
            cid = get_cid(share_code, password)
            
            if cid:
                new_line = f"{title} {share_code} {cid} {password}\n"
                new_lines.append(new_line)
                print(f"   ✅ 成功！CID: {cid}")
                success_count += 1
            else:
                print(f"   ❌ 获取CID失败")
                fail_count += 1
    
    # 写入结果
    if new_lines:
        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        print("\n" + "=" * 60)
        print("✅ 处理完成！")
        print(f"   📊 成功: {success_count} 条")
        print(f"   📊 失败: {fail_count} 条")
        print(f"   📄 已生成: {target_file}")
        print("\n生成的内容预览:")
        for line in new_lines[:3]:
            print(f"   {line.strip()}")
    else:
        print("\n❌ 没有生成任何记录")
        print("\n可能的原因:")
        print("   1. 115.txt 中没有有效的分享链接")
        print("   2. 分享链接已失效或密码错误")
        print("   3. Cookie 可能已过期")
        print("\n建议:")
        print("   1. 在浏览器中测试分享链接是否能正常访问")
        print("   2. 重新获取 Cookie 并更新 GitHub Secret")
        print("   3. 检查 115.txt 格式是否正确")

if __name__ == "__main__":
    main()
