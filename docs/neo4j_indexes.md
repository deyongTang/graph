# Neo4j 索引技术文档

本文档基于 `src/web/utils.py` 中的代码实现，介绍 Neo4j 中两种重要的索引类型：**全文索引 (Fulltext Index)** 和 **向量索引 (Vector Index)**。

## 1. 索引概述

在 Neo4j 图数据库中，索引用于提高查询性能。通过索引，数据库可以快速定位到满足特定条件的节点或关系，而无需遍历整个图。

在本项目中，我们主要使用了以下两种高级索引：

*   **全文索引 (Fulltext Index)**: 用于基于文本内容的关键词搜索（如模糊匹配、包含查询）。
*   **向量索引 (Vector Index)**: 用于基于语义的相似度搜索（如 RAG 系统中的召回）。

---

## 2. 全文索引 (Fulltext Index)

全文索引基于 Apache Lucene，允许我们在节点或关系的字符串属性上运行强大的文本搜索查询。

### 2.1 代码实现

在 `src/web/utils.py` 中，`create_full_text_index` 函数用于创建全文索引：

```python
def create_full_text_index(graph, index, label, property):
    cypher = f"""
    CREATE FULLTEXT INDEX {index}
    FOR (n:{label})
    ON EACH [n.{property}]
    """
    graph.query(cypher, {'index': index, 'label': label, 'property': property})
```

### 2.2 关键点解析

*   **`CREATE FULLTEXT INDEX {index}`**: 声明创建一个名为 `{index}` 的全文索引。
*   **`FOR (n:{label})`**: 指定索引应用于带有 `{label}` 标签的节点。
*   **`ON EACH [n.{property}]`**: 指定索引建立在节点的 `{property}` 属性上。

### 2.3 应用场景

项目中为以下实体创建了全文索引，主要用于通过名称快速查找商品或分类：

*   **SPU (Standard Product Unit)**: `spu_full_text_index`
*   **品牌 (BaseTrademark)**: `trademark_full_text_index`
*   **三级分类 (Category3)**: `category3_full_text_index`
*   **二级分类 (Category2)**: `category2_full_text_index`
*   **一级分类 (Category1)**: `category1_full_text_index`

---

## 3. 向量索引 (Vector Index)

向量索引是 Neo4j 5.x 引入的重要功能，它支持对高维向量进行索引，从而实现基于向量相似度（如余弦相似度、欧几里得距离）的快速查询。这是构建大模型应用（如 RAG）的核心组件。

### 3.1 代码实现

在 `src/web/utils.py` 中，`create_embedding_index` 函数展示了完整的向量索引构建流程：

1.  **获取文本数据**: 查询目标节点的文本属性。
2.  **生成 Embedding**: 使用 Embedding 模型将文本转换为向量。
3.  **存储向量**: 将生成的向量存储回节点的属性中。
4.  **创建索引**: 在向量属性上创建向量索引。

```python
# 3. 创建向量索引的关键 Cypher 语句
cypher_index = f"""
CREATE VECTOR INDEX {index}
FOR (n:{label})
ON n.{embedding_property}
OPTIONS {{indexConfig:{{
    `vector.dimensions`: {embedding_dim},
    `vector.similarity_function`: 'cosine'
    }}
}}
"""
```

### 3.2 关键点解析

*   **Embedding 模型**: 代码使用了 `langchain_huggingface.HuggingFaceEmbeddings` 加载 `BAAI/bge-small-zh-v1.5` 模型。
*   **`CREATE VECTOR INDEX {index}`**: 声明创建一个向量索引。
*   **`OPTIONS`**:
    *   `vector.dimensions`: 指定向量的维度（本项目中为 512）。这必须与使用的 Embedding 模型输出维度一致。
    *   `vector.similarity_function`: 指定相似度计算函数，这里使用的是 `'cosine'` (余弦相似度)。

### 3.3 应用场景

项目中为商品和分类构建了向量索引，用于支持语义搜索（例如用户搜索“夏季透气运动鞋”，可以通过向量相似度找到相关的 SPU，即使商品名称中没有完全匹配的词）。

*   **SPU**: `spu_embedding_index`
*   **品牌**: `trademark_embedding_index`
*   **分类**: `category3_embedding_index`, `category2_embedding_index`, `category1_embedding_index`

---

## 4. 索引管理

代码中还提供了 `drop_all_indexes` 函数，用于清理现有的全文索引和向量索引，方便重新构建。

```python
def drop_all_indexes(graph):
    # 查询所有类型为 VECTOR 或 FULLTEXT 的索引
    indexes = graph.query("show indexes where type in ['VECTOR','FULLTEXT']")
    # ... 遍历并删除 ...
```

*   **`SHOW INDEXES`**: 查看数据库中的所有索引。
*   **`DROP INDEX {index}`**: 删除指定名称的索引。

## 总结

| 特性 | 全文索引 (Fulltext) | 向量索引 (Vector) |
| :--- | :--- | :--- |
| **核心原理** | 倒排索引 (Lucene) | 向量空间相似度 (HNSW 等算法) |
| **匹配方式** | 关键词匹配、模糊查询、正则 | 语义相似度匹配 |
| **典型用途** | 传统的搜索框关键词搜索 | 语义搜索、推荐系统、RAG 上下文召回 |
| **输入数据** | 文本字符串 | 高维浮点数向量 (Embedding) |

该项目结合使用这两种索引，能够同时满足精确的关键词查找和模糊的语义探索需求，为图谱问答或搜索功能提供了坚实的基础。
