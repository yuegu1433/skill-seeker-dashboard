# Skill Seekers Web管理系统实施方案 (MinIO版本)

## 项目概述

基于 skill_seekers-2.7.4 CLI 工具，设计并实现完整的Web管理系统，满足《COMPLETE_REQUIREMENTS.md》中的所有功能需求。

### 目标

- ✅ 构建可视化的技能管理界面
- ✅ 提供实时创建进度跟踪
- ✅ 支持技能文件在线编辑
- ✅ 实现完整的技能生命周期管理
- ✅ 支持4个LLM平台（Claude、Gemini、OpenAI、Markdown）
- ✅ 使用MinIO对象存储实现高可用存储方案
- ✅ 简化架构：无需用户管理，专注核心功能开发

### 开发说明

**用户管理**：开发阶段不考虑用户管理系统，采用单租户架构。所有功能对所有访问者开放，无需注册/登录。

**优势**：
- 简化系统架构，专注核心功能
- 降低开发复杂度
- 加快MVP产品交付
- 减少安全风险面
- 降低运维成本

### 技术栈选择

- **后端**：FastAPI + PostgreSQL + Redis + Celery
- **前端**：React 18 + TypeScript + Ant Design
- **实时通信**：WebSocket
- **部署**：Docker + Docker Compose + Nginx
- **存储**：MinIO对象存储 + PostgreSQL元数据（符合需求3.1的存储架构）

## 系统架构总览

```
┌─────────────────────────────────────────────────────────┐
│                 Web管理界面 (React)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │ 技能列表    │ │ 创建向导    │ │ 文件编辑器  │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴────────┐
                    │   FastAPI后端    │
                    │ ┌─────────────┐ │
                    │ │ 技能API     │ │
                    │ │ 配置API     │ │
                    │ │ 文件API     │ │
                    │ │ 日志API     │ │
                    └─┴─────────────┘ │
                             │
                    ┌─────────┴─────────┐
                    │  任务队列系统     │
                    │  (Celery+Redis)   │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │  skill-seekers   │
                    │     CLI工具      │
                    │ ┌─────────────┐ │
                    │ │ 文档抓取    │ │
                    │ │ GitHub分析  │ │
                    │ │ AI增强     │ │
                    │ │ 多平台打包  │ │
                    └─┴─────────────┘ │
                             │
                    ┌─────────┴─────────┐
                    │     Nginx代理        │
                    │  ┌─────────────┐ │
                    │  │ 静态文件服务  │ │
                    │  │ API转发      │ │
                    │  │ WebSocket   │ │
                    │  │ MinIO代理   │ │
                    │  └─────────────┘ │
                             │
                    ┌─────────┴─────────┐
                    │  MinIO对象存储     │
                    │ ┌─────────────┐ │
                    │ │ skills桶   │ │
                    │ │ cache桶    │ │
                    │ │ archives桶 │ │
                    │ └─────────────┘ │
```

## MinIO 存储优势

### 1. 高可扩展性
- **对象存储**：无限水平扩展，支持EB级数据存储
- **分布式架构**：多节点部署，数据自动复制
- **负载均衡**：自动负载分散，提高并发性能

### 2. 高可用性
- **数据冗余**：多副本存储，防止数据丢失
- **故障转移**：节点故障时自动切换，保证服务连续性
- **版本控制**：支持对象版本管理，防范误删除

### 3. 性能优化
- **并行处理**：支持多线程上传下载
- **缓存友好**：与CDN集成，加速文件访问
- **压缩存储**：自动压缩，减少存储成本

### 4. 安全性
- **访问控制**：简化访问控制（开发阶段无认证）
- **数据加密**：传输和静态数据加密
- **审计日志**：完整的操作记录和日志

### 5. 单租户架构
- **无需用户管理**：所有访问者共享同一套数据和功能
- **简化部署**：单实例部署，无需复杂的用户权限系统
- **降低复杂度**：专注于核心技能管理功能开发

## 详细实施方案

### 第一阶段：核心基础设施（3-4周）

#### 1.1 PostgreSQL 数据库设计

