# ============================================================================
# AWS Secrets Manager
# ============================================================================

resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${local.name_prefix}/app-secrets"
  description = "Application secrets for Didin Fácil"

  recovery_window_in_days = var.environment == "production" ? 30 : 0

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    DATABASE_URL              = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/${var.db_name}"
    REDIS_URL                 = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
    JWT_SECRET_KEY            = var.jwt_secret_key
    OPENAI_API_KEY            = var.openai_api_key
    MERCADO_PAGO_ACCESS_TOKEN = var.mercado_pago_access_token
    EVOLUTION_API_KEY         = var.evolution_api_key
    CHATWOOT_ACCESS_TOKEN     = var.chatwoot_access_token
    SENTRY_DSN                = var.sentry_dsn
  })
}

# ============================================================================
# SSM Parameter Store (for non-sensitive config)
# ============================================================================

resource "aws_ssm_parameter" "app_config" {
  name  = "/${local.name_prefix}/config/app"
  type  = "String"
  value = jsonencode({
    environment   = var.environment
    domain        = var.domain_name
    api_url       = "https://api.${var.domain_name}"
    frontend_url  = "https://app.${var.domain_name}"
    cors_origins  = var.cors_origins
    s3_uploads    = aws_s3_bucket.uploads.id
  })

  tags = local.common_tags
}

resource "aws_ssm_parameter" "database_host" {
  name  = "/${local.name_prefix}/config/database-host"
  type  = "String"
  value = aws_db_instance.main.address

  tags = local.common_tags
}

resource "aws_ssm_parameter" "redis_host" {
  name  = "/${local.name_prefix}/config/redis-host"
  type  = "String"
  value = aws_elasticache_cluster.redis.cache_nodes[0].address

  tags = local.common_tags
}
