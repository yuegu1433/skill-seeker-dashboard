/**
 * Cache Manager Utility.
 *
 * This module provides a comprehensive caching system for managing
 * client-side caches with various storage strategies.
 */

export interface CacheConfig {
  /** Maximum cache size in bytes */
  maxSize?: number;
  /** Auto cleanup interval in milliseconds */
  cleanupInterval?: number;
  /** Enable compression */
  compress?: boolean;
  /** Enable encryption */
  encrypt?: boolean;
  /** Encryption key */
  encryptionKey?: string;
  /** Compressor implementation */
  compressor?: (data: string) => string;
  /** Decompressor implementation */
  decompressor?: (data: string) => string;
  /** Serializer implementation */
  serializer?: (data: any) => string;
  /** Deserializer implementation */
  deserializer?: (data: string) => any;
}

export interface CacheEntry<T = any> {
  /** Entry key */
  key: string;
  /** Entry value */
  value: T;
  /** Creation timestamp */
  created: number;
  /** Last access timestamp */
  accessed: number;
  /** Expiration timestamp */
  expires: number;
  /** Access count */
  accessCount: number;
  /** Entry size in bytes */
  size: number;
  /** Entry metadata */
  metadata?: Record<string, any>;
  /** Compression flag */
  compressed?: boolean;
  /** Encryption flag */
  encrypted?: boolean;
}

export type CacheStrategy = 'memory' | 'localStorage' | 'sessionStorage' | 'indexedDB' | 'hybrid';

export interface CacheStats {
  /** Cache hits */
  hits: number;
  /** Cache misses */
  misses: number;
  /** Cache sets */
  sets: number;
  /** Cache deletes */
  deletes: number;
  /** Cache clears */
  clears: number;
  /** Cache invalidations */
  invalidations: number;
  /** Cache errors */
  errors: number;
}

export interface CacheUpdateCallback {
  (data: {
    entries: Map<string, CacheEntry>;
    stats: CacheStats;
    hitRate: number;
    size: number;
  }): void;
}

/**
 * Compress data using LZ-String (simplified)
 */
const lzCompress = (data: string): string => {
  // Simple compression - in production, use a proper compression library
  return data;
};

/**
 * Decompress data using LZ-String (simplified)
 */
const lzDecompress = (data: string): string => {
  // Simple decompression - in production, use a proper compression library
  return data;
};

/**
 * JSON serializer
 */
const jsonSerializer = (data: any): string => {
  return JSON.stringify(data);
};

/**
 * JSON deserializer
 */
const jsonDeserializer = (data: string): any => {
  return JSON.parse(data);
};

/**
 * Simple XOR encryption
 */
const xorEncrypt = (data: string, key: string): string => {
  let result = '';
  for (let i = 0; i < data.length; i++) {
    result += String.fromCharCode(
      data.charCodeAt(i) ^ key.charCodeAt(i % key.length)
    );
  }
  return result;
};

/**
 * Cache Manager Class
 */
export class CacheManager {
  private config: Required<CacheConfig>;
  private strategy: CacheStrategy;
  private ttl: number;
  private analytics: boolean;
  private debug: boolean;
  private subscribers: Set<CacheUpdateCallback> = new Set();
  private entries: Map<string, CacheEntry> = new Map();
  private stats: CacheStats;
  private cleanupTimer: NodeJS.Timeout | null = null;
  private lruQueue: string[] = [];

  constructor(
    options: {
      config?: CacheConfig;
      strategy?: CacheStrategy;
      ttl?: number;
      analytics?: boolean;
      debug?: boolean;
    } = {}
  ) {
    const {
      config = {},
      strategy = 'memory',
      ttl = 300000, // 5 minutes
      analytics = false,
      debug = false,
    } = options;

    this.config = {
      maxSize: 50 * 1024 * 1024, // 50MB
      cleanupInterval: 60000, // 1 minute
      compress: false,
      encrypt: false,
      encryptionKey: '',
      compressor: lzCompress,
      decompressor: lzDecompress,
      serializer: jsonSerializer,
      deserializer: jsonDeserializer,
      ...config,
    };

    this.strategy = strategy;
    this.ttl = ttl;
    this.analytics = analytics;
    this.debug = debug;

    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      clears: 0,
      invalidations: 0,
      errors: 0,
    };

