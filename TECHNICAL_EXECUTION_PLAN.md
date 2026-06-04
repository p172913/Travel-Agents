# TravelSouls Technical Execution Plan

## Goal
Build an AI-powered multi-agent travel planning platform that:

- Generates complete trip plans from one prompt
- Researches destinations
- Tracks budgets
- Searches flights/hotels
- Gives personalized recommendations
- Shares itineraries
- Explains every recommendation
- Supports future auto-replanning

Target MVP: 12–16 weeks.

---

## Architecture

```
Frontend (Next.js)

        |
        v

API Gateway (FastAPI)

        |
        v

Orchestrator Agent
        |
 -------------------------------------------------
 |            |            |                     |
 v            v            v                     v

Research    Budget      Booking       Recommendation
Agent       Agent       Agent         Agent

 -------------------------------------------------
                    |
                    v

            PostgreSQL

                    |
                    v

               Redis

                    |
                    v

              Pinecone

                    |
                    v

              External APIs

- OpenAI / Claude
- Amadeus / Skyscanner
- OpenWeather
- Google Places
```

---

## Current Project Status

### Completed foundation

- Multi-service folder structure exists
- `api_gateway` FastAPI scaffold in place
- `orchestrator` service with prototype agent coordination
- `research_agent`, `budget_agent`, `booking_agent`, `recommendation_agent` services present
- Shared SQLAlchemy models for users, trips, plans, bookings, logs, feedback
- Local dev infra with Postgres, Redis, Docker Compose
- Frontend repository exists and is configured for Next.js 16 + Tailwind CSS

### Remaining work

- No authentication system implemented
- Frontend is still default placeholder content
- Agents are currently mock/prototype implementations
- No actual third-party travel API integrations
- No LangGraph workflow orchestration
- No personalization / embeddings / Pinecone integration
- No production deployment IaC
- No CI/CD pipelines or automated tests for complete system
- No structured explainability layer across all outputs

---

## Recommended Tech Stack

### Frontend

- Next.js 16
- TypeScript
- TailwindCSS
- Shadcn/UI
- Zustand
- React Query

### Backend

- FastAPI
- Python 3.13
- LangGraph
- PydanticAI
- PostgreSQL
- Redis

### AI

- OpenAI GPT-5.5 or Claude Sonnet
- OpenAI / Claude embeddings
- Pinecone

### DevOps

- Docker
- GitHub Actions
- AWS ECS Fargate
- AWS RDS PostgreSQL
- AWS ElastiCache Redis
- AWS S3
- CloudFront
- Monitoring: Grafana, Prometheus, Sentry

---

## Phase 1 — Foundation (Week 1–2)

### Deliverables

- Repository and service structure established
- Local Docker Compose development environment
- Database schema defined for core entities
- API gateway scaffolded with endpoints for research and budget
- Orchestrator prototype in place
- Shared schemas and models defined

### Status

- Completed in the repo as prototype scaffolding
- Still needs:
  - DB migrations (Alembic)
  - CI / branch protection
  - Auth service and login/signup flow
  - Backend config for environment management

### Tasks

1. Add Alembic migrations for Postgres models
2. Add a `.env` configuration pattern and secrets management guidance
3. Create GitHub Actions workflows for linting, tests, and build
4. Add basic auth endpoints in `api_gateway` and supporting user/password storage or third-party auth

---

## Phase 2 — Research Agent (Week 3)

### Responsibilities

- Destination research
- Weather
- Attractions
- Safety score
- Hidden gems

### Desired output

```json
{
  "destination": "Goa",
  "weather": "...",
  "safety_score": 8,
  "top_places": [],
  "hidden_gems": []
}
```

### Status

- Prototype exists with fallback mock research and basic Wikipedia/Tavily helper tools
- Needs production-ready sources and improved reliability

### Tasks

1. Add structured source integrations:
   - OpenWeather or weather API
   - Google Places / Places Details
   - Wikipedia or travel knowledge API
   - Optional search fallback (Tavily / SerpAPI)
2. Build the actual `research_agent` pipeline to create structured JSON output
3. Add caching in Redis for repeated destination lookups
4. Expose a `research` service endpoint and persist results in DB logs

