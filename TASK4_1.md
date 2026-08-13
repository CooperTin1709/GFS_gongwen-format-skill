# V4 公文格式整理 Skill —— HiAgent Linux 路径兼容性紧急修复

你现在位于已经完成开发并可以在本地运行的 V4 公文格式整理 Skill 项目中。

这次不是功能重构。

这是一次**非常保守的跨平台兼容性 Hotfix**。

真实 HiAgent 平台测试发现：

Skill 已经成功加载，但 Qwen3 调用脚本时失败。

平台提示大意如下：

```text
检测到技能文件路径中存在 Windows 风格的反斜杠（\），
实际应为 Linux 路径分隔符 /。

已定位到类似：

/home/runner/skills/V4-gongwen-format-skill/scripts\main.py

实际应为：

/home/runner/skills/V4-gongwen-format-skill/scripts/main.py

main.py 文件实际存在，
但当前 Linux 环境无法通过错误路径正确调用。
```

因此当前最重要的目标是：

> 修复整个 Skill 中 Windows 专用路径写法，使部署 ZIP 在 HiAgent Linux 沙箱中可以可靠调用，同时绝不能破坏 V4 已经实现的公文格式能力。

------

# 一、本轮最高原则：功能冻结

本轮禁止无关重构。

除非为解决路径兼容性绝对必要，否则不要修改：

- classify.py 的公文分类逻辑；
- title / salutation / heading_1~4 / body / attachment / signature 类型规则；
- 落款识别逻辑；
- 数字 Times New Roman 逻辑；
- 两字符首行缩进逻辑；
- 字体 XML 设置；
- 固定值 30 磅行距；
- 段前 0 磅；
- 段后 0 磅；
- 主标题后空一行；
- 附件前空一行；
- Renderer 的文字内容保护；
- Validator 的格式验证要求；
- NEEDS_REVIEW 逻辑；
- Browser Text 输入架构；
- format_rules.json 中已经确认的业务规则。

特别禁止：

为了“顺便优化”而重写：

```text
classify.py
render_docx.py
validate.py
```

除非发现其中存在与路径相关的明确问题。

这一次应优先修改：

```text
SKILL.md
main.py
路径工具函数
README.md
打包逻辑
测试
```

以及其他真正包含错误路径的文件。

------

# 二、先定位真实根因，不要凭猜测修改

第一步请搜索整个仓库。

重点寻找：

```text
\
\\
scripts\
scripts\\
main.py
Path
os.path
subprocess
shell=True
cmd.exe
powershell
python.exe
```

同时检查：

```text
SKILL.md
README.md
AGENTS.md
scripts/
config/
references/
打包脚本
测试
```

特别检查 SKILL.md 中 Qwen3 实际会读取并执行的命令。

确认究竟是哪一处最终导致平台组合出：

```text
scripts\main.py
```

而不是：

```text
scripts/main.py
```

在修改前先明确根因。

不要在最终报告中只写：

“已替换反斜杠”。

必须说明：

**到底哪个文件、哪段逻辑或哪条 Skill 指令造成了错误。**

------

# 三、Skill 内所有可执行路径必须使用 POSIX / 跨平台写法

HiAgent 运行环境是 Linux。

所有给智能体实际执行的命令必须写成：

```text
scripts/main.py
```

禁止：

```text
scripts\main.py
```

禁止：

```text
.\scripts\main.py
```

禁止：

```text
C:\xxx\scripts\main.py
```

禁止在 SKILL.md 中出现 Windows 专用可执行路径。

------

# 四、SKILL.md 是本轮重点检查对象

Qwen3 能力有限，因此 SKILL.md 必须给出非常明确、机械化、Linux 兼容的调用方法。

不要让 Qwen3 自己拼接路径。

不要告诉模型：

```text
找到skill目录，然后自己拼接 scripts + main.py
```

更不要出现：

```text
scripts\main.py
```

应明确使用：

```text
scripts/main.py
```

如果平台的 Skill 运行机制允许从 Skill 根目录执行，则优先写：

```bash
python3 scripts/main.py ...
```

而不是硬编码：

```text
/home/runner/skills/V4-gongwen-format-skill/...
```

