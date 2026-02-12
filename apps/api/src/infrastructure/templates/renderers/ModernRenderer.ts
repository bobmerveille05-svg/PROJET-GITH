// ============================================================
// MODERN TEMPLATE RENDERER
// Implements ITemplateRenderer for the Modern template
// ============================================================

import { ITemplateRenderer, IPageBreakStrategy } from '../../../domain/interfaces/ITemplateRenderer';
import { ResumeRenderData, ThemeConfig, TemplateMetadata, FontSize, Spacing } from '@cv-generator/shared-types';

export class SmartPageBreakStrategy implements IPageBreakStrategy {
  constructor(private options: { maxPages: number; orphanThreshold: number; widowThreshold: number }) {}
  
  optimize(html: string): string {
    // Page break optimization logic would go here
    // This is a simplified implementation
    return html;
  }
}

export class ModernTemplateRenderer implements ITemplateRenderer {
  readonly templateId = 'modern';
  readonly metadata: TemplateMetadata = {
    name: 'Modern',
    description: 'Clean and contemporary design with accent colors',
    thumbnail: '/templates/modern-thumb.png',
    category: 'general',
    isPremium: false,
    supportedLocales: ['en-US', 'fr-FR', 'de-DE', 'es-ES', 'ja-JP', 'ar-SA'],
    maxPages: 2,
    supportsPhoto: true,
    features: ['gradient-header', 'skill-badges', 'timeline-dots'],
  };
  
  supports(locale: string): boolean {
    return this.metadata.supportedLocales.includes(locale);
  }
  
  render(data: ResumeRenderData, config: ThemeConfig): string {
    const css = this.getCSS(config);
    const headerHTML = this.renderHeader(data.contact, config);
    const sectionsHTML = data.sections
      .filter(s => s.visible)
      .sort((a, b) => a.sortOrder - b.sortOrder)
      .map(s => this.renderSection(s, config))
      .join('\n');
    
    return `
      <!DOCTYPE html>
      <html lang="${data.locale}" dir="${data.direction}">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resume</title>
        <style>${css}</style>
      </head>
      <body class="resume-page">
        ${headerHTML}
        <main class="resume-body">${sectionsHTML}</main>
      </body>
      </html>
    `;
  }
  
  getCSS(config: ThemeConfig): string {
    const fontSizeMap: Record<FontSize, string> = { 
      small: '10px', 
      medium: '11px', 
      large: '12px' 
    };
    const spacingMap: Record<Spacing, string> = { 
      compact: '0.5rem', 
      comfortable: '0.75rem', 
      spacious: '1rem' 
    };
    
    return `
      :root {
        --primary: ${config.primaryColor};
        --font-family: ${config.fontFamily}, system-ui, sans-serif;
        --font-size-base: ${fontSizeMap[config.fontSize]};
        --section-gap: ${spacingMap[config.spacing]};
      }
      
      @page {
        size: A4;
        margin: 15mm 15mm 20mm 15mm;
      }
      
      body {
        font-family: var(--font-family);
        font-size: var(--font-size-base);
        line-height: 1.5;
        color: #1f2937;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        margin: 0;
        padding: 0;
      }
      
      .resume-page {
        max-width: 210mm;
        margin: 0 auto;
        background: white;
      }
      
      /* Header */
      .resume-header {
        background: linear-gradient(135deg, var(--primary), #0ea5e9);
        color: white;
        padding: 2rem;
        margin-bottom: 1.5rem;
      }
      
      .header-name {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.25rem 0;
      }
      
      .header-title {
        font-size: 1.1rem;
        opacity: 0.95;
        margin: 0 0 1rem 0;
      }
      
      .header-contact {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-size: 0.9rem;
      }
      
      .contact-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
      }
      
      /* Body */
      .resume-body {
        padding: 0 2rem 2rem;
      }
      
      .section-block {
        break-inside: avoid;
        page-break-inside: avoid;
        margin-bottom: var(--section-gap);
      }
      
      .section-title {
        color: var(--primary);
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary);
      }
      
      /* Experience */
      .experience-item {
        break-inside: avoid;
        page-break-inside: avoid;
        margin-bottom: 1.5rem;
      }
      
      .experience-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0.5rem;
      }
      
      .experience-role {
        font-weight: 600;
        font-size: 1.05rem;
      }
      
      .experience-company {
        color: var(--primary);
        font-weight: 500;
      }
      
      .experience-date {
        color: #6b7280;
        font-size: 0.9rem;
      }
      
      .experience-location {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
      }
      
      .experience-bullets {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      
      .experience-bullets li {
        position: relative;
        padding-left: 1.5rem;
        margin-bottom: 0.4rem;
      }
      
      .experience-bullets li:before {
        content: "•";
        color: var(--primary);
        font-weight: bold;
        position: absolute;
        left: 0.5rem;
      }
      
      /* Skills */
      .skill-group {
        margin-bottom: 1rem;
      }
      
      .skill-category {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #374151;
      }
      
      .skill-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      
      .skill-badge {
        background: var(--primary);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 500;
      }
      
      /* Education */
      .education-item {
        break-inside: avoid;
        margin-bottom: 1.25rem;
      }
      
      .education-degree {
        font-weight: 600;
        font-size: 1.05rem;
      }
      
      .education-institution {
        color: var(--primary);
        font-weight: 500;
      }
      
      .education-details {
        color: #6b7280;
        font-size: 0.9rem;
      }
      
      /* Summary */
      .summary-text {
        line-height: 1.7;
        color: #4b5563;
        margin-bottom: 1rem;
      }
      
      ${config.customCSS || ''}
    `;
  }
  
