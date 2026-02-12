// ============================================================
// SHARED TYPES - Cross-package TypeScript definitions
// ============================================================

// ---- Base Interfaces (Interface Segregation Principle) ----

export interface IIdentifiable {
  id: string;
}

export interface ISortable {
  sortOrder: number;
}

export interface IDateRange {
  startDate: string;   // ISO 8601: "2021-01"
  endDate?: string | null;
  isCurrent: boolean;
}

export interface IValidatable {
  validate(): ValidationResult;
}

export interface IRenderable {
  toRenderData(locale: string): Record<string, unknown>;
}

// ---- Enums ----

export enum ProficiencyLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert',
  NATIVE = 'native'
}

export enum SectionType {
  EXPERIENCE = 'experience',
  EDUCATION = 'education',
  SKILLS = 'skills',
  LANGUAGES = 'languages',
  CERTIFICATIONS = 'certifications',
  PROJECTS = 'projects',
  VOLUNTEERING = 'volunteering',
  PUBLICATIONS = 'publications',
  AWARDS = 'awards',
  CUSTOM = 'custom'
}

export enum ResumeStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived'
}

export enum SubscriptionTier {
  FREE = 'free',
  PRO = 'pro',
  ENTERPRISE = 'enterprise'
}

export enum LocationType {
  ONSITE = 'onsite',
  REMOTE = 'remote',
  HYBRID = 'hybrid'
}

export enum ContractType {
  FULL_TIME = 'full-time',
  PART_TIME = 'part-time',
  CONTRACT = 'contract',
  FREELANCE = 'freelance',
  INTERNSHIP = 'internship'
}

export enum FontSize {
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large'
}

export enum Spacing {
  COMPACT = 'compact',
  COMFORTABLE = 'comfortable',
  SPACIOUS = 'spacious'
}

export enum DisplayStyle {
  BADGES = 'badges',
  BARS = 'bars',
  LIST = 'list',
  DOTS = 'dots'
}

// ---- Contact Information ----

