#!/usr/bin/env python3
"""
从115分享链接获取CID（文件夹ID）
复用 check_115_share.py 中的方法
"""
import os
import sys
from p115client import P115Client

def get_cid_from_share(share_code: str, receive_code: str, cookie: str) -> str:
    """
    获取分享链接的CID
    返回 CID 字符串，失败返回 None
    """
    try:
        # 初始化客户端
        client = P115Client(cookie, app="web")
        
        # 步骤1: 获取分享信息
        share_info = client.share_get_info(share_code)
        if not share_info.get("state"):
            print(f"分享信息获取失败: {share_info}", file=sys.stderr)
            return None
        
        # 步骤2: 如果有提取码，需要接收分享
        if share_info.get("is_code"):
            try:
                # 接收分享，这会返回分享的文件信息
                receive_result = client.share_receive(share_code, receive_code)
                if receive_result and "data" in receive_result:
                    # 从返回结果中提取CID
                    data = receive_result["data"]
                    # 尝试多种可能的字段名
                    cid = (data.get("share_id") or 
                          data.get("file_id") or 
                          data.get("pick_code") or
                          data.get("cid"))
                    if cid:
                        return str(cid)
            except Exception as e:
                print(f"接收分享失败: {e}", file=sys.stderr)
                return None
        else:
            # 无需提取码的分享，直接获取
            # 尝试从分享信息中直接获取CID
            data = share_info.get("data", {})
            cid = (data.get("share_id") or 
                  data.get("file_id") or 
                  data.get("pick_code") or
                  data.get("cid"))
            if cid:
                return str(cid)
        
        print("未能从分享信息中提取CID", file=sys.stderr)
        return None
        
    except Exception as e:
        print(f"获取CID失败: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 3:
        print("用法: python get_cid_from_share.py <share_code> <receive_code>", file=sys.stderr)
        print("环境变量 COOKIE_115 必须设置", file=sys.stderr)
        sys.exit(1)
    
    share_code = sys.argv[1]
    receive_code = sys.argv[2]
    cookie = os.environ.get("COOKIE_115")
    
    if not cookie:
        print("错误: 环境变量 COOKIE_115 未设置", file=sys.stderr)
        sys.exit(1)
    
    cid = get_cid_from_share(share_code, receive_code, cookie)
    if cid:
        print(cid)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
