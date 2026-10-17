# pre-commit.md — 提交前检查清单

> AI 每次交付改动前逐条自查；宿主提交前复核。
> 风格参考 `D:/github_clone/MyWorkSpace/pre-code.md`。

1. 如果遇到 **pip install（新增依赖）**，禁止自行安装，应当停下并 QQ 通知宿主手动安装（依赖一律装进 `.venv`，禁止全局安装）。
2. 如果 **Git 有尚未提交的内容**，且和当前任务无关或关联不大，应当停下并 QQ 通知宿主手动提交。
3. **静态核对全过**（AI 侧唯一验收手段）：
   - 改动的 `.py` 文件 `python -m py_compile` 0 错误；
   - 已有 pytest 用例 0 失败（如已建测试）；
   - grep 确认改动全部落地（同文件批量修改后必须全量复查，防丢更新）。
4. **视觉/样式/交互改动**：AI 不代验、不启动 GUI/浏览器验证，交付时明确标注「待宿主目视确认」。
5. 交付时给出**建议的提交信息**（Conventional Commits：`feat:` / `fix:` / `docs:` / `refactor:` / `chore:`，必要时按模块拆分提交建议）；`git commit` 由宿主执行。
6. 涉及打包的改动（依赖、入口、资源文件），须确认 `build.bat` 流程仍然成立（venv 创建 / requirements / pyinstaller 参数）。
7. 未触碰 `AGENTS.md` 第 5 节红线（尤其：不重复造轮子、不硬编码色值、不改写 git 历史）。
