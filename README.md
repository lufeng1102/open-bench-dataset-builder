<div align="center">

<img src=".docs/imgs/favicon.png" alt="MLOps Dataset Agent Icon" width="96" />

# MLOps Dataset Agent

**把 Open Bench (http://www.open-bench.org/home) 数据集管理这件麻烦事，做成一条能稳定复用的流水线。**

![Platform](https://img.shields.io/badge/Platform-Open%20Bench-blue)
![Workflow](https://img.shields.io/badge/Workflow-Agent%20Driven-0a7ea4)
![Environment](https://img.shields.io/badge/Env-Portable-orange)
![Status](https://img.shields.io/badge/Status-Open%20Source%20Ready-brightgreen)

</div>

这个仓库服务于 **Open Bench 数据集平台** 的数据集维护与自动化操作。

它不是单纯放几个脚本的工具箱，而是把下面这些原本容易散、容易忘、容易出错的事情，收拢成一套可执行、可沉淀、可交接的工作流：

- 把分散的规范整理清楚
- 把原始数据制作成可上传的数据集
- 把上传、更新、校验、发布流程跑稳
- 把踩坑经验持续沉淀下来，避免团队反复交学费

<strong><span style="color: red;">而这一切，原则上都不需要人手工一项项去做。人类真正要做的，通常只是把杂乱的原始数据集目录交给 agent，然后在 agent 自己干活的过程中做必要监督。</span></strong>


## 快速使用

先把仓库拉下来，进入目录，然后启动任意 AI 编程 CLI 即可，例如 `codex`、`claude`、`gemini`：

```bash
cd mlops-dataset-agent
codex
```

如果你使用的是别的 CLI，把最后一行替换成对应命令即可，例如：

```bash
claude
```

```bash
gemini
```

## 为什么这个仓库有价值

数据集工作最消耗人的，往往不是“会不会写命令”，而是：

- 规范散落在不同地方，记不全
- 字段很多，语义强，填错就返工
- 原始输入格式不统一，不能靠经验硬套
- 上传流程容易受环境、代理、权限影响
- 新人接手成本高，经验只能口口相传

这个仓库的目标很直接：

**让人只需要说清楚任务，让 agent 负责把规范、制作、上传和经验回写串成闭环。**

## 这个仓库里有什么

- **`SKILL.md`**
  面向 agent 的主技能说明，负责数据集类型判断、字段规则、上传流程和冲突处理。
- **`references/`**
  结构化字段规范、ds-cli 操作手册和通用排障经验。
- **`scripts/`**
  可复用的公共脚本放这里，例如 `sf.jsonl` 的统一校验脚本、附加文件的批量发布与软链替换脚本。
- **`examples/`**
  可公开的最小示例数据集，用来展示 `df.jsonl/sf.jsonl/ef.jsonl` 组织方式。
- **`.codex/agents/`**
  项目级子代理配置。适合把“主代理判边界、子代理做单项执行”这类分工沉淀为可复用角色。
- **`references/TroubleShooting.md`**
  踩坑记录、经验总结和后续可复用结论。

## 新人最快上手路径

按这个顺序看，成本最低：

1. `README.md`
2. `SKILL.md`
3. `references/specs_20260325/` 中与你任务最接近的字段规范
4. `references/TroubleShooting.md`

## SKILL 覆盖的三类任务

先判断你要处理的是哪一类数据集，再按 `SKILL.md` 的对应章节执行：

一句话判断：

- 做物理训练集，生成并上传 `df.jsonl / sf.jsonl / ef.jsonl`。
- 做物理测试集，生成并上传 `df.json / df.jsonl / sf.jsonl`。
- 做逻辑数据集，整理目录结构或 JSONL 特征索引。

其中：

- 构建阶段负责字段整理、样本转换和本地校验。
- 搬运阶段负责 `ds-cli create/add/update/push/clone/release`。

## 最推荐的使用方式

如果你希望 agent 一次把事情接稳，直接把这些信息说清楚：

- 原始数据目录在哪里
- 任务类型是什么，例如 `WakeUp`、`ASR`
- 是训练集、测试集，还是逻辑数据集
- 数据集名称是什么
- 已确认的属性有哪些，例如客观正例、主观正例、品牌、型号、场景
- 输入文件格式是什么，以及每列的语义
- 是否有要忽略的子目录或特殊处理要求

你给的信息越完整，agent 越容易把这条链路一次跑通：

**制作 -> 校验 -> 上传/更新 -> 经验回写**

## 文档分工

为了避免规则重复漂移，这两个文档后续按下面分工使用：

- `README.md`
  - 给人类看
  - 负责解释仓库目标、目录结构和推荐工作方式
  - 只保留少量必须知道的关键规则
- `SKILL.md`
  - 给 agent 看
  - 负责具体执行约束、字段规则、命令前置动作和冲突处理
  - 作为当前项目内更权威的操作约束
- `references/TroubleShooting.md`
  - 负责沉淀实操踩坑、边界案例和经过验证的处理方式

如果你只想快速理解这个仓库，看 `README.md`。
如果你要判断 agent 具体应该怎么做，以 `SKILL.md` 为准。

## 当前必须知道的最小规则

这些规则在 README 保留，是因为人类协作时最常用：

- `df.json` 里拿不准的字段不要猜，必须先和人确认。
- 不要默认输入一定是 `use.wavlist + text`，也可能是 `wav.scp`、`utt2spk`、`utt2domain` 等组合。
- 如果用户没有明确给出数据集名称，必须先问清楚，不能擅自命名。
- `source` 不能再笼统写“质量测试数据”，必须先区分为 `自主采集`、`生成` 或内部质量中心的 `badcase数据`。
- 实际数据集默认放 `datasets/`，示例或模板才放 `datasets.example/`。
- 可复用的公共脚本统一放仓库根目录 `scripts/`，并纳入 git 管理。
- 对测试集，`sf.jsonl` 生成后默认先运行：
  - `python3 scripts/validate_sf_jsonl.py <sf.jsonl路径>`
- 如果上传时报大量 `sample_id` 已注册，先停下来判断是否重复上传同一批数据，不要默认加前缀重传。
- 线上已有数据集要改标签或标注时，不要重建数据集：先 `ds-cli clone` 拿线上全量样本作底本，再走 `ds-cli update` → `ds-cli push` → `ds-cli release`。
- 每次成功上传一个新数据集后，都应把可公开复用的经验回写到 `SKILL.md` 或 `references/TroubleShooting.md`。

## 当前项目里的子代理

当前仓库已经沉淀了一个项目级子代理：

- `物理测试集管理器 / Physical Testset Manager`
  - 配置文件：`.codex/agents/physical-testset-manager.toml`
  - 模型：`gpt-5.4-mini`
  - reasoning：`high`

它的职责不是自己探索一个项目，而是消费主代理已经确认好的“单个物理测试集任务”，然后完成：

- 判断该任务属于 `WakeUp`、`ASR` 或 `FalseTrigger`
- 按完整交付风格制作一套测试集目录：
  - `original_dataset/`
  - `AGENTS.md`
  - `df.json`
  - `df.jsonl`
  - `make_sf_jsonl.py`
  - `sf.jsonl`
- 调用 `ds-cli` 尝试上传
- 若遇到平台枚举或白名单阻塞，只返回阻塞项，不擅自改业务字段

这套模式适合批量上传时的分工：

- 主代理负责拆边界、问用户、定字段
- 子代理负责单测试集执行

更细的字段约束、样本级规则和命令执行要求，统一放在 `SKILL.md` 中维护，不在 README 继续展开复制。

## 文档使用原则

线上正式文档不一定能在当前环境直接访问，所以仓库会把可公开的规范摘要沉淀到 `references/`。

使用时遵循两条原则：

- 优先看 `references/specs_20260325/` 中的结构化字段摘要。
- 优先使用后续沉淀出的摘要、精简版和结构化知识，不要直接依赖旧记忆或零散经验。

## 这个仓库推荐的工作节奏

当你要新建、制作或上传一个数据集时，最稳的节奏是：

1. 先确认数据集名称、任务类型、数据集类型和输入文件格式。
2. 再选择对应的 builder 或 porter skill。
3. 先制作 `df.jsonl / sf.jsonl / ef.jsonl`，或逻辑数据集目录 / JSONL 索引。
4. 对测试集，先跑公共校验脚本确认 `sf.jsonl` 没有互斥字段错误。
5. 再执行创建、上传、更新和推送。
6. 成功后，把本次踩坑和经验沉淀回仓库。

这套节奏的意义不是“流程看起来完整”，而是：

**让数据集工作从一次性操作，变成团队可以稳定复制的能力。**

## Git 与仓库约定

- `git commit` 信息尽量写清楚、写中文、写人能快速看懂的话。
- `datasets/` 下的实际数据集目录默认不进 git。
- 仓库主要沉淀的是规范、技能、流程和经验，而不是把大体量数据直接塞进版本库。

## 开源发布约定

- 不提交真实账号、token、内网入口、个人主目录、平台克隆缓存和未脱敏截图。
- 示例路径优先使用相对路径，必须写绝对路径时使用 `<DATASET_ROOT>` 这类占位符。
- 新增 Office、截图或下载页面缓存前，先清理作者信息、访问 token 和内部项目名。

## 大家怎么评价

<blockquote>
  <p><strong><em>"以前最怕的是规范记不住、字段填错、命令跑挂。现在把原始目录和要求说清楚，agent 基本能把制作、上传、校验一路接住，省掉很多来回确认。"</em></strong></p>
</blockquote>
<div align="right"><em>—— 数据工程同学</em></div>

<blockquote>
  <p><strong><em>"这个仓库最有价值的不是某一个脚本，而是把规范、skill、踩坑经验和上传流程都串起来了。新人接手的时候，不用再靠口口相传。"</em></strong></p>
</blockquote>
<div align="right"><em>—— 平台维护同学</em></div>

<blockquote>
  <p><strong><em>"数据集这类事情最烦的不是操作本身，而是细节多、容易漏。现在至少流程比较稳，返工明显少了。"</em></strong></p>
</blockquote>
<div align="right"><em>—— 语音项目同学</em></div>

<blockquote>
  <p><strong><em>"线上文档不总是方便访问，这个仓库把本地缓存、经验回写和常用流程整理好了，调试机环境下会安心很多。"</em></strong></p>
</blockquote>
<div align="right"><em>—— 日常使用者</em></div>
