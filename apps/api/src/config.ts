// ============================================================
// CONFIGURATION
// Environment-based configuration management
// ============================================================

import 'dotenv/config';

export const config = {
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '3001', 10),
  host: process.env.HOST || '0.0.0.0',
  
  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432', 10),
    database: process.env.DB_NAME || 'cv_generator',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres',
    ssl: process.env.DB_SSL === 'true',
  },
  
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
  },
  
  auth: {
    jwtSecret: process.env.JWT_SECRET || 'your-secret-key-change-in-production',
    clerkPublishableKey: process.env.CLERK_PUBLISHABLE_KEY || '',
    clerkSecretKey: process.env.CLERK_SECRET_KEY || '',
  },
  
  storage: {
    provider: process.env.STORAGE_PROVIDER || 's3', // 's3' or 'r2'
    bucket: process.env.STORAGE_BUCKET || 'cv-generator-pdfs',
    region: process.env.STORAGE_REGION || 'us-east-1',
    accessKeyId: process.env.STORAGE_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.STORAGE_SECRET_ACCESS_KEY || '',
    endpoint: process.env.STORAGE_ENDPOINT || undefined, // For R2
  },
  
  pdf: {
    timeout: parseInt(process.env.PDF_TIMEOUT || '30000', 10),
    maxConcurrent: parseInt(process.env.PDF_MAX_CONCURRENT || '3', 10),
  },
  
  rateLimit: {
    pdfFree: parseInt(process.env.RATE_LIMIT_PDF_FREE || '5', 10), // per hour
    pdfPro: parseInt(process.env.RATE_LIMIT_PDF_PRO || '50', 10),
    api: parseInt(process.env.RATE_LIMIT_API || '100', 10), // per minute
  },
  
  cors: {
    origins: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
  },
  
  sentry: {
    dsn: process.env.SENTRY_DSN || '',
    environment: process.env.NODE_ENV || 'development',
  },
} as const;
