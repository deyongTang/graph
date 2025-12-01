import re
from typing import Dict, List, Any

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jGraph, Neo4jVector
from neo4j_graphrag.types import SearchType

from src.conf import config


class ChatService:
    def __init__(self):
        # Initialize LLM (Ali Bailian)

        self.llm = ChatTongyi(
            model="qwen-turbo",  # Balanced speed and performance
            api_key=config.BAILIAN_API_KEY,
        )

        # Initialize Neo4j connections
        self.graph = Neo4jGraph(
            url=config.NEO4J_CONFIG["url"],
            username=config.NEO4J_CONFIG["user"],
            password=config.NEO4J_CONFIG["password"],
        )

        # Embeddings + Vector store for hybrid retrieval
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            encode_kwargs={"normalize_embeddings": True}
        )

        self.vector_stores = {
            "SPU": Neo4jVector.from_existing_index(
                url=config.NEO4J_CONFIG["url"],
                username=config.NEO4J_CONFIG["user"],
                password=config.NEO4J_CONFIG["password"],
                embedding=self.embeddings,
                index_name="spu_embedding_index",
                keyword_index_name="spu_full_text_index",
                search_type=SearchType.HYBRID,
            ),
            "BaseTrademark": Neo4jVector.from_existing_index(
                url=config.NEO4J_CONFIG["url"],
                username=config.NEO4J_CONFIG["user"],
                password=config.NEO4J_CONFIG["password"],
                embedding=self.embeddings,
                index_name="trademark_embedding_index",
                keyword_index_name="trademark_full_text_index",
                search_type=SearchType.HYBRID,
            ),
            "Category3": Neo4jVector.from_existing_index(
                url=config.NEO4J_CONFIG["url"],
                username=config.NEO4J_CONFIG["user"],
                password=config.NEO4J_CONFIG["password"],
                embedding=self.embeddings,
                index_name="category3_embedding_index",
                keyword_index_name="category3_full_text_index",
                search_type=SearchType.HYBRID,
            ),
            "Category2": Neo4jVector.from_existing_index(
                url=config.NEO4J_CONFIG["url"],
                username=config.NEO4J_CONFIG["user"],
                password=config.NEO4J_CONFIG["password"],
                embedding=self.embeddings,
                index_name="category2_embedding_index",
                keyword_index_name="category2_full_text_index",
                search_type=SearchType.HYBRID,
            ),
            "Category1": Neo4jVector.from_existing_index(
                url=config.NEO4J_CONFIG["url"],
                username=config.NEO4J_CONFIG["user"],
                password=config.NEO4J_CONFIG["password"],
                embedding=self.embeddings,
                index_name="category1_embedding_index",
                keyword_index_name="category1_full_text_index",
                search_type=SearchType.HYBRID,
            ),
        }

        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()
        self._cypher_param_regex = re.compile(r"param_\d+")

    def _generate_cypher(self, question: str, schema_info: str):
        """
        使用 LLM 生成参数化的 Neo4j Cypher 查询语句
        
        主要逻辑:
        1. 构造 Prompt 模板,包含用户问题和知识图谱 schema 信息
        2. 调用 LLM (qwen-flash) 生成 Cypher 查询和需要对齐的实体列表
        3. 解析 LLM 返回的 JSON 结果
        
        Prompt 模板结构:
        ┌─────────────────────────────────────────────────────────┐
        │ 角色定位: 专业的 Neo4j Cypher 查询生成器                │
        ├─────────────────────────────────────────────────────────┤
        │ 输入信息:                                                │
        │   - 用户问题: {question}                                │
        │   - 知识图谱结构: {schema_info}                         │
        ├─────────────────────────────────────────────────────────┤
        │ 输出要求:                                                │
        │   1. 生成参数化 Cypher (使用 param_0, param_1...)       │
        │   2. 识别需要实体对齐的参数                             │
        │   3. 返回 JSON 格式结果                                 │
        └─────────────────────────────────────────────────────────┘
        
        期望的 LLM 返回格式:
        {
            "cypher_query": "MATCH (n:Label {property: $param_0}) RETURN n",
            "entities_to_align": [
                {
                    "param_name": "param_0",      # 参数名称
                    "entity": "用户输入的实体名",   # 原始实体文本
                    "label": "NodeLabel"          # Neo4j 节点标签
                }
            ]
        }
        
        注意事项:
        - Cypher 中应使用 $param_0 格式(带 $ 符号),但由于 Prompt 不够明确,
          LLM 有时会生成 param_0 (不带 $),导致偶现的语法错误
        - 这是典型的大模型能力不足 + Prompt 歧义导致的不稳定性问题
        
        Args:
            question: 用户的自然语言问题
            schema_info: Neo4j 知识图谱的 schema 信息 (节点、关系、属性等)
            
        Returns:
            dict: 包含 cypher_query 和 entities_to_align 的字典
        """
        generate_cypher_prompt = PromptTemplate(
            input_variables=["question", "schema_info"],
            template="""
                你是一个专业的Neo4j Cypher查询生成器。你的任务是根据用户问题生成一条Cypher查询语句，用于从知识图谱中获取回答用户问题所需的信息。

                用户问题：{question}

                知识图谱结构信息：{schema_info}

                要求：
                1. 生成参数化Cypher查询语句，用param_0, param_1等代替具体值
                2. 识别需要对齐的实体
                3. 必须严格使用以下JSON格式输出结果
                {{
                  "cypher_query": "生成的Cypher语句",
                  "entities_to_align": [
                    {{
                      "param_name": "param_0",
                      "entity": "原始实体名称",
                      "label": "节点类型"
                    }}
                  ]
                }}"""
        ).format(schema_info=schema_info, question=question)
        cypher = self.llm.invoke(generate_cypher_prompt)
        cypher = self.json_parser.invoke(cypher)
        return cypher

    def _entity_align(self, entities_to_align: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """使用向量+关键词检索修正实体名称"""
        for node in entities_to_align:
            if node['label'] in self.vector_stores:
                results = self.vector_stores[node['label']].similarity_search(node['entity'], k=1)
                if results:
                    node['entity'] = results[0].page_content
        return entities_to_align

    def _execute_cypher(self, cypher: str, prams: Dict[str, str]) -> List[Dict[str, Any]]:
        """执行 Cypher 查询并返回结果"""
        results = self.graph.query(cypher, params=prams)
        return results

    def _generate_final_answer(self, question: str, query_result: List[Dict[str, Any]]) -> str:
        """
        将 Cypher 查询结果生成自然语言答案
        """
        prompt = PromptTemplate(
            input_variables=["question", "query_result"],
            template="""
                你是一个电商智能客服，根据用户问题，以及数据库查询结果生成一段简洁、准确的自然语言回答。
                用户问题: {question}
                数据库返回结果: {query_result}
            """).format(question=question, query_result=query_result)
        result = self.llm.invoke(prompt)
        return self.str_parser.invoke(result)

    async def chat(self, question: str):
        from src.web.monitor import emit_event
        
        await emit_event("workflow_start", {"question": question})
        
        print("\n" + "=" * 80)
        print("🔍 开始处理问题:", question)
        print("=" * 80)

        # Step 1: 生成 Cypher
        await emit_event("step_start", {"step": "generate_cypher", "description": "Generating Cypher Query"})
        print("\n📝 Step 1: 调用 LLM 生成 Cypher...")
        print("graph.schema----------------------------:\n", self.graph.schema)
        
        cypher = self._generate_cypher(question, self.graph.schema)
        print("LLM 返回的完整结果:")
        print(cypher)

        cypher_query = cypher["cypher_query"]
        entities_to_align = cypher["entities_to_align"]
        
        await emit_event("step_end", {
            "step": "generate_cypher", 
            "output": {
                "cypher_query": cypher_query,
                "entities_to_align": entities_to_align
            }
        })

        print("\n📊 提取的信息:")
        print(f"  - Cypher 查询: {cypher_query}")
        print(f"  - 需要对齐的实体数量: {len(entities_to_align)}")
        print(f"  - 实体列表: {entities_to_align}")

        # Step 2: 实体对齐
        await emit_event("step_start", {"step": "entity_align", "description": "Aligning Entities"})
        print("\n🔄 Step 2: 实体对齐...")
        entities = self._entity_align(entities_to_align)
        print(f"对齐后的实体: {entities}")
        await emit_event("step_end", {"step": "entity_align", "output": {"entities": entities}})

        # Step 3: 构建参数
        await emit_event("step_start", {"step": "build_params", "description": "Building Parameters"})
        print("\n🔧 Step 3: 构建查询参数...")
        params = self._build_params(cypher_query, entities, question)
        print(f"最终参数字典: {params}")
        await emit_event("step_end", {"step": "build_params", "output": {"params": params}})

        # Step 4: 执行查询
        await emit_event("step_start", {"step": "execute_cypher", "description": "Executing Cypher Query"})
        print("\n⚡ Step 4: 执行 Cypher 查询...")
        print(f"执行的 Cypher: {cypher_query}")
        print(f"使‘用的参数: {params}")

        query_result = self._execute_cypher(cypher_query, params)

        print(f"\n✅ 查询结果: {query_result}")
        print("=" * 80 + "\n")
        await emit_event("step_end", {"step": "execute_cypher", "output": {"result": query_result}})
        
        # Step 5: 生成回答
        await emit_event("step_start", {"step": "generate_answer", "description": "Generating Final Answer"})
        answer = self._generate_final_answer(question, query_result)
        await emit_event("step_end", {"step": "generate_answer", "output": {"answer": answer}})
        
        await emit_event("workflow_end", {"answer": answer})

        return answer

    def _build_params(self, cypher_query: str, entities: List[Dict[str, str]], question: str) -> Dict[str, str]:
        """Build parameter dict and fill missing params with the raw question text."""
        params = {entity["param_name"]: entity["entity"] for entity in entities}
        ## set 集合
        required = set(self._cypher_param_regex.findall(cypher_query))
        missing = sorted(required - params.keys())
        for name in missing:
            # Fallback: use the user question when the model doesn't provide a value.
            params[name] = question
        return params
