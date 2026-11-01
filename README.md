# zy：本地文档检索实验

逐步构建 AI 应用和算法实验。本仓库使用 AI 辅助开发，提交记录不代表作者已独立掌握全部内容。

准备展示项目可阅读 [面试演示与讲解材料](INTERVIEW.md)：包含五分钟操作流程、代码定位、实验数字的适用范围、常见追问和自主练习清单。

## 运行

演示前可运行 `python doctor.py` 检查默认知识库；生成模式用 `python doctor.py --generate --model qwen3:4b`。详细说明见下方“启动自检”。

需要 Python 3.10+，无额外依赖。在仓库根目录运行：

```sh
python search.py "向量检索"
python search.py "Git" --docs docs --top-k 2
python search.py "Git" --json
python search.py "Git" --min-score 0.1 --method tfidf --json
python -m unittest -v
```

将 UTF-8 Markdown/TXT 放到 docs，或用 --docs 指定目录。程序按空行分段，以中文单字和英文词集合的 Jaccard 相似度排序，返回原文、文件名和段落序号。分数不是正确概率。search.py 只返回检索结果；qa.py 支持原文摘录和可选模型生成。

## 限制

`--min-score` 可过滤低相似度结果，范围为 0 到 1，默认 0 保持原有行为。等于阈值的匹配会保留；没有词重叠的段落始终不返回。阈值越高可能漏掉相关内容，应结合自己的评估题集调整；它不是置信度或答案正确率。

使用 `--json` 输出可供其他程序读取的 JSON 数组，每项包含 `score`、`source`、`paragraph`、`text`。无匹配时输出 `[]`。路径统一使用 `/`，中文以 JSON Unicode 转义输出，解析后保持原文，便于 Windows 管道传输。非法参数仍返回非零退出码并向标准错误输出提示。

中文单字匹配较粗糙，不理解同义词；每次查询扫描文件元数据，复用进程内段落缓存，适合小规模资料；不支持 PDF。资料只在本机读取。

## 后续计划

- [x] 文档检索、原文出处、命令行入口
- [x] 中文、英文、无匹配、数量限制和非法参数验证
- [x] 固定评估问题集与 Recall@k
- [x] 相似度阈值评估与配置记录
- [x] TF-IDF 与当前基线对比
- [x] MRR@k 排名评估
- [x] 进程内段落索引缓存
- [x] Python/CLI 问答接口与可选本地模型命令适配

## 检索评估

运行 `python evaluate.py --top-k 1` 或 `python evaluate.py --top-k 3`。
固定题集位于 `evaluation/cases.json`，以文件名和段落序号标注相关原文。
Recall@k = 前 k 条结果中的相关段落数 / 全部标注相关段落数，报告对问题取宏平均。
当前 4 个示例问题实测 Recall@1 为 0.875，Recall@3 为 1.0。
这是小型冒烟评估，不代表真实业务效果；改动资料段落后需同步核对标注。

### 评估相似度阈值

使用 `python evaluate.py --top-k 3 --min-score 0.1` 评估启用过滤后的召回率。
默认阈值为 0，与原评估行为一致；JSON 报告包含 `min_score`，便于记录和比较配置。
可分别以 0、0.1、0.3 运行，查看每题和宏平均 Recall@k 的变化。提高阈值可能过滤掉相关段落；零召回也会如实计入平均值，不会跳过无结果问题。
阈值范围为 0 到 1，边界相等时保留结果；非法值返回非零退出码。
该评估只衡量召回，不能据此证明精确率或答案质量提高。



TF-IDF 基线可用 --method tfidf 启用；默认仍使用 Jaccard，便于对比两种词项权重策略。TF-IDF 分数只用于排序，不是概率。


评估脚本也支持 `python evaluate.py --method tfidf`，报告会记录使用的评分方法，便于在同一题集上比较 Jaccard 与 TF-IDF。

