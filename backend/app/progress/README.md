# 实时进度跟踪模块 (Real-Time Progress Tracking Module)

## 概述

本模块为Skill Seekers Web Management System提供了一个完整的实时进度跟踪解决方案。该模块支持任务进度监控、日志管理、通知系统、数据可视化和WebSocket实时通信，为用户提供全面的任务执行状态跟踪体验。

## 核心功能

### 1. 任务进度管理 (Task Progress Management)
- **实时进度跟踪**: 支持0-100%进度百分比实时更新
- **多状态管理**: pending, running, completed, failed, paused, cancelled
- **步骤跟踪**: 支持当前步骤和总步骤数跟踪
- **时间估算**: 预估完成时间和实际耗时统计
- **任务分类**: 支持多种任务类型（skill_creation, skill_deployment等）
- **元数据支持**: 丰富的任务元数据存储

### 2. 日志管理系统 (Log Management)
- **多级别日志**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **实时日志流**: WebSocket实时日志推送
- **日志搜索**: 支持文本搜索和高级过滤
- **上下文信息**: 支持日志上下文和堆栈跟踪
- **附件支持**: 日志可附加文件和数据
- **批量操作**: 批量创建和管理日志条目

### 3. 通知系统 (Notification System)
- **多渠道传递**: WebSocket, Email, Push, Slack
- **优先级管理**: urgent, high, normal, low
- **通知类型**: info, success, warning, error, progress
- **自动推送**: 任务状态变化自动通知
- **批量通知**: 支持批量通知发送
- **传递状态**: 完整的传递状态跟踪

### 4. 数据可视化 (Data Visualization)
- **多种图表**: 线形图、柱状图、饼图、面积图、散点图、仪表盘、热力图
- **实时仪表板**: 自定义仪表板和小组件
- **性能指标**: 成功率、持续时间、吞吐量统计
- **活动热力图**: 用户活动时间分布可视化
- **历史趋势**: 进度历史数据分析和趋势
- **数据导出**: JSON和CSV格式导出

### 5. WebSocket实时通信 (Real-Time Communication)
- **连接管理**: 支持1000+并发连接
- **消息路由**: 智能消息分发和路由
- **广播功能**: 全局、用户级、任务级广播
- **心跳检测**: 自动连接健康监控
- **自动重连**: 连接断开自动重连机制
- **连接池**: 高效的连接池管理

## 架构设计

### 核心组件

```
progress/
├── models/                 # 数据模型
│   ├── task.py            # 任务模型
│   ├── log.py             # 日志模型
│   ├── notification.py    # 通知模型
│   └── metric.py          # 指标模型
├── schemas/               # 验证架构
│   ├── progress_operations.py  # 操作请求架构
│   ├── websocket_messages.py   # WebSocket消息架构
│   └── notification_config.py # 通知配置架构
├── utils/                 # 工具函数
│   ├── serializers.py     # 序列化工具
│   ├── validators.py       # 验证工具
│   └── formatters.py      # 格式化工具
├── progress_manager.py    # 任务进度管理器
├── log_manager.py         # 日志管理器
├── notification_manager.py # 通知管理器
├── visualization_manager.py # 可视化管理器
├── websocket_manager.py   # WebSocket管理器
├── websocket_handler.py   # WebSocket处理器
├── resource_manager.py    # 资源管理器
├── api.py                 # API路由
└── __init__.py            # 模块导出
```

### 数据流

```
用户操作 → API路由 → 业务管理器 → 数据模型 → WebSocket推送 → 前端更新
    ↓           ↓           ↓           ↓           ↓
日志记录 → 通知系统 → 可视化生成 → 资源监控 → 实时统计
```

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi sqlalchemy pydantic websockets psutil
```

### 2. 基本使用

```python
from app.progress.progress_manager import progress_manager
from app.progress.schemas.progress_operations import CreateTaskRequest

# 创建任务
task_request = CreateTaskRequest(
    task_id="task-001",
    user_id="user-123",
    task_type="skill_creation",
    task_name="创建技能",
    progress=0.0,
    status="running",
)

task = await progress_manager.create_task(task_request)

# 更新进度
await progress_manager.update_progress(
    task_id="task-001",
    progress=50.0,
    current_step="处理文件",
)

# 完成任务
await progress_manager.complete_task("task-001")
```

### 3. WebSocket连接

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/progress/ws?task_id=task-001&user_id=user-123');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('收到进度更新:', message);
};

// 发送进度更新
ws.send(JSON.stringify({
    type: 'progress_update',
    task_id: 'task-001',
    progress: 75.0,
    current_step: '验证输出',
}));
```

### 4. API使用示例

#### 创建任务
```bash
POST /api/v1/progress/tasks
{
    "task_id": "task-001",
    "user_id": "user-123",
    "task_type": "skill_creation",
    "task_name": "创建技能",
    "progress": 0.0,
    "status": "running"
}
```

#### 更新进度
```bash
PATCH /api/v1/progress/tasks/task-001/progress
{
    "progress": 50.0,
    "current_step": "处理文件"
}
```

#### 获取任务列表
```bash
GET /api/v1/progress/tasks?user_id=user-123&status=running
```

#### 创建日志
```bash
POST /api/v1/progress/logs
{
    "task_id": "task-001",
    "level": "INFO",
    "message": "任务开始执行",
    "source": "system"
}
```

## API文档

### 任务管理端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/progress/tasks | 创建任务 |
| GET | /api/v1/progress/tasks/{task_id} | 获取任务 |
| GET | /api/v1/progress/tasks | 列出任务 |
| PATCH | /api/v1/progress/tasks/{task_id}/progress | 更新进度 |
| PATCH | /api/v1/progress/tasks/{task_id}/status | 更新状态 |
| POST | /api/v1/progress/tasks/{task_id}/complete | 完成任务 |
| POST | /api/v1/progress/tasks/{task_id}/fail | 标记失败 |
| DELETE | /api/v1/progress/tasks/{task_id} | 删除任务 |
| GET | /api/v1/progress/tasks/stats | 获取统计 |

