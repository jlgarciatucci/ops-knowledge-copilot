# AWS Deployment Story

This project runs locally with Docker Compose, but the architecture maps directly to AWS.

## Local to AWS mapping

| Local component | AWS production equivalent |
|---|---|
| FastAPI Docker container | ECS Fargate service or EKS deployment |
| PostgreSQL/pgvector container | Amazon RDS for PostgreSQL with pgvector |
| `sample_docs/` local folder | Amazon S3 document bucket |
| `.env` file | AWS Secrets Manager or SSM Parameter Store |
| Console logs | Amazon CloudWatch Logs |
| Query logs table | PostgreSQL + CloudWatch metrics/dashboard |

## Suggested architecture

```text
Client
→ Application Load Balancer
→ ECS Fargate FastAPI service
→ RDS PostgreSQL with pgvector
→ S3 for uploaded documents
→ Secrets Manager for API keys and credentials
→ CloudWatch Logs and metrics
```

## Production considerations

- Store OpenAI/Anthropic/Bedrock credentials in Secrets Manager.
- Use RDS subnet groups and security groups to restrict database access.
- Use S3 object metadata to track document version and department.
- Add authentication and authorization before exposing document upload.
- Use CloudWatch alarms for high latency, 5xx errors and high token cost.
- Use autoscaling for the FastAPI service.
