/**
 * 技能服务
 *
 * 封装技能相关的API调用，提供统一的接口
 */

import { skillsApi, filesApi } from '@/api/client';
import type { Skill, SkillFilters, CreateSkillInput, UpdateSkillInput } from '@/types/skill.types';

export class SkillService {
  /**
   * 获取技能列表
   */
  static async getSkills(filters?: SkillFilters) {
    try {
      const response = await skillsApi.getSkills({
        platforms: filters?.platforms,
        statuses: filterStatus(filters?.statuses),
        tags: filters?.tags,
        search: filters?.search,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch skills:', error);
      throw error;
    }
  }

  /**
   * 获取单个技能详情
   */
  static async getSkill(id: string): Promise<Skill> {
    try {
      return await skillsApi.getSkill(id);
    } catch (error) {
      console.error(`Failed to fetch skill ${id}:`, error);
      throw error;
    }
  }

  /**
   * 创建技能
   */
  static async createSkill(data: CreateSkillInput): Promise<Skill> {
    try {
      return await skillsApi.createSkill(data);
    } catch (error) {
      console.error('Failed to create skill:', error);
      throw error;
    }
  }

  /**
   * 更新技能
   */
  static async updateSkill(id: string, data: UpdateSkillInput): Promise<Skill> {
    try {
      return await skillsApi.updateSkill(id, data);
    } catch (error) {
      console.error(`Failed to update skill ${id}:`, error);
      throw error;
    }
  }

  /**
   * 删除技能
   */
  static async deleteSkill(id: string): Promise<void> {
    try {
      await skillsApi.deleteSkill(id);
    } catch (error) {
      console.error(`Failed to delete skill ${id}:`, error);
      throw error;
    }
  }

  /**
   * 复制技能
   */
  static async duplicateSkill(id: string): Promise<Skill> {
    try {
      return await skillsApi.duplicateSkill(id);
    } catch (error) {
      console.error(`Failed to duplicate skill ${id}:`, error);
      throw error;
    }
  }

  /**
   * 导出技能
   */
  static async exportSkill(id: string, platform: string): Promise<Blob> {
    try {
      return await skillsApi.exportSkill(id, platform);
    } catch (error) {
      console.error(`Failed to export skill ${id} to ${platform}:`, error);
      throw error;
    }
  }

  /**
   * 获取技能文件列表
   */
  static async getSkillFiles(skillId: string) {
    try {
      return await filesApi.getSkillFiles(skillId);
    } catch (error) {
      console.error(`Failed to fetch files for skill ${skillId}:`, error);
      throw error;
    }
  }

  /**
   * 获取技能文件内容
   */
  static async getSkillFile(skillId: string, filePath: string) {
    try {
      return await filesApi.getSkillFile(skillId, filePath);
    } catch (error) {
      console.error(`Failed to fetch file ${filePath} for skill ${skillId}:`, error);
      throw error;
    }
  }

  /**
   * 创建技能文件
   */
  static async createSkillFile(skillId: string, data: { path: string; content: string }) {
    try {
      return await filesApi.createFile(skillId, data);
    } catch (error) {
      console.error(`Failed to create file for skill ${skillId}:`, error);
      throw error;
    }
  }

  /**
   * 更新技能文件
   */
  static async updateSkillFile(skillId: string, filePath: string, data: { content: string }) {
    try {
      return await filesApi.updateFile(skillId, filePath, data);
    } catch (error) {
      console.error(`Failed to update file ${filePath} for skill ${skillId}:`, error);
      throw error;
    }
  }

  /**
   * 删除技能文件
   */
  static async deleteSkillFile(skillId: string, filePath: string): Promise<void> {
    try {
      await filesApi.deleteFile(skillId, filePath);
    } catch (error) {
      console.error(`Failed to delete file ${filePath} for skill ${skillId}:`, error);
      throw error;
    }
  }

  /**
   * 下载技能文件
   */
  static async downloadSkillFile(skillId: string, filePath: string): Promise<Blob> {
    try {
      const file = await this.getSkillFile(skillId, filePath);
      const response = await fetch(file.downloadUrl);
      return await response.blob();
    } catch (error) {
      console.error(`Failed to download file ${filePath} for skill ${skillId}:`, error);
      throw error;
    }
  }

  /**
   * 批量删除技能
   */
  static async batchDeleteSkills(skillIds: string[]): Promise<void> {
    try {
      await Promise.all(skillIds.map(id => this.deleteSkill(id)));
    } catch (error) {
      console.error('Failed to batch delete skills:', error);
      throw error;
    }
  }

  /**
   * 批量导出技能
   */
  static async batchExportSkills(skillIds: string[], platform: string): Promise<Blob> {
    try {
      // 暂时不支持批量导出，返回第一个技能的导出
      // TODO: 实现真正的批量导出API
      return await this.exportSkill(skillIds[0], platform);
    } catch (error) {
      console.error('Failed to batch export skills:', error);
      throw error;
    }
  }

  /**
   * 搜索技能
   */
  static async searchSkills(query: string, filters?: {
    platforms?: string[];
    statuses?: string[];
  }): Promise<Skill[]> {
    try {
      // TODO: 实现真正的搜索API
      // 目前使用getSkills进行过滤
      const allSkills = await this.getSkills();
      return allSkills.filter(skill =>
        skill.name.toLowerCase().includes(query.toLowerCase()) ||
        skill.description.toLowerCase().includes(query.toLowerCase())
      );
    } catch (error) {
      console.error('Failed to search skills:', error);
      throw error;
    }
  }
}

/**
 * 将状态数组转换为API期望的格式
 */
function filterStatus(statuses?: string[]): string[] | undefined {
  if (!statuses || statuses.length === 0) {
    return undefined;
  }

  // 转换状态值以匹配API期望
  const statusMap: Record<string, string> = {
    'creating': 'pending',
    'enhancing': 'pending',
  };

  return statuses.map(status => statusMap[status] || status);
}

export default SkillService;
