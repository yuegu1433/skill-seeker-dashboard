# 多平台支持系统文档

## 概述

多平台支持系统是一个全面的LLM平台集成解决方案，支持Claude、Gemini、OpenAI和Markdown等主流平台。系统提供统一的接口、格式转换、兼容性验证、部署管理和实时监控能力。

## 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                 Platform Manager                           │
│              (统一管理接口)                                │
└─────────────────┬─────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│Deployer│   │Monitor│   │Validator│
└───┬───┘   └───┬───┘   └───┬───┘
    │             │             │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│Registry│   │Registry│   │Registry│
└───┬───┘   └───┬───┘   └───┬───┘
    │             │             │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│Claude │   │ Gemini│   │ OpenAI│
│Adapter│   │Adapter│   │Adapter│
└───────┘   └───────┘   └───────┘
```

### 核心模块

#### 1. PlatformManager (核心管理器)
- **功能**: 统一协调所有平台组件
- **职责**: 部署管理、状态监控、兼容性验证、格式转换
- **特性**:
  - 单点入口设计
  - 组件协调和生命周期管理
  - 统一错误处理
  - 性能统计和监控

#### 2. PlatformDeployer (部署管理器)
- **功能**: 统一的部署接口
- **支持**: 单个、批量、回退部署
- **特性**:
  - 异步部署支持
  - 状态跟踪和进度监控
  - 重试机制和错误恢复
  - 部署队列管理

#### 3. PlatformMonitor (状态监控器)
- **功能**: 实时健康检查和监控
- **检查项**: 连通性、能力、性能、限制
- **特性**:
  - 多维度健康检查
  - 智能告警系统
  - 历史数据追踪
  - 性能指标收集

#### 4. CompatibilityValidator (兼容性验证器)
- **功能**: 跨平台兼容性检查
- **验证项**: 格式、特性、大小、依赖
- **特性**:
  - 多平台同时验证
  - 详细兼容性报告
  - 智能问题诊断
  - 兼容性评分系统

#### 5. FormatConverter (格式转换器)
- **功能**: 统一的格式转换引擎
- **支持**: 10+种格式互转
- **特性**:
  - 智能转换路径
  - 并发转换支持
  - 缓存优化
  - 转换模板管理

#### 6. PlatformRegistry (平台注册表)
- **功能**: 适配器注册和管理
- **特性**:
  - 插件化架构
  - 动态发现和加载
  - 线程安全
  - 热插拔支持

#### 7. 平台适配器 (Adapters)
- **ClaudeAdapter**: Claude平台专属适配
- **GeminiAdapter**: Gemini多模态适配
- **OpenAIAdapter**: OpenAI Functions适配
- **MarkdownAdapter**: Markdown文档适配

## 快速开始

### 安装和配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export CLAUDE_API_KEY="your-claude-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```

### 基本使用

```python
from backend.app.platform.manager import PlatformManager

async def main():
    # 初始化管理器
    manager = PlatformManager()
    await manager.initialize()

    # 部署技能
    tasks = await manager.deploy_skill(
        skill_data=skill_data,
        target_platforms=["claude", "gemini", "openai"],
        validate_compatibility=True
    )

    # 检查部署状态
    for task in tasks:
        status = await manager.get_deployment_status(task.deployment_id)
        print(f"部署状态: {status['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 格式转换

```python
# 转换技能格式
yaml_result = await manager.convert_skill_format(
    skill_data=json_skill,
    target_format="yaml",
    source_format="json"
)

# 跨平台转换
claude_result = await manager.convert_skill_format(
    skill_data=json_skill,
    target_format="claude",
    platform_id="claude"
)
```

### 兼容性验证

```python
# 验证兼容性
report = await manager.validate_skill_compatibility(
    skill_data=skill_data,
    target_platforms=["claude", "gemini", "openai"]
)

print(f"兼容性评分: {report['compatibility_score']}")
print(f"兼容平台: {report['compatible_platforms']}")
print(f"推荐操作: {report['recommendations']}")
```

## API参考

### RESTful API

#### 平台管理
```http
GET    /api/v1/platforms                    # 列出平台
GET    /api/v1/platforms/{platform_id}       # 获取平台详情
POST   /api/v1/platforms/{id}/health-check  # 触发健康检查
GET    /api/v1/platforms/health              # 总体健康检查
```

#### 部署管理
```http
POST   /api/v1/deployments                # 部署技能
GET    /api/v1/deployments/{id}           # 获取部署状态
POST   /api/v1/deployments/batch         # 批量部署
POST   /api/v1/deployments/{id}/cancel    # 取消部署
POST   /api/v1/deployments/{id}/retry     # 重试部署
```

#### 兼容性验证
```http
POST   /api/v1/compatibility/validate          # 验证兼容性
POST   /api/v1/compatibility/validate/batch    # 批量验证
GET    /api/v1/compatibility/supported-platforms # 获取支持平台
POST   /api/v1/compatibility/best-platform    # 查找最佳平台
```

### WebSocket API

```javascript
// 连接到WebSocket
const ws = new WebSocket('ws://api.example.com/ws?client_id=client123');

// 订阅部署状态更新
ws.send(JSON.stringify({
    type: 'subscribe',
    event_types: ['deployment_status', 'platform_health']
}));

// 监听消息
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.event_type === 'deployment_status') {
        console.log('部署更新:', message.data);
    }
};
```

## 部署配置

### Celery配置

```python
# celery_config.py
from celery import Celery

app = Celery('platform_tasks')

