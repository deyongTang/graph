import pymysql
from neo4j import GraphDatabase
from pymysql.cursors import DictCursor

from conf import config


class MysqlReader:
    def __init__(self):
        """
            ** 是把一个 dict 拆成函数的关键字参数假设你的配置是一个 dict：
                    MYSQL_CONFIG = {
                        "host": "127.0.0.1",
                        "port": 3306,
                        "user": "root",
                        "password": "123456",
                        "database": "test"
                    }
                Python 会自动变成：

                pymysql.connect(
                    host="127.0.0.1",
                    port=3306,
                    user="root",
                    password="123456",
                    database="test"
                )
        """

        self.connection = pymysql.connect(**config.MYSQL_CONFIG)
        self.cursor = self.connection.cursor(cursor=DictCursor)

    def read_data(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connection.close()


class Neo4jWriter:
    def __init__(self):
        self.neo4j_driver = GraphDatabase.driver(
            uri=config.NEO4J_CONFIG["url"],
            auth=(config.NEO4J_CONFIG["user"], config.NEO4J_CONFIG["password"]),
        )

    """
      UNWIND 把 batch 中的每个对象展开成 row；MERGE 根据 id 和 name 创建（或复用）节点。  
    """

    def write_nodes(self, label, batch_data, batch_size=20):
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i: i + batch_size]
            properties = {"batch": batch}
            cypher = f"""
            UNWIND $batch AS row
            MERGE (n:{label} {{id: row.id, name: row.name}})
            """
            print(cypher)
            # 使用 execute_query 方法执行查询
            self.neo4j_driver.execute_query(cypher, parameters_=properties)

    def write_relationships(self, start_node_label, end_node_label, relationships, relationship_type, batch_size=20):
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i: i + batch_size]
            properties = {"batch": batch}
            cypher = f"""
            UNWIND $batch AS row
            MATCH (start:{start_node_label} {{id: row.start_id}}),
                  (end:{end_node_label} {{id: row.end_id}})
            MERGE (start)-[:{relationship_type}]->(end)
            """
            self.neo4j_driver.execute_query(cypher, parameters_=properties)