不要把：

```text
V4-gongwen-format-skill
```

这个目录名写死为部署依赖。

因为未来 Skill 包名称可能变化。

------

# 五、禁止硬编码 HiAgent 绝对路径

不要写：

```text
/home/runner/skills/V4-gongwen-format-skill/scripts/main.py
```

作为唯一运行方法。

真实部署目录可能变化。

优先：

```text
python3 scripts/main.py
```

或者使用当前 Skill 根目录解析出的路径。

如果必须在 Python 内部得到项目路径，应基于：

```python
Path(__file__).resolve()
```

推导。

例如逻辑上：

```python
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_ROOT / "config" / "format_rules.json"
```

不要：

```python
"C:\\..."
```

不要：

```python
"..\\config\\format_rules.json"
```

------

# 六、Python 内所有文件路径统一使用 pathlib

审计项目中所有：

- config 文件；
- work/output 目录；
- result.json；
- review.json；
- format_rules.json；
- 临时文件；
- output.docx；
- references；
- ZIP 打包路径。

优先使用：

```python
from pathlib import Path
```

例如：

```python
config_path = skill_root / "config" / "format_rules.json"
```

不要手工拼：

```python
root + "\\config\\format_rules.json"
```

也不要手工拼：

```python
root + "/config/format_rules.json"
```

Python 内部统一使用 Path 对象。

最终只有在：

- JSON 输出；
- subprocess 参数；
- 日志；

需要字符串时：

```python
str(path)
```

------

# 七、不要使用字符串 replace 修路径

禁止这种粗暴修复：

```python
path = path.replace("\\", "/")
```

作为主要解决方案。

这会掩盖真实架构问题，而且 Windows 输入路径中还有盘符等问题。

正确方案是：

```text
内部路径全部 pathlib
+
SKILL.md 调用命令全部 POSIX forward slash
```

只有明确处理外部非可信路径字符串时，才允许进行必要兼容。

------

# 八、检查 main.py 的资源路径

即使：

```text
scripts/main.py
```

能够启动，

main.py 内部还可能再次使用 Windows 路径访问：

```text
config\format_rules.json
```

所以必须检查整个运行链。

保证以下全部 Linux 可用：

```text
scripts/main.py
config/format_rules.json
references/format_spec.md
work/
output.docx
result.json
review.json
```

不能只修入口后又在第二步失败。

------

# 九、工作目录不能成为隐式假设

HiAgent 调用 Skill 时，current working directory 不一定永远等于 Skill 根目录。

因此 Python 内：

禁止大量依赖：

```python
Path.cwd()
```

来定位 Skill 自身资源。

例如不应写：

```python
Path("config/format_rules.json")
```

然后假设 cwd 一定正确。

对于 Skill 自身文件，应从：

```python
__file__
```

定位。

推荐统一：

```python
SKILL_ROOT = Path(__file__).resolve().parent.parent
```

然后：

```python
CONFIG_PATH = SKILL_ROOT / "config" / "format_rules.json"
```

这样无论从：

```text
/home/runner
```

还是：

```text
/home/runner/skills/xxx
```

启动，都能正确找到配置。

------

# 十、用户输出目录与 Skill 目录分开处理

Skill 自己的静态资源：

```text
SKILL_ROOT
```

用户任务输出：

使用 main.py 接收到的：

```text
output_dir
```

不要把所有生成文件都强制写进：

```text
/home/runner/skills/...
```

如果当前项目已有正确输出目录逻辑，请保持。

不要为了本轮修复修改成熟逻辑。

------

# 十一、subprocess 如非必要不要使用 shell=True

检查是否存在：

```python
subprocess.run("python scripts\\main.py ...", shell=True)
```

如果存在，应优先改成：

```python
subprocess.run(
    [sys.executable, str(script_path), ...],
    check=True
)
```

不要自行拼 shell command string。

如果项目根本不需要 subprocess：

不要新增。

------

# 十二、不要假设 Python 命令一定叫 python.exe

Skill 运行说明不得写：

```text
python.exe
```

Linux 平台通常使用：

```text
python
```

或：

```text
python3
```

SKILL.md 中优先采用平台已验证可执行的 Python 命令。

