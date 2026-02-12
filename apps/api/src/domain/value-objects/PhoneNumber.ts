// ============================================================
// VALUE OBJECT: PhoneNumber
// Handles phone number validation and normalization
// ============================================================

import { parsePhoneNumberFromString, PhoneNumber as LibPhoneNumber } from 'libphonenumber-js';

export class PhoneNumber {
  private constructor(
    public readonly raw: string,
    public readonly e164: string,
    public readonly countryCode: string,
    public readonly formatted: string,
    public readonly isValid: boolean
  ) {}

  static parse(input: string, defaultCountry?: string): PhoneNumber {
    const cleaned = input.replace(/[^\d+\-\s()]/g, '').trim();
    
    if (!cleaned) {
      return new PhoneNumber(input, '', defaultCountry || '', '', false);
    }
    
    const parsed = parsePhoneNumberFromString(
      cleaned,
      defaultCountry as any
    );
    
    if (parsed && parsed.isValid()) {
      return new PhoneNumber(
        input,
        parsed.format('E.164'),
        parsed.country || defaultCountry || '',
        parsed.formatNational(),
        true
      );
    }
    
    // Numéro invalide mais on stocke quand même le raw
    return new PhoneNumber(
      input,
      cleaned,
      defaultCountry || '',
      cleaned,
      false
    );
  }

  equals(other: PhoneNumber): boolean {
    return this.e164 === other.e164;
  }

  toJSON() {
    return {
      raw: this.raw,
      e164: this.e164,
      countryCode: this.countryCode,
      formatted: this.formatted,
      isValid: this.isValid,
    };
  }
}
