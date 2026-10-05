from mcp.server.mcpserver import MCPServer
import memory_db  # 导入我们刚刚写好的数据库模块

# 初始化 MCP 服务器和数据库连接
mcp = MCPServer("MemoryServer")
conn = memory_db.init_db("memories.db")

# ================= 工具1：记录记忆 =================
@mcp.tool()
def add_memory(content: str) -> str:
    """
    当用户表达个人偏好（如喜欢、讨厌）、日程安排（如明天开会）或客观事实（如名字、住址）时，
    调用此工具记录记忆。系统会自动分类并计算置信度。
    如果系统无法确定分类（置信度低），会自动标记为“需人工确认”。
    """
    memory = memory_db.save_memory(conn, content)
    return f"记录成功！ID: {memory.id} | 自动分类: {memory.category.value} | 置信度: {memory.confidence}"

# ================= 工具2：查询单条记忆 =================
@mcp.tool()
def search_memory(memory_id: int) -> str:
    """
    当用户提供具体记忆 ID，并询问该记忆的详细内容时，调用此工具查询。
    """
    memory = memory_db.get_memory_by_id(conn, memory_id)
    if not memory:
        return f"未找到 ID 为 {memory_id} 的记忆。"
    return f"ID: {memory.id}\n内容: {memory.content}\n分类: {memory.category.value}\n状态: {memory.state.value}\n置信度: {memory.confidence}"

# ================= 工具3：列出需人工确认的记忆 =================
@mcp.tool()
def list_needs_confirmation() -> str:
    """
    当用户询问“有什么需要我确认的记忆吗”或者“有没有模糊的信息”时调用。
    返回所有被系统标记为“需人工确认”的记忆列表。
    """
    rows = memory_db.get_memories_by_state(conn, memory_db.MemoryState.ACTIVE.value)
    pending = [row for row in rows if row[2] == memory_db.MemoryCategory.NEEDS_CONFIRMATION.value]
    
    if not pending:
        return "太棒了，目前没有需要人工确认的模糊记忆。"
        
    result = "以下记忆因置信度低被拦截，需要您确认分类：\n"
    for row in pending:
        result += f"  - ID: {row[0]} | 内容: '{row[1]}'\n"
    return result

# ================= 工具4：改变记忆状态（归档/删除） =================
@mcp.tool()
def change_memory_state(memory_id: int, new_state: str) -> str:
    """
    当用户表示某条记忆不再需要（归档）或者要求彻底遗忘（删除）时调用。
    new_state 参数只能是 'archived' 或 'deleted'。
    """
    if new_state not in [memory_db.MemoryState.ARCHIVED.value, memory_db.MemoryState.DELETED.value]:
        return "错误：new_state 只能是 'archived' 或 'deleted'。"
        
    success = memory_db.update_memory_state(conn, memory_id, new_state)
    if success:
        return f"ID 为 {memory_id} 的记忆已成功标记为 {new_state}。"
    return f"操作失败，未找到 ID 为 {memory_id} 的记忆。"

# ================= 工具5：人工确认模糊记忆 =================
@mcp.tool()
def confirm_memory_category(memory_id: int, category: str) -> str:
    """
    当用户对之前被标记为“需人工确认”的记忆给出了明确指示时调用此工具。
    例如用户说“那个苹果是指我喜欢吃的水果”，就将分类修正为“偏好”。
    可选 category: '事实', '偏好', '日程'。
    """
    valid_categories = [
        memory_db.MemoryCategory.FACT.value,
        memory_db.MemoryCategory.PREFERENCE.value,
        memory_db.MemoryCategory.SCHEDULE.value
    ]
    if category not in valid_categories:
        return f"错误：分类只能是 {valid_categories} 之一。"
        
    success = memory_db.update_memory_category(conn, memory_id, category)
    if success:
        return f"ID 为 {memory_id} 的记忆已成功更新为 '{category}'，置信度提升为 1.0。"
    return f"操作失败，未找到 ID 为 {memory_id} 的记忆。"

# ================= 工具6：两数相加 =================
@mcp.tool()
def add(a: float, b: float) -> str:
    """
    当用户需要计算两个数字相加时调用此工具。
    返回 a 与 b 的和。
    """
    return f"{a} + {b} = {a + b}"

# ================= 启动服务器 =================
if __name__ == "__main__":
    mcp.run(transport="stdio")