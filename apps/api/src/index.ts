// ============================================================
// API SERVER - Main Entry Point
// ============================================================

import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import { config } from './config';
import { logger } from './infrastructure/logging/logger';
import { resumeRoutes } from './api/routes/resumeRoutes';
import { templateRoutes } from './api/routes/templateRoutes';
import { pdfRoutes } from './api/routes/pdfRoutes';
import { errorHandler } from './api/middleware/errorHandler';

async function buildServer() {
  const server = Fastify({
    logger: logger,
    requestIdLogLabel: 'reqId',
    disableRequestLogging: false,
  });

  // Security headers
  await server.register(helmet, {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "'unsafe-inline'"],
        styleSrc: ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
        imgSrc: ["'self'", 'data:', 'https://*.amazonaws.com', 'https://*.cloudflare.com'],
        fontSrc: ["'self'", 'https://fonts.gstatic.com'],
        connectSrc: ["'self'"],
        frameAncestors: ["'none'"],
      },
    },
  });

  // CORS
  await server.register(cors, {
    origin: config.cors.origins,
    credentials: true,
  });

  // Rate limiting
  await server.register(rateLimit, {
    max: 100,
    timeWindow: '1 minute',
    redis: config.redis.url ? config.redis.url : undefined,
  });

  // Swagger documentation
  await server.register(swagger, {
    openapi: {
      info: {
        title: 'CV Generator API',
        description: 'Professional CV/Resume Generation SaaS Platform API',
        version: '1.0.0',
      },
      servers: [
        {
          url: 'http://localhost:3001',
          description: 'Development server',
        },
      ],
      tags: [
        { name: 'resumes', description: 'Resume operations' },
        { name: 'templates', description: 'Template management' },
        { name: 'pdf', description: 'PDF generation' },
      ],
    },
  });

  await server.register(swaggerUi, {
    routePrefix: '/api-docs',
    uiConfig: {
      docExpansion: 'list',
      deepLinking: false,
    },
  });

  // Health check
  server.get('/health', async () => {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    };
  });

  // API Routes
  await server.register(resumeRoutes, { prefix: '/api/v1/resumes' });
  await server.register(templateRoutes, { prefix: '/api/v1/templates' });
  await server.register(pdfRoutes, { prefix: '/api/v1/pdf' });

  // Error handler
  server.setErrorHandler(errorHandler);

  return server;
}

async function start() {
  try {
    const server = await buildServer();
    
    await server.listen({
      port: config.port,
      host: config.host,
    });

    logger.info(`🚀 Server listening on http://${config.host}:${config.port}`);
    logger.info(`📚 API Documentation: http://${config.host}:${config.port}/api-docs`);
    
    // Graceful shutdown
    const signals = ['SIGINT', 'SIGTERM'];
    signals.forEach((signal) => {
      process.on(signal, async () => {
        logger.info(`Received ${signal}, shutting down gracefully...`);
        await server.close();
        process.exit(0);
      });
    });
  } catch (err) {
    logger.error(err);
    process.exit(1);
  }
}

start();
