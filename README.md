# MCP 智能记忆服务器 (mcp-memory-server)

这是一个基于官方 Python MCP SDK 实现的智能记忆服务器，能够帮助 AI 助手持久化记忆，并自动分类。

## ✨ 核心功能
1. **智能分类**：自动判断记忆属于“事实”、“偏好”还是“日程”。
2. **置信度兜底**：置信度低于 0.7 或模糊的信息，自动标记为“需人工确认”，避免污染数据库。
3. **标准 MCP 工具**：对外暴露 5 个核心工具，供 AI 自主调用：
   - `add_memory`：记录并自动分类记忆
   - `search_memory`：按 ID 查询记忆
   - `list_needs_confirmation`：列出所有需人工确认的模糊记忆
   - `change_memory_state`：归档或删除记忆
   - `confirm_memory_category`：人工修正记忆分类
4. **SQLite 落库**：使用 Python 标准库 `sqlite3`，包含建表、索引、可重复执行的迁移脚本。

## 🛠️ 快速开始
1. 克隆仓库并进入目录：
   ```bash
   git clone https://github.com/你的用户名/mcp-memory-server.git
   cd mcp-memory-server
