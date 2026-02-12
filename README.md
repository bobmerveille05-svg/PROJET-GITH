# CV Generator SaaS Platform

A professional CV/Resume generation SaaS application built with modern technologies and clean architecture principles.

## 🏗️ Architecture

This project follows **Clean Architecture** with **SOLID** principles:

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│              Next.js App Router + REST API                  │
├─────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                        │
│          Use Cases, Commands, Queries, Services             │
├─────────────────────────────────────────────────────────────┤
│                      DOMAIN LAYER                           │
│    Entities, Value Objects, Domain Logic (No Dependencies)  │
├─────────────────────────────────────────────────────────────┤
│                  INFRASTRUCTURE LAYER                       │
│   Database, External Services, Template Engine, PDF Gen     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Technology Stack

### Frontend
- **Next.js 14+** (App Router, React Server Components)
- **Tailwind CSS 4** (Utility-first styling)
- **Zustand** (State management)
- **React Hook Form** (Form handling)
- **Zod** (Validation)

### Backend
- **Node.js 20+** with **TypeScript**
- **Fastify** (High-performance API)
- **PostgreSQL 16** (Primary database with JSONB)
- **Redis 7** (Caching & sessions)
- **Puppeteer** (PDF generation)

### Infrastructure
- **Docker + Docker Compose** (Local development)
- **Kubernetes** (Production deployment)
- **AWS S3 / Cloudflare R2** (Object storage)
- **Clerk / Auth0** (Authentication)

## 📁 Project Structure

```
cv-generator-saas/
├── apps/
│   ├── api/                    # Backend API (Fastify)
│   │   ├── src/
│   │   │   ├── domain/         # Domain layer (entities, value objects)
│   │   │   ├── application/    # Use cases, services
│   │   │   ├── infrastructure/ # Database, external services
│   │   │   └── api/            # REST API routes, middleware
│   │   └── package.json
│   │
│   ├── web/                    # Frontend (Next.js)
│   │   ├── src/
│   │   │   ├── app/            # App router pages
│   │   │   ├── components/     # React components
│   │   │   ├── lib/            # Utilities, hooks
│   │   │   └── stores/         # Zustand stores
│   │   └── package.json
│   │
│   └── pdf-worker/             # PDF Generation Service
│       └── src/
│
├── packages/
│   ├── database/               # Shared database schema & migrations
│   ├── shared-types/           # TypeScript shared types
│   └── validation/             # Zod schemas
│
├── docker/                     # Docker configurations
├── k8s/                        # Kubernetes manifests
└── docs/                       # Documentation
```

## 🛠️ Setup Instructions

### Prerequisites

- Node.js 20+
- pnpm 8+
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7

### Installation

```bash
# Clone repository
git clone <repository-url>
cd cv-generator-saas

# Install dependencies
pnpm install

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Start infrastructure (PostgreSQL, Redis)
docker-compose up -d

# Run database migrations
pnpm db:migrate

# Seed database with templates
pnpm db:seed

# Start development servers
pnpm dev
```

This will start:
- API Server: http://localhost:3001
- Web App: http://localhost:3000
- PDF Worker: http://localhost:3002

## 🧪 Testing

```bash
# Run all tests
pnpm test

# Unit tests
pnpm test:unit

# Integration tests
pnpm test:integration

# E2E tests
pnpm test:e2e

# Test coverage
pnpm test:coverage
```

## 🔒 Security Features

- **XSS Protection**: DOMPurify sanitization, CSP headers
- **SQL Injection**: Parameterized queries, ORM
- **SSRF Protection**: Sandboxed PDF generation
- **Rate Limiting**: Redis-based rate limiters
- **Authentication**: OAuth 2.0, JWT, MFA support
- **RGPD Compliance**: Data encryption, soft delete, export

## 📝 API Documentation

API documentation is available at:
- Development: http://localhost:3001/docs
- Swagger/OpenAPI: http://localhost:3001/api-docs

## 🎨 Template System

The application supports multiple CV templates:

1. **Modern** - Clean, contemporary design with accent colors
2. **Classic** - Traditional, professional layout
3. **Minimal** - Simple, elegant typography-focused

Templates follow the **Strategy Pattern** for easy extensibility.

## 🌍 Internationalization

Supported languages:
- English (en-US)
- French (fr-FR)
- German (de-DE)
- Spanish (es-ES)
- Japanese (ja-JP)
- Arabic (ar-SA) - RTL support

## 🚢 Deployment

### Docker

```bash
# Build images
docker build -t cv-api:latest ./apps/api
docker build -t cv-web:latest ./apps/web

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up
```

### Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n cv-generator
```

## 📊 Monitoring

- **Metrics**: Prometheus + Grafana
- **Logging**: Loki + structured logs
- **Tracing**: OpenTelemetry
- **Error Tracking**: Sentry

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with ❤️ following Clean Architecture and SOLID principles.

---

For detailed technical documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
