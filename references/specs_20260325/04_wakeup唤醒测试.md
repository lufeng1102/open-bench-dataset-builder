# wakeup唤醒测试 结构化摘要

- 来源：`references/测试数据标签管理v20260325更新.xlsx`
- 对应文件：`04_wakeup唤醒测试.md`
- 适用任务：`WakeUp`
- 使用顺序：先读 `01_数据通用维度标签.md` 和 `02_业务维度标签.md`，再读当前任务 sheet。
- 表内分段标记：`数据通用维度标签`、`本测试任务特有标签`

## 必填字段速览
- audio.tag
- audio.audio_format
- audio.generation
- audio.speech.language
- audio.speech.dialect
- audio.speech.anno_method
- audio.speech.preprocessing_method
- audio.acoustic.device
- audio.acoustic.channels
- audio.acoustic.sample_rate
- audio.acoustic.mics
- audio.acoustic.mic_id
- audio.acoustic.refs
- audio.acoustic.ref_id
- audio.acoustic.mic_type
- audio.acoustic.array_type
- audio.acoustic.array_spacing
- source
- data_generate_time
- tag
- info
- test_content
- wakeup_words
- test_date
- data_user

## 通用维度字段

| 字段路径 | 标签名称 | 必填 | 枚举/取值摘要 | 备注 |
| --- | --- | --- | --- | --- |
| audio.tag | - | Y | silence / speech / noise / music / audio_event / other | - |
| audio.audio_format | - | Y | ogg / mp3 / wav / flac / pcm / opus / aac / m4a / 混合 | - |
| audio.generation | - | Y | record（原始录制） / real(真人交互体验) / synthetic(人工合成) / augment(数据增强) / other（其他） | - |
| audio.voice_length_type | - |  | 短语音 / 长语音 / 未知 / 混合 | - |
| audio.speech.style | - |  | 自然人声 / 自然环境音 / 清晰合成音 / 机械/机器人音 / 伪影/电音失真 / 未知 | - |
| audio.speech.genre | - |  | 对话 / 娱乐 / 采访 / 唱歌 / 戏剧 / 电影 / 视频博客 / 直播 / 演讲 / 剧集 / 朗诵 / 广告 / 动物叫声 / 枪声 / 未知 | - |
| audio.speech.language | - | Y | zh / en / es / fr / ja / ko / pt / ru / sv / de / ... | - |
| audio.speech.dialect | - | Y | tts_putonghua / unknown / dialect / accent / putonghua / kouyin-beijing / ... | - |
| audio.speech.sentiment | - |  | 开心 / 嫌弃 / 不安 / 伤心 / 生气 / 惊奇 / 讽刺 / 中性 / 未知 | - |
| audio.speech.sensitive_information | - |  | 无敏感信息 / 色情不适宜 / 仇恨言论 / 暴力 / 政治敏感 / 含敏感个人信息 / 已脱敏 | - |
| audio.speech.anno_method | - | Y | manu（人工） / other（其它） | - |
| audio.speech.preprocessing_method | - | Y | raw / aec / sep | - |
| audio.noise.style | - |  | add (叠加噪声) / conv(卷积噪声) | - |
| audio.noise.genre | - |  | 外部环境噪声 / 设备噪声 | - |
| audio.music | - |  | 自定义 | - |
| audio.voiceprint.speaker_gender | - |  | 男 / 女 / 儿童 / 老人 / 多性别组合 / 未知 | - |
| audio.voiceprint.speaker_count | - |  | 单人 / 双人 / 多人 / 嘈杂人群 / 未知 | - |
| audio.acoustic.sstc | - |  | 连续稳态 / 间歇性 / 瞬态突发 / 周期性 | - |
| audio.acoustic.clarity_intelligibility | - |  | 极清晰 / 清晰 / 沉闷/模糊 / 难以分辨 / 乱码/无法听懂 | - |
| audio.acoustic.device | - | Y | phone(手机录制） / hifi（高保真） / ondevice（嵌入式内置设备录制） / array(麦克风阵列) | - |
| audio.acoustic.distance | - |  | near / far | - |
| audio.acoustic.background | - |  | quiet / noisy / mix | - |
| audio.acoustic.snr_estimation | - |  | high(>20db高信噪比) / medium(10~20db中信噪比) / low(0~10db低信噪比) / very_low(<0db极低信噪比) | - |
| audio.acoustic.channels | - | Y | 1 / 2 / 3 / 4 / 5 / 6 / ... | - |
| audio.acoustic.sample_rate | - | Y | 8000 / 16000 / 24000 / 32000 / 48000 / 44100 / 22050 / 96000 | - |
| audio.acoustic.mics | - | Y | 1 / 2 / 3 / 4 / 5 / 6 / ...... | - |
| audio.acoustic.mic_id | - | Y | 1 / 2 / 3 / 4 / 5 / 6 | - |
| audio.acoustic.refs | - | Y | 0 / 1 / 2 / 3 / 4 / 5 / 6 | - |
| audio.acoustic.ref_id | - | Y | 0 / 1 / 2 / 3 / 4 / 5 / 6 | - |
| audio.acoustic.mic_type | - | Y | 数字麦 / 模拟麦 / 指向麦 / 其他 | - |
| audio.acoustic.array_info | - |  | 自定义 | - |
| audio.acoustic.array_type | - | Y | 单麦 / 线麦 / 环麦 / 车载分布式 / 其他 | - |
| audio.acoustic.array_spacing | - | Y | 60 / 55 / 70 / 80 / 35 / 0 / 30 / 26 | - |

## 数据集公共字段

| 字段路径 | 标签名称 | 必填 | 枚举/取值摘要 | 备注 |
| --- | --- | --- | --- | --- |
| type | 数据模态 |  | - | - |
| source | 数据来源 | Y | 购买 / 生成 / 自主采集 / 公开数据 / 云端业务数据回流 / 本地业务数据回流 / 私有化业务数据回流 / badcase数据 / 历史未知数据 | - |
| source_ds_id | 父数据集ID |  | 数据集ID | - |
| data_generate_time | 数据产生时间 | Y | 2023年以前 / 2023年 / 2024年 / 2025年 / 2026Q1 / 2026Q2... ... / 未知 | - |
| pms_id | pms_id |  | - | - |
| tag | 数据集标签 | Y | 定制 / 通用 or 公司 / 学术 | - |
| info | 数据集文字描述 | Y | 自定义 | - |

## 任务特有字段

| 字段路径 | 标签名称 | 必填 | 枚举/取值摘要 | 备注 |
| --- | --- | --- | --- | --- |
| test_content | 测试内容 | Y | 唤醒定位 / 小音量 / 快语速 / 近似词 / 首次唤醒 / 客观正例 / 主观正例 / 混合唤醒 / 口音唤醒 / 方言唤醒 | - |
| wakeup_words | 唤醒词条 | Y | 无 / 你好仰望 / 哈喽大众 / 小依同学 / 你好吉米 / .......... | - |
| test_date | 测试日期 | Y | 20251210 | - |
| data_user | 数据使用方 | Y | 业务使用 / 研究使用 / 客户使用 | - |

## 使用提示

- 当前 sheet 明确增量字段：test_content, wakeup_words, test_date, data_user。
- 若任务 sheet 里的通用字段与 `01`/`02` 重复，执行时仍应以三者组合判断，不要只看当前文件。
- 物理训练集和逻辑数据集不适用这套 sheet。
