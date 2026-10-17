# AGENTS.md — PictureSticker 截图工具 操作宪章

> 本文件是 AI 编程助手与本仓库开发者的**操作契约**。所有改动（代码、构建、文档）均须遵守本文约定。

## TL;DR（太长了不看）

1. 本仓库是 **Python 3.14 + PySide6** 的 Windows 截图工具（桌面悬浮球 / 全屏选区截图 / 选区编辑 / 钉图窗口），改动完成前必须通过**静态核对**（见第 2 节）。
2. **模块化高复用是硬性要求**：颜色选择器、滑块行、弹出工具条、遮罩层等同类控件只允许存在一份实现（见第 5 节红线第 5 条）。同类功能（如多处颜色调整）一律参数化复用，禁止复制粘贴式新写。
3. **严禁 AI 执行 `git commit`**（提交仅由宿主执行），已有提交一律保留不撤回（详见第 5 节红线第 1 条）。
4. **AI 不得自行开浏览器或启动 GUI 做视觉验证**。PySide6 界面的视觉/交互由**宿主运行程序目视核验**；AI 的验收手段仅限静态核对（`py_compile` / 测试 / grep），静态结论不得当作视觉验收结论上报，必须标注「待宿主目视确认」。

---

## 1. 项目身份与边界

| 维度 | 事实 |
| --- | --- |
| 定位 | Windows 桌面截图工具：悬浮球入口、全屏截图选区（未选择/未确定/已选择三态）、选区编辑（形状/箭头/画笔/文本/马赛克）、钉图窗口管理（拖动/缩放/多选/绑定/右键菜单） |
| 技术栈 | **Python 3.14**（系统解释器 `C:\Python314\python.exe`）+ **PySide6**（Qt6 绑定，UI 与绘图基座）+ **pywin32**（Win32 API：窗口检测、剪贴板增强）+ **PyInstaller**（打包 exe） |
| 运行环境 | 一律使用项目 venv `.venv\`（`build.bat` 会自动创建）；**禁止全局 pip install** |
| 入口 | `main.py`（启动悬浮球） |
| 设计规范 | [`DESIGN.md`](./DESIGN.md)（唯一样式依据）；需求原型 [`design-mockup.html`](./design-mockup.html)；任务分期 [`STAGE.md`](./STAGE.md) |
| 打包 | `build.bat` → PyInstaller `--onefile --windowed` → `dist\PictureSticker.exe` |
| AI 职责范围 | 功能开发、Bug 修复、组件/结构重构、构建脚本维护、文档维护；静态核对 |
| AI 不负责 | 提交 git、发布、推送远程（由宿主执行）；**开浏览器 / 启动 GUI 做视觉核验**（由宿主目视执行） |

---

## 2. 常用命令

| 场景 | 命令 |
| --- | --- |
| 创建 venv（首次） | `C:\Python314\python.exe -m venv .venv`（`build.bat` 自动做） |
| 安装依赖 | 激活 `.venv` 后 `pip install -r requirements.txt`；**新增依赖须先停下 QQ 通知宿主**（见 `pre-commit.md`） |
| 开发运行 | `.venv\Scripts\python main.py` |
| 打包 | `build.bat`（双击或命令行执行，产出 `dist\PictureSticker.exe`） |
| 验收（AI 侧，唯一允许的手段） | `.venv\Scripts\python -m py_compile <改动文件>`（0 错误）+ pytest（如已建测试，0 失败）+ grep 核对改动落地。**AI 不得开浏览器或启动 GUI 做任何验证** |
| 验收（宿主侧·视觉/交互） | 由宿主运行 `main.py` 目视核验，AI 不代劳、不代测 |

---

## 3. 架构与模块约定

预期目录结构（随 STAGE.md 阶段逐步建立）：

```
main.py              # 入口
ui/theme.py          # 设计令牌唯一来源（对应 DESIGN.md 第 1 节）
ui/widgets/          # 通用复用组件（ColorSwatches / SliderRow / Seg / ToolPopover / Switch …）
ball/                # 悬浮球 + 设置面板
capture/             # 全屏覆盖层、选区状态机（None/Pending/Selected）、编辑器与撤销栈
pin/                 # 钉图窗口、分组绑定、右键菜单
core/                # 剪贴板、Win32 窗口检测、截图抓取
```

- **复用组件规则**：`ui/widgets/` 里的组件是唯二实现——第二处需要同类控件时必须复用并参数化，不允许新写平行实现。
- 设计令牌（色值/字体/圆角/阴影）只写在 `ui/theme.py`，组件一律引用 token，**禁止硬编码色值**。
- 选区状态机枚举统一放 `capture` 模块，钉图多选/分组状态集中管理，不散落局部变量。

---

## 4. 决策树（增改功能的入口）

- **新增编辑工具**：在 `capture/editor` 注册工具项（图标/名称/二级面板配置），复用 `ToolPopover` 组装二级面板。
- **新增颜色参数**：直接复用 `ColorSwatches`（传入默认色），禁止新写色板。
- **新增滑块参数**：复用 `SliderRow`（传 min/max/默认值）。
- **新增设置项**：在 `ball/settings` 面板分区追加，持久化项走统一 settings 存取。
- **新增钉图右键菜单项**：改 `pin/menu` 的菜单定义表（单选/多选两张表）。
- **改样式**：先改 `DESIGN.md`，再同步 `ui/theme.py`。

---

## 5. 红线

1. **禁止 AI 提交 git**：`git commit` 仅能由宿主执行，AI 不得提交（`git add` 暂存亦须经宿主确认）。已有提交一律保留，不得撤回 / reset / rebase 改写历史。AI 只负责把工作区留到可通过静态核对的状态，并给出建议的提交信息。
2. **禁止 AI 自行开浏览器或启动 GUI 做验证**：包括无头/有头浏览器、Playwright/Puppeteer、任何截图或像素测量工具，以及运行 PySide6 程序进行「跑一下看看」。视觉/交互由宿主目视核验；AI 验收仅限静态核对，且须标注「待宿主目视确认」。
3. **禁止全局 pip install**：所有依赖装进 `.venv`；新增依赖前停下并 QQ 通知宿主（见 `pre-commit.md`）。
4. **禁止改写 git 历史**、禁止 `git push -f`。
5. **禁止重复造轮子**：同类 UI 控件（颜色选择、滑块、弹出面板、开关等）只允许一份实现，位于 `ui/widgets/`，其余处引用。
6. **禁止硬编码色值**：一律引用 `ui/theme.py` 的设计令牌。
7. 任何改动交付前必须完成 `pre-commit.md` 的检查清单。

---

## 6. Git 工作流

- 本机当前分支直接开发；**提交、推送远程均由宿主执行**（红线第 1 条）。
- Conventional Commits：`feat:` / `fix:` / `docs:` / `refactor:` / `chore:`（例 `feat(capture): 选区状态机支持 hover 待定选区`）。
- AI 交付方式：改动留在工作区 → 完成静态核对 → 在回答里给出建议的提交信息，由宿主自行提交。
- 提交前（宿主侧）：`pre-commit.md` 清单全过、未触碰红线、只提交相关文件（不含 `.venv/` `build/` `dist/` `__pycache__/`）。

---

## 7. 质量规范

- Python 代码带类型注解（函数签名必注）；遵循 PEP 8。
- 每个改动是**能运行、逻辑自洽的完整状态**；不留死代码、不留未用 import。
- 修 bug 时优先把根因沉淀为可复现的回归用例（纯逻辑部分用 pytest）。
- Qt 对象跨线程操作禁止（截图/剪贴板操作回主线程执行）。

---

## 8. 文档更新契约

1. **冲突即提示**：本文与代码不一致时（Python 版本、目录、命令），必须主动指出并说明以代码为准还是改本文。
2. **保持精简**：每条规则须能被「是否遵守」直接检查。
3. **变更记录**：改本文后由宿主提交，提交信息用 `docs(agents): ...` 并一句话概括。
