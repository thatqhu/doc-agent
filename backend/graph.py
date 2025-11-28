from langgraph.graph import StateGraph, END
from state import GraphState
from nodes import RAGNodes

def build_rag_graph(components):
    nodes = RAGNodes(components)
    workflow = StateGraph(GraphState)

    workflow.add_node("websearch", nodes.web_search)
    workflow.add_node("retrieve", nodes.retrieve)
    workflow.add_node("grade_documents", nodes.grade_documents)
    workflow.add_node("generate", nodes.generate)

    workflow.set_conditional_entry_point(
        nodes.route_question,
        {"websearch": "websearch", "vectorstore": "retrieve"}
    )

    # 添加边
    workflow.add_edge("websearch", "generate")
    workflow.add_edge("retrieve", "grade_documents")

    # 条件边: 评分后 -> 生成 或 搜索
    workflow.add_conditional_edges(
        "grade_documents",
        nodes.decide_to_generate,
        {"websearch": "websearch", "generate": "generate"}
    )

    # 条件边: 生成后 -> 结束、搜索 或 重试
    workflow.add_conditional_edges(
        "generate",
        nodes.grade_generation,
        {
            "not supported": "generate",  # 幻觉 -> 重生成
            "not useful": "websearch",    # 答非所问 -> 搜网
            "useful": END,                # 通过
            "max retries": END
        }
    )

    return workflow.compile()