TF-IDF 使用原始词频、平滑 IDF = 1 + ln((N+1)/(df+1)) 和余弦相似度，分数范围为 0 到 1。N 为段落数；查询中未出现在语料里的词仍计入查询向量长度。修正前的 TF-IDF 分数不可直接沿用阈值。

评估报告新增 `mrr`（MRR@k）及逐题 `reciprocal_rank`：取前 k 条中首个相关段落排名的倒数，再对所有问题平均；无相关命中计 0。例如首个相关结果排名第 2，得分为 0.5。它衡量首个相关结果的位置，不衡量生成答案质量；原 Recall 字段保留。


## 问答入口

运行 `python qa.py "Git"`，默认输出原文摘录及 sources（文件、段落、分数、引用编号），不需要模型。
也可在 Python 中使用 `from qa import answer`，调用 `answer("docs", "Git")`。
无匹配时返回 no_evidence，不调用模型；空问题报错。

可选模型接入：`python qa.py "Git" --model-command '["python","my_model.py"]'`。
命令须为你信任的可执行程序及参数 JSON 数组；适配脚本从 UTF-8 标准输入读取提示词，调用你选定的模型，并将答案写入标准输出。无需 shell，超时为 120 秒，非零退出码和空输出会报错。Windows 参数转义取决于所用终端，亦可直接用 Python 接口传入列表。
模型接入单元测试使用模拟返回值；另有本地 Ollama 真实运行记录，见下方验证说明，尚未进行系统性答案质量评估。模型可能编造答案或引用，返回 sources 不等于已经验证引用正确。外部适配程序若使用云端模型，会发送问题和选中段落。凭据应由适配程序从环境变量读取，不要提交到 Git。
每段上下文最多 4000 字符，默认最多三段；这可能截断相关内容。

## 缓存范围

缓存按绝对文件路径、纳秒修改时间和文件大小标识，最多保留 128 个文件的解析段落；文件新增和删除在下次查询反映。缓存只在同一 Python 进程内复用，重启后重建，不产生磁盘索引。若内容变化但大小及修改时间均被保留，需调用 `search.cached_passages.cache_clear()`。当前缓存不保存 TF-IDF 权重，大语料仍需进一步优化。

## 本地网页演示

运行 `python app.py`，浏览器访问 http://127.0.0.1:8080 。POST /api/ask 接收 JSON `{ "question": "RAG", "generate": false }`；GET /health 返回服务状态。
模型生成使用 Ollama 官方 /api/chat 接口（https://docs.ollama.com/api/chat），固定连接本机 11434 端口。先安装并启动 Ollama、准备本地模型，再在 PowerShell 设置 `$env:OLLAMA_MODEL="你已安装的模型名"` 并启动 app.py。网页勾选生成后才调用模型。无需提交 API 密钥。
显示响应耗时、证据段落和未知引用编号；引用编号合法不代表语义正确。当前无账户、持久化对话或流式输出，仅适合本机演示，不应直接暴露公网。HTTPServer 不是生产部署方案。

## 可复现实验与求职范围

evaluation/baseline_results.json 是现有四题上实际运行的 Jaccard/TF-IDF、k=1/3 结果。可用 evaluate.py 相同参数复现。数据太小，不能证明真实业务提升；模型协议测试使用模拟响应，没有伪装成真实模型实验。

演示顺序：启动 app.py → 查询 RAG → 展开原文 → 对比 evaluate.py 两种算法 → 配好 Ollama 后再演示生成和引用。模型未配置时保持摘录模式。

当前可据实描述：基于 Python 构建本地文档检索与问答应用，实现 TF-IDF 检索、进程内缓存、HTTP/网页入口、Ollama 模型适配、引用编号检查及 Recall/MRR 评估。
不要声称已验证幻觉降低、生产并发能力、企业落地或真实用户规模。

