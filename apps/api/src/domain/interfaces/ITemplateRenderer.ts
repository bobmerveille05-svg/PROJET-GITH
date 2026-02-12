// ============================================================
// PORT: ITemplateRenderer (Strategy Pattern)
// Defines contract for template rendering engines
// ============================================================

import { ResumeRenderData, ThemeConfig, TemplateMetadata } from '@cv-generator/shared-types';

export interface IPageBreakStrategy {
  optimize(html: string): string;
}

export interface ITemplateRenderer {
  readonly templateId: string;
  readonly metadata: TemplateMetadata;
  
  render(data: ResumeRenderData, config: ThemeConfig): string;
  supports(locale: string): boolean;
  getCSS(config: ThemeConfig): string;
  getPageBreakStrategy(): IPageBreakStrategy;
}
