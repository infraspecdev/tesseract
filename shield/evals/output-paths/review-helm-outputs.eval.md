---
name: review-helm-outputs
skill_under_test: shield:review-helm
scenario: /review-helm writes summary.md and three detailed/<skill>.md files under reviews/code/{date}/, not legacy code-review/{N}-{slug}/
---

## Setup
```bash
mkdir -p docs/shield/review-helm-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p charts/example/templates
cat > charts/example/Chart.yaml <<'EOF'
apiVersion: v2
name: example
version: 0.1.0
EOF
cat > charts/example/templates/deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: app
          image: nginx
EOF
```

## Prompt
> Follow the /review-helm command's Output Path conventions to run a stub Helm chart review for a feature named "review-helm-test-20260522". Do NOT actually invoke any reviewer skills — synthesize stub review content yourself (a placeholder summary, plus three detailed files: detailed/helm-structure.md, detailed/k8s-security.md, detailed/k8s-operations.md — each with a one-line stub finding). Do NOT ask the user any questions. Write all outputs to the new flat-path layout — do NOT create numbered-run subfolders or any `code-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter`. If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "review-helm-test-20260522".

## Success criteria

### Structural
- review-helm-test-20260522/reviews/code/2026-05-22(_\d+)?/summary\.md
- review-helm-test-20260522/reviews/code/2026-05-22(_\d+)?/detailed/helm-structure\.md
- review-helm-test-20260522/reviews/code/2026-05-22(_\d+)?/detailed/k8s-security\.md
- review-helm-test-20260522/reviews/code/2026-05-22(_\d+)?/detailed/k8s-operations\.md

## Pass threshold
4 of 4 structural
