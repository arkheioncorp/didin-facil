# ============================================================================
# ECS Task Definition for Database Migrations
# ============================================================================
# Standalone task for running Alembic migrations
# ============================================================================

resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.name}-api-migration"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "migration"
      image     = "${aws_ecr_repository.api.repository_url}:latest"
      essential = true

      command = ["alembic", "upgrade", "head"]

      workingDirectory = "/app"

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:DATABASE_URL::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${local.name}-migrations"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migration"
        }
      }
    }
  ])

  tags = local.tags
}

# CloudWatch Log Group for Migrations
resource "aws_cloudwatch_log_group" "migrations" {
  name              = "/ecs/${local.name}-migrations"
  retention_in_days = 30

  tags = local.tags
}

# IAM Policy for ECS Task to run migrations (if needed)
resource "aws_iam_role_policy" "migration_secrets" {
  name = "${local.name}-migration-secrets"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.app_secrets.arn
      }
    ]
  })
}