  getPageBreakStrategy(): IPageBreakStrategy {
    return new SmartPageBreakStrategy({
      maxPages: this.metadata.maxPages,
      orphanThreshold: 2,
      widowThreshold: 2,
    });
  }
  
  private renderHeader(contact: any, config: ThemeConfig): string {
    const fullName = this.escapeHTML(`${contact.fullName || ''}`);
    const title = contact.professionalTitle ? this.escapeHTML(contact.professionalTitle) : '';
    
    const contactItems: string[] = [];
    if (contact.email) contactItems.push(`<span class="contact-item">📧 ${this.escapeHTML(contact.email)}</span>`);
    if (contact.phone) contactItems.push(`<span class="contact-item">📞 ${this.escapeHTML(contact.phone)}</span>`);
    if (contact.location) contactItems.push(`<span class="contact-item">📍 ${this.escapeHTML(contact.location)}</span>`);
    if (contact.links?.linkedin) contactItems.push(`<span class="contact-item">🔗 LinkedIn</span>`);
    if (contact.links?.website) contactItems.push(`<span class="contact-item">🌐 Website</span>`);
    
    return `
      <header class="resume-header">
        <h1 class="header-name">${fullName}</h1>
        ${title ? `<div class="header-title">${title}</div>` : ''}
        <div class="header-contact">
          ${contactItems.join('\n')}
        </div>
      </header>
      ${contact.summary ? `<div class="summary-text" style="padding: 0 2rem;">${this.escapeHTML(contact.summary)}</div>` : ''}
    `;
  }
  
  private renderSection(section: any, config: ThemeConfig): string {
    const renderers: Record<string, (s: any) => string> = {
      experience: (s) => this.renderExperience(s),
      education: (s) => this.renderEducation(s),
      skills: (s) => this.renderSkills(s),
    };
    
    const renderer = renderers[section.type] || (() => '');
    return `
      <section class="section-block">
        <h2 class="section-title">${this.escapeHTML(section.title)}</h2>
        ${renderer(section)}
      </section>
    `;
  }
  
  private renderExperience(section: any): string {
    return section.items.map((item: any) => `
      <div class="experience-item">
        <div class="experience-header">
          <div>
            <div class="experience-role">${this.escapeHTML(item.jobTitle || '')}</div>
            <div class="experience-company">${this.escapeHTML(item.companyName || '')}</div>
          </div>
          <div class="experience-date">${this.formatDateRange(item)}</div>
        </div>
        ${item.location ? `<div class="experience-location">${this.escapeHTML(item.location)}</div>` : ''}
        ${item.bullets && item.bullets.length > 0 ? `
          <ul class="experience-bullets">
            ${item.bullets.filter((b: any) => b.isVisible).map((b: any) => 
              `<li>${this.escapeHTML(b.text)}</li>`
            ).join('')}
          </ul>
        ` : ''}
      </div>
    `).join('');
  }
  
  private renderEducation(section: any): string {
    return section.items.map((item: any) => `
      <div class="education-item">
        <div class="education-degree">${this.escapeHTML(item.degree || '')}</div>
        <div class="education-institution">${this.escapeHTML(item.institution || '')}</div>
        <div class="education-details">
          ${this.formatDateRange(item)}
          ${item.gpa ? ` • GPA: ${this.escapeHTML(item.gpa)}` : ''}
        </div>
      </div>
    `).join('');
  }
  
  private renderSkills(section: any): string {
    return section.items.map((group: any) => `
      <div class="skill-group">
        <div class="skill-category">${this.escapeHTML(group.category)}</div>
        <div class="skill-badges">
          ${group.skills.map((skill: any) => 
            `<span class="skill-badge">${this.escapeHTML(skill.name)}</span>`
          ).join('')}
        </div>
      </div>
    `).join('');
  }
  
  private formatDateRange(item: any): string {
    if (item.isCurrent && item.startDate) {
      return `${item.startDate} – Present`;
    }
    if (item.startDate && item.endDate) {
      return `${item.startDate} – ${item.endDate}`;
    }
    return item.startDate || '';
  }
  
  private escapeHTML(str: string): string {
    const escapeMap: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return str.replace(/[&<>"']/g, (m) => escapeMap[m]);
  }
}
