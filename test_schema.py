"""
测试脚本: 查看 Neo4j Graph Schema 的实际内容
"""
from langchain_neo4j import Neo4jGraph
from src.conf import config

# 连接到 Neo4j
graph = Neo4jGraph(
    url=config.NEO4J_CONFIG["url"],
    username=config.NEO4J_CONFIG["user"],
    password=config.NEO4J_CONFIG["password"],
)

# 打印 schema 信息
print("="*80)
print("📊 Neo4j Graph Schema 信息")
print("="*80)
print("\n类型:", type(graph.schema))
print("\n完整内容:")
print(graph.schema)
print("\n" + "="*80)