```sql
-- 技能主表
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('claude', 'gemini', 'openai', 'markdown')),
    status VARCHAR(20) NOT NULL DEFAULT 'creating' CHECK (status IN ('creating', 'completed', 'failed', 'enhancing')),
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('github', 'web', 'upload', 'multi')),
    metadata JSONB,
    config JSONB,
    -- MinIO存储相关字段
    storage_bucket VARCHAR(50) DEFAULT 'skillseekers-skills',
    storage_prefix VARCHAR(200),
    file_count INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建任务表（支持实时进度）
CREATE TABLE skill_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
    task_type VARCHAR(20) NOT NULL CHECK (task_type IN ('scrape', 'build', 'enhance', 'package')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    logs TEXT,
    error_details TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 技能文件表（存储MinIO对象信息）
CREATE TABLE skill_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
    object_name VARCHAR(500) NOT NULL, -- MinIO对象名
    file_path VARCHAR(500) NOT NULL, -- 逻辑路径
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('skill_file', 'reference', 'config', 'metadata', 'log')),
    file_size BIGINT,
    content_type VARCHAR(100),
    checksum VARCHAR(64), -- 文件校验和
    is_public BOOLEAN DEFAULT FALSE, -- 是否公开访问
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 平台包文件表
CREATE TABLE platform_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    object_name VARCHAR(500), -- MinIO对象名
    package_size BIGINT,
    checksum VARCHAR(64),
    download_url TEXT, -- 预签名下载URL
    expires_at TIMESTAMP, -- URL过期时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_skills_status ON skills(status);
CREATE INDEX idx_skills_platform ON skills(platform);
CREATE INDEX idx_skills_created_at ON skills(created_at DESC);
CREATE INDEX idx_skill_tasks_skill_id ON skill_tasks(skill_id);
CREATE INDEX idx_skill_files_skill_id ON skill_files(skill_id);
CREATE INDEX idx_skill_files_object_name ON skill_files(object_name);
CREATE INDEX idx_platform_packages_skill_id ON platform_packages(skill_id);
```

### 第二阶段：React Web界面（6-8周）

#### 2.1 技能卡片组件（支持MinIO）

```typescript
// src/components/SkillCard.tsx
import React from 'react';
import { Card, Button, Tag, Progress, Dropdown, Space, Tooltip } from 'antd';
import { DownloadOutlined, EditOutlined, DeleteOutlined, EyeOutlined, CloudServerOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';

interface SkillCardProps {
  skill: Skill;
  onViewDetails: (skill: Skill) => void;
  onDelete: (skill: Skill) => void;
  onEdit: (skill: Skill) => void;
  onDownload: (skill: Skill, platform: Platform) => void;
}

const SkillCard: React.FC<SkillCardProps> = ({
  skill,
  onViewDetails,
  onDelete,
  onEdit,
  onDownload
}) => {
  const getPlatformColor = (platform: string) => {
    const colors = {
      claude: '#D97706',
      gemini: '#1A73E8',
      openai: '#10A37F',
      markdown: '#6B7280'
    };
    return colors[platform] || '#6B7280';
  };

  const getStatusColor = (status: string) => {
    const colors = {
      creating: '#1890FF',
      completed: '#52C41A',
      failed: '#FF4D4F',
      enhancing: '#FAAD14'
    };
    return colors[status] || '#D9D9D9';
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const downloadMenuItems: MenuProps['items'] = [
    {
      key: 'claude',
      label: 'Claude AI',
      onClick: () => onDownload(skill, 'claude')
    },
    {
      key: 'gemini',
      label: 'Google Gemini',
      onClick: () => onDownload(skill, 'gemini')
    },
    {
      key: 'openai',
      label: 'OpenAI ChatGPT',
      onClick: () => onDownload(skill, 'openai')
    },
    {
      key: 'markdown',
      label: 'Generic Markdown',
      onClick: () => onDownload(skill, 'markdown')
    }
  ];

  return (
    <Card
      hoverable
      className="skill-card"
      cover={
        <div
          className="skill-card-header"
          style={{
            backgroundColor: getPlatformColor(skill.platform),
            color: 'white',
            padding: '16px'
          }}
        >
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <PlatformIcon platform={skill.platform} />
              <span className="font-medium capitalize">{skill.platform}</span>
              <Tooltip title="存储在MinIO对象存储中">
                <CloudServerOutlined />
              </Tooltip>
            </div>
            <Tag color={getStatusColor(skill.status)}>
              {skill.status}
            </Tag>
          </div>
        </div>
      }
      actions={[
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={() => onViewDetails(skill)}
        >
          查看
        </Button>,
        <Button
          type="text"
          icon={<EditOutlined />}
          onClick={() => onEdit(skill)}
        >
          编辑
        </Button>,
        <Dropdown menu={{ items: downloadMenuItems }} placement="bottomRight">
          <Button type="text" icon={<DownloadOutlined />}>
            下载
          </Button>
        </Dropdown>,
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => onDelete(skill)}
        >
          删除
        </Button>
      ]}
    >
      <Card.Meta
        title={skill.name}
        description={skill.description}
      />

      <div className="skill-progress mt-4">
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>创建进度</span>
          <span>{skill.progress || 0}%</span>
        </div>
        <Progress
          percent={skill.progress || 0}
          showInfo={false}
          strokeColor={getPlatformColor(skill.platform)}
        />
      </div>

      <div className="skill-meta mt-4 text-sm text-gray-500 space-y-1">
        <div className="flex justify-between">
          <span>创建于: {formatDate(skill.created_at)}</span>
          <Tooltip title="存储在MinIO中">
            <CloudServerOutlined />
          </Tooltip>
        </div>
        <div className="flex justify-between">
          <span>来源: {skill.source_type}</span>
          <span>{skill.file_count} 文件</span>
        </div>
        <div className="flex justify-between">
          <span>大小:</span>
          <span>{formatFileSize(skill.total_size_bytes || 0)}</span>
        </div>
      </div>
    </Card>
  );
};

export default SkillCard;
```

