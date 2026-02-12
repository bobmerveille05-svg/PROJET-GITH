// ============================================================
// PORT: IPDFGenerator
// PDF generation abstraction
// ============================================================

import { PDFGenerationOptions, PDFResult } from '@cv-generator/shared-types';

export interface IPDFGenerator {
  generate(html: string, options: PDFGenerationOptions): Promise<Buffer>;
  validateHTML(html: string): Promise<boolean>;
}