---

## Phase 3 — Budget Agent (Week 4)

### Responsibilities

- Budget allocation
- Trip cost prediction
- Alerts

### Example output

```json
{
  "flights": 20000,
  "hotel": 15000,
  "food": 8000,
  "activities": 7000,
  "misc": 0
}
```

### Status

- Prototype budget agent exists with heuristic allocation logic
- Needs integration with destination cost data and improved accuracy

### Tasks

1. Add destination-specific cost modeling and realistic unit costs
2. Add budget feasibility checks and alert generation
3. Persist budget plans in `TripPlan` and link to each trip
4. Add endpoint and UI to request budget allocation

---

## Phase 4 — Booking Agent (Week 5–6)

### Responsibilities

- Flight search
- Hotel search
- Ranking

### Integrations

- Amadeus or Skyscanner for flights
- Amadeus Hotels or Booking.com affiliate for hotels

### Status

- Booking agent currently returns mock flight/hotel data
- No real external search integration

### Tasks

1. Implement Amadeus / Skyscanner flight search
2. Implement hotel search via Amadeus or affiliate API
3. Build ranking logic for best flights/hotels
4. Add `POST /api/booking` and normalize search response schema
5. Persist booking candidates and search metadata

---

## Phase 5 — Recommendation Agent (Week 6–7)

### Responsibilities

- Personalized restaurants
- Activities
- Hidden gems
- Local recommendations aligned to travel style
- Simple preference-driven suggestions

### Output schema

```json
{
  "recommendations": [
    {
      "name": "Thalassa",
      "type": "restaurant",
      "category": "dining",
      "rating": 4.7,
      "price_level": "mid",
      "reason": "Highly rated seaside dinner for sunset",
      "estimated_cost": 2500
    }
  ]
}
```

### Status

- Recommendation agent scaffold exists in the repo
- No recommendation endpoint is wired to the frontend
- User preference capture and feedback loops are not implemented

### Tasks

1. Define the recommendation output model with type, reason, rating, and cost
2. Add `POST /api/recommendation` in `api_gateway`
3. Expand recommendation agent to consume destination, budget, and travel style
4. Persist recommendations and feedback in DB tables
5. Add frontend recommendation cards for saved trips and plan details

### Acceptance criteria

- `POST /api/recommendation` returns structured recommendation JSON
- Recommendation output includes `reason` and category metadata
- Frontend can display at least 3 recommendation cards inside trip details
- Basic feedback buttons (`useful`, `not useful`) are wired to the backend

---

## Phase 6 — Orchestrator Agent (Week 7–8)

### Responsibilities

- Coordinate research, budget, booking, and recommendation agents
- Sequence agent calls and merge partial results
- Handle agent errors and recover with partial outputs
- Store orchestration request, status, and timings

### Workflow

```text
User Prompt
    |
Orchestrator
    +--> Research Agent
    +--> Budget Agent
    +--> Booking Agent
    +--> Recommendation Agent
    |
Merge Results
    v
Final Travel Plan
```

### Status

- Orchestrator is architected in the repo
- Workflow execution is not production hardened
- Error handling, retries, and agent orchestration state are incomplete

### Tasks

1. Implement the orchestration pipeline using LangGraph or a custom coordinator
2. Add timeouts and retry logic for each downstream agent call
3. Define partial-result merge rules and fallback behavior
4. Persist orchestration requests, results, and logs in DB
5. Wire `POST /api/plan/orchestrate` to generate a saved trip plan

### Acceptance criteria

- `POST /api/plan/orchestrate` returns a combined plan object
- Orchestrator can return a partial plan if one agent fails
- Orchestration request and result are stored in the DB
- Orchestration latency is measured and logged

---

## Phase 7 — Trip Plan Generator (Week 8–9)

### Responsibilities

- Generate a day-by-day itinerary from merged agent outputs
- Include hotel, attraction, activities, meals, and travel legs
- Present a readable schedule with time windows and explanations

### Example output

