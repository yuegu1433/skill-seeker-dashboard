/**
 * Integration Test: WebSocket Progress Tracking
 *
 * Tests real-time progress updates and WebSocket functionality
 */

import { test, expect } from '@playwright/test';
import { testHelpers } from '../utils/test-helpers';

test.describe('WebSocket Progress Tracking', () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate before each test
    await testHelpers.login(page);
  });

  test('should establish WebSocket connection', async ({ page }) => {
    // Navigate to skills page
    await page.goto('/skills');

    // Check if WebSocket connection is established
    const wsConnected = await page.evaluate(() => {
      return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8000/ws');
        let timeout;

        ws.onopen = () => {
          ws.close();
          clearTimeout(timeout);
          resolve(true);
        };

        ws.onerror = () => {
          clearTimeout(timeout);
          resolve(false);
        };

        timeout = setTimeout(() => {
          ws.close();
          resolve(false);
        }, 5000);
      });
    });

    expect(wsConnected).toBe(true);
  });

  test('should receive progress updates', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Progress Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');

    // Click on the skill
    await page.click('[data-testid="skill-card"]');

    // Wait for skill detail page to load
    await expect(page.locator('[data-testid="skill-name"]')).toContainText('Progress Test Skill');

    // Mock WebSocket connection
    await page.evaluate(() => {
      const originalWebSocket = window.WebSocket;
      let mockWs: any;

      (window as any).WebSocket = class MockWebSocket {
        readyState = 1; // OPEN
        onopen: ((this: WebSocket, ev: Event) => any) | null = null;
        onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null = null;
        onerror: ((this: WebSocket, Event) => any) | null = null;
        onclose: ((this: WebSocket, CloseEvent) => any) | null = null;

        constructor(public url: string) {
          setTimeout(() => {
            if (this.onopen) {
              this.onopen({} as Event);
            }
          }, 100);
        }

        send(data: any) {
          // Handle incoming messages
        }

        close() {
          if (this.onclose) {
            this.onclose({} as CloseEvent);
          }
        }
      };

      mockWs = new (window as any).WebSocket('ws://localhost:8000/ws');
    });

    // Simulate progress update
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'PROGRESS_UPDATE',
          payload: {
            skillId: 'test-skill-id',
            progress: 50,
            stage: 'Processing',
            status: 'running'
          }
        }));
      };
    });

    // Wait for progress to update
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('value', '50');
    await expect(page.locator('[data-testid="progress-stage"]')).toContainText('Processing');
  });

  test('should display log updates', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Log Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');
    await page.click('[data-testid="skill-card"]');

    // Wait for page to load
    await expect(page.locator('[data-testid="skill-name"]')).toContainText('Log Test Skill');

    // Verify log viewer is present
    await expect(page.locator('[data-testid="log-viewer"]')).toBeVisible();

    // Simulate log message
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'TASK_LOG',
          payload: {
            taskId: 'test-task-id',
            log: {
              timestamp: new Date().toISOString(),
              level: 'info',
              message: 'Starting skill creation process'
            }
          }
        }));
      };
    });

    // Verify log appears
    await expect(page.locator('[data-testid="log-entry"]')).toContainText('Starting skill creation process');
  });

  test('should handle WebSocket disconnection', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Disconnect Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');
    await page.click('[data-testid="skill-card"]');

    // Verify WebSocket is connected
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('已连接');

    // Simulate disconnection
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.close();
      };
    });

    // Wait for disconnection to be detected
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('连接已断开');

    // Verify retry attempt
    await expect(page.locator('[data-testid="reconnecting"]')).toBeVisible();
  });

  test('should handle WebSocket reconnection', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Reconnect Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');
    await page.click('[data-testid="skill-card"]');

    // Simulate disconnection
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.close();
      };
    });

    // Wait for disconnection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('连接已断开');

    // Simulate reconnection
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        // Connection restored
      };
    });

    // Verify reconnection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('已连接');
  });

  test('should display error messages', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Error Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');
    await page.click('[data-testid="skill-card"]');

    // Simulate error message
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'ERROR',
          payload: {
            message: 'Skill creation failed',
            code: 'CREATION_FAILED'
          }
        }));
      };
    });

    // Verify error is displayed
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Skill creation failed');
  });

  test('should update task status in real-time', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Status Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');
    await page.click('[data-testid="skill-card"]');

    // Wait for page to load
    await expect(page.locator('[data-testid="skill-name"]')).toContainText('Status Test Skill');

    // Verify initial status
    await expect(page.locator('[data-testid="skill-status"]')).toContainText('进行中');

    // Simulate status update
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'STATUS_UPDATE',
          payload: {
            skillId: 'test-skill-id',
            status: 'completed'
          }
        }));
      };
    });

    // Verify status updated
    await expect(page.locator('[data-testid="skill-status"]')).toContainText('已完成');
  });

  test('should handle multiple concurrent updates', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Concurrent Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');
    await page.click('[data-testid="skill-card"]');

    // Simulate multiple rapid updates
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        // Send progress updates
        ws.send(JSON.stringify({
          type: 'PROGRESS_UPDATE',
          payload: {
            skillId: 'test-skill-id',
            progress: 25,
            stage: 'Stage 1',
            status: 'running'
          }
        }));

        setTimeout(() => {
          ws.send(JSON.stringify({
            type: 'PROGRESS_UPDATE',
            payload: {
              skillId: 'test-skill-id',
              progress: 50,
              stage: 'Stage 2',
              status: 'running'
            }
          }));
        }, 100);

        setTimeout(() => {
          ws.send(JSON.stringify({
            type: 'PROGRESS_UPDATE',
            payload: {
              skillId: 'test-skill-id',
              progress: 75,
              stage: 'Stage 3',
              status: 'running'
            }
          }));
        }, 200);
      };
    });

    // Wait for final progress
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('value', '75');
  });

  test('should handle network latency', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Latency Test Skill' });

    // Navigate to skill detail page
    await page.goto('/skills');
    await page.click('[data-testid="skill-card"]');

    // Simulate slow network
    await page.route('**/ws', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      route.continue();
    });

    // Verify loading indicator appears
    await expect(page.locator('[data-testid="connecting"]')).toBeVisible();

    // Wait for connection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('已连接');
  });
});