app.conf.update(
    broker_url='redis://localhost:6379',
    result_backend='redis://localhost:6379',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'platform.deployment': {'queue': 'platform_deployment'},
        'platform.validation': {'queue': 'platform_validation'},
        'platform.monitoring': {'queue': 'platform_monitoring'},
    },
    task_defaults={
        'rate_limit': '10/s',
        'task_time_limit': 3600,
        'task_soft_time_limit': 3300,
    }
)
```

### 启动服务

```bash
# 启动Celery Worker
celery -A celery_config worker --loglevel=info

# 启动Flower监控
celery -A celery_config flower

# 启动FastAPI服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 性能优化

### 缓存配置

```python
# 启用缓存
PERFORMANCE_CONFIG = {
    "caching": {
        "enabled": True,
        "ttl": 3600,  # 1小时
        "max_size": 1000
    },
    "concurrency": {
        "max_concurrent_operations": 10,
        "max_concurrent_api_calls": 20,
        "max_concurrent_deployments": 5
    }
}
```

### 优化策略

1. **缓存优化**: 启用格式转换缓存
2. **并发控制**: 限制并发操作数量
3. **批量处理**: 使用批量操作提升效率
4. **懒加载**: 大数据集懒加载
5. **连接池**: API连接复用

### 性能指标

- **响应时间**: 平均<100ms
- **吞吐量**: 1000+请求/分钟
- **成功率**: 95%+部署成功率
- **资源使用**: CPU<30%，内存<1GB

## 监控和告警

### 健康检查

```python
# 检查平台健康
health = await manager.get_platform_health()

# 获取监控摘要
summary = await manager.get_platform_summary()

# 检查总体健康
overall_health = await manager.health_check()
```

### 告警管理

```python
# 获取活动告警
alerts = monitor.get_active_alerts()

# 确认告警
monitor.acknowledge_alert(alert_id, "admin")

# 解决告警
monitor.resolve_alert(alert_id, "admin", "问题已修复")
```

### 监控指标

- **平台状态**: healthy、degraded、unhealthy
- **部署统计**: 总数、成功率、平均耗时
- **告警统计**: 活动告警、严重告警
- **性能指标**: 响应时间、吞吐量

## 最佳实践

### 1. 技能设计
```python
# 推荐的技能结构
skill = {
    "name": "Clear and descriptive name",
    "description": "Detailed description",
    "format": "json",  # 或 yaml, markdown
    "version": "1.0.0",
    "content": {
        "type": "skill",
        "parameters": {...},
        "capabilities": [...],
        "metadata": {...}
    }
}
```

### 2. 部署策略
```python
# 首选+回退部署
result = await manager.deploy_with_fallback(
    skill_data=skill_data,
    preferred_platforms=["claude", "gemini", "openai"],
    fallback_platforms=["markdown"],
    validate_compatibility=True
)
```

### 3. 错误处理
```python
try:
    result = await manager.deploy_skill(...)
except ValidationError as e:
    # 处理验证错误
    logger.error(f"验证失败: {e}")
except DeploymentError as e:
    # 处理部署错误
    logger.error(f"部署失败: {e}")
```

### 4. 监控集成
```python
# 添加事件处理器
manager.add_event_handler("deployment_complete", lambda data: send_notification(data))

# 监控部署状态
async def monitor_deployment(deployment_id):
    while True:
        status = await manager.get_deployment_status(deployment_id)
        if status["status"] in ["success", "failed", "cancelled"]:
            break
        await asyncio.sleep(5)
```

## 故障排除

### 常见问题

1. **部署失败**
   - 检查平台API密钥配置
   - 验证技能格式和内容
   - 查看兼容性验证报告

2. **性能问题**
   - 启用缓存优化
   - 调整并发限制
   - 监控资源使用

3. **兼容性错误**
   - 检查技能格式支持
   - 验证平台限制
   - 查看详细报告

### 调试模式

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 启用性能监控
optimizer = get_performance_optimizer()
stats = optimizer.get_performance_statistics()
print(json.dumps(stats, indent=2))
```

### 日志分析

```bash
# 查看部署日志
tail -f logs/deployment.log

# 查看错误日志
grep "ERROR" logs/platform.log

# 查看性能统计
grep "PERFORMANCE" logs/platform.log
```

## 安全考虑

### API密钥管理
- 使用环境变量存储敏感信息
- 定期轮换API密钥
- 限制API密钥权限

### 网络安全
- 启用HTTPS
- 使用API密钥认证
- 限制访问IP

### 数据安全
- 加密传输数据
- 安全存储技能信息
- 审计日志记录

## 扩展开发

### 添加新平台

```python
from backend.app.platform.adapters import PlatformAdapter

class CustomAdapter(PlatformAdapter):
    platform_id = "custom"
    display_name = "Custom Platform"
    supported_formats = ["json", "yaml"]

    async def deploy_skill(self, skill_data, deployment_config=None):
        # 实现部署逻辑
        return {"deployment_id": "new-deployment"}
```

### 自定义转换规则

```python
converter = FormatConverter()
converter.add_conversion_rule(
    "custom_format",
    "json",
    {
        "method": "custom_conversion",
        "priority": 1
    }
)
```

### 扩展监控指标

```python
from backend.app.platform.monitor import HealthCheckResult

class CustomHealthCheck:
    async def check_custom_metric(self):
        return HealthCheckResult(
            platform_id="custom",
            status=HealthCheckStatus.PASS,
            message="Custom metric is healthy",
            response_time_ms=10
        )
```

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 支持

如有问题或建议，请联系：
- 邮箱: support@example.com
- 文档: https://docs.example.com
- GitHub: https://github.com/example/platform

---

**最后更新**: 2026-01-31
**版本**: 1.0.0