```markdown
Day 1
9:00 AM - Arrive and check in at beachfront hotel
11:00 AM - Explore the local market
1:00 PM - Lunch at seaside restaurant
4:00 PM - Sunset boat cruise
7:30 PM - Dinner at Thalassa
```

### Status

- Itinerary model is defined and the repo now generates a structured daily plan
- Trip detail pages render a readable itinerary and itinerary item metadata
- The plan includes item-level reasoning for why each activity or booking is recommended

### Tasks

1. Define a `TripItineraryItem` model for date, time, title, location, notes, and explanation
2. Add itinerary generation logic that merges research, budget, booking, and recommendation outputs
3. Persist itinerary items with each saved trip plan
4. Add frontend plan detail views for daily schedules
5. Add explanation metadata for each itinerary item

### Acceptance criteria

- Saved trips include a structured itinerary with at least 3 days of items
- Frontend displays a daily schedule per trip
- Each itinerary item includes a `reason` or `why` field
- Users can access trip plan details from the `/trips` page

---

## Phase 8 — Explainability Layer (Week 9)

### Responsibilities

- Provide rationale for every recommendation
- Add trust signals and reasoning details

### Status

- Explainability metadata is implemented in itinerary items and plan explanations
- Trip details render item-level reasons and recommendation rationale
- The backend now stores explanation text in saved plans

### Example reason output

```text
Why AI picked this:
✓ Within budget
✓ 4.6 rating
✓ Near attractions
✓ Matches travel style
```

### Tasks

1. Add `reason` and `explanation` metadata to agent outputs
2. Render explanations in frontend plan view
3. Store explanation text in DB logs
4. Add unit tests for explainability output

### Acceptance criteria

- Every major itinerary item includes a reason or explanation
- Frontend displays the why/reason for each recommended itinerary item
- Plan explanation text is persisted and visible in trip details
- Explainability output is covered by tests

---

## Phase 9 — Frontend MVP (Week 9–10)

### Screens

- Authentication
- Dashboard
- Planner
- Generated plan detail
- Trip detail
- Share placeholder

### Tasks

1. Build auth screens and protected routes
2. Add dashboard for saved trips
3. Add planning form at `/start`
4. Add `/trips` and `/trips/[tripId]`
5. Add share page stub for future public links

---

## Phase 10 — Personalization Engine (Week 10–11)

### Responsibilities

- Store preferences and travel style
- Use feedback to tailor recommendations
- Support user memory for repeat trips

### Tasks

1. Add preferences and feedback tables
2. Add endpoints for user profile and preference updates
3. Store feedback from recommendation cards
4. Update Pinecone embeddings with user signals
5. Use personalization in recommendation and orchestrator workflows

---

## Phase 11 — Testing (Week 11–13)

### Unit Testing

- Backend business logic with pytest
- Frontend components with Jest/React Testing Library

### Integration Testing

- API contracts
- Orchestration workflow
- DB persistence
- Mocked external API integrations

### AI Testing

- Golden prompt dataset of 100 examples
- Validate output schema and budget accuracy
- Detect hallucinations and invalid JSON

### Tasks

1. Add unit tests for core backend services
2. Add integration tests for API flows
3. Add frontend UI tests for planner flow
4. Add AI schema validation tests
5. Implement CI test gating

---

## Phase 12 — Production Deployment (Week 13–14)

### Infrastructure

- AWS ECS Fargate for backend
- AWS RDS PostgreSQL
- AWS ElastiCache Redis
- AWS S3 for assets
- CloudFront for frontend

### Tasks

1. Create Terraform / CloudFormation templates
2. Configure staging and production deploy environments
3. Add GitHub Actions deploy pipelines
4. Use secrets management and environment isolation
5. Add database backups and recovery policy

---

## Phase 13 — Beta Launch (Week 15)

### Goals

- Release to 20–50 users
- Measure plan generation performance
- Collect user feedback

### Metrics

- Plan generation success rate
- API latency
- User satisfaction / NPS
- Error rate

---

## Phase 14 — Production Launch (Week 16)

### Launch criteria

- All core agents working reliably
- 95%+ uptime in staging and prod
- Budget accuracy within ±8%
- NPS > 50
- SUS > 85
- Load tested to 1,000 concurrent users

