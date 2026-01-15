---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*)
summary: 读取最近的 git 更改作为上下文准备
description: 此命令读取最近的 git 更改，包括：当前 git 状态、最新的 commit 记录、未暂存和已暂存的更改，帮助大模型了解项目的最新状态。
  使用场景：
  - 在开始新的开发任务前了解项目状态
  - 在代码审查前查看变更内容
  - 在调试前了解最近的修改
  - 在切换回项目时快速了解进展
---

# 读取最近的 git 更改

请帮我读取项目的最近 git 更改，包括：

1. **当前 git 状态** - 查看工作目录和暂存区的状态
2. **最近的 commit 记录** - 查看最新的提交历史
3. **未暂存的更改** - 查看工作目录中未暂存的修改
4. **已暂存的更改** - 查看已暂存但未提交的修改

这些信息将帮助我了解项目的当前状态，为后续的问题回答提供必要的上下文背景。

请使用 `git status`、`git log --oneline -10`、`git diff` 和 `git diff --cached` 等命令来获取这些信息。
