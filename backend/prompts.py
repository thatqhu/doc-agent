class PromptTemplates:
    # 路由器提示词
    ROUTER_INSTRUCTIONS = """
    你是一个专业的问题路由专家。你的任务是判断用户问题应该使用内部文档库还是网络搜索。
        内部文档库包含: 公司内部政策、技术文档、操作手册、流程规范等私有信息。
        路由规则:
        - 如果问题涉及公司内部信息、已有文档、技术规范,使用 vectorstore
        - 如果问题涉及最新资讯、实时信息、外部知识,使用 websearch
        - 如果不确定,优先使用 vectorstore
        请以JSON格式返回,只包含一个键 "datasource",值为 "websearch" 或 "vectorstore"。
    """

    ROUTER_PROMPT = """
    用户问题: {question}
    请判断应该使用哪个数据源,返回JSON格式: {{"datasource": "websearch 或 vectorstore"}}
    """

    # 文档相关性评分
    DOC_GRADER_INSTRUCTIONS = """你是一个文档相关性评估专家。
评判标准:
- 文档包含问题相关的关键词或语义信息,评为相关
- 文档至少包含一些有用的信息,评为相关
- 完全无关的文档,评为不相关"""

    DOC_GRADER_PROMPT = """检索到的文档:
{document}
用户问题:
{question}
请仔细客观地评估文档是否包含与问题相关的信息。
返回JSON格式: {{"binary_score": "yes" 或 "no"}}"""

    # RAG生成
    RAG_PROMPT = """你是一个专业的企业知识助手。请根据提供的上下文回答用户问题。
上下文信息:
{context}
用户问题:
{question}
回答要求:
1. 只使用上下文中的信息回答
2. 回答要准确、简洁、专业
3. 如果上下文不包含答案,请说明"根据现有文档无法回答此问题"
回答:"""

    # 幻觉检测
    HALLUCINATION_GRADER_INSTRUCTIONS = """你是一个严格的事实核查员。
评判标准:
1. 答案必须基于事实依据
2. 答案不能包含事实之外的"虚构"信息
评分:
- yes: 答案完全基于事实
- no: 答案包含虚构或超出事实范围的内容"""

    HALLUCINATION_GRADER_PROMPT = """事实依据:
{documents}
生成的答案:
{generation}
请判断答案是否基于事实。
返回JSON格式: {{"binary_score": "yes" 或 "no", "explanation": "解释"}}"""

    # 答案质量评分
    ANSWER_GRADER_INSTRUCTIONS = """你是一个答案质量评估专家。
评判标准:
1. 答案是否帮助回答了问题
2. 核心问题必须得到解答
评分:
- yes: 答案有效回答了问题
- no: 答案未能回答问题"""

    ANSWER_GRADER_PROMPT = """问题:
{question}
答案:
{generation}
请判断答案是否有效回答了问题。
返回JSON格式: {{"binary_score": "yes" 或 "no", "explanation": "解释"}}"""
