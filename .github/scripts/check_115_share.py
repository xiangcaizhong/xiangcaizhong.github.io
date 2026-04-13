#!/usr/bin/env python3
"""
检查115分享链接有效性，并清理失效链接
"""
import os
import re
import sys
from pathlib import Path
from p115client import P115Client
from p115client.exception import P115Warning, AuthenticationError, BusyError, DataError

# 分享列表文件路径（相对于仓库根目录）
SHARE_FILE = "115share_list.txt"

# 失效状态码（经验值，可能变化）
INVALID_SHARE_CODES = {20004, 20008, 20010, 20011, 20012, 20013, 20014, 20015, 20016}


def validate_share(client: P115Client, share_code: str, receive_code: str, cid: str = "") -> bool:
    """
    检查单个分享是否有效
    - share_code: 分享码
    - receive_code: 提取码
    - cid: 可选目录ID
    返回 True 表示有效，False 表示失效
    """
    try:
        # 尝试获取分享信息
        resp = client.share_get_info(share_code)
        if not resp.get("state"):
            return False

        # 进一步检查是否需要提取码以及提取码是否正确
        if resp.get("is_code"):
            # 需要提取码，验证提取码是否正确
            try:
                client.share_receive(share_code, receive_code, cid=cid or None)
            except (DataError, BusyError, AuthenticationError) as e:
                code = getattr(e, 'code', 0)
                if code in INVALID_SHARE_CODES:
                    return False
                # 其他错误（如网络问题）暂时放过，当作有效
                return True
        return True
    except (P115Warning, DataError) as e:
        code = getattr(e, 'code', 0)
        if code in INVALID_SHARE_CODES:
            return False
        # 无法确定时先当作有效
        print(f"  ⚠️ 检查异常（code={code}），暂时保留")
        return True
    except Exception as e:
        print(f"  ❌ 未预期错误: {e}")
        return False


def main():
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        print("❌ 错误：未设置 COOKIE_115 环境变量")
        sys.exit(1)

    client = P115Client(cookie, app="web")
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    share_path = repo_root / SHARE_FILE

    if not share_path.exists():
        print(f"❌ 文件 {SHARE_FILE} 不存在")
        sys.exit(1)

    with open(share_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    valid_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            valid_lines.append(line)
            continue

        parts = line.split()
        if len(parts) < 3:
            print(f"⚠️ 跳过格式错误行: {line}")
            valid_lines.append(line)
            continue

        name = parts[0]
        share_code = parts[1]
        cid = parts[2] if len(parts) > 2 else ""
        password = parts[3] if len(parts) > 3 else ""

        print(f"检查: {name} ({share_code}) ... ", end="")
        if validate_share(client, share_code, password, cid):
            print("✅ 有效")
            valid_lines.append(line)
        else:
            print("❌ 失效，已移除")

    # 写回文件
    with open(share_path, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines) + "\n")

    print(f"\n清理完成，保留 {len(valid_lines)} 条有效分享。")


if __name__ == "__main__":
    main()
