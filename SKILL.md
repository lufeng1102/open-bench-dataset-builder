---
name: open-bench-dataset-builder
description: 制作、校验、整理和上传 Open Bench 数据集产物，覆盖物理测试集、物理训练集和逻辑数据集。当用户要求生成 df.jsonl/sf.jsonl/ef.jsonl、把 wav.scp/text/utt2* 等原始标注转换成平台格式、校对字段规范、处理 ds-cli create/add/update/push/release/clone 流程、排查数据集上传失败或维护已有数据集时使用。
---

# Open Bench Dataset Builder

## 使用前先读

按任务需要读取最小必要参考，不要一次性把所有大文档塞进上下文：

- 测试集字段规范：优先读 `references/specs_20260325/` 下对应任务的结构化摘要；若目录不存在，再读 `references/测试数据标签管理v20260325更新.xlsx`。
- ds-cli 外部操作：读 `references/开源社区数据集cli工具操作手册-对外-1786008602380.md`。
- 已知排障经验：读 `references/TroubleShooting.md`。
- 样本互斥校验：运行 `python3 scripts/validate_sf_jsonl.py <sf.jsonl路径>`。

字段来源优先级：

- 上传版 `df.jsonl` 以 `ds-cli` 外部手册、`ds-cli -h` 和服务端 schema 校验结果为准。
- `references/specs_20260325/` 是测试标签规范摘要，不等同于 `df.jsonl` 可上传字段白名单。
- 如果服务端报“存在非法字段”，必须删除该字段或迁移到允许的结构里，不要为了满足标签规范继续保留。
- `data_generate_time` 不要写入上传版 `df.jsonl`，除非当前 CLI/schema 明确接受。
- `source_info` 在上传版 `df.jsonl` 中是字符串，不要写成对象。
- 顶层 `tag` 不要默认写入上传版 `df.jsonl`。即使字段说明写为可选，若当前训练/测试 schema 报非法字段，必须省略；只有服务端明确接受时才可写入 `list<string>`。
- `audio.audio_format` 不在当前公开上传 schema 中，不要默认写入。
- 当前训练数据集创建会要求顶层 `license` 为必填字符串。公开数据优先填写上游许可证；没有可靠依据时先问用户，不要留空或臆造。

开源安全约束：

- 不要把真实数据库账号、API key、Cookie、token、内网 IP、个人主目录或机器专用绝对路径写回仓库。
- 文档示例里的私有入口统一写成占位符，例如 `<OPEN_BENCH_URL>`、`<ENUM_ADMIN_URL>`、`<DATASET_ROOT>`。
- 新增截图、表格或 Office 文档前，先确认不含个人信息、内部路径、内部项目名和文档元数据。
- `.ds_cache/`、`.DS_Store`、本地下载页面缓存和平台克隆缓存不应作为开源产物提交。

## 一、判断数据集类型

先判断用户要处理的是哪类数据集，再选择字段和命令。不要把三类数据集混用。

### 物理测试集

- 产物通常是 `df.json`、`df.jsonl`、`sf.jsonl`，需要时再加 `ef.jsonl`。
- 首次创建用 `ds-cli create ... --test`。
- 先读通用测试集规范，再读任务专属规范。
- `test_content`、`wakeup_words`、`product_info` 等测试集字段只在确有语义时填写。

### 物理训练集

- 产物通常是 `df.jsonl`、`sf.jsonl`、`ef.jsonl`。
- 首次创建用 `ds-cli create`，不要加 `--test`。
- 不使用测试集专属字段，例如 `test_content`、`wakeup_words`、`product_line`。
- 噪声/RIR 数据走 `audio.noise`，无转录样本不要强造 `annotation`。

### 逻辑数据集

- 不是物理三件套，常见形态是 `tr/`、`cv/`、`data/`、`lexicon/`、`scp`、`ark`、`utt2pid` 或 JSONL 特征索引。
- 创建用 `ds-cli create -n <name> -t logic --task <task> --env <prod|dev>`。
- 目录版整理最小目录结构；JSONL 版必须包含 `feat`，上传时加 `-pm jsonl`。

## 二、物理测试集构建

### 基本流程