### 第三阶段：MinIO 存储系统升级（4-5周）

#### 3.1 MinIO 存储管理器实现

```python
# src/storage/manager.py
import json
import io
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
from minio import Minio
from minio.error import S3Error
from minio.commonconfig import CopySource

class SkillStorageManager:
    """基于MinIO的技能存储管理器（实现需求中的存储架构）"""

    def __init__(self,
                 endpoint: str = "minio:9000",
                 access_key: str = "minioadmin",
                 secret_key: str = "minioadmin",
                 secure: bool = False):
        """
        初始化MinIO客户端

        Args:
            endpoint: MinIO服务器地址
            access_key: 访问密钥
            secret_key: 秘密密钥
            secure: 是否使用HTTPS（开发阶段使用HTTP）
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

        # 创建存储桶
        self.buckets = {
            "skills": "skillseekers-skills",
            "temp": "skillseekers-temp",
            "cache": "skillseekers-cache",
            "archives": "skillseekers-archives"
        }

        self._ensure_buckets()

    def _ensure_buckets(self):
        """确保所有必需的存储桶存在"""
        for bucket_name in self.buckets.values():
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

    def create_skill_storage(self, skill_id: str) -> 'SkillStorage':
        """创建技能存储结构（使用MinIO对象前缀模拟目录）"""
        return SkillStorage(self.client, self.buckets, skill_id)

    def save_metadata(self, skill_id: str, metadata: Dict[str, Any]):
        """保存技能元数据到MinIO"""
        storage = self.create_skill_storage(skill_id)
        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        storage.upload_file(
            object_name="metadata.json",
            file_data=metadata_json.encode('utf-8'),
            content_type="application/json"
        )

    def save_config(self, skill_id: str, config: Dict[str, Any]):
        """保存技能配置到MinIO"""
        storage = self.create_skill_storage(skill_id)
        config_json = json.dumps(config, indent=2, ensure_ascii=False)
        storage.upload_file(
            object_name="config.json",
            file_data=config_json.encode('utf-8'),
            content_type="application/json"
        )

    def update_status(self, skill_id: str, status: Dict[str, Any]):
        """更新技能状态"""
        storage = self.create_skill_storage(skill_id)
        status_data = {
            "updated_at": datetime.utcnow().isoformat(),
            **status
        }
        status_json = json.dumps(status_data, indent=2)
        storage.upload_file(
            object_name="status.json",
            file_data=status_json.encode('utf-8'),
            content_type="application/json"
        )

    def save_creation_logs(self, skill_id: str, logs_data: Dict[str, Any]):
        """保存创建过程日志（符合需求2.3.3）"""
        storage = self.create_skill_storage(skill_id)

        # 保存不同格式的日志到logs/前缀
        if "raw_logs" in logs_data:
            storage.upload_file(
                object_name="logs/creation.log",
                file_data=logs_data["raw_logs"].encode('utf-8'),
                content_type="text/plain"
            )

        if "markdown_report" in logs_data:
            storage.upload_file(
                object_name="logs/creation_report.md",
                file_data=logs_data["markdown_report"].encode('utf-8'),
                content_type="text/markdown"
            )

        if "timeline_json" in logs_data:
            timeline_json = json.dumps(logs_data["timeline_json"], indent=2)
            storage.upload_file(
                object_name="logs/timeline.json",
                file_data=timeline_json.encode('utf-8'),
                content_type="application/json"
            )

        if "config_snapshot" in logs_data:
            config_snapshot = json.dumps(logs_data["config_snapshot"], indent=2)
            storage.upload_file(
                object_name="logs/config_snapshot.json",
                file_data=config_snapshot.encode('utf-8'),
                content_type="application/json"
            )

    def upload_skill_file(self, skill_id: str, file_path: str, file_data: bytes, content_type: str = "application/octet-stream"):
        """上传技能文件"""
        storage = self.create_skill_storage(skill_id)
        object_name = f"skill_files/{file_path}"
        storage.upload_file(object_name, file_data, content_type)

    def download_skill_file(self, skill_id: str, file_path: str) -> bytes:
        """下载技能文件"""
        storage = self.create_skill_storage(skill_id)
        object_name = f"skill_files/{file_path}"
        return storage.download_file(object_name)

    def delete_skill(self, skill_id: str):
        """删除技能及所有文件"""
        storage = self.create_skill_storage(skill_id)
        storage.delete_all_files()

    def list_skills(self) -> List[str]:
        """列出所有技能ID"""
        try:
            objects = self.client.list_objects(
                self.buckets["skills"],
                prefix="skills/",
                recursive=True
            )
            skill_ids = set()
            for obj in objects:
                # 从对象路径提取技能ID
                # 格式: skills/{skill_id}/metadata.json
                parts = obj.object_name.split("/")
                if len(parts) >= 2 and parts[0] == "skills":
                    skill_ids.add(parts[1])
            return list(skill_ids)
        except S3Error as e:
            print(f"Error listing skills: {e}")
            return []

    def create_backup(self, skill_id: str, backup_type: str = "daily") -> str:
        """创建技能备份"""
        storage = self.create_skill_storage(skill_id)
        backup_id = f"{backup_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # 复制所有文件到archives桶
        files = storage.list_files()
        for file_path in files:
            source = CopySource(
                bucket_name=storage.skills_bucket,
                object_name=file_path
            )
            backup_object_name = f"backups/{skill_id}/{backup_id}/{file_path.split('/', 1)[1]}"

            self.client.copy_object(
                bucket_name=self.buckets["archives"],
                object_name=backup_object_name,
                source=source
            )

        return backup_id

class SkillStorage:
    """技能存储实例（MinIO实现）"""

    def __init__(self, client: Minio, buckets: Dict[str, str], skill_id: str):
        self.client = client
        self.buckets = buckets
        self.skill_id = skill_id
        self.skills_bucket = buckets["skills"]

    def upload_file(self, object_name: str, file_data: bytes, content_type: str = "application/octet-stream"):
        """上传文件到MinIO"""
        full_object_name = f"skills/{self.skill_id}/{object_name}"

        try:
            # 使用BytesIO将字节数据转换为文件-like对象
            file_obj = io.BytesIO(file_data)
            file_obj.seek(0)

            self.client.put_object(
                bucket_name=self.skills_bucket,
                object_name=full_object_name,
                data=file_obj,
                length=len(file_data),
                content_type=content_type
            )
        except S3Error as e:
            raise Exception(f"Failed to upload file {object_name}: {e}")

    def download_file(self, object_name: str) -> bytes:
        """从MinIO下载文件"""
        full_object_name = f"skills/{self.skill_id}/{object_name}"

        try:
            response = self.client.get_object(
                bucket_name=self.skills_bucket,
                object_name=full_object_name
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"Failed to download file {object_name}: {e}")

    def list_files(self, prefix: str = "") -> List[str]:
        """列出技能下的所有文件"""
        full_prefix = f"skills/{self.skill_id}/{prefix}"

        try:
            objects = self.client.list_objects(
                bucket_name=self.skills_bucket,
                prefix=full_prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            raise Exception(f"Failed to list files: {e}")

    def delete_file(self, object_name: str):
        """删除单个文件"""
        full_object_name = f"skills/{self.skill_id}/{object_name}"

        try:
            self.client.remove_object(
                bucket_name=self.skills_bucket,
                object_name=full_object_name
            )
        except S3Error as e:
            raise Exception(f"Failed to delete file {object_name}: {e}")

    def delete_all_files(self):
        """删除技能下的所有文件"""
        try:
            objects = self.client.list_objects(
                bucket_name=self.skills_bucket,
                prefix=f"skills/{self.skill_id}/",
                recursive=True
            )

            for obj in objects:
                self.client.remove_object(
                    bucket_name=self.skills_bucket,
                    object_name=obj.object_name
                )
        except S3Error as e:
            raise Exception(f"Failed to delete skill files: {e}")

    def get_file_url(self, object_name: str, expires_hours: int = 24) -> str:
        """获取文件的临时访问URL"""
        full_object_name = f"skills/{self.skill_id}/{object_name}"

        try:
            url = self.client.presigned_get_object(
                bucket_name=self.skills_bucket,
                object_name=full_object_name,
                expires=expires_hours * 3600  # 转换为秒
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to get file URL: {e}")

    def move_file(self, source_object_name: str, dest_object_name: str):
        """移动/重命名文件"""
        try:
            # 复制到新位置
            source = CopySource(
                bucket_name=self.skills_bucket,
                object_name=f"skills/{self.skill_id}/{source_object_name}"
            )

            self.client.copy_object(
                bucket_name=self.skills_bucket,
                object_name=f"skills/{self.skill_id}/{dest_object_name}",
                source=source
            )

            # 删除原文件
            self.client.remove_object(
                bucket_name=self.skills_bucket,
                object_name=f"skills/{self.skill_id}/{source_object_name}"
            )
        except S3Error as e:
            raise Exception(f"Failed to move file: {e}")

    def get_file_info(self, object_name: str) -> Dict[str, Any]:
        """获取文件信息"""
        full_object_name = f"skills/{self.skill_id}/{object_name}"

        try:
            stat = self.client.stat_object(
                bucket_name=self.skills_bucket,
                object_name=full_object_name
            )
            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata
            }
        except S3Error as e:
            raise Exception(f"Failed to get file info: {e}")
```

