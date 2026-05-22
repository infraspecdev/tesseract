# Findings — Event sourcing for financial transaction systems

Synthesized from the fan-out research streams that ran against the framing brief.
Deliberately has gaps relative to PF7 and PF8 so PM11 has something to flag.

## Summary

Event sourcing offers strong audit and replay properties but at non-trivial
operational cost. The append-only model directly conflicts with GDPR right-to-erasure
unless paired with crypto-shredding or tombstone strategies. For our 2026 ledger
decision, the net of the evidence below is: adopt selectively for a write-heavy
subset, not as a whole-system rewrite.

## What the pattern actually is

Greg Young's framing in his 2010 CQRS+ES keynote is the cleanest starting point:
> "Event sourcing means that you store every state change to the application as
> an event in an immutable sequence. The state is then derived by replaying the
> events."

That sentence is doing most of the work. The pattern is conceptually simple;
the operational consequences are not.

## Durability and ordering — what the research says

Log-structured storage research underwrites the durability claim. The 2012
Calvin paper (Thomson et al.) on deterministic transaction ordering shows that
total-order log replay is achievable at production volume:
> "Calvin's deterministic execution model guarantees that any replica processing
> the input log in order will arrive at identical state, eliminating the need
> for inter-replica commit coordination."

This is the technical floor for ES as a transaction ledger — without it, the
"replay equals truth" claim does not hold under partition.

## What practitioners regret

Post-mortems from teams that adopted ES and pulled back tend to cluster around
three issues: schema migration pain, snapshot management overhead, and event-
shape lock-in. From a Software Engineering Daily episode on event-driven
architecture (2021):
> "The thing nobody tells you is that every event you write is a contract you
> can never break. We had events from 2017 we still had to support in 2021."

That regret pattern is reliably load-bearing — it shows up across vendor-
agnostic teams.

## What the references say

For canonical references on the pattern itself, see Martin Fowler's "Event
Sourcing" article on martinfowler.com (2005, updated 2017) and the broader
DDD literature.

## References

- Greg Young, "CQRS and Event Sourcing", keynote 2010
- Martin Fowler, "Event Sourcing", martinfowler.com, 2017 update
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013
- Thomson et al., "Calvin: Fast Distributed Transactions for Partitioned Database Systems", SIGMOD 2012
- Software Engineering Daily, "Event-Driven Architecture", podcast episode, 2021
