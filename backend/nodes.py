import json
import re
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from prompts import PromptTemplates

class RAGNodes:
    def __init__(self, components):
        self.c = components
        self.p = PromptTemplates

    def _parse_json(self, content):
        """JSON解析辅助函数"""
        content = content.content.strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match: content = match.group()
        try:
            return json.loads(content)
        except:
            return {}

    # --- 节点函数 ---
    async def retrieve(self, state):
        print("检索文档...")
        return {"documents": await self.c.retriever.ainvoke(state["question"])}

    async def generate(self, state):
        print("生成答案...")
        docs_txt = "\n\n".join([d.page_content for d in state["documents"]])
        prompt = self.p.RAG_PROMPT.format(context=docs_txt, question=state["question"])
        return {"generation": await self.c.llm.ainvoke([HumanMessage(content=prompt)]), "loop_step": state.get("loop_step", 0) + 1}

    async def grade_documents(self, state):
        print("评分文档...")
        filtered = []
        web_search = "No"
        for doc in state["documents"]:
            prompt = self.p.DOC_GRADER_PROMPT.format(document=doc.page_content[:500], question=state["question"])
            res = await self.c.llm_json.ainvoke([SystemMessage(content=self.p.DOC_GRADER_INSTRUCTIONS), HumanMessage(content=prompt)])
            if self._parse_json(res).get("binary_score", "no").lower() == "yes":
                filtered.append(doc)
            else:
                web_search = "Yes"
        return {"documents": filtered, "web_search": web_search}

    async def web_search(self, state):
        print("网络搜索...")
        res = await self.c.search_tool.ainvoke(state["question"])
        return {"documents": state.get("documents", []) + [Document(page_content=res)]}

    # --- 路由与决策函数 ---
    async def route_question(self, state):
        prompt = self.p.ROUTER_PROMPT.format(question=state["question"])
        res = await self.c.llm_json.ainvoke([SystemMessage(content=self.p.ROUTER_INSTRUCTIONS), HumanMessage(content=prompt)])
        source = self._parse_json(res).get("datasource", "vectorstore")
        print(f"路由方向: {source}")
        return source

    def decide_to_generate(self, state):
        return "websearch" if state["web_search"] == "Yes" else "generate"

    async def grade_generation(self, state):
        print("质量检查...")
        max_retries = state.get("max_retries", 3)
        if state["loop_step"] > max_retries: return "max retries"

        # 1. 幻觉检测
        docs_txt = "\n".join([d.page_content for d in state["documents"]])
        hal_prompt = self.p.HALLUCINATION_GRADER_PROMPT.format(documents=docs_txt[:2000], generation=state["generation"].content)
        hal_res = self._parse_json(await self.c.llm_json.ainvoke([SystemMessage(content=self.p.HALLUCINATION_GRADER_INSTRUCTIONS), HumanMessage(content=hal_prompt)]))

        if hal_res.get("binary_score") == "yes":
            # 2. 答案相关性检测
            ans_prompt = self.p.ANSWER_GRADER_PROMPT.format(question=state["question"], generation=state["generation"].content)
            ans_res = self._parse_json(await self.c.llm_json.ainvoke([SystemMessage(content=self.p.ANSWER_GRADER_INSTRUCTIONS), HumanMessage(content=ans_prompt)]))
            return "useful" if ans_res.get("binary_score") == "yes" else "not useful"
        return "not supported"