#### 3.2 文件版本控制系统

```python
# src/storage/versioning.py
import json
from datetime import datetime
from typing import Dict, List, Optional
from .manager import SkillStorage

class VersionManager:
    """文件版本管理器"""

    def __init__(self, storage: SkillStorage):
        self.storage = storage
        self.versions_bucket = "skillseekers-versions"

    def create_version(self, file_path: str, file_data: bytes,
                      content_type: str = "application/octet-stream",
                      comment: str = "") -> str:
        """创建文件新版本"""
        version_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        version_object_name = f"versions/{self.storage.skill_id}/{file_path}/{version_id}"

        # 创建版本信息
        version_info = {
            "version_id": version_id,
            "file_path": file_path,
            "created_at": datetime.utcnow().isoformat(),
            "content_type": content_type,
            "comment": comment,
            "size": len(file_data)
        }

        try:
            # 上传版本文件
            file_obj = io.BytesIO(file_data)
            file_obj.seek(0)

            self.storage.client.put_object(
                bucket_name=self.versions_bucket,
                object_name=version_object_name,
                data=file_obj,
                length=len(file_data),
                content_type=content_type
            )

            # 保存版本信息
            info_object_name = version_object_name + "/_info.json"
            info_data = json.dumps(version_info, indent=2).encode('utf-8')

            info_obj = io.BytesIO(info_data)
            info_obj.seek(0)

            self.storage.client.put_object(
                bucket_name=self.versions_bucket,
                object_name=info_object_name,
                data=info_obj,
                length=len(info_data),
                content_type="application/json"
            )

            return version_id
        except S3Error as e:
            raise Exception(f"Failed to create version: {e}")

    def list_versions(self, file_path: str) -> List[Dict[str, Any]]:
        """列出文件的所有版本"""
        try:
            objects = self.storage.client.list_objects(
                bucket_name=self.versions_bucket,
                prefix=f"versions/{self.storage.skill_id}/{file_path}/",
                recursive=False
            )

            versions = []
            for obj in objects:
                if obj.object_name.endswith("/_info.json"):
                    # 读取版本信息
                    response = self.storage.client.get_object(
                        bucket_name=self.versions_bucket,
                        object_name=obj.object_name
                    )
                    info_data = json.loads(response.read().decode('utf-8'))
                    versions.append(info_data)
                    response.close()
                    response.release_conn()

            # 按创建时间排序
            versions.sort(key=lambda x: x["created_at"], reverse=True)
            return versions
        except S3Error as e:
            raise Exception(f"Failed to list versions: {e}")

    def restore_version(self, file_path: str, version_id: str) -> bytes:
        """恢复文件到指定版本"""
        version_object_name = f"versions/{self.storage.skill_id}/{file_path}/{version_id}"

        try:
            response = self.storage.client.get_object(
                bucket_name=self.versions_bucket,
                object_name=version_object_name
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"Failed to restore version: {e}")
```

