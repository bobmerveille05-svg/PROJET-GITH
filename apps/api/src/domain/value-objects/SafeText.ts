// ============================================================
// VALUE OBJECT: SafeText
// Ensures text is properly sanitized and normalized
// ============================================================

import { CHAR_LIMITS } from '@cv-generator/shared-types';

type TextCategory = keyof typeof CHAR_LIMITS;

export class SafeText {
  private constructor(private readonly value: string) {}

  static create(
    input: string,
    category: TextCategory = 'bullet'
  ): SafeText {
    const maxLen = CHAR_LIMITS[category];
    
    let text = input
      .normalize('NFC')                              // Normalisation Unicode
      .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '') // Supprime control chars (sauf \n, \r, \t)
      .replace(/\s+/g, ' ')                          // Normalise whitespace
      .trim();
    
    if (text.length > maxLen) {
      text = text.substring(0, maxLen);
    }
    
    return new SafeText(text);
  }

  toString(): string {
    return this.value;
  }

  get length(): number {
    return this.value.length;
  }

  isEmpty(): boolean {
    return this.value.length === 0;
  }

  equals(other: SafeText): boolean {
    return this.value === other.value;
  }
}