1. 确认目标确实是物理测试集。
2. 确认数据集名；若用户未给出，先问清楚，不要代取名。
3. 确认输入文件、列语义、任务类型和高风险业务字段。
4. 基于用户确认字段生成可读版 `df.json`。
5. 单独编写 `make_sf_jsonl.py`，只负责从原始输入生成 `sf.jsonl`。
6. 运行 `make_sf_jsonl.py` 生成 `sf.jsonl`。
7. 运行 `python3 scripts/validate_sf_jsonl.py <sf.jsonl路径>`。
8. 由 `df.json` 生成上传版单行 `df.jsonl`。
9. 检查 JSON 可解析、`sample_id` 唯一、路径可达、关键字段齐全。

### 推荐交付目录

正式制作时保留可复查目录，不只留下最小上传产物：

- `original_dataset/`：原始输入的软链或必要入口文件。
- `AGENTS.md`：简短记录任务边界、字段真值和关键命令。
- `df.json`：可读主描述。
- `df.jsonl`：上传版单行描述。
- `make_sf_jsonl.py`：样本转换脚本。
- `sf.jsonl`：样本标注。
- `ef.jsonl`：仅在确有附加文件时保留，不能是空文件。

### 字段规则

- `source` 是顶层字段，不写到 `audio.source`。
- `df.json` 中拿不准的业务字段必须问人，不要猜。
- 高风险字段包括 `application_domain`、`category`、`product_info.brand`、`project_name`、`environment`、`data_user`、`source`、`source_info`、`tag`、`audio.speech.dialect`。
- `source` 不能笼统写旧口径的“质量测试数据”；应按事实区分 `自主采集`、`生成`、`badcase数据`、`公开数据`、业务回流等。
- 反例/误唤醒测试集的 `test_content` 默认用 `误唤醒`；正例测试集根据任务语义和用户确认选择 `主观正例` 或 `客观正例`。
- 顶层 `tag` 不要默认写入上传版 `df.jsonl`；若服务端明确接受，必须写成 `list<string>`，不要写成字符串，也不要再写旧字段 `ds_task_tag`。
- 若没有有效内容，删除空的 `sample_info`、`spatial_info`、`speaker`、`custom` 等壳对象。

### 样本规则

- 若输入 manifest 已有唯一 `key`、`utt_id` 或等价样本 ID，优先用它作为 `sample_id`。
- 只有没有现成样本 ID 时，才默认用音频文件名去掉扩展名；长音频切片或多条样本共用同一音频时，不能用音频 basename 当 `sample_id`。
- `parent_sample_id` 默认不填。只有数据明确从其它样本仿真、派生或继承，并且用户要求保留血缘时才填写。
- 不要默认输入一定是 `use.wavlist + text`；先确认文件清单和列含义。
- 如果原始清单记录旧机器绝对路径但当前目录有同名音频，优先回退到本地同名文件。
- `attribute.path` 应指向当前可访问路径；上传本地数据时通常写绝对路径，开源示例中使用相对路径。
- `annotation[].transcription.text` 必须写成字符串数组，例如 `["文本"]`，不要写成裸字符串。
- 可追溯但非标准字段放入 `annotation[].custom`；历史机器绝对路径不要原样写入 custom，优先保留相对来源路径、原始 key、dataset、split、duration 等。

### 互斥校验

- `annotation[].transcription.keyword` 与 `annotation[].transcription.text` 互斥。
- `annotation[].timestamp` 与 `transcription.keyword + transcription.repeat_times` 互斥。
- 若样本已有 `timestamp.begin_time/end_time`，不要再写 `repeat_times`。
- 若样本使用弱标签命令词/唤醒词，优先写 `keyword`；完整转写场景才写 `text`。
- `timestamp.end_time` 不能写 `null`；没有人工分段但能读 wav 时长时，写实际秒数。

### 发音与语种

- 发音统一写在 `annotation[].transcription.pronunciation`，不要写到 `custom.pronunciation`。
- 中文发音可额外写 `annotation[].transcription.pronunciation_unsigned`；英文和其它语种默认不要补这个字段。
- 发音字段使用原始发音/拼音列，词条字段使用真实词条列，不要互相替代。
- `audio.speech.language` 使用语言代码，普通单语不拼地区码，例如英语写 `en`，中文写 `zh`。
- 明确 code-switch 时使用 `cs_<主语种>-<嵌入语种>`，不要把明确双语改成 `multi-lang`。

