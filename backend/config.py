import os
import getpass

def setup_environment():
    """配置必要的API密钥"""
    if not os.environ.get("DASHSCOPE_API_KEY"):
        api_key = getpass.getpass("请输入阿里云 DashScope API密钥: ")
        os.environ["DASHSCOPE_API_KEY"] = api_key

    print("环境配置完成")
