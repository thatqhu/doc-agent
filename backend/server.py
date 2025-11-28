from contextlib import asynccontextmanager
import os
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

# 导入我们的项目模块
from config import setup_environment
from components import RAGComponents
from graph import build_rag_graph

class InitRequest(BaseModel):
    urls: Optional[List[str]] = None
    force_rebuild: bool = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_graph, components
    print("初始化系统组件...")

    try:
        setup_environment()
    except Exception as e:
        print(f"环境变量配置警告: {e}")

    components = RAGComponents()

    # 3. 尝试加载已有向量库
    try:
        components.setup_vectorstore()
        print("[Startup] 向量数据库加载成功")
    except Exception as e:
        print(f"[Startup] 向量库未就绪 (需调用 /init 初始化): {e}")

    # 4. 构建工作流图
    rag_graph = build_rag_graph(components)
    print("[Startup] RAG 工作流构建完成")
    yield
    print("[Shutdown] 清理资源...")

app = FastAPI(lifespan=lifespan, title="Adaptive RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_graph = None
components = None

# --- API 路由 ---

@app.get("/chat/stream")
async def chat_stream_endpoint(message: str):
    """
    SSE 流式对话接口
    实时返回 RAG 工作流的每一步状态
    """
    if not rag_graph:
        raise HTTPException(status_code=503, detail="系统未初始化")

    async def event_generator():
        inputs = {
            "question": message,
            "max_retries": 3,
            "loop_step": 0
        }

        print(f"[Stream] 开始处理: {message}")

        try:
            async for event in rag_graph.astream(inputs, stream_mode="values"):

                # event 是当前的 GraphState 字典
                current_step = "unknown"
                content = ""

                # 根据 state 变化判断当前步骤 (简单的启发式判断)
                if "generation" in event and event["generation"]:
                    current_step = "final_answer"
                    content = event["generation"].content
                elif "documents" in event and len(event["documents"]) > 0:
                    # 区分是检索出的还是搜索出的略复杂，这里简化
                    current_step = "retrieved_docs"
                    content = f"获取到 {len(event['documents'])} 份文档"
                elif "web_search" in event and event["web_search"] == "Yes":
                     current_step = "decision"
                     content = "决定进行网络搜索"
                else:
                    current_step = "processing"
                    content = "正在处理..."

                # 构造发送给前端的数据包
                payload = {
                    "step": current_step,
                    "content": content,
                    # 可以把整个 state 发过去，但通常太大了，建议按需提取
                    # "full_state": str(event)
                }

                # SSE 格式: data: <json_string>\n\n
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

                # 稍微让出控制权，避免密集计算阻塞
                await asyncio.sleep(0.01)

            # 发送结束标记
            yield "data: [DONE]\n\n"

        except Exception as e:
            print(f"[Stream Error] {e}")
            error_payload = {"error": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- 启动入口 ---
if __name__ == "__main__":
    # 运行服务: python server.py
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
