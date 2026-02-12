// ============================================================
// TEMPLATE REGISTRY (Open/Closed Principle)
// Manages template renderers using Strategy pattern
// ============================================================

import { ITemplateRenderer } from '../../domain/interfaces/ITemplateRenderer';
import { TemplateMetadata } from '@cv-generator/shared-types';

export class TemplateNotFoundError extends Error {
  constructor(templateId: string) {
    super(`Template '${templateId}' not found in registry`);
    this.name = 'TemplateNotFoundError';
  }
}

export class TemplateRegistry {
  private renderers = new Map<string, ITemplateRenderer>();
  
  register(renderer: ITemplateRenderer): void {
    if (this.renderers.has(renderer.templateId)) {
      throw new Error(`Template '${renderer.templateId}' already registered`);
    }
    this.renderers.set(renderer.templateId, renderer);
  }
  
  get(templateId: string): ITemplateRenderer {
    const renderer = this.renderers.get(templateId);
    if (!renderer) {
      throw new TemplateNotFoundError(templateId);
    }
    return renderer;
  }
  
  has(templateId: string): boolean {
    return this.renderers.has(templateId);
  }
  
  listAvailable(filters?: {
    locale?: string;
    category?: string;
    isPremium?: boolean;
  }): TemplateMetadata[] {
    let templates = Array.from(this.renderers.values());
    
    if (filters?.locale) {
      templates = templates.filter(t => t.supports(filters.locale!));
    }
    if (filters?.category) {
      templates = templates.filter(t => t.metadata.category === filters.category);
    }
    if (filters?.isPremium !== undefined) {
      templates = templates.filter(t => t.metadata.isPremium === filters.isPremium);
    }
    
    return templates.map(t => t.metadata);
  }
  
  getAll(): ITemplateRenderer[] {
    return Array.from(this.renderers.values());
  }
}
