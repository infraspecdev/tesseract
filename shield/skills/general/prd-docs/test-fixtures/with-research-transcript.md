# Research Transcript — Add Gift-Card Support

> **Source:** `/research` session, 2026-05-10
> **Feature:** Add Gift-Card Support
> **Researcher:** @pm-handle

---

## Q&A Session

**Q: What is the core problem we're solving?**
A: Customers cannot currently send or receive digital gift cards through our platform. About 12% of inbound support and feature requests in Q1 2026 mention gift cards. Competitors (Shopify, BigCommerce) have had this for years. The biggest pain point is losing gift-driven purchase occasions — holiday, birthdays, milestones — to competitors because we have no gift-card product.

**Q: Who are the primary users affected?**
A: Two user groups:
1. **Gift senders** — customers who want to purchase a digital gift card and send it to a friend or family member via email. They're typically existing customers. Pain: no gift option; must go elsewhere.
2. **Gift recipients** — people who receive a gift card (may or may not be existing customers). Pain: they receive a competitor gift card because our platform doesn't exist in this space.
There's also a third internal persona: **Finance / Admin** who will need to track outstanding gift-card liability and flag fraudulent redemptions.

**Q: What constraints apply — compliance, existing systems, technical?**
A: PCI-DSS is the big one. Gift-card codes are stored-value instruments — they're effectively payment credentials. The security team has flagged that codes must be stored hashed, must never appear in logs, and the code validation endpoint needs rate limiting to prevent enumeration attacks. The legal team also flagged that some jurisdictions treat gift cards as regulated stored-value products requiring disclosure of expiry terms and non-refundability rules. Initial launch will be US-only to avoid multi-jurisdiction complexity. Technically, the existing payments service can handle gift-card purchase as a standard payment event — an eng spike confirmed this. The email delivery service (SendGrid) supports custom HTML templates and can handle the gift-card notification email. No new infrastructure is needed; this is additive to existing systems.

**Q: What does the competitive landscape look like?**
A: All major e-commerce platforms support digital gift cards. Key differentiators we could offer:
- Partial redemption (most competitors support this)
- Self-gifting (sending to yourself — useful for deferred purchases)
- Custom denominations (vs. fixed tiers only)
The baseline expectation is: purchase → email delivery → code at checkout. Anything beyond that is a differentiator.

**Q: What does success look like in 90 days?**
A: 1,000 gift cards sold per month; redemption rate ≥ 60% within 90 days of receipt; support ticket rate < 2% of total volume. The gift-card GMV should not require more than 1% fraud loss rate. These numbers come from our PM's analysis of comparable launch cohorts at similar-stage companies.

---

## Key Findings

### Problem summary
Digital gift cards are a table-stakes e-commerce feature. We are losing gifting occasions to competitors. The market window is pre-Q3 to capture the holiday season.

### Target users (personas extracted)
- **P1: Gift Sender** — existing customer, wants to purchase and send gift card via email
- **P2: Gift Recipient** — may be new to the platform; wants frictionless redemption
- **P3: Admin / Finance** — internal; needs liability tracking and fraud signals

### Constraints (existing systems / compliance)
- PCI-DSS applies to gift-card codes (stored hashed, no plaintext in logs, rate-limited validation endpoint)
- US-only launch (legal review required for multi-jurisdiction)
- Existing payments service: compatible (spike confirmed)
- Existing email service (SendGrid): supports custom templates (validated)
- Legal ToS update required for gift-card terms (expiry, non-refundable policy)

### Open questions surfaced during research
- Expiry policy: 12 months? No expiry? Jurisdiction-specific?
- Partial vs. single-use redemption codes
- Maximum gift-card denomination ($500 cap proposed, not yet agreed)

## Glossary

| Term | Definition |
|---|---|
| ICP | Ideal Customer Profile — the company size and shape we win at most. |
| PLG | Product-led growth — self-serve activation without a sales call. |
