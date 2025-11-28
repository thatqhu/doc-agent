import os
import re
from typing import List
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader, TextLoader
from posthog import api_key

class RAGComponents:

    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")

        # 1. 初始化模型
        self.llm = ChatTongyi(
            model="qwen-plus",
            temperature=0,
            dashscope_api_key=api_key
        )
        # 用于JSON输出的模型实例
        self.llm_json = ChatTongyi(
            model="qwen-plus",
            temperature=0,
            dashscope_api_key=self.api_key
        )

        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=self.api_key
        )

        # 2. 初始化工具
        self.search_tool = DuckDuckGoSearchRun()

        # 3. 向量库占位符
        self.vectorstore = None
        self.retriever = None
        self.persist_directory = "./chroma_db"

    def setup_vectorstore(self, urls: List[str] = None):
        if not urls and os.path.exists(self.persist_directory):
            print("加载本地向量数据库...")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="internal_docs"
            )

        elif urls:
            print(f"从 {len(urls)} 个URL构建向量数据库...")
            docs_list = []
            for url in urls:
                try:
                    pdf_loader = DirectoryLoader(url, glob="**/*.pdf", loader_cls=PyMuPDFLoader)
                    # NOTE, need clear the content
                    docs_list.extend(pdf_loader.load())
                except Exception as e:
                    print(f"加载失败 {url}: {e}")

            if not docs_list:
                 # 如果是初始化调用但没加载到文档，不要报错，只是不创建库
                 print("未加载到任何文档，跳过构建")
                 return None

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", "。", "！", "，", " ", ""])
            doc_splits = text_splitter.split_documents(docs_list)

            self.vectorstore = Chroma.from_documents(
                documents=doc_splits,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                collection_name="internal_docs"
            )

        # 3. 如果 vectorstore 成功创建，初始化 retriever
        if self.vectorstore:
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

        return self.vectorstore

if __name__ == "__main__":
    # 测试组件初始化
    components = RAGComponents()
    components.setup_vectorstore()
