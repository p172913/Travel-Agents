# Hosting TravelSouls

This project includes local production-like deployment and AWS deployment templates.

## Local production deployment

1. Copy `.env.example` to `.env` and fill in the values.
2. Start the production stack:

```bash
cd infra
docker compose -f docker-compose.prod.yml up --build
```

3. The app will be available at:

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000

## Render deployment

This is the recommended backend host if you want a simple service deployment for the FastAPI API.

### Quick start

1. Create a new Render Web Service.
2. Choose `Connect a repository` and select this project.
3. Use the following settings:
   - Environment: `Docker`
   - Dockerfile path: `Dockerfile`
   - Start command: `uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000`
   - Branch: `main`
   - Auto deploy: enabled

4. Add a managed Postgres database in Render.
5. Add a managed Redis instance in Render.
6. Set the backend service environment variables:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `FRONTEND_URL` = `https://<your-vercel-domain>`
   - `NEXT_PUBLIC_API_URL` = `https://<your-backend-domain>`
   - `LOG_LEVEL` = `INFO`
   - `OPENAI_API_KEY` (optional)
   - `OPENWEATHER_API_KEY` (optional)
   - `TAVILY_API_KEY` (optional)
   - `PINECONE_API_KEY` (optional)
   - `PINECONE_ENVIRONMENT` (optional)
   - `PINECONE_INDEX_NAME` (optional)
   - `SENTRY_DSN` (optional)

### Using `render.yaml`

A `render.yaml` file is included at the repository root for Render service configuration.
You can use it as a deployment blueprint or import it in Render.

### Connect frontend

On Vercel, set `NEXT_PUBLIC_API_URL` to the Render backend URL.
If you are using the frontend from `frontend/` on Vercel, do not forget to set this environment variable in your Vercel project.

---

## AWS deployment (ECR + ECS)

### Prerequisites

- AWS account with permissions for ECR and ECS
- AWS CLI configured locally
- GitHub repository secrets configured

### Required secrets

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `AWS_ACCOUNT_ID`
- `ECR_REPOSITORY` (default: `travelsouls/api-gateway`)
- `ECS_CLUSTER`
- `ECS_SERVICE`

### Deployment workflow

1. Create an ECR repository:

```bash
aws ecr create-repository --repository-name travelsouls/api-gateway --region us-east-1
```

2. Update `infra/aws/ecs-task-definition.json` with your AWS account ID and region.
3. Configure an ECS cluster and service using Fargate.
4. Push code to `main` to trigger `.github/workflows/deploy.yml`.

### Monitoring and logs

The ECS task definition includes AWS CloudWatch logging configuration.

### Notes

- Sensitive configuration should be stored in AWS Secrets Manager or ECS task environment variables.
- The frontend and backend can also be hosted separately if desired.
