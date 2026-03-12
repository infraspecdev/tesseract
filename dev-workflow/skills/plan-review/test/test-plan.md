# Phase 4: API Gateway Migration

## Overview

Migrate our API gateway from Kong to AWS API Gateway to reduce operational overhead and integrate better with our AWS-native services.

Timeline: Week 8-10

## Architecture

Current: Kong running on EC2 instances behind an NLB in us-east-1.
Target: AWS API Gateway (REST API) with Lambda authorizer, connected to existing ECS services.

Traffic flows: Client → API Gateway → VPC Link → NLB → ECS services

## Stories

### Story 1: Set Up API Gateway Infrastructure

Create the API Gateway REST API, VPC link, and connect to existing NLB.

**Tasks:**
- [ ] Create REST API in API Gateway
- [ ] Set up VPC link to existing NLB
- [ ] Configure appropriate settings
- [ ] Test connectivity

**Acceptance Criteria:**
- [ ] API Gateway is deployed
- [ ] VPC link works

### Story 2: Implement Lambda Authorizer

Build a Lambda function for JWT validation, replacing Kong's JWT plugin.

**Tasks:**
- [ ] Write Lambda authorizer function
- [ ] Deploy with appropriate IAM role
- [ ] Configure caching

**Acceptance Criteria:**
- [ ] Auth works correctly
- [ ] Performance is acceptable

### Story 3: Migrate Routes

Move all API routes from Kong to API Gateway, updating path mappings and integrations.

**Tasks:**
- [ ] Export Kong routes
- [ ] Recreate in API Gateway
- [ ] Update DNS as needed

**Acceptance Criteria:**
- [ ] All routes work
- [ ] No downtime during migration

### Story 4: Monitoring Setup

Set up monitoring for the new API Gateway.

**Tasks:**
- [ ] Configure CloudWatch dashboards
- [ ] Set up alerts

**Acceptance Criteria:**
- [ ] Monitoring works

## Success Criteria

- All traffic routed through API Gateway
- Kong instances decommissioned
- No customer-facing issues during migration
