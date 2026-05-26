---
name: 02-architecture-flows-prompting
skill_under_test: shield:prd-docs
scenario: A flow-heavy feature should get a populated §5; a trivial one should allow §5 empty
---

## Setup
```bash
mkdir -p docs/shield/payment-checkout
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
```

## Prompt
> Author a standard PRD for "payment-checkout" — a new checkout flow integrating with three PSPs (Stripe, Adyen, Braintree), 3DS challenges, and idempotency keys. Walk all sections. When you reach §5 Architecture & flows, propose what diagrams (if any) make sense and include at least one Mermaid block if the flows warrant it. Output the final prd.md content only.

## Success criteria

### Structural
- ## 5\. Architecture & flows
- ```mermaid

### Qualitative
- §5 contains at least one Mermaid code block showing a meaningful payment flow or system topology (not a placeholder).
- The diagram references PSPs, 3DS, or idempotency — terms central to the feature's flow complexity.

## Pass threshold
2 of 2 structural + 2 of 2 qualitative.