    this.lruQueue = [];
  }

  /**
   * Initialize cache manager
   */
  init(): void {
    this.log('Initializing cache manager');

    // Load existing cache for persistent strategies
    if (this.strategy !== 'memory') {
      this.loadFromStorage();
    }

    // Start cleanup timer
    this.startCleanupTimer();

    this.notifySubscribers();
  }

  /**
   * Destroy cache manager
   */
  destroy(): void {
    this.log('Destroying cache manager');

    // Stop cleanup timer
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }

    // Save to storage for persistent strategies
    if (this.strategy !== 'memory') {
      this.saveToStorage();
    }

    // Clear subscribers
    this.subscribers.clear();

    // Clear entries
    this.entries.clear();
    this.lruQueue = [];
  }

  /**
   * Subscribe to cache updates
   */
  subscribe(callback: CacheUpdateCallback): () => void {
    this.subscribers.add(callback);

    // Immediately call with current state
    callback({
      entries: this.entries,
      stats: this.stats,
      hitRate: this.getHitRate(),
      size: this.getSize(),
    });

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Get cache entry
   */
  get<T>(key: string): T | null {
    try {
      const entry = this.entries.get(key);

      if (!entry) {
        this.stats.misses++;
        this.notifySubscribers();
        return null;
      }

      // Check expiration
      if (Date.now() > entry.expires) {
        this.entries.delete(key);
        this.removeFromLRU(key);
        this.stats.misses++;
        this.notifySubscribers();
        return null;
      }

      // Update access info
      entry.accessed = Date.now();
      entry.accessCount++;

      // Update LRU queue
      this.updateLRU(key);

      this.stats.hits++;
      this.notifySubscribers();

      // Deserialize and decrypt if needed
      let value = entry.value as any;

      if (typeof value === 'string') {
        value = this.config.deserializer(value);
      }

      if (entry.encrypted && this.config.encrypt) {
        value = this.decrypt(value as string);
      }

      if (entry.compressed && this.config.compress) {
        value = this.decompress(value as string);
      }

      return value;
    } catch (error) {
      this.log(`Error getting cache entry for key: ${key}`, error);
      this.stats.errors++;
      this.notifySubscribers();
      return null;
    }
  }

  /**
   * Set cache entry
   */
  set<T>(key: string, value: T, options?: { ttl?: number; strategy?: CacheStrategy }): void {
    try {
      const now = Date.now();
      const ttl = options?.ttl || this.ttl;

      // Serialize and encrypt if needed
      let serializedValue = this.config.serializer(value);

      if (this.config.compress) {
        serializedValue = this.config.compressor(serializedValue);
      }

      if (this.config.encrypt) {
        serializedValue = this.encrypt(serializedValue);
      }

      // Calculate size
      const size = this.calculateSize(serializedValue);

      // Create entry
      const entry: CacheEntry<T> = {
        key,
        value: serializedValue as any,
        created: now,
        accessed: now,
        expires: now + ttl,
        accessCount: 0,
        size,
        compressed: this.config.compress,
        encrypted: this.config.encrypt,
      };

      // Check size limits
      if (size > this.config.maxSize) {
        throw new Error(`Cache entry size (${size} bytes) exceeds maximum size (${this.config.maxSize} bytes)`);
      }

      // Remove existing entry
      if (this.entries.has(key)) {
        this.removeFromLRU(key);
      }

      // Add to cache
      this.entries.set(key, entry);
      this.updateLRU(key);

      // Evict if necessary
      this.evictIfNeeded();

      this.stats.sets++;
      this.notifySubscribers();

      this.log(`Set cache entry: ${key} (${size} bytes)`);
    } catch (error) {
      this.log(`Error setting cache entry for key: ${key}`, error);
      this.stats.errors++;
      this.notifySubscribers();
      throw error;
    }
  }

  /**
   * Delete cache entry
   */
  delete(key: string): boolean {
    try {
      const deleted = this.entries.delete(key);
      this.removeFromLRU(key);

      if (deleted) {
        this.stats.deletes++;
        this.notifySubscribers();
        this.log(`Deleted cache entry: ${key}`);
      }

      return deleted;
    } catch (error) {
      this.log(`Error deleting cache entry for key: ${key}`, error);
      this.stats.errors++;
      this.notifySubscribers();
      return false;
    }
  }

  /**
   * Check if cache entry exists
   */
  has(key: string): boolean {
    return this.entries.has(key);
  }

  /**
   * Clear all cache
   */
  clear(): void {
    try {
      this.entries.clear();
      this.lruQueue = [];
      this.stats.clears++;
      this.notifySubscribers();
      this.log('Cleared all cache entries');
    } catch (error) {
      this.log('Error clearing cache', error);
      this.stats.errors++;
      this.notifySubscribers();
    }
  }

  /**
   * Get cache size
   */
  getSize(): number {
    let totalSize = 0;
    this.entries.forEach(entry => {
      totalSize += entry.size;
    });
    return totalSize;
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Get hit rate
   */
  getHitRate(): number {
    const total = this.stats.hits + this.stats.misses;
    return total > 0 ? (this.stats.hits / total) * 100 : 0;
  }

  /**
   * Clean expired entries
   */
  clean(): number {
    const now = Date.now();
    let cleanedCount = 0;

    this.entries.forEach((entry, key) => {
      if (now > entry.expires) {
        this.entries.delete(key);
        this.removeFromLRU(key);
        cleanedCount++;
      }
    });

    this.log(`Cleaned ${cleanedCount} expired cache entries`);
    return cleanedCount;
  }

  /**
   * Invalidate cache by pattern
   */
  invalidate(pattern: string): number {
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    let invalidatedCount = 0;

    this.entries.forEach((entry, key) => {
      if (regex.test(key)) {
        this.entries.delete(key);
        this.removeFromLRU(key);
        invalidatedCount++;
      }
    });

    this.stats.invalidations += invalidatedCount;
    this.notifySubscribers();

    this.log(`Invalidated ${invalidatedCount} cache entries matching pattern: ${pattern}`);
    return invalidatedCount;
  }

  /**
   * Preload data
   */
  async preload<T>(key: string, loader: () => Promise<T>, options?: { ttl?: number; strategy?: CacheStrategy }): Promise<T> {
    try {
      // Check if already cached
      const cached = this.get<T>(key);
      if (cached) {
        return cached;
      }

      // Load data
      const data = await loader();

      // Cache the result
      this.set(key, data, options);

      return data;
    } catch (error) {
      this.log(`Error preloading cache entry for key: ${key}`, error);
      this.stats.errors++;
      this.notifySubscribers();
      throw error;
    }
  }

  /**
   * Export cache
   */
  export(): string {
    try {
      const exportData = {
        entries: Array.from(this.entries.entries()).map(([key, entry]) => [key, entry]),
        stats: this.stats,
        timestamp: Date.now(),
      };

      return JSON.stringify(exportData);
    } catch (error) {
      this.log('Error exporting cache', error);
      this.stats.errors++;
      this.notifySubscribers();
      return '{}';
    }
  }

  /**
   * Import cache
   */
  import(data: string): void {
    try {
      const importData = JSON.parse(data);

      if (importData.entries) {
        this.entries = new Map(importData.entries);
        this.lruQueue = Array.from(this.entries.keys());
      }

      if (importData.stats) {
        this.stats = importData.stats;
      }

      this.notifySubscribers();
      this.log('Imported cache data');
    } catch (error) {
      this.log('Error importing cache', error);
      this.stats.errors++;
      this.notifySubscribers();
    }
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      clears: 0,
      invalidations: 0,
      errors: 0,
    };
    this.notifySubscribers();
  }

  /**
   * Get all keys
   */
  getKeys(): string[] {
    return Array.from(this.entries.keys());
  }

  /**
   * Get all entries
   */
  getEntries(): Map<string, CacheEntry> {
    return new Map(this.entries);
  }

  /**
   * Start cleanup timer
   */
  private startCleanupTimer(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    this.cleanupTimer = setInterval(() => {
      this.clean();
    }, this.config.cleanupInterval);
  }

  /**
   * Update LRU queue
   */
  private updateLRU(key: string): void {
    const index = this.lruQueue.indexOf(key);
    if (index > -1) {
      this.lruQueue.splice(index, 1);
    }
    this.lruQueue.push(key);
  }

  /**
   * Remove from LRU queue
   */
  private removeFromLRU(key: string): void {
    const index = this.lruQueue.indexOf(key);
    if (index > -1) {
      this.lruQueue.splice(index, 1);
    }
  }

  /**
   * Evict entries if needed
   */
  private evictIfNeeded(): void {
    while (this.getSize() > this.config.maxSize && this.lruQueue.length > 0) {
      const lruKey = this.lruQueue.shift();
      if (lruKey) {
        this.entries.delete(lruKey);
        this.log(`Evicted cache entry: ${lruKey}`);
      }
    }
  }

  /**
   * Calculate entry size
   */
  private calculateSize(data: string): number {
    // Approximate size calculation
    return new Blob([data]).size;
  }

  /**
   * Encrypt data
   */
  private encrypt(data: string): string {
    if (!this.config.encrypt || !this.config.encryptionKey) {
      return data;
    }
    return xorEncrypt(data, this.config.encryptionKey);
  }

  /**
   * Decrypt data
   */
  private decrypt(data: string): string {
    if (!this.config.encrypt || !this.config.encryptionKey) {
      return data;
    }
    return xorEncrypt(data, this.config.encryptionKey);
  }

  /**
   * Compress data
   */
  private compress(data: string): string {
    if (!this.config.compress) {
      return data;
    }
    return this.config.compressor(data);
  }

  /**
   * Decompress data
   */
  private decompress(data: string): string {
    if (!this.config.compress) {
      return data;
    }
    return this.config.decompressor(data);
  }

  /**
   * Load from storage
   */
  private loadFromStorage(): void {
    try {
      // Implementation depends on strategy
      // This is a simplified version
      const stored = localStorage.getItem(`cache:${this.strategy}`);
      if (stored) {
        const data = JSON.parse(stored);
        this.entries = new Map(data.entries || []);
        this.lruQueue = Array.from(this.entries.keys());
      }
    } catch (error) {
      this.log('Error loading from storage', error);
    }
  }

  /**
   * Save to storage
   */
  private saveToStorage(): void {
    try {
      const data = {
        entries: Array.from(this.entries.entries()),
        timestamp: Date.now(),
      };
      localStorage.setItem(`cache:${this.strategy}`, JSON.stringify(data));
    } catch (error) {
      this.log('Error saving to storage', error);
    }
  }

  /**
   * Notify subscribers
   */
  private notifySubscribers(): void {
    this.subscribers.forEach(callback => {
      callback({
        entries: this.entries,
        stats: this.stats,
        hitRate: this.getHitRate(),
        size: this.getSize(),
      });
    });
  }

  /**
   * Log debug message
   */
  private log(message: string, error?: any): void {
    if (this.debug) {
      if (error) {
        console.error(`[CacheManager] ${message}`, error);
      } else {
        console.log(`[CacheManager] ${message}`);
      }
    }
  }
}

export default CacheManager;