求职核心项目验收仍需：
- [x] 在真实本地模型上记录一轮回答、来源和证据约束不足案例（四个冒烟问题，非质量基准）
- [ ] 扩充独立标注的问题集，包含无答案与同义表达，划分调参/测试集
- [ ] 用户独立讲解并修改检索、评估、缓存和模型调用代码
- [ ] 使用真实评估结果完善简历中的量化描述

### 记录真实本地模型验证

安装 Ollama 并下载模型后，在 PowerShell 中运行：

```powershell
$env:OLLAMA_MODEL="qwen3:4b"
python smoke_local.py --output evaluation/local_smoke.json
```

该命令实际调用本机模型，记录运行时间、模型清单、四个问题的回答、来源、引用检查和错误；任何调用失败都会返回非零退出码，仍保留已完成的结果。问题覆盖 RAG、Git、语料未提供答案的问题及无词项匹配的输入。无检索结果时不会调用模型。

这是连通性和行为验证，不会自动给答案质量打分。尤其应人工检查无答案问题是否错误引用无关材料：目前词项相似不能判断证据是否足够。报告中的耗时受硬件、首次加载和模型思考过程影响，不能直接作为性能基准。提交结果前检查其中是否含有私人文档内容。

2026-11-01 实际记录见 `evaluation/local_smoke.json`：Ollama 0.40.13、qwen3:4b（Q4_K_M）、RTX 4060 Laptop 8 GB。RAG 和 Git 两题生成成功，引用编号均存在；两个无匹配输入返回 `no_evidence`。RAG 首次调用耗时 72.54 秒，Git 随后调用耗时 21.45 秒，未分离加载、思考与生成时间。四个调用无运行错误，不代表答案准确率为 100%。

人工检查发现：RAG 回答补充了证据未给出的英文全称 Retrieval-Augmented Generation。即使该扩展符合常识，也不满足严格的“仅依据证据”约束，而引用编号检查无法发现这类问题。该轮无答案问题都未召回段落；后续困难负例验证见下节。

### 困难负例与开发/测试划分

`evaluation/qa_cases.json` 新增 12 题，dev/test 各 6 题：每组有 3 个可回答问题、2 个有词项命中但证据不支持答案的困难负例、1 个无匹配输入。包含中文同义表达和英文问题。题目和预期答案由 AI 根据现有示例语料编写，问题不重复，但共享同一份小语料、主题相近，不是独立人工标注的业务测试集，也不足以证明泛化能力。原四题检索基准仍保留，结果不能与新题集直接混算。

```powershell
python evaluate_qa.py --split dev --output evaluation/qa_dev_retrieval.json
$env:OLLAMA_MODEL="qwen3:4b"
python evaluate_qa.py --split test --generate --output evaluation/qa_test_results.json
```

默认只检索；`--generate` 才会实际调用本地模型。每完成一题便保存原始回答、证据、预期答案、错误及语料/题集哈希，`complete` 表示所有题均已尝试，不等于全部成功。调用失败使退出码非零。报告的 Recall@3 只对可回答题计算，错误按未命中计入；无答案题单独统计有检索命中的数量，**该数量不是错误回答数或拒答率**。拒答要阅读全文判断，不能靠引用合法或包含某个词判分。

本轮固定现有提示词后运行测试集，不根据测试题调参；后续可用 dev 调整，再重新报告 test 结果。测试题已经公开，若持续据此修改实现，应另建未用于调参的测试集。独立人工复核和更丰富的文档仍在待办中。

本轮实际结果：测试集六题无运行错误，三道可回答题 Recall@3 = 1.0；两道困难负例都召回了无关段落，但模型回答“insufficient evidence”；无匹配题未调用模型。见 `evaluation/qa_test_results.json` 和逐题检查 `evaluation/qa_review.md`。检查由开发助手完成，不是独立人工评测；这些小样本结果不可包装为通用准确率或业务提升。

### 多文档与冲突证据实验