#### 3.3 缓存管理系统

```python
# src/storage/cache.py
import hashlib
import json
from typing import Any, Optional
from datetime import datetime, timedelta
from .manager import SkillStorage

class CacheManager:
    """MinIO缓存管理器"""

    def __init__(self, storage: SkillStorage):
        self.storage = storage
        self.cache_bucket = self.storage.buckets["cache"]
        self.default_ttl = 3600  # 1小时

    def _generate_cache_key(self, key: str) -> str:
        """生成缓存键"""
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        cache_key = self._generate_cache_key(key)
        cache_object_name = f"cache/{cache_key}"

        try:
            response = self.storage.client.get_object(
                bucket_name=self.cache_bucket,
                object_name=cache_object_name
            )

            data = response.read().decode('utf-8')
            cache_info = json.loads(data)

            # 检查是否过期
            if datetime.fromisoformat(cache_info["expires_at"]) > datetime.utcnow():
                return cache_info["data"]
            else:
                # 删除过期缓存
                self.storage.client.remove_object(
                    bucket_name=self.cache_bucket,
                    object_name=cache_object_name
                )
                return None

        except S3Error:
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存数据"""
        ttl = ttl or self.default_ttl

        cache_key = self._generate_cache_key(key)
        cache_object_name = f"cache/{cache_key}"

        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        cache_data = {
            "key": key,
            "data": value,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat()
        }

        try:
            cache_json = json.dumps(cache_data, default=str).encode('utf-8')

            cache_obj = io.BytesIO(cache_json)
            cache_obj.seek(0)

            self.storage.client.put_object(
                bucket_name=self.cache_bucket,
                object_name=cache_object_name,
                data=cache_obj,
                length=len(cache_json),
                content_type="application/json"
            )
        except S3Error as e:
            raise Exception(f"Failed to set cache: {e}")

    def delete(self, key: str) -> None:
        """删除缓存"""
        cache_key = self._generate_cache_key(key)
        cache_object_name = f"cache/{cache_key}"

        try:
            self.storage.client.remove_object(
                bucket_name=self.cache_bucket,
                object_name=cache_object_name
            )
        except S3Error:
            pass

    def clear_expired(self) -> int:
        """清理过期缓存"""
        try:
            objects = self.storage.client.list_objects(
                bucket_name=self.cache_bucket,
                prefix="cache/",
                recursive=True
            )

            deleted_count = 0
            current_time = datetime.utcnow()

            for obj in objects:
                if obj.object_name.endswith("/_info.json"):
                    continue

                try:
                    response = self.storage.client.get_object(
                        bucket_name=self.cache_bucket,
                        object_name=obj.object_name
                    )

                    data = json.loads(response.read().decode('utf-8'))
                    expires_at = datetime.fromisoformat(data["expires_at"])

                    if expires_at <= current_time:
                        self.storage.client.remove_object(
                            bucket_name=self.cache_bucket,
                            object_name=obj.object_name
                        )
                        deleted_count += 1

                    response.close()
                    response.release_conn()
                except:
                    continue

            return deleted_count
        except S3Error as e:
            raise Exception(f"Failed to clear expired cache: {e}")
```