如果当前 HiAgent 已经确认：

```text
python3
```

可用，则使用：

```text
python3 scripts/main.py
```

如果现有平台运行方式使用：

```text
python
```

且已经验证，则保持。

不要无依据在二者之间大范围更换。

Python 内需要调用当前解释器时：

```python
sys.executable
```

优于硬编码。

------

# 十三、重点检查部署 ZIP

最终 ZIP：

```text
dist/gongwen-format-skill.zip
```

根目录仍必须直接包含：

```text
SKILL.md
README.md
config/
references/
scripts/
```

必须确认：

```text
scripts/main.py
```

ZIP member 名称使用：

```text
/
```

而不是：

```text
scripts\main.py
```

ZIP 标准内部路径应使用 POSIX `/`。

如果当前打包逻辑直接：

```python
zipfile.write(...)
```

请检查 `arcname`。

应显式保证：

```python
arcname = path.relative_to(package_root).as_posix()
```

避免在 Windows 本地打包时 ZIP 中保存错误风格路径。

这一点非常重要：

> 本地是在 Windows 上生成 ZIP，但 ZIP 最终在 Linux HiAgent 中展开。

------

# 十四、必须新增“ZIP路径兼容性测试”

由于当前 Bug 就出现在：

```text
Windows开发
→ ZIP
→ Linux部署
```

所以必须新增回归测试。

测试生成 ZIP 后，读取：

```python
zipfile.ZipFile(...)
```

检查：

所有 member name：

不得包含：

```text
\
```

例如必须有：

```text
scripts/main.py
config/format_rules.json
```

不能有：

```text
scripts\main.py
config\format_rules.json
```

如果任何 ZIP member 含：

```text
\
```

测试必须失败。

------

# 十五、必须增加 Skill 文本路径审计测试

自动检查部署必需文本文件，至少：

```text
SKILL.md
README.md
```

确保没有实际执行命令使用：

```text
scripts\main.py
```

或：

```text
.\scripts\
```

可以通过针对执行路径的精确检查实现。

不要因为参考文字里出现“Windows反斜杠”说明就误报。

测试重点是：

**当前可执行调用示例。**

------

# 十六、增加 Linux 风格启动测试

即使当前 Codex 运行在 Windows，

也要构造一个不依赖 Windows 分隔符的测试。

使用 Python：

```python
sys.executable
```

和：

```python
Path
```

调用：

```text
scripts/main.py
```

不要通过 PowerShell 特有命令。

例如测试逻辑：

```python
subprocess.run(
    [
        sys.executable,
        str(skill_root / "scripts" / "main.py"),
        ...
    ],
    cwd=temp_dir,
    ...
)
```

重点：

`cwd` 故意设置为：

```text
非Skill根目录
```

然后验证 main.py 仍然能够找到：

```text
config/format_rules.json
```

这可以直接发现隐含 cwd 依赖。

------

# 十七、必须测试中文/空格路径

为了提高鲁棒性，再测试 Skill 被放到：

```text
临时目录/公文 格式 Skill/
```

这种：

- 中文；
- 空格；

路径下。

程序仍应可以：

```text
读取配置
处理Browser文本
生成DOCX
validate SUCCESS
```

不要自己手工拼命令字符串。

------

# 十八、本轮禁止重新调整公文业务逻辑

再次强调：

不要因为看到旧代码可以“更优雅”，就改：

```text
signature detection
digit runs
firstLineChars
classification threshold
title detection
blank policy
```

当前用户已经验证：

> V4 在本地基本功能可用，当前阻塞是 HiAgent Linux 路径。

因此：

**功能稳定 > 代码美观。**

如果某个业务模块和本次路径 Bug 没有关系：

不要碰。

------

# 十九、V3作为行为底线

如果当前仓库/本地能够找到 V3 的：

- 测试结果；
- 样例；
- 输出；
- tag；
- commit；
- ZIP；

可以作为回归参考。

但：

不要把 V3 代码整体复制回来。

目标是：

```text
V4现有功能
+
修复Linux部署路径
```

而不是：

```text
重新做一个V3.5
```

------

# 二十、原有全部关键需求必须继续通过