---

## Engineering Execution Details

### Core data model

Entities:

- `users`
- `trips`
- `trip_requests`
- `trip_plans`
- `bookings`
- `preferences`
- `agent_logs`
- `feedback`

### API contract examples

#### POST /api/plan/orchestrate

Request:

```json
{
  "destination": "Goa",
  "start_date": "2026-07-01",
  "end_date": "2026-07-08",
  "total_budget": 50000,
  "travel_style": "balanced",
  "travelers": 2
}
```

Response:

```json
{
  "trip_id": 123,
  "plan_id": 456,
  "plan": {
    "itinerary": [...],
    "budget_breakdown": {...},
    "explanation": "..."
  }
}
```

### DevOps and infrastructure

- Local dev uses `docker compose`
- Staging and prod use AWS ECS + RDS + ElastiCache
- GitHub Actions for CI/CD
- Use secrets manager for API keys and DB credentials

### Observability

- Track metrics: request latency, error rate, agent status, orchestration time
- Structured logging to a central store
- Tracing for request and agent workflows
- Alerts on high latency, errors, and downstream failures

### Security

- Auth required for trip creation and saved trips
- Secure cookie/JWT strategy for frontend
- CORS restricted to trusted origins
- Validate all external data before persisting
- Protect sensitive user data

### Risk management

- External API failure → fallback / retry / cached results
- AI hallucinations → schema validation + guardrails
- Cost overruns → caching, request limiting, API usage monitoring
- Orchestration latency → parallel calls, timeouts, and degrade gracefully
- Scope creep → keep MVP focused on core trip planning

---

## What is missing from the project today

1. A fully defined engineering backlog for each phase
2. Authentication and user profile management
3. Real external travel API integrations
4. Production-ready orchestrator workflow
5. Production deployment IaC and pipelines
6. Full explainability and personalization
7. Comprehensive automated testing

---

## Next steps

1. Convert this plan into an issue backlog
2. Assign tasks to sprints
3. Implement the highest-risk MVP pieces first
4. Validate working APIs and frontend flows
5. Deploy to staging before production

This document now contains the complete technical execution plan needed to take TravelSouls from idea to MVP and production.

4. Save search results in DB and optionally in `Booking` entities
5. Keep booking status as search-only; do not charge or finalize bookings in MVP

---

## Phase 5 — Recommendation Agent (Week 6–7)

### Responsibilities

- Personalized restaurants
- Activities
- Hidden gems
- Family recommendations

### Status

- Current implementation is hardcoded by travel style
- No personalization store or embeddings

### Tasks

1. Add user preference model support in `Preference`
2. Build Pinecone embedding index for destinations, interests, and feedback
3. Query similarity search for personalized recommendations
4. Add recommendation scoring and explainability rationale
5. Store user history and preference signals for improved suggestions

---

## Phase 6 — Orchestrator Agent (Week 7–8)

### Responsibilities

- Coordinate agents and merge results
- Ensure end-to-end trip planning workflow

### Status

- Prototype orchestrator exists using `asyncio.gather`
- Not yet using LangGraph or a formal workflow engine

### Tasks

1. Migrate orchestrator to LangGraph for workflow orchestration
2. Define input/output schemas and agent contracts
3. Add retries, timeouts, and fallback behavior
4. Merge research, budget, booking, and recommendation outputs into a single `TripPlan`
5. Optimize to target response under 10 seconds for MVP calls

---

## Phase 7 — Trip Plan Generator (Week 8–9)

### Responsibilities

- Generate day-by-day itinerary
- Include hotels, attractions, restaurants, travel time

### Status

- Basic mock itinerary generation exists in orchestrator
- Needs richer day-planning logic and formatting

### Tasks

1. Build a day-by-day itinerary generator using agent outputs
2. Include time slots, activity sequencing, location grouping, and travel legs
3. Produce a shareable structured plan in JSON
4. Save final itinerary in `TripPlan.itinerary`

---

## Phase 8 — Explainability Layer (Week 9)

### Responsibilities

- Explain every recommendation
- Provide trust signals for users

### Minimal output