export interface ContactInfo {
  id: string;
  resumeId: string;
  firstName: string;
  lastName: string;
  professionalTitle?: string;
  email?: string;
  phoneRaw?: string;
  phoneE164?: string;
  phoneCountry?: string;
  city?: string;
  region?: string;
  countryCode?: string;
  postalCode?: string;
  linkedinUrl?: string;
  websiteUrl?: string;
  githubUrl?: string;
  portfolioUrl?: string;
  customLinks?: CustomLink[];
  photoUrl?: string;
  summary?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface CustomLink {
  label: string;
  url: string;
  icon?: string;
}

// ---- Resume ----

export interface Resume {
  id: string;
  userId: string;
  title: string;
  slug?: string;
  status: ResumeStatus;
  templateId: string;
  locale: string;
  themeConfig: ThemeConfig;
  sectionOrder: string[];
  version: number;
  createdAt: Date;
  updatedAt: Date;
  publishedAt?: Date;
}

export interface ThemeConfig {
  primaryColor: string;
  fontFamily: string;
  fontSize: FontSize;
  spacing: Spacing;
  showPhoto: boolean;
  customCSS?: string;
}

// ---- Sections ----

export interface ResumeSection {
  id: string;
  resumeId: string;
  type: SectionType;
  title?: string;
  visible: boolean;
  sortOrder: number;
  content: SectionContent[];
  createdAt: Date;
  updatedAt: Date;
}

export type SectionContent = 
  | ExperienceItem 
  | EducationItem 
  | SkillGroup 
  | LanguageItem 
  | CertificationItem
  | ProjectItem
  | CustomSectionItem;

// ---- Experience Section ----

export interface BulletPoint extends IIdentifiable, ISortable {
  text: string;
  isVisible: boolean;
}

export interface ExperienceItem extends IIdentifiable, ISortable, IDateRange {
  companyName: string;
  jobTitle: string;
  location?: string;
  locationType?: LocationType;
  contractType?: ContractType;
  bullets: BulletPoint[];
  companyUrl?: string;
  companyLogo?: string;
  tags?: string[];
}

// ---- Education Section ----

export interface EducationItem extends IIdentifiable, ISortable, IDateRange {
  institution: string;
  degree: string;
  fieldOfStudy?: string;
  location?: string;
  gpa?: string;
  gpaScale?: string;
  honors?: string[];
  relevantCourses?: string[];
  thesis?: string;
  activities?: string[];
}

// ---- Skills Section ----

export interface SkillGroup extends IIdentifiable, ISortable {
  category: string;
  skills: SkillItem[];
  displayStyle: DisplayStyle;
}

export interface SkillItem extends IIdentifiable, ISortable {
  name: string;
  level?: ProficiencyLevel;
  yearsOfExperience?: number;
}

// ---- Languages Section ----

export interface LanguageItem extends IIdentifiable, ISortable {
  language: string;
  proficiency: ProficiencyLevel;
  certifications?: string[];
}

// ---- Certifications Section ----

export interface CertificationItem extends IIdentifiable, ISortable {
  name: string;
  issuer: string;
  issueDate?: string;
  expiryDate?: string;
  credentialId?: string;
  credentialUrl?: string;
}

// ---- Projects Section ----

export interface ProjectItem extends IIdentifiable, ISortable, IDateRange {
  name: string;
  description: string;
  role?: string;
  url?: string;
  technologies?: string[];
  bullets?: BulletPoint[];
}

// ---- Custom Section ----

export interface CustomSectionItem extends IIdentifiable, ISortable {
  title: string;
  subtitle?: string;
  dateRange?: IDateRange;
  description?: string;
  bullets?: BulletPoint[];
  tags?: string[];
}

// ---- Templates ----

export interface Template {
  id: string;
  name: string;
  description: string;
  thumbnailUrl?: string;
  category: 'general' | 'creative' | 'academic' | 'technical';
  isPremium: boolean;
  supportedLocales: string[];
  layoutConfig: LayoutConfig;
  maxPages: number;
  supportsPhoto: boolean;
  createdAt: Date;
  isActive: boolean;
  version: number;
}

export interface LayoutConfig {
  columns: number;
  headerStyle: string;
  sectionSpacing: Spacing;
  features: string[];
}

export interface TemplateMetadata {
  name: string;
  description: string;
  thumbnail: string;
  category: 'general' | 'creative' | 'academic' | 'technical';
  isPremium: boolean;
  supportedLocales: string[];
  maxPages: number;
  supportsPhoto: boolean;
  features: string[];
}

// ---- PDF Generation ----

export interface PDFGeneration {
  id: string;
  resumeId: string;
  userId: string;
  fileUrl?: string;
  fileSizeBytes?: number;
  pageCount?: number;
  generationTimeMs?: number;
  templateId?: string;
  locale?: string;
  ipAddress?: string;
  userAgent?: string;
  status: 'pending' | 'success' | 'failed';
  errorMessage?: string;
  createdAt: Date;
}

export interface PDFGenerationOptions {
  format: 'A4' | 'Letter';
  printBackground: boolean;
  margin: {
    top: string;
    right: string;
    bottom: string;
    left: string;
  };
  displayHeaderFooter: boolean;
  timeout: number;
  maxPages: number;
}

export interface PDFResult {
  url: string;
  sizeBytes: number;
  generationTimeMs: number;
  pageCount?: number;
}

// ---- User ----

export interface User {
  id: string;
  externalAuthId: string;
  email: string;
  emailVerified: boolean;
  displayName?: string;
  avatarUrl?: string;
  locale: string;
  timezone: string;
  subscription: SubscriptionTier;
  createdAt: Date;
  updatedAt: Date;
  lastLoginAt?: Date;
  deletedAt?: Date;
}

// ---- Render Data (for templates) ----

export interface ResumeRenderData {
  contact: ContactRenderData;
  sections: SectionRenderData[];
  locale: string;
  direction: 'ltr' | 'rtl';
}

export interface ContactRenderData {
  fullName: string;
  professionalTitle?: string;
  email?: string;
  phone?: string;
  location?: string;
  links: Record<string, string>;
  summary?: string;
  photoUrl?: string;
}

export interface SectionRenderData {
  id: string;
  type: SectionType;
  title: string;
  visible: boolean;
  sortOrder: number;
  items: any[];
}

// ---- Validation ----

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

// ---- API DTOs ----

export interface CreateResumeDTO {
  title: string;
  templateId?: string;
  locale?: string;
}

export interface UpdateResumeDTO {
  title?: string;
  templateId?: string;
  status?: ResumeStatus;
  themeConfig?: Partial<ThemeConfig>;
}

export interface CreateSectionDTO {
  type: SectionType;
  title?: string;
  content?: any[];
}

export interface UpdateContactDTO {
  firstName?: string;
  lastName?: string;
  professionalTitle?: string;
  email?: string;
  phoneRaw?: string;
  phoneCountry?: string;
  city?: string;
  region?: string;
  countryCode?: string;
  linkedinUrl?: string;
  websiteUrl?: string;
  githubUrl?: string;
  summary?: string;
}

export interface PhoneValidationRequest {
  phone: string;
  country?: string;
}

export interface PhoneValidationResponse {
  valid: boolean;
  e164?: string;
  formatted?: string;
  countryCode?: string;
  error?: string;
}

// ---- API Response Wrapper ----

export interface ApiResponse<T> {
  data: T;
  meta?: Record<string, any>;
  error?: ApiError;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// ---- Events (for event-driven architecture) ----

export interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  occurredAt: Date;
  data: Record<string, any>;
}

export interface ResumeCreatedEvent extends DomainEvent {
  eventType: 'resume.created';
  data: {
    resumeId: string;
    userId: string;
    templateId: string;
  };
}

export interface PDFGenerationRequestedEvent extends DomainEvent {
  eventType: 'pdf.generation.requested';
  data: {
    resumeId: string;
    userId: string;
    templateId: string;
  };
}

// ---- Constants ----

export const CHAR_LIMITS = {
  name: 100,
  title: 200,
  bullet: 500,
  summary: 2000,
  short: 50,
  email: 320,
  phone: 50,
  url: 500,
} as const;

export const MAX_ITEMS = {
  experience: 10,
  education: 5,
  skills: 8,
  skillsPerGroup: 20,
  certifications: 15,
  languages: 10,
  bullets: 8,
  customSections: 10,
} as const;

export const SUPPORTED_LOCALES = [
  'en-US',
  'fr-FR',
  'de-DE',
  'es-ES',
  'ja-JP',
  'ar-SA',
] as const;

export const SUPPORTED_IMAGE_FORMATS = [
  'image/jpeg',
  'image/png',
  'image/webp',
] as const;

export const MAX_FILE_SIZES = {
  photo: 5 * 1024 * 1024, // 5MB
  pdf: 10 * 1024 * 1024, // 10MB
} as const;