### 日志管理端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/progress/logs | 创建日志 |
| GET | /api/v1/progress/tasks/{task_id}/logs | 获取任务日志 |
| GET | /api/v1/progress/logs | 列出日志 |
| DELETE | /api/v1/progress/tasks/{task_id}/logs | 删除日志 |
| GET | /api/v1/progress/logs/stats | 获取统计 |

### 通知管理端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/progress/notifications | 创建通知 |
| GET | /api/v1/progress/notifications | 列出通知 |
| GET | /api/v1/progress/users/{user_id}/notifications | 获取用户通知 |
| PATCH | /api/v1/progress/notifications/{notification_id}/read | 标记已读 |
| DELETE | /api/v1/progress/notifications/{notification_id} | 删除通知 |
| GET | /api/v1/progress/notifications/stats | 获取统计 |

### 可视化端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/progress/visualizations/progress-chart | 创建进度图表 |
| POST | /api/v1/progress/visualizations/status-distribution | 创建状态分布图 |
| POST | /api/v1/progress/visualizations/performance-metrics | 创建性能图表 |
| POST | /api/v1/progress/visualizations/activity-heatmap | 创建活动热力图 |
| POST | /api/v1/progress/visualizations/dashboard | 创建仪表板 |
| GET | /api/v1/progress/visualizations/dashboard/{dashboard_id} | 获取仪表板数据 |

### WebSocket端点

| 路径 | 描述 |
|------|------|
| /api/v1/progress/ws | WebSocket连接端点 |

## 配置选项

### WebSocket配置
```python
websocket_manager = WebSocketManager(
    max_connections=1000,      # 最大连接数
    heartbeat_interval=30.0,  # 心跳间隔(秒)
    connection_timeout=300.0,  # 连接超时(秒)
)
```

### 资源管理配置
```python
resource_manager = ResourceManager()
resource_manager.register_pool(
    DatabaseSessionPool(
        max_size=50,
        min_size=5,
        acquire_timeout=30.0,
        idle_timeout=300.0,
    )
)
```

## 性能特性

### 高并发支持
- 支持1000+ WebSocket并发连接
- 连接池复用和自动管理
- 异步I/O和协程支持

### 内存优化
- 内存缓存池和LRU淘汰
- 自动垃圾回收触发
- 内存使用监控和告警

### 数据库优化
- 数据库连接池管理
- 查询优化和索引
- 批量操作支持

### 网络优化
- 消息压缩和批处理
- 心跳检测和健康监控
- 自动重连和故障恢复

## 监控和统计

### 系统指标
- CPU和内存使用率
- 网络连接数
- 活跃线程数
- 垃圾回收统计

### 业务指标
- 任务创建和完成统计
- 日志生成统计
- 通知传递统计
- WebSocket连接统计

### 性能指标
- 平均响应时间
- 吞吐量统计
- 错误率统计
- 资源利用率

## 测试

### 运行集成测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
python test_progress_integration.py

# 或使用pytest
pytest test_progress_integration.py -v
```

### 测试覆盖范围
- 单元测试：各个组件的功能测试
- 集成测试：组件间交互测试
- 压力测试：高并发和负载测试
- 端到端测试：完整流程测试

## 最佳实践

### 1. 任务设计
- 使用描述性的任务ID和名称
- 合理设置任务步骤和预估时间
- 及时更新任务进度和状态

### 2. 日志记录
- 使用合适的日志级别
- 提供有意义的日志消息
- 包含必要的上下文信息

### 3. 通知管理
- 控制通知频率避免骚扰
- 使用合适的优先级
- 提供清晰的行动建议

### 4. 性能优化
- 定期监控资源使用
- 及时清理无用数据
- 优化数据库查询

## 故障排除

### 常见问题

**Q: WebSocket连接频繁断开？**
A: 检查网络稳定性，调整心跳间隔和连接超时设置

**Q: 进度更新不及时？**
A: 确认WebSocket连接状态，检查消息路由配置

**Q: 内存使用过高？**
A: 调整缓存池大小，启用内存优化，监控垃圾回收

**Q: 数据库连接池耗尽？**
A: 增加连接池大小，优化查询效率，检查连接泄露

### 日志分析
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查WebSocket统计
stats = websocket_manager.get_stats()
print(f"Active connections: {stats['active_connections']}")

# 检查资源使用
stats = resource_manager.get_comprehensive_stats()
print(f"Memory usage: {stats['system']['latest']['memory_percent']}%")
```

## 扩展指南

### 添加新的任务类型
1. 在`models/task.py`中添加新类型
2. 更新验证规则
3. 添加特定的处理逻辑

### 添加新的通知渠道
1. 在`notification_manager.py`中实现发送方法
2. 注册渠道处理器
3. 更新通知配置

### 添加新的可视化图表
1. 在`visualization_manager.py`中实现图表生成
2. 添加API端点
3. 更新前端组件

## 许可证

本模块遵循MIT许可证。详见LICENSE文件。

## 贡献指南

欢迎提交Issue和Pull Request。请确保：
1. 代码符合项目规范
2. 添加适当的测试
3. 更新相关文档
4. 通过所有测试检查

## 更新日志

### v1.0.0 (2024-01-31)
- 初始版本发布
- 完整的任务进度跟踪功能
- WebSocket实时通信
- 日志管理系统
- 通知系统
- 数据可视化
- 系统集成测试

## 联系方式

如有问题或建议，请联系开发团队。