```json
"why": [
  "Within budget",
  "4.6 rating",
  "Near attractions",
  "Matches solo traveler profile"
]
```

### Status

- Basic `TripPlan.explanation` field exists
- No standardized explanation across agents

### Tasks

1. Add explanation metadata to each agent output
2. Build a consistent schema for why each item was selected
3. Surface explanations in UI and API responses
4. Log explainability data for auditability

---

## Phase 9 — Frontend MVP (Week 9–10)

### Screens

- Login / Signup
- Dashboard (current and upcoming trips)
- Planner chat UI
- Generated plan view
- Share page (`/t/{id}`)

### Status

- Frontend folder exists, but app remains placeholder

### Tasks

1. Build auth UI and route protection
2. Build dashboard listing trips and status
3. Build planner input form or chat interface
4. Render combined trip plan with budget, flights, hotels, activities, explanations
5. Build shareable public itinerary page

---

## Phase 10 — Personalization Engine (Week 10–11)

### Responsibilities

- Store travel styles, favorite hotels, budget range, cuisine preferences
- Update embeddings with feedback

### Status

- Preference model is defined, but not used for personalization

### Tasks

1. Capture user preferences in signup and profile flows
2. Add thumbs-up / thumbs-down feedback for recommendations
3. Update embedding store with feedback signals
4. Use preference history to bias new recommendations
5. Add personalization quality tracking

---

## Phase 11 — Testing (Week 11–13)

### Unit Testing

- Backend: pytest
- Frontend: Jest / React Testing Library
- Goal: 95%+ coverage on core services

### Integration Testing

- Validate Amadeus / weather / Pinecone / Redis integration paths
- Exercise orchestrator end-to-end

### AI Testing

- Golden dataset of 100 travel prompts
- Validate JSON schemas, budget correctness, and recommendation quality

### Status

- No comprehensive tests currently present

### Tasks

1. Add pytest suites for agent outputs and API routes
2. Add frontend component tests for key flows
3. Create integration tests for the orchestrator pipeline
4. Build an AI validation dataset and run automated schema checks

---

## Phase 12 — Production Deployment (Week 13–14)

### Infrastructure

- AWS ECS Fargate for services
- AWS RDS PostgreSQL
- AWS ElastiCache Redis
- AWS S3 for assets and shareable content
- AWS CloudFront for frontend delivery

### Observability

- Grafana / Prometheus for metrics
- Sentry for errors
- OpenTelemetry for distributed tracing

### Status

- Local Docker Compose exists only

### Tasks

1. Add deployment IaC or CloudFormation / Terraform manifest
2. Add GitHub Actions deploy workflows
3. Add monitoring, logging, and alerting
4. Configure S3 for static assets and public share pages

---

## Phase 13 — Beta Launch (Week 15)

### Goals

- Launch to 20–50 users
- Track plan generation success rate
- Track time to plan
- Track user satisfaction

### Success metrics

- NPS > 40
- SUS > 70
- Reliable plan generation

### Tasks

1. Build internal early access onboarding
2. Implement usage analytics and feedback capture
3. Monitor production performance and correctness
4. Iterate based on beta feedback

---

## Recommended Immediate Priorities

1. Implement authentication and frontend MVP
2. Replace mock agents with real data/API-backed behavior
3. Add LangGraph orchestrator and structured merge logic
4. Add DB migrations, CI, and test coverage
5. Establish production deployment path

---

## Gap Summary

### Already present

- Service scaffolding and folder layout
- Core backend models and local dev infra
- Prototype agent and orchestrator code

### Not yet present

- Real travel API integrations
- Auth and user-facing frontend
- Workflow orchestration
- Personalization and embeddings
- Production deployment and observability
- Comprehensive automated testing

---

## How to use this plan

- Use this file as the engineering roadmap for the next 12–16 weeks
- Convert each phase into GitHub issues or sprint cards
- Track the remaining work in each phase as a dependency chain
- Start with foundations, then move service-by-service, then complete UX and deployment

---

## Notes

This plan is intentionally aligned to the existing repository state. It preserves the current prototype and turns it into a prioritized, actionable roadmap from idea → MVP → production.