### WakeUp 与 FalseTrigger

- WakeUp 的 `wakeup_words` 从真实词条列去重得到，不取拼音列或文件名片段。
- 普通唤醒任务使用 `WakeUp`；误唤醒/反例任务优先使用 `FalseTrigger`。
- 如果平台提示 `wakeup_words`、`application_domain`、`category`、`product_info.brand` 等枚举无效，不要擅自改字段绕过。提示用户去平台枚举管理入口 `<ENUM_ADMIN_URL>` 补充或确认改用已有枚举。

## 三、物理训练集构建

### 基本流程

1. 确认目标是物理训练集，不加 `--test`。
2. 确认数据集名、任务类型、输入文件格式和列语义。
3. 生成 `df.jsonl`、`sf.jsonl`，确有附加文件时生成非空 `ef.jsonl`。
4. 检查 JSON 行格式、`sample_id` 唯一、路径可达、必填字段完整。

### 高频规则

- 训练集数据来源字段是顶层 `source`。
- 训练集上传版 `df.jsonl` 必须包含非空字符串 `license`；公开数据按上游许可证填写。
- `transcription.text`、`pronunciation`、`domain`、`confidence` 等优先按数组字段组织。
- 原始输入没有拼音列时，不补 `pronunciation` 或 `pronunciation_unsigned`。
- 纯 TTS 生成音频通常按 `source=生成`、`audio.generation=synthetic` 处理。
- `attribute.duration` 由平台计算，不主动上传。
- `custom` 只放标准字段外且确有保留价值的信息。
- 噪声或 RIR 数据无转录时，每条样本只保留 `sample_id` 和 `attribute`。

### 路径与去重

- 若输入清单带挂载别名前缀，应归一化为平台或当前机器可访问的真实路径，并用 `--check-paths` 或等价方式验证。
- 同一 basename 出现在不同子目录时，先比对内容哈希。同哈希可去重；不同哈希不能静默合并，应让源数据加可追溯后缀。
- 不要把本机私有绝对路径写进开源示例。

## 四、逻辑数据集构建

### 基本流程

1. 确认任务类型和环境，例如 `ASR`、`TTS`、`KWS`，以及 `prod` 或 `dev`。
2. 若未明确数据集名，先问用户。
3. 选择目录版或 JSONL 版交付形式。
4. 目录版整理 `tr/`、`cv/`、`data/`、`lexicon/`、`utt2pid` 等最小结构。
5. JSONL 版生成含 `feat` 的索引文件。
6. 上传前检查路径、最小目录和血缘关系。

规则：

- `tr`、`cv` 缺失时优先视为不合规。
- `utt2pid` 第一列是逻辑样本 `sample_id`，后续列是物理样本 `sample_id`。
- 物理样本缺失但特征可用时，可写 `_sample_unk`。
- 不要把逻辑数据集当作物理数据集三件套输出。
- 文档写“暂无规范”的任务类型，不要臆造结构。

## 五、ds-cli 操作

### 通用前置

