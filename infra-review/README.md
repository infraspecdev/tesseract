# infra-review

A Claude Code plugin for reviewing Terraform infrastructure in Atmos component repositories. Provides specialized review agents, skills, and slash commands covering security, architecture, operations, cost optimization, the AWS Well-Architected Framework, and terraform plan analysis.

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- A Terraform/Atmos component repository (single-component `src/` or multi-component `components/terraform/*/` layout)

## Installation

Place this plugin in your Claude Code plugins directory:

```
~/.claude/plugins/local/infra-review/
```

The plugin activates automatically when you open a Terraform component repository.

### Companion: terraform-skill

For general Terraform best practices (naming, module patterns, testing strategy, CI/CD, code structure), install [antonbabenko/terraform-skill](https://github.com/antonbabenko/terraform-skill):

```
/plugin marketplace add antonbabenko/terraform-skill
```

This plugin handles Atmos-specific and AWS-specific reviews; terraform-skill handles general Terraform/OpenTofu patterns. They complement each other.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/review-component` | Full 4-perspective review (security, architecture, operations, cost) |
| `/review-security` | Security-focused review (IAM, encryption, network, Checkov) |
| `/review-cost` | Cost optimization analysis with environment-specific recommendations |
| `/review-hygiene` | Quick Atmos component conventions check |
| `/review-cicd` | GitHub Actions workflow audit |
| `/review-well-architected` | AWS Well-Architected Framework review across all 6 pillars |
| `/analyze-plan` | Analyze `terraform plan` output for security, cost, and destructive action impact |

## Review Agents

Each agent has a distinct persona and checklist:

| Agent | Persona | Focus |
|-------|---------|-------|
| `security-reviewer` | Senior Cloud Security Engineer | IAM policies, encryption, network exposure, Checkov skips, secrets management |
| `architecture-reviewer` | Senior Infrastructure Architect | File layout, naming, variable/output interface, DRY patterns, Atmos integration, reliability, tests |
| `operations-reviewer` | Senior SRE | Monitoring, tagging, blast radius, state safety, observability, CI/CD gates |
| `cost-reviewer` | Senior FinOps Engineer | NAT gateway patterns, right-sizing, toggleable resources, environment tiering, data transfer |
| `well-architected-reviewer` | AWS Solutions Architect | All 6 WAF pillars with cross-pillar trade-off analysis |

The security and cost agents are plan-aware: when a plan analysis exists, they cross-reference planned changes against their checklists for more accurate findings.

## Skills

Skills are invoked automatically when relevant, or used by commands internally:

| Skill | When It Activates |
|-------|-------------------|
| `atmos-repo-review` | Reviewing an Atmos repository structure (stacks, components, catalog) |
| `atmos-component-hygiene` | Adding or modifying Terraform components -- runs R1-R8 repo checks and C1-C10 per-component checks |
| `terraform-security-audit` | Auditing IAM policies, network exposure, encryption, and Checkov configuration |
| `terraform-cost-review` | Identifying cost drivers and recommending environment-specific variable overrides |
| `terraform-test-coverage` | Reviewing `.tftest.hcl` files for coverage across 6 dimensions |
| `terraform-plan-analyzer` | Parsing `terraform plan -json` output for security, cost, drift, and destructive action analysis |
| `github-actions-reviewer` | Auditing GitHub Actions for version drift, permissions, concurrency, and path filters |

## Plan Analysis

The `/analyze-plan` command provides runtime analysis of Terraform execution plans. It parses `terraform plan -json` output and surfaces:

- **Change summary** -- resource counts by action (create, update, replace, destroy)
- **Destructive action warnings** -- flags destroy/replace on stateful resources (RDS, S3, DynamoDB, KMS)
- **Security-sensitive changes** -- IAM policy modifications, security group rule changes, encryption downgrades, public access changes
- **Cost impact estimates** -- NAT gateways, VPC endpoints, compute instances being added or removed
- **Drift detection** -- resources changed outside Terraform

Plan sources (in priority order):
1. User-provided plan JSON file
2. Saved `plan.tfplan` file converted via `terraform show -json`
3. Generated locally via `terraform plan -json -lock=false` (requires `terraform init`)

## Hooks

- **SessionStart** -- Detects if the current directory is an Atmos component repo and surfaces available commands
- **PostToolUse** (Write/Edit) -- Reminds to run `terraform fmt` and `terraform validate` after `.tf` file edits, and suggests `/analyze-plan` to preview impact

## Output

All review reports are written to the target repository under:

```
<repo-root>/claude/infra-review/
```

| Command | Output File |
|---------|-------------|
| `/review-component` | `review.md` |
| `/review-security` | `security-review.md` |
| `/review-cost` | `cost-review.md` |
| `/review-hygiene` | `hygiene-review.md` |
| `/review-cicd` | `cicd-review.md` |
| `/review-well-architected` | `well-architected-review.md` |
| `/analyze-plan` | `plan-analysis.md` |

The `atmos-repo-review` skill writes to `claude/atmos-repo-review/analysis.md` and `plan.md`.

## Supported Repository Layouts

**Single-component** (template-based):
```
src/
  main.tf
  variables.tf
  outputs.tf
  versions.tf
  providers.tf
```

**Multi-component**:
```
components/terraform/
  vpc/
    main.tf, variables.tf, outputs.tf, versions.tf, ...
  s3-bucket/
    main.tf, variables.tf, outputs.tf, versions.tf, ...
```

## License

MIT