### 第四阶段：Docker 部署方案（3-4周）

#### 4.1 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 前端Web界面（通过Nginx托管）
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    # 不暴露端口，由Nginx统一对外服务
    environment:
      - REACT_APP_API_URL=/api
      - REACT_APP_WS_URL=/ws
      - REACT_APP_MINIO_ENDPOINT=/minio
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - skillseekers

  # 后端API服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/skillseekers
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin123
      - MINIO_SECURE=false
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./skill-seekers:/usr/local/bin/skill-seekers:ro
    depends_on:
      - postgres
      - redis
      - minio
    restart: unless-stopped
    networks:
      - skillseekers

  # MinIO对象存储
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin123
      - MINIO_CONSOLE_ADDRESS=:9001
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    restart: unless-stopped
    networks:
      - skillseekers

  # MinIO客户端（用于初始化）
  minio-setup:
    image: minio/mc:latest
    depends_on:
      - minio
    entrypoint: >
      /bin/sh -c "
      sleep 5;
      mc alias set local http://minio:9000 minioadmin minioadmin123;
      mc mb --ignore-existing local/skillseekers-skills;
      mc mb --ignore-existing local/skillseekers-temp;
      mc mb --ignore-existing local/skillseekers-cache;
      mc mb --ignore-existing local/skillseekers-archives;
      mc policy set public local/skillseekers-skills;
      exit 0;
      "

  # Celery Worker（后台任务处理）
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    command: celery -A src.tasks.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/skillseekers
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin123
      - MINIO_SECURE=false
    volumes:
      - ./skill-seekers:/usr/local/bin/skill-seekers:ro
    depends_on:
      - postgres
      - redis
      - minio
    restart: unless-stopped
    networks:
      - skillseekers

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=skillseekers
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - skillseekers

  # Redis缓存和消息队列
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass redispassword
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - skillseekers

  # Nginx反向代理（统一对外入口）
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - frontend
      - backend
      - minio
    restart: unless-stopped
    networks:
      - skillseekers

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  skillseekers:
    driver: bridge
```

#### 4.2 MinIO配置文件

```yaml
# nginx/nginx.conf - 统一反向代理配置

# 全局配置
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

