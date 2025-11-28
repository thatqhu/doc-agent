from typing import List, Annotated
from typing_extensions import TypedDict
import operator

class GraphState(TypedDict):
    """
    图状态定义

    Attributes:
        question: 用户问题
        generation: LLM生成的答案
        web_search: 是否需要搜索的标志 ('Yes'/'No')
        max_retries: 最大重试次数
        loop_step: 当前循环次数
        documents: 检索到的文档列表
    """
    question: str
    generation: str
    web_search: str
    max_retries: int
    loop_step: Annotated[int, operator.add]
    documents: List[str]
