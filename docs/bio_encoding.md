# BIO 序列标注编码速览

## 核心含义
- `B` (Begin): 实体的第一个 token。
- `I` (Inside): 实体内部的 token（除首个外）。
- `O` (Outside): 不属于任何实体的 token。

## 边界规则（IOB2/BIO 约定）
- 实体必须以 `B` 开头，后续可以有若干 `I`，然后结束或回到 `O/B`。
- `O` 之后不能直接出现 `I`，否则起点不明（应当改为 `B`）。
- 单 token 实体标为 `B`（在 BIOES/BILOU 里可用单独的 `S/U`）。

## 作用与理由
- 用标签序列即可复原每个实体的起止位置，无需单独存 `start/end`。
- 适配 CRF/RNN/Transformer 等序列标注模型；`labels` 直接作为监督信号。
- 与主流数据集/工具链兼容（如 CoNLL 共享任务、Transformers Trainer）。

## 常见变体
- **BIO/IOB2**: 当前使用的方案，所有实体都以 `B` 开头。
- **BIOES/BILOU**: 在 BIO 基础上增加 `E`(End)/`S`(Single) 或 `L`/`U`，边界更明确，部分任务上效果更好。

## 多类型实体时的扩展
- 将类型附在标签后：如人名 `B-PER/I-PER`，地名 `B-LOC/I-LOC`，组织 `B-ORG/I-ORG`，其余仍为 `O`。
- 仍遵循同样的边界规则：每个实体段落以对应类型的 `B-XXX` 开始，内部用 `I-XXX`。

## 与本项目的对应
- 文件 `src/ner/preprocess.py` 中的 `id2label = ["B", "I", "O"]`/`label2id` 定义了单一“是否为实体”的 BIO 标签。
- 若需要区分多种实体类型，应扩展 `id2label`/`label2id` 并在生成标签时按类型填充。***