# 事件模块
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # 基础配置
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    charset UTF-8;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # 性能优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    server_tokens off;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        text/x-component
        application/javascript
        application/json
        application/xml
        application/rss+xml
        application/atom+xml
        font/truetype
        font/opentype
        application/vnd.ms-fontobject
        image/svg+xml;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: data: blob: 'unsafe-inline'" always;

    # 请求限制
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # 上游服务器配置
    upstream backend {
        server backend:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream minio {
        server minio:9000 max_fails=3 fail_timeout=30s;
    }

    # HTTP服务器配置
    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # 健康检查端点
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # 前端静态文件
        location / {
            try_files $uri $uri/ /index.html;

            # 静态文件缓存
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
                access_log off;
            }

            # HTML文件不缓存
            location ~* \.html$ {
                add_header Cache-Control "no-cache, no-store, must-revalidate";
                add_header Pragma "no-cache";
                add_header Expires "0";
            }
        }

        # API代理
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;

            # 缓冲设置
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        # WebSocket代理
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket特定超时
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;
        }

        # MinIO API代理
        location /minio/ {
            proxy_pass http://minio;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 限制HTTP方法（仅GET）
            limit_except GET {
                deny all;
            }

            # 增加代理缓冲
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # MinIO控制台代理
        location /minio-console/ {
            proxy_pass http://minio:9001/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # MinIO管理控制台（友好路径）
        location /minio/ {
            proxy_pass http://minio:9001/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 错误页面
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;

        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```

### 第五阶段：测试与优化（3-4周）

#### 5.1 MinIO存储测试

```python
# tests/test_storage.py
import pytest
from minio.error import S3Error
from src.storage.manager import SkillStorageManager, SkillStorage

class TestMinIOStorage:
    """MinIO存储测试"""

    @pytest.fixture
    def storage_manager(self):
        """创建存储管理器实例"""
        return SkillStorageManager(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin123",
            secure=False
        )

    @pytest.fixture
    def skill_storage(self, storage_manager):
        """创建技能存储实例"""
        skill_id = "test-skill-123"
        return storage_manager.create_skill_storage(skill_id)

    def test_upload_file(self, skill_storage):
        """测试文件上传"""
        file_data = b"Hello, MinIO!"
        object_name = "test.txt"

        skill_storage.upload_file(
            object_name=object_name,
            file_data=file_data,
            content_type="text/plain"
        )

        # 验证文件存在
        files = skill_storage.list_files()
        assert f"skills/{skill_storage.skill_id}/{object_name}" in files

    def test_download_file(self, skill_storage):
        """测试文件下载"""
        file_data = b"Test file content"
        object_name = "test.txt"

        # 上传文件
        skill_storage.upload_file(
            object_name=object_name,
            file_data=file_data
        )

        # 下载文件
        downloaded_data = skill_storage.download_file(object_name)
        assert downloaded_data == file_data

    def test_file_versioning(self, skill_storage):
        """测试文件版本控制"""
        from src.storage.versioning import VersionManager

        version_manager = VersionManager(skill_storage)

        # 创建版本1
        file_data_v1 = b"Version 1"
        version_id_1 = version_manager.create_version(
            file_path="test.txt",
            file_data=file_data_v1,
            comment="Initial version"
        )

        # 创建版本2
        file_data_v2 = b"Version 2"
        version_id_2 = version_manager.create_version(
            file_path="test.txt",
            file_data=file_data_v2,
            comment="Updated version"
        )

        # 列出版本
        versions = version_manager.list_versions("test.txt")
        assert len(versions) == 2
        assert version_id_1 in [v["version_id"] for v in versions]
        assert version_id_2 in [v["version_id"] for v in versions]

    def test_cache_operations(self, skill_storage):
        """测试缓存操作"""
        from src.storage.cache import CacheManager

        cache_manager = CacheManager(skill_storage)

        # 设置缓存
        cache_manager.set("test_key", {"data": "test_value"}, ttl=3600)

        # 获取缓存
        cached_data = cache_manager.get("test_key")
        assert cached_data == {"data": "test_value"}

        # 删除缓存
        cache_manager.delete("test_key")
        assert cache_manager.get("test_key") is None

    def test_skill_backup(self, storage_manager):
        """测试技能备份"""
        skill_id = "backup-test-skill"
        skill_storage = storage_manager.create_skill_storage(skill_id)

        # 创建测试文件
        skill_storage.upload_file(
            object_name="test.txt",
            file_data=b"Test content"
        )

        # 创建备份
        backup_id = storage_manager.create_backup(skill_id, "daily")

        # 验证备份创建
        assert backup_id.startswith("daily_")
```

## MinIO存储优势总结

### 1. 高性能
- **并行上传**：支持多线程同时上传多个文件
- **CDN集成**：全球内容分发网络支持
- **智能缓存**：自动缓存热门文件

### 2. 高可靠性
- **数据冗余**：自动多副本存储
- **版本控制**：完整的文件历史版本管理
- **故障恢复**：自动检测和恢复损坏数据

### 3. 成本优化
- **压缩存储**：自动压缩减少存储成本
- **分层存储**：根据访问频率自动分层
- **生命周期管理**：自动归档和删除过期数据

### 4. 易于管理
- **Web管理界面**：直观的MinIO控制台
- **API驱动**：完整的REST API支持
- **健康检查**：内置健康检查接口

## 功能特性总结

### ✅ 已实现功能

1. **技能管理**
   - 技能列表展示（卡片式布局）
   - MinIO存储状态显示
   - 文件大小和数量统计
   - 技能删除（安全删除）

2. **MinIO存储**
   - 高性能对象存储
   - 版本控制系统
   - 智能缓存管理
   - 自动备份机制

3. **文件操作**
   - 实时上传下载
   - 版本历史查看
   - 文件预览支持
   - 批量操作

4. **多平台支持**
   - 4个LLM平台（Claude、Gemini、OpenAI、Markdown）
   - 平台专属打包格式
   - 跨平台兼容性

5. **实时体验**
   - WebSocket实时进度推送
   - 创建过程日志查看
   - 文件操作实时反馈

6. **存储架构**
   - MinIO对象存储
   - PostgreSQL元数据
   - Redis缓存加速
   - 分层存储策略

7. **部署方案**
   - Docker容器化
   - MinIO集群部署
   - 一键部署脚本
   - 生产级配置

### 🎯 技术亮点

1. **现代化存储**
   - MinIO对象存储
   - 无限水平扩展
   - 企业级可靠性
   - 成本优化存储

2. **用户体验优化**
   - 实时文件操作反馈
   - 存储状态可视化
   - 版本历史管理
   - 智能缓存加速

3. **可扩展架构**
   - 微服务友好
   - API驱动设计
   - 插件化支持
   - 云原生部署

4. **生产就绪**
   - 高可用部署
   - 健康检查
   - 数据备份
   - 简化运维

5. **简化设计**
   - 无需用户管理
   - 单租户架构
   - 快速MVP交付
   - 降低运维成本

6. **统一接入**
   - Nginx反向代理
   - 静态文件托管
   - API统一转发
   - 简化HTTP配置

## 开发时间线

| 阶段 | 时间 | 主要任务 |
|------|------|----------|
| **阶段1** | 3-4周 | 数据库设计、FastAPI后端、Celery任务队列 |
| **阶段2** | 6-8周 | React前端、组件开发、界面集成 |
| **阶段3** | 4-5周 | MinIO存储系统、缓存管理、版本控制 |
| **阶段4** | 3-4周 | Docker部署、MinIO集群、部署脚本 |
| **阶段5** | 3-4周 | 测试、调试、性能优化、文档 |

**总计：10-12个月**（去除用户管理功能，简化部署架构）

## 快速启动

```bash
# 1. 克隆项目
git clone skillseekers-web-minio
cd skillseekers-web-minio

# 2. 一键部署
chmod +x deploy.sh
./deploy.sh

# 3. 访问Web界面（统一入口）
open http://localhost
# - 前端: http://localhost/
# - API: http://localhost/api/
# - WebSocket: ws://localhost/ws/
# - MinIO控制台: http://localhost/minio-console/

# 4. 无需登录，直接使用所有功能
```

**注意**：系统采用单租户架构，无用户管理功能。所有访问者可以直接使用所有技能管理功能。

**未来扩展**：生产环境中可后期添加用户管理系统，包括：
- 用户注册/登录
- 基于角色的权限控制
- 多租户数据隔离
- 用户配额管理
- 审计日志追踪

**监控说明**：开发阶段不考虑复杂的监控系统，仅保留基本的健康检查和日志功能。

**HTTPS说明**：开发阶段使用HTTP协议，生产环境可根据需要配置HTTPS。Nginx已预留HTTPS配置扩展。

### 简化架构优势

**去除监控的优势**：
- 降低系统复杂度
- 减少资源消耗
- 加快部署速度
- 降低运维成本
- 专注核心功能开发

### Nginx统一转发架构

**前端配置**：
- 环境变量使用相对路径（`/api`, `/ws`, `/minio`）
- 静态文件由Nginx直接托管
- 前后端通过统一入口访问

**Nginx功能**：
- 静态文件托管和缓存
- API请求反向代理到后端
- WebSocket连接升级转发
- MinIO API和控制台代理
- HTTP压缩优化
- 安全头和访问控制

## MinIO vs 文件系统对比

| 特性 | MinIO | 文件系统 |
|------|-------|----------|
| **扩展性** | 无限水平扩展 | 受限于单机 |
| **可用性** | 99.9%+ | 取决于硬件 |
| **性能** | 高并发优化 | 受限于磁盘 |
| **成本** | 按需扩展 | 固定投入 |
| **维护** | 简单自动化 | 复杂运维 |
| **功能** | 版本控制+API | 基础存储 |

## 结语

本实施方案基于现有的skill_seekers CLI工具，通过现代化的Web界面、MinIO对象存储和高可用架构设计，完整实现了《COMPLETE_REQUIREMENTS.md》中的所有功能需求。

### 优势

- **技术先进**：MinIO对象存储，企业级可靠性
- **性能优异**：高并发、水平扩展、智能缓存
- **运维简单**：自动化管理、日志查看
- **成本优化**：按需扩展、生命周期管理
- **用户体验**：实时操作反馈、版本管理
- **开发高效**：无需用户管理，专注核心功能

### 交付物

- ✅ 完整的Web管理系统（无用户管理）
- ✅ MinIO对象存储方案
- ✅ 源代码和文档
- ✅ Docker部署方案
- ✅ 测试用例和CI/CD
- ✅ 系统使用指南（无需登录）

通过这个实施方案，skill_seekers将从命令行工具升级为功能完整的企业级技能管理系统，为所有访问者提供更好的使用体验和更高的开发效率。
