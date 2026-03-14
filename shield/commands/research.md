---
name: research
description: Research a technical topic with structured citations and expert sources
---

# Research

Invoke the Shield research skill to investigate a technical topic.

## Usage

`/research [topic]`

## Behavior

1. If a topic is provided as an argument, use it directly
2. If no topic, ask the user what they'd like to research
3. Invoke the `shield:general:research` skill with the topic
4. The skill handles the full research workflow: clarify scope, parallel research, synthesize, write document
5. After completion, invoke the `shield:general:summarize` skill to produce a research summary
6. Write the summary to the run directory