`evaluation/multidoc/docs` 包含五份 AI 编写的虚构资料，分别模拟 Orion 新旧规则、相似产品 Lyra、相互矛盾且没有优先级的 Vega 记录。所有数值都是测试设定，不代表真实产品或实验性能。实验语料独立保存，网页仍默认查询 `docs`，原始基准的语料不会因此改变。

```powershell
python evaluate_qa.py --docs evaluation/multidoc/docs --cases evaluation/multidoc/cases.json --split dev --output evaluation/multidoc/dev_retrieval.json
$env:OLLAMA_MODEL="qwen3:4b"
python evaluate_qa.py --docs evaluation/multidoc/docs --cases evaluation/multidoc/cases.json --split test --generate --output evaluation/multidoc/test_results.json
```

Python 调用也可使用 `ask(question, generate=True, docs=Path("evaluation/multidoc/docs"))`；文档路径只由本地代码或命令行指定，不向网页请求开放。

多文档标签使用 `{"source":"文件名", "paragraph":2}`，避免不同文件中的同号段落被误计为正确命中。旧的整数标签仍解释为 `intro.md` 的段落。冲突题需要召回两条证据，理想回答应引用双方、说明冲突，不能在缺乏优先级时任意选择。当前仅观察模型行为，没有添加自动冲突检测器。

新报告的 `corpus_manifest` 记录所有 Markdown/TXT 文件的路径和内容 SHA-256；`corpus_sha256` 改为该清单排序 JSON 的哈希，并有 `corpus_hash_format` 标识。此前没有该格式字段的报告只记录 `intro.md` 内容哈希，两种格式不可直接比较。

真实运行与逐题检查见 `evaluation/multidoc/test_results.json`、`evaluation/multidoc/REVIEW.md`：四题无运行错误，模型区分新旧规则、列出冲突并在缺少并发数据时拒答。但 Orion 问题的首条检索结果是无关的 Lyra 文档；Recall@3 满分不能掩盖这个排名问题。该实验只有少量 AI 合成题，尚无独立人工复核。

### 可选标题匹配重排

`search.py`、`qa.py` 和 `evaluate_qa.py` 支持 `--rerank title`，默认 `none`。Python 接口 `search`、`answer`、`ask` 支持关键字参数 `rerank="title"`。网页仍采用默认检索策略。

```powershell
python qa.py "Orion 当前文档上传上限是多少？旧规则是否仍然适用？" --docs evaluation/multidoc/docs --rerank title
python compare_rerank.py --split dev --output-dir evaluation/rerank
python compare_rerank.py --split test --output-dir evaluation/rerank
```

该策略优先排列 Markdown 首行标题与问题存在英文词项匹配的候选文档，再按原相似度排序；在截断候选前执行，不改变相似度数值或阈值过滤。没有标题或没有匹配时退回原排序。它是简单词项规则，不是语义重排模型，不保证中文实体、别名或噪声标题下有效。

评估新增可回答题的 MRR@3 和 Hit@1。实际对照中，多文档测试集三道可回答题 Hit@1 从 2/3 到 3/3，MRR@3 从 0.8333 到 1.0，Recall@3 保持 1.0；原题集指标不变。详见 `evaluation/rerank/REVIEW.md`。测试题此前已公开且用于发现问题，因此这些数值仅是小样本回归结果；本轮未重新生成答案，不能据此宣称回答质量提高。标题策略暂不设为默认。

### 标题随正文分块

新增可选 `--chunking heading_context`，可用于 `search.py`、`qa.py`、`evaluate_qa.py`；Python 的 `search`、`answer`、`ask` 接受同名关键字参数。默认仍为 `paragraph`，网页默认行为不变。

对 Markdown 文件，独立的 ATX 标题块（`#` 至 `######`）不再单独进入候选集，而是按层级附在后续正文前。正文仍以原空行分段编号定位；返回文本包含继承标题，不再只是该编号的原文。TXT 文件保持原行为。标题变化会通过原文件缓存失效机制反映。

