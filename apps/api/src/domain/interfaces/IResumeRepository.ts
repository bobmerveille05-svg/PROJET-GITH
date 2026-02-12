// ============================================================
// PORT: IResumeRepository (Dependency Inversion)
// Domain layer defines the contract, infrastructure implements it
// ============================================================

import { Resume, ResumeSection, ContactInfo } from '@cv-generator/shared-types';

export interface IResumeRepository {
  // Resume operations
  findById(id: string): Promise<Resume | null>;
  findByUserId(userId: string): Promise<Resume[]>;
  findBySlug(slug: string): Promise<Resume | null>;
  create(resume: Omit<Resume, 'id' | 'createdAt' | 'updatedAt'>): Promise<Resume>;
  update(id: string, resume: Partial<Resume>): Promise<Resume>;
  delete(id: string): Promise<void>;
  
  // Contact info operations
  getContactInfo(resumeId: string): Promise<ContactInfo | null>;
  upsertContactInfo(contactInfo: Omit<ContactInfo, 'id' | 'createdAt' | 'updatedAt'>): Promise<ContactInfo>;
  
  // Section operations
  getSections(resumeId: string): Promise<ResumeSection[]>;
  getSectionById(sectionId: string): Promise<ResumeSection | null>;
  createSection(section: Omit<ResumeSection, 'id' | 'createdAt' | 'updatedAt'>): Promise<ResumeSection>;
  updateSection(sectionId: string, section: Partial<ResumeSection>): Promise<ResumeSection>;
  deleteSection(sectionId: string): Promise<void>;
  reorderSections(resumeId: string, sectionIds: string[]): Promise<void>;
  
  // Versioning
  createVersion(resumeId: string, snapshot: any): Promise<void>;
  getVersions(resumeId: string): Promise<any[]>;
  restoreVersion(resumeId: string, version: number): Promise<Resume>;
}
