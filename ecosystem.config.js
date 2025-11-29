/**
 * PM2 Ecosystem Configuration
 * ============================
 * Gerencia todos os workers do Didin Fácil
 * 
 * Uso:
 *   pm2 start ecosystem.config.js
 *   pm2 start ecosystem.config.js --only scheduler
 *   pm2 logs scheduler
 *   pm2 restart scheduler
 *   pm2 stop all
 * 
 * Monitoramento:
 *   pm2 monit
 *   pm2 plus (dashboard web)
 */

module.exports = {
  apps: [
    // ============================================
    // Post Scheduler Worker
    // ============================================
    {
      name: 'scheduler',
      script: 'python',
      args: '-m workers.scheduler_runner',
      cwd: './backend',
      interpreter: 'none',
      
      // Ambiente
      env: {
        PYTHONUNBUFFERED: '1',
        ENVIRONMENT: 'development'
      },
      env_production: {
        PYTHONUNBUFFERED: '1',
        ENVIRONMENT: 'production'
      },
      
      // Restart automático
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      
      // Logs
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: './logs/scheduler-error.log',
      out_file: './logs/scheduler-out.log',
      merge_logs: true,
      
      // Recursos
      max_memory_restart: '500M',
      
      // Graceful shutdown
      kill_timeout: 10000,
      wait_ready: true,
      listen_timeout: 10000
    },
    
    // ============================================
    // WhatsApp Reconnection Worker
    // ============================================
    {
      name: 'whatsapp-reconnect',
      script: 'python',
      args: '-m workers.whatsapp_reconnect',
      cwd: './backend',
      interpreter: 'none',
      
      env: {
        PYTHONUNBUFFERED: '1',
        ENVIRONMENT: 'development'
      },
      env_production: {
        PYTHONUNBUFFERED: '1',
        ENVIRONMENT: 'production'
      },
      
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: './logs/whatsapp-reconnect-error.log',
      out_file: './logs/whatsapp-reconnect-out.log',
      merge_logs: true,
      
      max_memory_restart: '200M',
      kill_timeout: 5000
    },
    
    // ============================================
    // API Server (Development only)
    // ============================================
    {
      name: 'api',
      script: 'uvicorn',
      args: 'api.main:app --host 0.0.0.0 --port 8000 --reload',
      cwd: './backend',
      interpreter: 'none',
      
      env: {
        PYTHONUNBUFFERED: '1',
        ENVIRONMENT: 'development'
      },
      
      // Apenas para dev - em prod usar gunicorn/uvicorn direto
      autorestart: true,
      watch: ['./backend/api'],
      ignore_watch: ['__pycache__', '*.pyc', 'logs'],
      
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log',
      merge_logs: true,
      
      max_memory_restart: '1G'
    },
    
    // ============================================
    // Scraper Worker (On-demand)
    // ============================================
    {
      name: 'scraper',
      script: 'python',
      args: '-m scraper.main',
      cwd: './backend',
      interpreter: 'none',
      
      // Não inicia automaticamente
      autorestart: false,
      
      env: {
        PYTHONUNBUFFERED: '1',
        PLAYWRIGHT_BROWSERS_PATH: '/ms-playwright'
      },
      
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: './logs/scraper-error.log',
      out_file: './logs/scraper-out.log',
      merge_logs: true,
      
      max_memory_restart: '2G'
    }
  ],
  
  // ============================================
  // Deploy Configuration
  // ============================================
  deploy: {
    production: {
      user: 'deploy',
      host: ['production-server'],
      ref: 'origin/main',
      repo: 'git@github.com:arkheioncorp/didin-facil.git',
      path: '/var/www/didin-facil',
      'pre-deploy-local': '',
      'post-deploy': 'cd backend && pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    },
    staging: {
      user: 'deploy',
      host: ['staging-server'],
      ref: 'origin/develop',
      repo: 'git@github.com:arkheioncorp/didin-facil.git',
      path: '/var/www/didin-facil-staging',
      'post-deploy': 'cd backend && pip install -r requirements.txt && pm2 reload ecosystem.config.js --env development'
    }
  }
};
