# TED_pre_master

面向中文课堂汇报、研究分享、技术解释与公开演讲的写作技能。研究 TED 一手指导和六种演讲样本，依据听众、证据与现场时间安排讲述次序，并完成口语修订。

独立开源项目。`TED_pre_master` 是仓库与显示名称，兼容 Codex 的技能标识为 `ted-pre-master`。

## 使用

```text
请使用 $ted-pre-master。
听众：学过基础概率的本科生。
时长：15分钟，包含演示与切换。
任务：先解释四种随机性检查，再讨论区间估计。
重点：为什么采用这些方法，尤其是重叠窗口和模拟参照。
语气：平实、自然，依据附件事实，避免虚构经历。
交付：完整讲稿、简短画面提示和时间安排。
```

也可直接要求修改一段、审查既有稿或准备删减版本。技能会优先利用已提供的资料，并按当前任务决定是否需要补充信息。

## 安装

需要 Python 3.10 或更高版本。克隆后运行安装脚本，目标目录已存在时会停止，方便先检查原版本。

```powershell
git clone https://github.com/LeoAndJellyfish/TED_pre_master.git
cd TED_pre_master
python scripts/install_skill.py
```

默认安装到 `~/.codex/skills/ted-pre-master/`。也可用 `--dest` 指定目录。发布版ZIP内的 `ted-pre-master/` 同样可以解压到技能目录。

## 内容

- [技能入口](SKILL.md)：按任务选择起稿、修订、重点处理或研究说明。
- [TED研究依据](references/ted-evidence.md)：当前官方指导、六种作品定位、观察与编辑判断。
- [结构设计](references/architecture.md)：观点、理解前提、可选路径、图表和收尾。
- [中文口语编辑](references/spoken-chinese.md)：声线、具体动作、句群、节奏与原创改写。
- [事实与排练](references/facts-and-rehearsal.md)：来源反查、数字归属、时间与现场检查。
- [行为评测协议](evaluation/protocol.md)：真实性、推理、听众、声线、时间及任务约束。

## 排练检查

```powershell
python scripts/speech_check.py 讲稿.md --section 讲稿正文
python scripts/speech_check.py 讲稿.md --section 讲稿正文 --cpm 230 --forbid "不意味着"
```

工具报告可读字符、明确舞台耗时和用户指定的词句命中。`--cpm` 使用讲者按同一计数口径试读所得的速度；输出时长为估算。讲稿的事实与理解效果分别接受来源核对和试讲检验。

舞台提示示例：`[停顿 2秒]`、`[演示 20秒]`、`[画面：指向第三个窗口]`。附录放在“讲稿正文”章节之外，便于独立计数。

## 开发验证

```powershell
python -m unittest discover -s tests -v
python scripts/validate_package.py
python scripts/build_release.py
```

测试覆盖计数和舞台提示、资源完整性、发布包复现及安装行为。行为评阅记录与测试结果分别报告。真实讲者的语速、声线及现场理解反馈用于最终排练。

原始工具、文档和示例采用 [MIT许可](LICENSE)。TED来源保留各自的权利；仓库提供原创分析、简短定位与来源链接。
