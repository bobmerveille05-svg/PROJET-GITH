# CV Generator SaaS - Technical Architecture

## Overview

This document provides a detailed technical overview of the CV Generator SaaS platform, built following Clean Architecture and SOLID principles.

## Architecture Layers

### 1. Domain Layer (Core Business Logic)
**Location**: `apps/api/src/domain/`

**Purpose**: Contains pure business logic with zero external dependencies.

**Components**:
- **Entities**: Core business objects (Resume, ContactInfo, Section)
- **Value Objects**: Immutable domain primitives (SafeText, PhoneNumber, EmailAddress, DateRange)
- **Interfaces (Ports)**: Define contracts for infrastructure (IResumeRepository, ITemplateRenderer, IPDFGenerator)
- **Domain Errors**: Business rule violations

**SOLID Principles Applied**:
- **Single Responsibility**: Each entity manages one business concept
- **Dependency Inversion**: Domain defines interfaces, infrastructure implements them
- **Interface Segregation**: Separate interfaces for different capabilities (IValidatable, IRenderable)

### 2. Application Layer (Use Cases)
**Location**: `apps/api/src/application/`

**Purpose**: Orchestrates domain logic to fulfill use cases.

**Components**:
- **Commands**: Write operations (CreateResumeCommand, UpdateSectionCommand, GeneratePDFCommand)
- **Queries**: Read operations (GetResumeQuery, ListTemplatesQuery)
- **Services**: Coordinate multiple domain operations
- **Validators**: Input validation using Zod schemas

### 3. Infrastructure Layer (External Concerns)
**Location**: `apps/api/src/infrastructure/`

**Purpose**: Implements domain interfaces with actual technology.

**Components**:
- **Persistence**: PostgreSQL repository implementations
- **External Services**: Clerk auth, S3 storage, phone validation
- **Template Engine**: HTML/CSS rendering using Strategy pattern
- **PDF Generation**: Puppeteer-based PDF creation
- **Caching**: Redis implementation

### 4. Presentation Layer (API)
**Location**: `apps/api/src/api/`

**Purpose**: Exposes HTTP endpoints, handles requests/responses.

**Components**:
- **Routes**: REST API endpoints
- **Middleware**: Authentication, rate limiting, sanitization, error handling
- **DTOs**: Data transfer objects for API contracts
- **Mappers**: Convert between domain and API models

## Database Schema

### Key Design Decisions

1. **JSONB for Flexibility**: Section content stored as JSONB to support polymorphic data structures
2. **Normalized Contact Info**: Separate table for 1:1 relationship with resumes
3. **Phone Number Handling**: Stores both raw input and E.164 normalized format
4. **Versioning**: Complete snapshot history for undo/restore
5. **Soft Delete**: Users table includes `deleted_at` for RGPD compliance

### Tables

```
users → resumes → [contact_info, resume_sections, resume_versions]
templates (registry)
pdf_generations (audit trail)
```

## Template System

### Strategy Pattern Implementation

The template system uses the **Strategy Pattern** for extensibility:

```typescript
interface ITemplateRenderer {
  templateId: string;
  metadata: TemplateMetadata;
  render(data: ResumeRenderData, config: ThemeConfig): string;
  supports(locale: string): boolean;
  getCSS(config: ThemeConfig): string;
  getPageBreakStrategy(): IPageBreakStrategy;
}
```

### Template Registry (Open/Closed Principle)

New templates can be added without modifying existing code:

```typescript
const registry = new TemplateRegistry();
registry.register(new ModernTemplateRenderer());
registry.register(new ClassicTemplateRenderer());
registry.register(new MinimalTemplateRenderer());
// Adding new template = 1 line + 1 class implementation
```

### Available Templates

1. **Modern**: Gradient header, skill badges, timeline dots
2. **Classic**: Traditional professional layout
3. **Minimal**: Typography-focused, clean design
4. **Creative** (Premium): Two-column, colorful for creative professionals
5. **Academic**: Formal layout with publications support

## PDF Generation Pipeline

### Flow

```
Client Request → API → Message Queue → Worker → Puppeteer → S3 → Client Notification
```

### Security Measures

1. **Sandboxed Execution**: Puppeteer runs in isolated container
2. **Network Isolation**: Worker can only access S3, no internal network
3. **Input Sanitization**: DOMPurify + custom sanitization
4. **Rate Limiting**: 5/hour (free), 50/hour (pro)
5. **Timeout Protection**: 30s max generation time

### HTML Rendering

```typescript
1. Load resume data from database
2. Sanitize all text content (XSS prevention)
3. Select template renderer
4. Generate HTML with inline CSS
5. Optimize page breaks
6. Convert to PDF via Puppeteer
7. Upload to S3
8. Return signed URL
```

## Security Architecture

### Defense in Depth

| Layer | Security Measures |
|-------|------------------|
| **Network** | WAF, Rate Limiting, CORS, CSP Headers |
| **Authentication** | OAuth 2.0 via Clerk, JWT tokens, MFA support |
| **Authorization** | User ownership validation on every request |
| **Input Validation** | Zod schemas, DOMPurify, libphonenumber-js |
| **Output Encoding** | HTML escaping in templates |
| **Data Protection** | TLS 1.3, PostgreSQL encryption at rest |
| **RGPD Compliance** | Soft delete, data export, right to be forgotten |

### XSS Prevention

```typescript
// 1. Client-side: DOMPurify before storing
// 2. Server-side: sanitize-html
// 3. Template rendering: HTML escape all user content
// 4. CSP headers: Restrict inline scripts
```

