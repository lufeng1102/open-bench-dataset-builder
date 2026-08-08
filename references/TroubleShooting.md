# TroubleShooting

本文件只记录可公开复用的排障模式。不要写入真实账号、token、内网 IP、个人路径、平台私有 URL、客户项目名或未脱敏截图。

## 快速定位

1. 先确认数据集类型：物理测试集、物理训练集或逻辑数据集。
2. 再确认失败阶段：样本生成、JSON 校验、`ds-cli create`、`add/update/rm`、`push`、`release`、`clone/version`。
3. 保存最小必要日志，不保留含路径、账号、token 的完整终端截图。

## 样本文件校验失败

常见原因：

- `attribute.file_type` 写成文件后缀，例如 `wav`，应写类型，例如 `audio`。
- `transcription.keyword` 和 `transcription.text` 同时存在。
- `timestamp` 与 `keyword + repeat_times` 同时存在。
- `timestamp.end_time` 写成 `null`。
- 空对象被保留下来，例如空 `speaker`、`custom`、`sample_info`。

处理方式：

```bash
python3 scripts/validate_sf_jsonl.py <sf.jsonl路径>
```

校验没过时，先修 `make_sf_jsonl.py`，重新生成 `sf.jsonl`，不要直接手改上传文件。

## 输入路径不可达

如果原始清单记录的是旧机器绝对路径：

- 先在当前数据目录查找同名文件。
- 若 `original_dataset/wavs/` 或同类目录下存在同名 wav，生成 `sf.jsonl` 时优先回退到该相对路径。
- 若没有可达文件，暂停并向用户确认源数据位置。

开源示例中不要写本机私有绝对路径，优先写相对路径。

## 代理或网络异常

每一条 `ds-cli` 命令前都重新清理代理环境变量：

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY
```

不要假设父 shell 或上一条命令已经清过。若仍然失败，再判断是网络、权限、平台服务还是字段校验问题。

## 枚举或白名单失败

如果平台提示 `wakeup_words`、`application_domain`、`category`、`product_info.brand` 等枚举无效：

- 不要把真实业务字段改成 `未知` 或其它已有值来绕过。
- 汇总同一批任务中所有需要补充的枚举，一次性交给用户确认。
- 由用户在平台枚举管理入口 `<ENUM_ADMIN_URL>` 补充规则，或明确要求改用已有合法枚举后再重试。

## sample_id 冲突

如果平台提示样本 ID 已注册：

- 先判断冲突规模和来源，尤其关注是否整批数据重复上传。
- 大量冲突或来源不清楚时暂停，让用户确认是否继续作为新数据集保留。
- 只有确认不是重复数据集时，才按可追溯规则重生 `sample_id`，例如 `<dataset_prefix>__<origin_sample_id>`。
- 不要默认用 `--ignore` 跳过冲突样本，否则容易把数据集做残。

## 已有数据集补传或修改

线上已有数据集需要修改时：

1. `ds-cli clone <平台数据集名>` 获取工作目录。
2. 以克隆出的全量描述或样本为底本修改。
3. 数据集级字段用 `ds-cli update -df`。
4. 样本级标注用 `ds-cli update -sf`。
5. 修改后执行 `ds-cli push`。
6. 需要正式版本时执行 `ds-cli release`，再用 `ds-cli version` 确认。

不要因为本地缓存目录缺失就重新创建同名数据集。

## push 中断或发布耗时

- 大体量 `push` 建议落盘日志，避免管道吞日志。
- 如果进程静默退出，检查本地缓存变更目录是否还有待推分片；必要时重新执行 `ds-cli push`。
- `release` 通常是异步流程，返回申请成功不代表正式版本已完成。
- 以 `ds-cli version` 中“最新版本号 == 最新正式版本号”作为发布完成依据。

## 附加文件

- 没有附加文件时不要上传空 `ef.jsonl`。
- 追加目录时先生成非空 `ef.jsonl`，每行形如 `{"path":"..."}`。
- 同名附加文件会在新版本中替换旧文件。
- 删除源文件或改软链前，先比对源文件和平台副本的大小与哈希。

## 开源前检查

发布前至少运行：

```bash
rg -n --hidden -g '!.git' -i "(api[_-]?key|secret|token=|password|passwd|authorization|bearer|private[_ -]?key|access[_-]?key|-----BEGIN|/Users/|/home/|/mnt/|10\\.|172\\.16\\.|192\\.168\\.)"
```

命中后逐条判断。示例字段名可以保留，真实凭据、内部入口和个人路径必须删除或改成占位符。
