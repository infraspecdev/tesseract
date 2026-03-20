# Architecture Review — Plan Review Mode

**Score:** 52/100 | **Grade:** B-

## Check Results

| # | Check | Grade | Notes |
|---|-------|-------|-------|
| CA1 | Service topology | B | Correct layering: validation -> error handling -> auth. Dependency graph is sound. |
| CA2 | Scalability | D | In-memory dict, global counter. No persistence. No multi-worker support. |
| CA3 | High availability | D | No deployment topology. Shallow health check. No graceful shutdown. |
| CA4 | Multi-region | F | Not addressed. Understandable for demo but scope not stated. |
| CA5 | Network design | D | No CORS, no rate limiting, no network topology. |
| CA6 | Blast radius | C | Global exception handler is good. No request size limits, no store bounds. |
| CA7 | Technology selection | B | FastAPI + Pydantic + PyJWT are excellent choices. In-memory dict is the weak point. |
| CA8 | Environment parity | D | No dev/staging/prod differentiation. No config management across environments. |

## Key Finding

Well-structured application-layer hardening, but completely ignores deployment, persistence, and operational concerns.

## P0 Recommendations

1. Replace in-memory store or explicitly scope plan as "demo only, not for production"
2. Add rate limiting to login endpoint

## P1 Recommendations

1. Add CORS middleware configuration
2. Deepen health check (verify downstream dependencies)
3. Add request body size limits at middleware level
4. Address _counter race condition (use uuid4)
5. Add JWT secret rotation story