每次执行 `ds-cli` 子命令前都重新清代理，不能假设父 shell 或上一条命令已经处理过：

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY
```

这条规则适用于 `create`、`add`、`update`、`rm`、`push`、`release`、`version`、`clone`、`info`、`search`。

### 物理测试集上传

1. 确认目录中有 `df.json`、`df.jsonl`、`make_sf_jsonl.py`、`sf.jsonl`。
2. 首次创建用 `ds-cli create ... --test`。
3. 创建成功后保留自动生成的 `_phy_*` 目录。
4. 后续修改进入 `_phy_*` 目录执行 `ds-cli add/update/rm`。
5. 修改后执行 `ds-cli push`。
6. 需要正式版本时按平台发布流程执行 `ds-cli release` 并用 `ds-cli version` 确认。

### 物理训练集上传

1. 首次上传用 `ds-cli create`，不要加 `--test`。
2. 创建成功通常会自动完成首次推送。
3. 后续增量用 `ds-cli add`，定向修改用 `ds-cli update`，删除用 `ds-cli rm`。
4. `add/update/rm` 后必须执行 `ds-cli push`。
5. 需要正式版本时执行 `ds-cli release`，再用 `ds-cli version` 确认。

### 逻辑数据集上传

1. `ds-cli create -n <name> -t logic --task <task> --env <prod|dev>`
2. 进入数据集目录。
3. 用 `ds-cli add -p <file_or_dir>` 上传内容。
4. JSONL 版追加 `-pm jsonl`。
5. 执行 `ds-cli push`。
6. 需要正式版本时发布并确认版本。

### 维护已有数据集

- 线上已有数据集要改标签或标注时，不要重建。先 `ds-cli clone <平台数据集名>`，以克隆出的全量样本或描述为底本，再 `update`、`push`、`release`。
- 平台已有测试集但样本数为 0 时，优先进入本地 `_phy_*` 目录补传样本，不要重新创建同名数据集。
- `ds-cli update -sf` 按 `sample_id` 覆盖更新。
- `ds-cli add -sf` 遇到已有 `sample_id` 会覆盖。
- `ds-cli update -df` 只更新提交的 key；`ds-cli add -df` 是全量覆盖。
- 大体量 `push` 建议落盘日志；若静默中断，检查缓存变更目录是否仍有待推分片，必要时重跑 `push` 续推。

### 发布确认

- `ds-cli release` 返回申请成功不代表正式版本已经完成。
- 以 `ds-cli version` 中“最新版本号 == 最新正式版本号”作为发布完成依据。
- 发布过程中若提示数据集正在被操作，通常表示原申请仍在处理，继续轮询，不要盲目重复提交。

### 附加文件

- 没有附加文件时省略 `-ef`，不要上传空 `ef.jsonl`。
- 追加目录时，先把目录下普通文件逐行写成 `{"path":"..."}`，确认非空后再上传。
- 同名附加文件会被新版本替换；未重传的历史附加文件会被平台带入新版本。
- 删除源文件或改软链前，先对源文件和平台副本逐一做大小与哈希校验。

## 六、字段速查

数据集级常见字段：

- 标准字段：`info`、`type`、`supported_tasks`、`source`、`source_info`、`environment`、`license`。当前训练数据集创建要求 `license` 必填且为字符串；`tag` 只在当前 CLI/schema 明确接受时写入。实际上传时以 CLI/schema 接受的字段为准。
- 音频字段：`audio.tag`、`audio.generation`、`audio.acoustic.channels`、`audio.acoustic.sample_rate`、`audio.acoustic.device`、`audio.acoustic.distance`、`audio.acoustic.background`、`audio.acoustic.array_info`。
- 语音字段：`audio.speech.language`、`audio.speech.dialect`、`audio.speech.anno_method`、`audio.speech.genre`、`audio.speech.style`。
- 噪声字段：`audio.noise.style`。
- 测试集业务扩展：`application_domain`、`category`、`project_name`、`product_info.brand`、`product_info.model`、`data_user`、`test_content`、`wakeup_words`、`pms_id`、`test_date`、`voice_length_type`。这些字段只在当前 schema 明确接受时写入。

样本级常见字段：

- 必填底座：`sample_id`、`attribute.path`、`attribute.file_type`。
- 高频标注：`annotation[].timestamp.begin_time`、`annotation[].timestamp.end_time`、`annotation[].transcription.language`、`annotation[].transcription.text`、`annotation[].transcription.keyword`、`annotation[].transcription.pronunciation`、`annotation[].transcription.pronunciation_unsigned`。
- 常用补充：`annotation[].custom`、`annotation[].speaker.id`。
- 默认不填：`parent_sample_id`、空对象、无来源依据的 `custom` 字段。

常见数据来源枚举：

`购买`、`生成`、`自主采集`、`公开数据`、`云端业务数据回流`、`本地业务数据回流`、`私有化业务数据回流`、`badcase数据`、`历史未知数据`。

## 七、冲突处理

- 文档之间冲突时，以最新字段规范和 `ds-cli -h` 的实际行为为准。
- 用户要求与规范冲突时，先指出风险，再按用户最终确认执行。
- 平台枚举、白名单或字段校验失败时，不要通过改业务真值绕过；先让用户确认补平台规则还是改用已有合法值。
- 上传前发现大量 `sample_id` 撞库时，暂停并判断是否重复上传同一批数据，不要默认加前缀重传。
- 每次形成新的稳定经验后，回写到 `SKILL.md` 或 `references/TroubleShooting.md`，但必须先脱敏。