修复后完整回归以下行为：

## 输入

```text
HiAgent Browser纯文本
```

仍为合法输入。

------

## title

```text
方正小标宋简体
22pt
居中
固定30磅
段前0
段后0
无首行缩进
```

标题后恰好一个空白段。

------

## salutation

例如：

```text
行领导：
XX部门：
```

应：

```text
仿宋_GB2312
16pt
左对齐
无首行缩进
固定30磅
段前0
段后0
```

------

## heading_1

```text
黑体
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

------

## heading_2

```text
楷体_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

------

## heading_3

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

------

## heading_4

同样：

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

------

## body

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

------

## attachment

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

附件前恰好空一行。

------

## signature

典型：

```text
数据管理部
2025年8月12日
```

必须：

```text
两个段落均 classification=signature
仿宋_GB2312
16pt
RIGHT
无首行缩进
固定30磅
段前0
段后0
```

------

## 数字

所有阿拉伯数字：

```text
Times New Roman
```

字号继承所在段落。

------

## Normal Style

```text
space_before=0
space_after=0
```

------

## 内容完整性

Browser 输入非空段落：

```text
==
```

输出 DOCX 非空段落。

必须：

```text
数量一致
顺序一致
逐字符一致
```

------

# 二十一、不要降低 Validator

如果路径修复后测试失败：

不能通过以下方式解决：

- 删除测试；
- 放宽 Validator；
- 跳过 XML 检查；
- 关闭内容完整性；
- 将错误变 warning；
- 不检查 signature；
- 不检查段距；
- 不检查数字字体。

必须修真实问题。

------

# 二十二、SKILL.md 针对 Qwen3 的路径调用要特别简单

Qwen3 能力有限。

所以执行步骤不要写成复杂说明。

应该类似：

```text
当 Browser 已返回完整公文文本时：

1. 将 Browser 返回的完整文本作为 source_text。
2. 调用公文格式处理入口。
3. 使用 Linux 路径，脚本路径必须是 scripts/main.py，不使用反斜杠。
4. 如果 status=SUCCESS，返回 output_file。
5. 如果 status=NEEDS_REVIEW，只处理 review_file 中的少量候选项。
6. 不尝试下载原DOCX。
7. 不自行修改正文。
```

不要让 Qwen3：

- 猜 Skill 根目录；
- 自己转换 Windows/Linux 路径；
- 自己找 main.py；
- 自己修脚本。

------

# 二十三、如果 Skill 平台支持相对路径，优先相对路径

优先：

```text
scripts/main.py
```

而不是：

```text
/home/runner/skills/xxx/scripts/main.py
```

如果 SKILL.md 当前调用机制必须包含 Skill 根路径变量，

请使用平台实际支持的方式。

但是不要发明不存在的：

```text
$SKILL_DIR
```

除非当前 Skill 平台明确提供。

如果平台没有 Skill root 变量：

保持最简单、当前平台可执行的相对路径方式。

------

# 二十四、本轮测试必须实际运行

执行：

```bash
python -m unittest discover -s tests -v
```

使用当前环境正确 Python 命令。

所有原测试 + 新增 portability 测试必须通过。

------

# 二十五、真实 E2E 仍必须跑

使用已有：

```text
samples/browser_input.txt
```

或当前正式 Browser fixture。

执行整个：

```text
Browser text
→ main
→ classify
→ render
→ validate
→ output.docx
```

必须：

```text
SUCCESS
```

不能因为这次只修路径就省略 E2E。

------

# 二十六、额外执行“非项目根目录启动”E2E

非常重要。

从一个与 Skill 根目录不同的位置运行 main.py。

例如 Python 测试中：

```text
cwd = 临时目录
```

调用：

```text
<skill_root>/scripts/main.py
```

确认程序仍能找到内部 config。

这个测试直接针对 HiAgent 环境。

------

# 二十七、打包后重新解压测试

最终生成 ZIP 后：

不要只检查 ZIP 存在。

自动：

```text
创建临时目录
→ 解压dist ZIP
→ 检查目录
→ 从非Skill cwd启动
→ 运行Browser Text E2E
```

也就是说测试的是：

**真正要上传 HiAgent 的 ZIP 内容。**

