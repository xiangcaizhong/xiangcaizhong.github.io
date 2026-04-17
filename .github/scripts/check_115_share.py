# ========== 新增：获取 CID 功能 ==========
def get_cid_only(share_code: str, receive_code: str) -> str:
    """只获取 CID，不检查有效性"""
    cookie = os.environ.get("COOKIE_115")
    if not cookie:
        return None
    
    client = P115Client(cookie, app="web")
    
    try:
        # 获取分享信息
        resp = client.share_get_info(share_code)
        if not resp.get("state"):
            return None
        
        # 如果需要提取码
        if resp.get("is_code"):
            result = client.share_receive(share_code, receive_code)
            if result and "data" in result:
                data = result["data"]
                # 提取 CID
                if isinstance(data, dict):
                    return str(data.get("share_id") or data.get("file_id") or data.get("pick_code") or "")
                elif isinstance(data, list) and len(data) > 0:
                    return str(data[0].get("share_id") or data[0].get("file_id") or "")
        else:
            # 无需提取码
            data = resp.get("data", {})
            return str(data.get("share_id") or data.get("file_id") or data.get("pick_code") or "")
        
        return None
    except Exception as e:
        print(f"获取CID错误: {e}", file=sys.stderr)
        return None


# 命令行入口
if __name__ == "__main__":
    import sys
    
    # 如果第一个参数是 'getcid'，则只获取 CID
    if len(sys.argv) > 1 and sys.argv[1] == "getcid":
        if len(sys.argv) < 4:
            print("用法: python check_115_share.py getcid <share_code> <receive_code>")
            sys.exit(1)
        share_code = sys.argv[2]
        receive_code = sys.argv[3]
        cid = get_cid_only(share_code, receive_code)
        if cid:
            print(cid)
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # 原有的检查功能
        main()
