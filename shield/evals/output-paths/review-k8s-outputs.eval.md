---
name: review-k8s-outputs
skill_under_test: shield:review-k8s
scenario: /review-k8s writes summary.md and three detailed/<skill>.md files under reviews/code/{date}/, not legacy code-review/{N}-{slug}/
---

## Setup
```bash
mkdir -p docs/shield/review-k8s-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p k8s
cat > k8s/deployment.yaml <<'EOF'
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
> Follow the /review-k8s command's Output Path conventions to run a stub Kubernetes manifest review for a feature named "review-k8s-test-20260522". Do NOT actually invoke any reviewer skills or dispatch the platform-engineer agent — synthesize stub review content yourself (a placeholder summary, plus three detailed files: detailed/k8s-security.md, detailed/k8s-cost.md, detailed/k8s-operations.md — each with a one-line stub finding). Do NOT ask the user any questions. Write all outputs to the new flat-path layout — do NOT create numbered-run subfolders or any `code-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter`. If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "review-k8s-test-20260522".

## Success criteria

### Structural
- review-k8s-test-20260522/reviews/code/2026-05-22
- detailed/k8s-security\.md
- detailed/k8s-cost\.md
- detailed/k8s-operations\.md

### Qualitative
- The agent wrote (or attempted to write) `summary.md` plus three `detailed/*.md` files (k8s-security, k8s-cost, k8s-operations) under a path ending in `reviews/code/2026-05-22/` inside the `review-k8s-test-20260522` feature folder.
- No legacy `code-review/{N}-<slug>/` folder pattern appears anywhere in the agent-written file paths or output narration.

## Pass threshold
4 of 4 structural + 2 of 2 qualitative