### SSRF Prevention (PDF Generation)

```typescript
// 1. Puppeteer in isolated container
// 2. Network namespace: S3 only
// 3. No external URLs in HTML
// 4. Whitelist allowed resources
```

## API Design

### RESTful Endpoints

```
POST   /api/v1/resumes                    # Create resume
GET    /api/v1/resumes/:id                # Get resume
PUT    /api/v1/resumes/:id/contact        # Update contact
POST   /api/v1/resumes/:id/sections       # Add section
PATCH  /api/v1/resumes/:id/sections/reorder  # Reorder sections
POST   /api/v1/resumes/:id/generate/pdf   # Generate PDF
GET    /api/v1/templates                  # List templates
```

### Response Format

```json
{
  "data": { /* result */ },
  "meta": { /* pagination, version, etc. */ },
  "error": { /* if error */ }
}
```

## Frontend Architecture (Next.js)

### Structure

```
apps/web/src/
├── app/               # App Router pages
│   ├── (auth)/       # Authentication pages
│   ├── dashboard/    # User dashboard
│   └── editor/[id]/  # CV editor
├── components/
│   ├── ui/           # Shadcn components
│   ├── editor/       # Editor-specific components
│   └── preview/      # Live preview component
├── lib/
│   ├── api-client.ts # API communication
│   └── hooks/        # Custom React hooks
└── stores/
    └── resume.ts     # Zustand state management
```

### State Management

**Zustand** for global state:
- Resume data
- Editor state (active section, validation errors)
- Preview sync

**React Hook Form** for forms:
- Contact info form
- Section item forms
- Validation with Zod

### Live Preview

```typescript
// Debounced auto-save every 2s
useEffect(() => {
  const timer = setTimeout(() => {
    saveResume(resumeData);
  }, 2000);
  return () => clearTimeout(timer);
}, [resumeData]);

// Real-time preview update
<PreviewPane 
  data={resumeData} 
  template={selectedTemplate}
  theme={themeConfig}
/>
```

## Data Flow

### Creating a Resume

```
1. User clicks "Create Resume"
2. POST /api/v1/resumes
3. Application layer: CreateResumeCommand
4. Domain layer: Resume entity validation
5. Infrastructure: PostgreSQL insert
6. Return resume ID
7. Redirect to editor
```

### Generating PDF

```
1. User clicks "Download PDF"
2. POST /api/v1/resumes/:id/generate/pdf
3. Application: GeneratePDFCommand
4. Load resume data from repository
5. Sanitize all content
6. Get template renderer from registry
7. Render HTML + CSS
8. Queue PDF job (Redis/SQS)
9. Worker picks up job
10. Puppeteer generates PDF
11. Upload to S3
12. Notify user via WebSocket
13. Return signed URL
```

## Performance Optimizations

### Caching Strategy

```
Redis Cache:
- Templates metadata (1 hour TTL)
- User session (30 min TTL)
- Rate limit counters

PostgreSQL:
- Indexes on user_id, resume_id, status
- GIN index on JSONB content for search
```

### PDF Generation

```
- Worker pool (3 concurrent)
- Resource limits (1GB RAM, 2 CPU cores per worker)
- Timeout: 30s
- Queue: Redis Streams or AWS SQS
```

## Monitoring & Observability

### Metrics (Prometheus)

- API request rate, latency, errors
- PDF generation time, success rate
- Database query performance
- Redis cache hit rate

### Logging (Structured JSON)

```json
{
  "level": "info",
  "msg": "PDF generated",
  "resumeId": "uuid",
  "templateId": "modern",
  "timeMs": 3245,
  "sizeBytes": 245123
}
```

### Error Tracking (Sentry)

- Unhandled exceptions
- API errors
- PDF generation failures
- User-reported issues

## Deployment

### Kubernetes Architecture

```
Ingress (nginx) 
  → API Pods (3-10, HPA)
  → PDF Worker Pods (2-5, HPA)
  
External Services:
  → PostgreSQL (RDS)
  → Redis (ElastiCache)
  → S3 (Object Storage)
```

### Continuous Deployment

```
GitHub Actions:
1. Lint + Type Check
2. Unit Tests
3. Integration Tests
4. Security Scan (Trivy)
5. Build Docker Images
6. Push to Registry
7. Deploy to Staging
8. E2E Tests
9. Deploy to Production (Canary)
```

## Testing Strategy

### Unit Tests (Vitest)
- Domain entities and value objects
- Application services
- Template renderers

### Integration Tests
- API endpoints with test database
- Repository implementations
- PDF generation workflow

### E2E Tests (Playwright)
- User flows: create, edit, download CV
- Cross-browser compatibility
- Responsive design

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- PDF workers can scale independently
- Database read replicas for queries

### Database Optimization
- Partition pdf_generations by date
- Archive old resume versions
- Index optimization based on query patterns

### CDN Strategy
- Static assets (templates, thumbnails)
- Generated PDFs with signed URLs
- Edge caching for common queries

## Conclusion

This architecture provides:
- ✅ **Maintainability**: Clean separation of concerns
- ✅ **Extensibility**: Easy to add new templates, sections
- ✅ **Testability**: Dependency injection, interface-based design
- ✅ **Security**: Defense in depth, input validation, sanitization
- ✅ **Performance**: Caching, async processing, optimized queries
- ✅ **Scalability**: Stateless services, horizontal scaling ready

---

*For implementation details, see source code in respective directories.*
