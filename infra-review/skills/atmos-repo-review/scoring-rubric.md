# Scoring Rubric

## Evaluation Dimensions (1-5 scale)

| Criterion | What to Evaluate |
|-----------|-----------------|
| **Atmos-native structure** | Separation of stacks/components, catalog usage, naming |
| **Environment strategy** | Dev/stage/prod separation, region/account patterns |
| **Reuse & DRY** | Imports, globals, context variables, minimal duplication |
| **Naming conventions** | Component, stack, stage, path consistency |
| **Layering & overrides** | Precedence order, explicit patterns, minimal magic |
| **Security & governance** | Secrets handling, IAM boundaries, cross-account |
| **Operability** | Discoverability, documentation, guardrails, terraform-docs automation |
| **Scalability** | Can add stacks/regions/accounts without restructuring |
| **CI/CD fit** | Validation, formatting, drift detection, promotions |
| **Blast-radius control** | State isolation, stack boundaries, safe defaults |

## Grading Scale

| Grade | Meaning |
|-------|---------|
| **A** | Production-ready, follows all best practices, scales well |
| **B** | Solid foundation, minor improvements needed, operational |
| **C** | Functional but has structural issues affecting scale/safety |
| **D** | Significant problems, needs refactoring before scaling |
| **F** | Fundamentally broken or missing critical Atmos patterns |
