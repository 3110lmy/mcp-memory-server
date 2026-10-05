import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple

# 1. 定义状态枚举（状态机）
class MemoryState(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

# 2. 定义记忆分类枚举
class MemoryCategory(str, Enum):
    FACT = "事实"
    PREFERENCE = "偏好"
    SCHEDULE = "日程"
    NEEDS_CONFIRMATION = "需人工确认"  # 置信度低或模糊时使用

# 3. 定义记忆数据结构（扩充了分类和置信度）
@dataclass
class Memory:
    content: str
    state: MemoryState = MemoryState.ACTIVE
    category: MemoryCategory = MemoryCategory.NEEDS_CONFIRMATION
    confidence: float = 0.0
    id: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

# 4. 核心：自动归类分拣机（用关键词模拟AI判断）
def classify_memory(content: str) -> Tuple[MemoryCategory, float]:
    """根据关键词给记忆打标签，并返回(分类, 置信度)"""
    content_lower = content.lower()
    
    # 规则1：日程类
    schedule_keywords = ["明天", "下周", "下个月", "提醒我", "日程", "安排", "去", "出差", "开会"]
    if any(kw in content_lower for kw in schedule_keywords):
        return MemoryCategory.SCHEDULE, 0.85  # 把握比较大
        
    # 规则2：偏好类
    preference_keywords = ["喜欢", "讨厌", "爱吃", "不爱", "偏好", "习惯"]
    if any(kw in content_lower for kw in preference_keywords):
        return MemoryCategory.PREFERENCE, 0.90  # 把握很大
        
    # 规则3：事实类
    fact_keywords = ["我的名字", "我住在", "我养了", "我是"]
    if any(kw in content_lower for kw in fact_keywords):
        return MemoryCategory.FACT, 0.95  # 事实类最确信
        
    # 规则4：兜底处理（模棱两可或没命中关键词）
    # 比如输入“苹果”，既没命中偏好，也没命中午餐，无法判断
    return MemoryCategory.NEEDS_CONFIRMATION, 0.3  # 置信度很低，需要人工确认

# 5. 初始化数据库（建表 + 索引，这次加了新列）
def init_db(db_path="memories.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 注意：这里为了演示方便，如果表已存在会直接建新表。
    # 实战中，你需要执行 ALTER TABLE 加字段。为了新手友好，这里直接建新表。
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            state TEXT NOT NULL,
            category TEXT NOT NULL,      -- 新增：分类
            confidence REAL NOT NULL,    -- 新增：置信度
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_state ON memories(state)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_category ON memories(category)")  # 新增：按分类建索引
    conn.commit()
    return conn

# 6. 写入记忆（改造：自动分拣）
def save_memory(conn, content: str) -> Memory:
    # 1. 先调用分拣机，拿到分类和置信度
    category, confidence = classify_memory(content)
    
    # 2. 根据分类和置信度，判断是否需要人工确认
    if confidence < 0.7:
        final_category = MemoryCategory.NEEDS_CONFIRMATION
    else:
        final_category = category
        
    # 3. 组装记忆对象
    memory = Memory(
        content=content,
        state=MemoryState.ACTIVE,
        category=final_category,
        confidence=confidence
    )
    
    # 4. 存入数据库
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memories (content, state, category, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
        (memory.content, memory.state.value, memory.category.value, memory.confidence, memory.created_at)
    )
    conn.commit()
    memory.id = cursor.lastrowid
    return memory

# 7. 查询记忆（带出分类信息）
def get_memory_by_id(conn, memory_id: int) -> Optional[Memory]:
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, state, category, confidence, created_at FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()
    if row:
        return Memory(
            id=row[0], content=row[1], state=MemoryState(row[2]),
            category=MemoryCategory(row[3]), confidence=row[4], created_at=row[5]
        )
    return None

# ================= 测试运行 =================
if __name__ == "__main__":
    connection = init_db()
    
    # 测试用例1：清晰明确的日程
    print("--- 测试1：输入清晰明确的日程 ---")
    mem1 = save_memory(connection, "提醒我明天下午三点去开会")
    print(f"内容: {mem1.content}")
    print(f"分类: {mem1.category.value} | 置信度: {mem1.confidence} (高，直接入库)")
    print(f"查询验证: {get_memory_by_id(connection, mem1.id).category.value}\n")
    
    # 测试用例2：清晰明确的偏好
    print("--- 测试2：输入清晰明确的偏好 ---")
    mem2 = save_memory(connection, "用户很喜欢吃火锅，不爱吃香菜")
    print(f"内容: {mem2.content}")
    print(f"分类: {mem2.category.value} | 置信度: {mem2.confidence} (高，直接入库)\n")
    
    # 测试用例3：模糊不清的信息
    print("--- 测试3：输入模糊不清的信息（关键测试） ---")
    mem3 = save_memory(connection, "苹果")
    print(f"内容: {mem3.content}")
    print(f"分类: {mem3.category.value} | 置信度: {mem3.confidence} (低，触发人工确认！)")
    print(f"查询验证: 数据库里存的分类是: {get_memory_by_id(connection, mem3.id).category.value}")

    connection.close()
 # 在 memory_db.py 的末尾添加这两个函数

def update_memory_state(conn, memory_id: int, new_state: str) -> bool:
    """更新记忆的状态（如归档、删除）"""
    cursor = conn.cursor()
    cursor.execute("UPDATE memories SET state = ? WHERE id = ?", (new_state, memory_id))
    conn.commit()
    return cursor.rowcount > 0

def update_memory_category(conn, memory_id: int, new_category: str) -> bool:
    """人工确认后，修正记忆的分类，并将置信度设为1.0"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE memories SET category = ?, confidence = 1.0 WHERE id = ?", 
        (new_category, memory_id)
    )
    conn.commit()
    return cursor.rowcount > 0

def get_memories_by_state(conn, state: str):
    """按状态查询所有记忆"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, category, confidence FROM memories WHERE state = ?", (state,))
    return cursor.fetchall()
   