/**
 * Central Type Exports
 *
 * This file exports all type definitions from the types directory,
 * providing a single import point for the entire application.
 */

// Core types
export * from './skill.types';
export * from './task.types';
export * from './api.types';

// Common utility types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type PartialExcept<T, K extends keyof T> = Partial<T> & Pick<T, K>;
