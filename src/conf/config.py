import os
from pathlib import Path

# 1. 目标路径
ROOT_DIR = Path(__file__).parent.parent.parent

DATA_DIR = ROOT_DIR / 'data'
NER_DIR = DATA_DIR / 'ner'

RAW_DATA_DIR = NER_DIR / 'raw'

PROCESS_DATA_DIR = NER_DIR / 'processed'

LOG_DIR = ROOT_DIR / 'log'

CHECKPOINT_DIR = ROOT_DIR / 'checkpoint'

RAW_DATA_FILE = str(RAW_DATA_DIR / 'data.json')

MODEL_NAME = 'google-bert/bert-base-chinese'

WEB_STATIC_DIR = ROOT_DIR / 'src' / 'web' / 'static'

# 超参数
BATCH_SIZE = 8
EPOCHS = 5
LEARNING_RATE = 1e-5

SAVE_STEPS = 20

LABELS = ['B', 'I', 'O']

NEO4J_CONFIG = {
    "url": "neo4j://localhost:7688",
    "user": "neo4j",
    "password": "password"
}

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "db": "gmail",
    "charset": "utf8mb4"
}

# API keys
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY", "sk-d70dacbef88047e29b8ecd3438c0c59e")