```powershell
python qa.py "Orion 当前文档上传上限是多少？" --docs evaluation/multidoc/docs --rerank title --chunking heading_context
python compare_chunking.py --split dev --output-dir evaluation/chunking
python compare_chunking.py --split test --output-dir evaluation/chunking
```

分块对照固定 `rerank=title`，只改变分块方式。两套测试题合计 21 条检索结果中，纯标题结果从 3 条降为 0 条；可回答题的 Recall@3、MRR@3、Hit@1 均未下降。见 `evaluation/chunking` 中原始结果及检查记录。统计按各次检索返回条目计数，并非独立文档数。

这是受限的 Markdown 规则，不是完整解析器：仅将独立标题块继承到正文；标题与正文没有空行时保留原块，Setext 标题、列表等不做专门处理。围栏代码中的井号不会被当作标题删除，但代码仍沿用原空行切分。重复标题增加上下文长度并改变词频/IDF，分数及阈值不可与旧模式直接混用；长段落仍受问答入口 4000 字符截断限制。更大的独立语料验证之前不更改默认模式。

### 网页交互演示

网页现在可以选择基础知识库或虚构多文档演示库，以及排序和分块方式；默认仍为基础库、原始排序、按段落。此前各节“网页默认行为不变”指默认选项，实验策略现可手动选择。

点击回答中的 `[1]` 等引用，会展开并定位对应证据。证据区同时显示送入问答的检索上下文和原文件对应段落，便于区分继承标题及截断。未知引用标为“无对应证据”；仅解析方括号数字，不自动识别 `Evidence ID 1` 等其它写法，也不做语义核验。文档和模型文本以纯文本插入页面。

演示步骤：运行 `app.py`，打开 `http://127.0.0.1:8080` → 选择“多文档演示” → 选择“标题匹配优先”和“标题随正文” → 提问“Orion 当前文档上传上限是多少？旧规则是否仍然适用？” → 点击引用查看原文。配置 `OLLAMA_MODEL` 后可勾选本地模型生成。等待时禁用表单，新查询先清空旧结果；结果显示本次实际配置。

`POST /api/ask` 新增可选字段 `corpus`（intro/multidoc）、`rerank`（none/title）、`chunking`（paragraph/heading_context）。非法值返回 400；知识库只从服务器预设映射中选择，没有开放任意文件路径。HTTP 返回的来源新增 `original_text`，指响应时磁盘上的原段落，不是历史版本快照。接口与页面仍仅用于本机演示。

### 评估指标边界修正

QA 评估的 Recall@3、MRR@3、Hit@1 现在使用一致的前三条候选范围。即使传入超过三条的结果，第四条之后的相关段落也不会计入 Recall@3；新增回归测试覆盖第四条未命中与第三条命中的边界。此前已保存的实验每题最多返回三条，因此该修正不改变这些历史结果，也不表示检索效果提升。

### 启动自检

```powershell
python doctor.py
python doctor.py --docs evaluation/multidoc/docs
python doctor.py --generate --model qwen3:4b
python doctor.py --generate --json
```

自检检查 Python 版本、Markdown/TXT 文件存在性、UTF-8 可读性及非空内容。默认仅检查检索准备状态，不连接模型；`--generate` 才查询本机 Ollama 的模型列表，检查 `--model` 或 `OLLAMA_MODEL` 指定的模型。未带标签的名称按 `:latest` 匹配。失败退出码为 1，参数错误为 2，全部通过为 0；`--json` 输出结构化报告。

`--model` 只影响这次自检，不设置环境变量；启动网页仍需设置 `OLLAMA_MODEL`。工具不下载模型、不修改配置、不发送文档、不执行推理，也不检查 8080 端口、显存容量或回答质量。纯标题文件仍可能通过非空检查，因此通过不等于每种分块方式都能返回证据。需要验证生成时再运行 `smoke_local.py`。Windows 输出乱码时可使用 `--json`（ASCII 转义，解析后保留中文）。
