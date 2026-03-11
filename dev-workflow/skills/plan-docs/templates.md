# Plan Docs — HTML Templates

## Architecture / ADR Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Phase {N}: {Name}</title>
<style>
body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }
h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
h2 { color: #202124; border-bottom: 1px solid #dadce0; padding-bottom: 8px; margin-top: 30px; }
h3 { color: #5f6368; margin-top: 20px; }
table { border-collapse: collapse; width: 100%; margin: 15px 0; }
th, td { border: 1px solid #dadce0; padding: 10px; text-align: left; }
th { background-color: #f1f3f4; font-weight: bold; }
tr:nth-child(even) { background-color: #f8f9fa; }
code { background-color: #f1f3f4; padding: 2px 6px; border-radius: 4px; font-family: 'Courier New', monospace; }
pre { background-color: #f1f3f4; padding: 15px; border-radius: 8px; overflow-x: auto; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 12px; }
blockquote { border-left: 4px solid #1a73e8; margin: 15px 0; padding: 10px 20px; background-color: #e8f0fe; }
ul { margin: 10px 0; }
li { margin: 5px 0; }
ol li { margin: 8px 0; }
hr { border: none; border-top: 1px solid #dadce0; margin: 30px 0; }
.nav { margin: 20px 0; padding: 10px 0; border-bottom: 1px solid #dadce0; }
.nav a { color: #1a73e8; text-decoration: none; margin-right: 15px; }
.nav a:hover { text-decoration: underline; }
</style>
</head>
<body>

<div class="nav">
  <a href="../00-overview.html">&larr; Back to Overview</a> |
  <a href="detailed-plan.html">Detailed Plan &rarr;</a> |
  <a href="../{prev-phase}/architecture.html">&larr; Phase {N-1}: {PrevName}</a> |
  <a href="../{next-phase}/architecture.html">&rarr; Phase {N+1}: {NextName}</a>
</div>

<h2>Phase {N}: {Name}</h2>

<p><strong>Timeline:</strong> Week {X} ({duration}) | <strong>Month {M}</strong> | <strong>Depends on:</strong> {dependencies or "None"}</p>

<h3>Problem</h3>

<p>{1-2 paragraphs explaining what is broken, missing, or needs to change}</p>

<h3>Context</h3>

<p><strong>Existing Infrastructure:</strong></p>

<table>
  <tr><th>Resource</th><th>Details</th><th>Status</th></tr>
  <tr><td>{resource}</td><td><code>{id}</code> {description}</td><td>Exists</td></tr>
  <tr><td>{resource}</td><td>{description}</td><td><strong>To create</strong></td></tr>
</table>

<blockquote>
<strong>Key Insight:</strong> {important context that affects the approach}
</blockquote>

<h3>Solution</h3>

<p><strong>Approach:</strong> {1-2 paragraphs describing the solution}</p>

<pre>
{ASCII architecture diagram}
</pre>

<p><strong>What changes:</strong></p>

<table>
  <tr><th>Component</th><th>Action</th></tr>
  <tr><td>{component}</td><td>{what happens to it}</td></tr>
</table>

<p><strong>What does NOT change:</strong></p>

<ul>
  <li>{thing that stays the same and why}</li>
</ul>

<h3>Deliverables</h3>

<ul>
  <li>{concrete output}</li>
</ul>

<h3>Rollback Strategy</h3>

<p>{How to undo this phase if needed}</p>

</body>
</html>
```

## Detailed Execution Plan Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Phase {N}: {Name} &mdash; Detailed Plan</title>
<style>
body { font-family: Arial, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; line-height: 1.6; }
h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
h2 { color: #202124; border-bottom: 1px solid #dadce0; padding-bottom: 8px; margin-top: 30px; }
h3 { color: #5f6368; margin-top: 20px; }
h4 { color: #202124; margin-top: 15px; }
table { border-collapse: collapse; width: 100%; margin: 15px 0; }
th, td { border: 1px solid #dadce0; padding: 10px; text-align: left; }
th { background-color: #f1f3f4; font-weight: bold; }
tr:nth-child(even) { background-color: #f8f9fa; }
code { background-color: #f1f3f4; padding: 2px 6px; border-radius: 4px; font-family: 'Courier New', monospace; }
pre { background-color: #f1f3f4; padding: 15px; border-radius: 8px; overflow-x: auto; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 12px; }
blockquote { border-left: 4px solid #1a73e8; margin: 15px 0; padding: 10px 20px; background-color: #e8f0fe; }
ul { margin: 10px 0; }
li { margin: 5px 0; }
hr { border: none; border-top: 1px solid #dadce0; margin: 30px 0; }
.nav { margin: 20px 0; padding: 10px 0; border-bottom: 1px solid #dadce0; }
.nav a { color: #1a73e8; text-decoration: none; margin-right: 15px; }
.nav a:hover { text-decoration: underline; }
.checklist { list-style-type: none; padding-left: 0; }
.checklist li { padding-left: 25px; position: relative; margin: 8px 0; }
.checklist li:before { content: "\2610"; position: absolute; left: 0; }

/* EPIC metadata */
.epic-meta { background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 8px; padding: 15px 20px; margin: 20px 0; }
.epic-meta table { margin: 0; }
.epic-meta td { border: none; padding: 4px 15px 4px 0; }
.epic-meta td:first-child { font-weight: bold; white-space: nowrap; }

/* Badges */
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; text-decoration: none; }
.badge-clickup { background-color: #e8f0fe; color: #1a73e8; border: 1px solid #1a73e8; }
.badge-clickup:hover { background-color: #d2e3fc; }
.badge-to-create { background-color: #fff3e0; color: #e65100; border: 1px solid #e65100; }
.badge-done { background-color: #e6f4ea; color: #1e8e3e; }
.badge-in-dev { background-color: #e8f0fe; color: #1a73e8; }
.badge-ready { background-color: #f1f3f4; color: #5f6368; }

/* Stories summary table */
.stories-table tr.to-create { background-color: #fff8e1; }
.stories-table td, .stories-table th { font-size: 14px; }

/* Story sections */
.story { border: 1px solid #dadce0; border-radius: 8px; padding: 20px; margin: 25px 0; }
.story-header { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 10px; }
.story-header h3 { margin: 0; color: #202124; flex: 1 1 100%; }
.story-meta { font-size: 13px; color: #5f6368; }
.story-description { margin: 10px 0; padding: 10px 15px; background-color: #f8f9fa; border-radius: 6px; }

/* Acceptance criteria */
.acceptance { background-color: #e6f4ea; padding: 15px; border-radius: 8px; margin: 15px 0; }

/* Success criteria */
.success-criteria { background-color: #fef7e0; padding: 15px; border-radius: 8px; margin: 15px 0; }

/* Phase color — only use for inline accents, NOT for h1 or blockquotes */
.phase-color { color: #1a73e8; }
</style>
</head>
<body>

<div class="nav">
  <a href="../00-overview.html">&larr; Back to Overview</a> |
  <a href="architecture.html">Architecture &rarr;</a>
</div>

<h1>Phase {N}: {Name} &mdash; Detailed Plan</h1>
<p><strong>Week {X}</strong> | {one-line summary of what this phase delivers}</p>

<!-- EPIC Metadata -->
<div class="epic-meta">
  <table>
    <tr><td>EPIC</td><td><span class="badge badge-to-create">to create</span> [EPIC] {Project} | Phase {N}: {Name}</td></tr>
    <tr><td>Status</td><td>&mdash;</td></tr>
    <tr><td>Assignee</td><td>&mdash;</td></tr>
    <tr><td>Timeline</td><td>Week {X}</td></tr>
  </table>
</div>

<!-- Infrastructure -->
<h2>Infrastructure</h2>

<table>
  <tr><th>Resource</th><th>ID / Value</th><th>Status</th></tr>
  <tr><td>{resource}</td><td><code>{id}</code> {details}</td><td>Exists</td></tr>
  <tr><td>{resource}</td><td>{description}</td><td><strong>To create</strong></td></tr>
</table>

<blockquote>
<strong>{Summary insight}.</strong> {Brief context about infrastructure state.}
</blockquote>

<hr>

<!-- Stories Summary Table -->
<h2>Stories</h2>

<table class="stories-table">
  <tr>
    <th>#</th>
    <th>Story</th>
    <th>ClickUp</th>
    <th>Status</th>
    <th>Assignee</th>
  </tr>
  <tr class="to-create">
    <td>1</td>
    <td><a href="#story-1">{Story name}</a></td>
    <td><span class="badge badge-to-create">to create</span></td>
    <td><span class="badge badge-ready">ready for dev</span></td>
    <td>&mdash;</td>
  </tr>
  <!-- When ClickUp ID exists: -->
  <!--
  <tr>
    <td>1</td>
    <td><a href="#story-1">{Story name}</a></td>
    <td><a href="https://app.clickup.com/t/{id}" class="badge badge-clickup">{id}</a></td>
    <td><span class="badge badge-ready">ready for dev</span></td>
    <td>&mdash;</td>
  </tr>
  -->
</table>

<hr>

<!-- STORY 1 -->
<div class="story" id="story-1">
  <div class="story-header">
    <h3>Story 1: {Descriptive name}</h3>
    <span class="badge badge-to-create">to create</span>
    <span class="badge badge-ready">ready for dev</span>
    <span class="story-meta">Week {X}, Day {Y}</span>
  </div>

  <div class="story-description">
    <p>{2-3 sentences: what needs to happen, why, and any key constraints. Direct prose, no user story format.}</p>
  </div>

  <h4>Tasks</h4>
  <ul class="checklist">
    <li>{Concrete action with resource IDs, config values, or commands}</li>
    <li>{Another action — specific enough to execute without ambiguity}</li>
  </ul>

  <h4>Existing Infrastructure</h4>
  <table>
    <tr><th>Resource</th><th>ID</th><th>Notes</th></tr>
    <tr><td>{resource}</td><td><code>{id}</code></td><td>Exists — {context}</td></tr>
  </table>

  <div class="acceptance">
    <h4>Acceptance Criteria</h4>
    <ul>
      <li>{Verifiable outcome — testable command or measurable state}</li>
      <li>{Another verifiable outcome}</li>
    </ul>
  </div>
</div>

<!-- Repeat story blocks... -->

<hr>

<div class="success-criteria">
  <h2>Phase Success Criteria</h2>
  <ul>
    <li>{Overall phase acceptance criterion}</li>
  </ul>
</div>

</body>
</html>
```

## Markdown Detailed Plan Template

```markdown
# Phase {N}: {Name} — Detailed Plan

**Week {X}** | {one-line summary}

> **EPIC:** `to create` — [EPIC] {Project} | Phase {N}: {Name}
> **Status:** —
> **Assignee:** —
> **Timeline:** Week {X}

## Infrastructure

| Resource | ID / Value | Status |
|---|---|---|
| {resource} | `{id}` {details} | Exists |
| {resource} | {description} | **To create** |

---

## Stories

| # | Story | ClickUp | Status | Assignee |
|---|---|---|---|---|
| 1 | [{Story name}](#story-1-story-name) | `to create` | ready for dev | — |

---

### Story 1: {Descriptive name}

`to create` · `ready for dev` · Week {X}, Day {Y}

{2-3 sentences describing what needs to happen and why.}

#### Tasks
- [ ] {Concrete action with resource IDs}
- [ ] {Another specific action}

#### Existing Infrastructure
| Resource | ID | Notes |
|---|---|---|
| {resource} | `{id}` | Exists |

#### Acceptance Criteria
- [ ] {Verifiable outcome}
- [ ] {Another verifiable outcome}

[CU:] <!-- ClickUp ID populated after sync -->

---

## Phase Success Criteria
- [ ] {Overall acceptance criterion}
```

## Markdown Architecture / ADR Template

```markdown
# Phase {N}: {Name}

**Timeline:** Week {X} ({duration}) | **Month {M}** | **Depends on:** {deps}

### Problem

{1-2 paragraphs on what's broken or missing}

### Context

**Existing Infrastructure:**

| Resource | Details | Status |
|---|---|---|
| {resource} | `{id}` {description} | Exists |
| {resource} | {description} | **To create** |

> **Key Insight:** {important context that affects the approach}

### Solution

**Approach:** {1-2 paragraphs describing the solution}

```
{ASCII architecture diagram}
```

**What changes:**

| Component | Action |
|---|---|
| {component} | {what happens} |

**What does NOT change:**
- {thing that stays the same}

### Deliverables
- {concrete output}

### Rollback Strategy

{How to undo if needed}
```
