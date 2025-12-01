from datasets import load_dataset
from transformers import AutoTokenizer

from conf import config


def process():
    # 加载数据
    dataset = load_dataset("json", data_files=config.RAW_DATA_FILE)["train"]
    print(dataset)
    dataset = dataset.remove_columns(["id", "annotator", "annotation_id", "created_at", "updated_at", "lead_time"])

    # 先分出 80% 作为训练集，剩下 20% 暂存为 test
    dataset_dict = dataset.train_test_split(train_size=0.8)
    # 再把上一步的 20% 平分成验证/最终测试，各 10%
    dataset_dict["test"], dataset_dict["valid"] = dataset_dict["test"].train_test_split(test_size=0.5).values()

    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)

    id2label = ["B", "I", "O"]
    """
    {
        B:0,
        I:1,
        O:2
    }
    """
    label2id = {label: id for id, label in enumerate(id2label)}

    def map_func(example):
        """
        tokens = list(example["text"]) 把字符串逐字符拆成列表。
        list() 是 Python 内置函数：对可迭代对象（字符串、列表、元组等）生成一个列表。
        这里 example["text"] 是一句话，list(...) 得到按字符分割的序列，后续按字符做标注/编码。
        """

        """
            麦德龙德国进口双心多维叶黄素护眼营养软胶囊30粒x3盒眼干涩
        """
        tokens = list(example["text"])
        inputs = tokenizer(tokens, truncation=True, is_split_into_words=True)
        # [label2id["O"]] * len(tokens) 生成一个同长度的列表，全是 “O” 对应的编号
        labels = [label2id["O"]] * len(tokens)

        """
            这是 label 的结构
            {
                "start": 3,
                "end": 7,
                "text": "德国进口",
                "labels": [
                "TAG"
                ]
            }
            start，end 是 标签在原始文本的坐标
        """

        for entity in example["label"]:
            start = entity["start"]
            end = entity["end"]
            labels[start:end] = [label2id["B"]] + [label2id["I"]] * (end - start - 1)
        labels = [-100] + labels + [-100]
        inputs["labels"] = labels
        return inputs

    dataset_dict = dataset_dict.map(map_func, batched=False, remove_columns=["text", "label"])

    dataset_dict.save_to_disk(config.PROCESS_DATA_DIR)


if __name__ == "__main__":
    process()