不是源代码仓库。

这点非常重要。

------

# 二十八、解压部署包必须验证

解压之后必须有：

```text
SKILL.md
scripts/main.py
config/format_rules.json
```

而且：

```text
scripts/main.py
```

真实可被 Python打开。

不要依赖 Linux execute bit：

因为调用方式应该是：

```text
python3 scripts/main.py
```

不是：

```text
./scripts/main.py
```

所以一般不需要脚本本身具有 executable bit。

截图中的：

“确保Python脚本具有可执行权限”

不是当前最优修复方向。

**核心问题是路径。**

------

# 二十九、不要为了截图提示去加入 chmod 依赖

除非 HiAgent 明确要求：

```text
./main.py
```

否则不要增加：

```text
chmod +x
```

流程。

我们使用：

```text
python3 scripts/main.py
```

时，只需要文件可读。

Windows 打 ZIP 时 Unix execute bit 还会增加额外兼容复杂度。

所以本轮：

**不把 executable permission 当核心方案。**

------

# 三十、重新生成部署 ZIP

最终生成：

```text
dist/gongwen-format-skill.zip
```

或者保留当前正式命名。

不要无意义从 V4 改 V5。

部署包内：

```text
SKILL.md
README.md
config/
references/
scripts/
```

如果当前平台要求其他元数据，保持。

ZIP 内所有路径：

```text
POSIX /
```

------

# 三十一、Git diff 严格审查

修改完成后执行：

```text
git diff
```

本轮理想 diff 应该相对集中。

如果发现大量：

```text
classifier重写
renderer大规模变化
格式规则重写
测试fixture全部重写
```

请重新评估。

除非有充分必要原因，否则撤销无关修改。

目标：

> 最小改动解决部署路径问题。

------

# 三十二、最终验收要求

只有全部满足才允许完成。

## HiAgent路径

部署 Skill 中不再有实际运行路径：

```text
scripts\main.py
```

而是：

```text
scripts/main.py
```

------

## Python内部

内部资源路径全部跨平台。

不能依赖 Windows separator。

不能依赖 cwd 等于 Skill 根目录。

------

## ZIP

ZIP member 全部使用：

```text
/
```

不得有：

```text
\
```

------

## 解压E2E

最终 ZIP 解压后：

从 Skill 外部 cwd 调用仍能：

```text
SUCCESS
```

------

## 业务功能

所有原有公文功能完整回归通过。

------

# 三十三、最终报告必须回答

完成后请明确报告：

1. 本次 HiAgent 报错的真实根因；
2. 哪个文件/哪条指令产生了 `scripts\main.py`；
3. 修改了哪些文件；
4. 有没有修改任何公文业务逻辑；
5. 如果修改了，为什么绝对必要；
6. SKILL.md 最终如何调用 main.py；
7. 是否存在硬编码 `/home/runner/...`；
8. Python 内资源路径如何定位 Skill Root；
9. 是否依赖当前工作目录；
10. ZIP 中 `scripts/main.py` 的真实 member name；
11. ZIP 是否存在任何包含反斜杠的 member；
12. 从非 Skill cwd 启动测试是否通过；
13. 中文+空格路径测试是否通过；
14. 解压最终 ZIP 后 E2E 是否通过；
15. 原 unittest 总数；
16. 所有 unittest 是否通过；
17. Browser Text E2E 是否 SUCCESS；
18. title 回归是否通过；
19. heading 1~4 回归是否通过；
20. 两字符缩进是否通过；
21. Times New Roman 数字是否通过；
22. signature 右对齐是否通过；
23. 段前段后0是否通过；
24. 固定30磅是否通过；
25. 内容逐字符完整性是否通过；
26. NEEDS_REVIEW 是否通过；
27. 最终部署 ZIP 路径。

如果任何业务回归测试失败：

继续修复。

绝不能通过降低 V4 原有验收要求来解决。

最终目标：

**保持当前 V4 已经验证可用的所有公文功能完全不变，只修复 Windows 开发环境 → HiAgent Linux Skill 沙箱之间的路径兼容问题，让最终部署 ZIP 可以在 Linux 中稳定执行 scripts/main.py。**