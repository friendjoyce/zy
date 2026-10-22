# zy：本地文档检索实验

逐步构建 AI 应用和算法实验。本仓库使用 AI 辅助开发，提交记录不代表作者已独立掌握全部内容。

## 运行

需要 Python 3.10+，无额外依赖。在仓库根目录运行：

```sh
python search.py "向量检索"
python search.py "Git" --docs docs --top-k 2
python search.py "Git" --json
python -m unittest -v
```

将 UTF-8 Markdown/TXT 放到 docs，或用 --docs 指定目录。程序按空行分段，以中文单字和英文词集合的 Jaccard 相似度排序，返回原文、文件名和段落序号。分数不是正确概率。当前不生成回答，不调用外部 API。

## 限制

使用 `--json` 输出可供其他程序读取的 JSON 数组，每项包含 `score`、`source`、`paragraph`、`text`。无匹配时输出 `[]`。路径统一使用 `/`，中文以 JSON Unicode 转义输出，解析后保持原文，便于 Windows 管道传输。非法参数仍返回非零退出码并向标准错误输出提示。

中文单字匹配较粗糙，不理解同义词；每次查询扫描目录，适合小规模资料；不支持 PDF。资料只在本机读取。

## 后续计划

- [x] 文档检索、原文出处、命令行入口
- [x] 中文、英文、无匹配、数量限制和非法参数验证
- [x] 固定评估问题集与 Recall@k
- [ ] TF-IDF 与当前基线对比
- [ ] 索引缓存
- [ ] 问答接口与可选模型接入

## 检索评估

运行 `python evaluate.py --top-k 1` 或 `python evaluate.py --top-k 3`。
固定题集位于 `evaluation/cases.json`，以文件名和段落序号标注相关原文。
Recall@k = 前 k 条结果中的相关段落数 / 全部标注相关段落数，报告对问题取宏平均。
当前 4 个示例问题实测 Recall@1 为 0.875，Recall@3 为 1.0。
这是小型冒烟评估，不代表真实业务效果；改动资料段落后需同步核对标注。
