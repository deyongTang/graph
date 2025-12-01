import evaluate  # 导入 evaluate 库，用于加载评估指标（如 seqeval）
from datasets import load_from_disk  # 从 datasets 库导入 load_from_disk，用于加载本地保存的数据集
from transformers import (  # 从 transformers 库导入所需的类
    AutoModelForTokenClassification,  # 用于 Token 分类（如 NER）的自动模型类
    AutoTokenizer,  # 自动分词器类
    DataCollatorForTokenClassification,  # 用于 Token 分类任务的数据整理器（处理 padding 等）
    EvalPrediction,  # 评估预测结果的数据结构
    Trainer,  # Hugging Face 的训练器，封装了训练循环
    TrainingArguments,  # 训练参数配置类
)

from conf import config  # 导入本地配置文件，包含路径、超参数等常量

# label映射关系

"""
LABELS = ['B', 'I', 'O']
"""
# 创建 id 到 label 的映射字典，enumerate 遍历 config.LABELS 列表
id2label = {id: label for id, label in enumerate(config.LABELS)}
# 创建 label 到 id 的映射字典，用于模型内部处理
label2id = {label: id for id, label in enumerate(config.LABELS)}

# 模型
# 加载预训练的 Token 分类模型
model = AutoModelForTokenClassification.from_pretrained(
    config.MODEL_NAME,  # 预训练模型的名称或路径（来自配置）
    num_labels=len(id2label),  # 标签的总数量
    id2label=id2label,  # id 到 label 的映射
    label2id=label2id,  # label 到 id 的映射
)

# 数据集
# 从磁盘加载预处理好的训练数据集
train_dataset = load_from_disk(config.PROCESS_DATA_DIR / "train")
# 从磁盘加载预处理好的验证数据集
valid_dataset = load_from_disk(config.PROCESS_DATA_DIR / "valid")

# 评价指标
# 加载 seqeval 指标，这是 NER 任务的标准评估库
seqeval = evaluate.load("seqeval")


def compute_metrics(prediction: EvalPrediction) -> dict:  # 定义计算评估指标的函数
    logits = prediction.predictions  # 获取模型的预测输出 logits，形状为 [batch_size, seq_len, num_labels]
    preds = logits.argmax(axis=-1)  # 在最后一个维度取最大值索引，得到预测的 label id，形状为 [batch_size, seq_len]
    labels = prediction.label_ids  # 获取真实的 label ids，形状为 [batch_size, seq_len]

    # 过滤掉 label 为 -100 的特殊 token（如 padding 或 subword），并获取预测的真实 label 名称
    true_predictions = [
        [id2label[p] for (p, l) in zip(pred, label) if l != -100]  # 遍历每个样本，如果真实 label 不是 -100，则取出预测的 label 名称
        for pred, label in zip(preds, labels)  # 遍历 batch 中的每一个样本
    ]
    # 过滤掉 label 为 -100 的特殊 token，并获取真实的 label 名称
    true_labels = [
        [id2label[l] for (p, l) in zip(pred, label) if l != -100]  # 遍历每个样本，如果真实 label 不是 -100，则取出真实的 label 名称
        for pred, label in zip(preds, labels)  # 遍历 batch 中的每一个样本
    ]

    # 使用 seqeval 计算指标（Precision, Recall, F1, Accuracy），传入处理后的预测列表和真实标签列表
    return seqeval.compute(predictions=true_predictions, references=true_labels)


# 初始化分词器，使用与模型相同的预训练名称
tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
# 初始化数据整理器，用于将 batch 数据动态 padding 到最大长度，并转换为 PyTorch 张量
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer, padding=True, return_tensors="pt")

# 定义训练参数
training_args = TrainingArguments(
    output_dir=str(config.CHECKPOINT_DIR / "ner"),  # 模型检查点和输出文件的保存目录
    logging_dir=str(config.LOG_DIR / "ner"),  # TensorBoard 日志的保存目录
    per_device_train_batch_size=config.BATCH_SIZE,  # 每个 GPU/CPU 的训练 batch size
    num_train_epochs=config.EPOCHS,  # 训练的总轮数 (epochs)
    learning_rate=config.LEARNING_RATE,  # 初始学习率
    logging_steps=config.SAVE_STEPS,  # 每隔多少步记录一次日志
    save_steps=config.SAVE_STEPS,  # 每隔多少步保存一次模型检查点
    save_total_limit=3,  # 最多保留最近的 3 个模型检查点，防止占满磁盘
    eval_strategy="steps",  # 设置评估策略为按步数评估
    eval_steps=config.SAVE_STEPS,  # 每隔多少步进行一次评估（需要与 evaluation_strategy 配合，这里默认可能是 "no" 或 "steps"）
    load_best_model_at_end=True,  # 训练结束后加载在验证集上表现最好的模型
    metric_for_best_model="eval_overall_f1",  # 用于判断“最好”模型的指标（这里是整体 F1 分数）
    greater_is_better=True,  # 指标越大越好（F1 是越大越好）
)

# 初始化 Trainer
trainer = Trainer(
    model=model,  # 待训练的模型
    args=training_args,  # 训练参数
    data_collator=data_collator,  # 数据整理器
    train_dataset=train_dataset,  # 训练数据集
    eval_dataset=valid_dataset,  # 验证数据集
    compute_metrics=compute_metrics,  # 评估指标计算函数
)

# 开始训练
trainer.train()
# 保存最终的最佳模型到指定目录
trainer.save_model(config.CHECKPOINT_DIR / "ner" / "best_model")
