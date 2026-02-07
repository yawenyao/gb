#!/usr/bin/env python3
"""
验证 Kimi API 是否配置正确、能否在 Cursor 中正常调用
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import KIMI_API_KEY, KIMI_BASE_URL
from utils.kimi_client import KimiClient
from utils.logger import logger


def main():
    print("=" * 60)
    print("Kimi API 配置检查（在 Cursor 中运行本脚本即可验证）")
    print("=" * 60)
    
    if not KIMI_API_KEY or KIMI_API_KEY == "sk-your-kimi-api-key":
        print("错误: 未配置 KIMI_API_KEY，请在 .env 中设置或使用 config 中的默认值")
        sys.exit(1)
    
    print(f"KIMI_BASE_URL: {KIMI_BASE_URL}")
    print(f"KIMI_API_KEY: {KIMI_API_KEY[:12]}...{KIMI_API_KEY[-4:]}")
    print()
    
    client = KimiClient()
    messages = [{"role": "user", "content": "请只回复：Kimi API 连接成功"}]
    
    try:
        reply = client.chat(messages, temperature=0)
        if reply:
            print("Kimi API 连接成功:", reply.strip())
            print()
            print("配置正确，可以在 Cursor 中运行 prepare_base_data.py 或 extract_with_ai.py。")
            return 0
        else:
            print("Kimi API 返回为空，请检查 Key 是否有效、网络是否正常。")
            sys.exit(1)
    except Exception as e:
        logger.exception("Kimi API 调用失败")
        print("错误:", e)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
