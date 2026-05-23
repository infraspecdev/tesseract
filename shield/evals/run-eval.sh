#!/usr/bin/env bash
# Shield eval runner — dispatches a subagent via the `claude` CLI, captures
# output, and runs structural + qualitative checks defined in the eval file.
#
# Usage:
#   ./shield/evals/run-eval.sh <path-fragment>
#   ./shield/evals/run-eval.sh prd-docs/01-terminologies-autofill
#   ./shield/evals/run-eval.sh prd-docs            # run all in folder
set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
  echo "run-eval: requires the \`claude\` CLI in PATH" >&2
  exit 127
fi

# Per-dispatch timeout (seconds). Override with EVAL_TIMEOUT / EVAL_JUDGE_TIMEOUT.
# An eval that overruns the timeout is recorded as a FAIL with `TIMEOUT` in the
# output, rather than blocking the rest of the batch.
EVAL_TIMEOUT="${EVAL_TIMEOUT:-300}"
EVAL_JUDGE_TIMEOUT="${EVAL_JUDGE_TIMEOUT:-90}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:?Usage: run-eval.sh <folder-or-eval-path>}"

OVERALL_EXIT=0
EVAL_PASS=0
EVAL_TOTAL=0

run_one() {
  local eval_file="$1"
  local name
  name=$(basename "$eval_file" .md)
  echo "=== $name ==="
  local workdir
  workdir=$(mktemp -d)
  # Parse setup, prompt, criteria from eval markdown (simple sectional split)
  python3 "$SCRIPT_DIR/_parse_eval.py" "$eval_file" "$workdir"

  # Run the setup
  if [[ -f "$workdir/setup.sh" ]]; then
    (cd "$workdir" && bash setup.sh) >"$workdir/setup.log" 2>&1
  fi

  # Dispatch the subagent under test.
  # Touch a sentinel file just before launching so we can distinguish
  # setup-created files from agent-written files in the fallback search.
  touch "$workdir/.agent_start"
  local prompt
  prompt=$(cat "$workdir/prompt.txt")
  # Run from the plugin root so skills are visible, but add-dir the workdir so
  # the agent resolves relative paths (docs/shield/...) there, not in the repo.
  # Wrap in `timeout` so a hung dispatch can't block the rest of the batch.
  local dispatch_rc=0
  timeout --kill-after=10 "$EVAL_TIMEOUT" \
    claude --print --dangerously-skip-permissions --add-dir "$workdir" \
    --append-system-prompt "Your working directory for this task is $workdir. Resolve ALL relative file paths — both reads and writes — against $workdir. The .shield.json and all project files (docs/, research transcripts, etc.) are under $workdir. Always use absolute paths prefixed with $workdir when reading or writing any file." \
    <<<"$prompt" >"$workdir/output.txt" 2>"$workdir/output.err" || dispatch_rc=$?
  if [[ "$dispatch_rc" -eq 124 ]] || [[ "$dispatch_rc" -eq 137 ]]; then
    echo "  TIMEOUT: dispatch exceeded ${EVAL_TIMEOUT}s (rc=$dispatch_rc)" >&2
    echo "[TIMEOUT after ${EVAL_TIMEOUT}s]" >>"$workdir/output.txt"
  fi

  # Collect agent-written files once (newer than sentinel). Used by both
  # structural matching and the bidirectional "no unaccounted file" check.
  local agent_files=()
  while IFS= read -r wf; do
    agent_files+=("$wf")
  done < <(find "$workdir" -newer "$workdir/.agent_start" -type f \
              ! -name "output.txt" ! -name "output.err" \
              2>/dev/null)

  # Run structural checks — for each assertion, find at least one matching
  # source: output.txt narration, an agent-written file's PATH, or its CONTENT.
  local struct_pass=0 struct_total=0 qual_pass=0 qual_total=0
  while IFS= read -r assertion; do
    [[ -z "$assertion" ]] && continue
    struct_total=$((struct_total + 1))
    if grep -qE "$assertion" "$workdir/output.txt"; then
      struct_pass=$((struct_pass + 1))
    else
      local found=0
      for wf in "${agent_files[@]:-}"; do
        [[ -z "$wf" ]] && continue
        local rel="${wf#$workdir/}"
        if echo "$rel" | grep -qE "$assertion" 2>/dev/null; then
          found=1
          break
        fi
        if grep -qE "$assertion" "$wf" 2>/dev/null; then
          found=1
          break
        fi
      done
      if [[ "$found" -eq 1 ]]; then
        struct_pass=$((struct_pass + 1))
      else
        echo "  STRUCT FAIL: $assertion"
      fi
    fi
  done <"$workdir/structural.txt"

  # Bidirectional check: every agent-written file's PATH must match at least
  # one structural assertion. Catches improvised/legacy paths positively:
  # a file at a wrong path won't match any assertion and is reported here.
  # This replaces the old "must-not-find" qualitative anti-pattern checks.
  #
  # Implicitly-allowed derived globals (no per-eval declaration required):
  #   - docs/shield/manifest.json   (regenerated on every write)
  #   - docs/shield/index.html      (regenerated on every write)
  #   - any file under outputs/     (rendered HTML side-artifacts)
  # Per the hardening plan's strengthened-eval guidance.
  local extra_total=0 extra_unmatched=0
  for wf in "${agent_files[@]:-}"; do
    [[ -z "$wf" ]] && continue
    extra_total=$((extra_total + 1))
    local rel="${wf#$workdir/}"
    # Exempt derived globals.
    if echo "$rel" | grep -qE "(^|/)(manifest\.json|index\.html)$|(^|/)outputs/"; then
      continue
    fi
    local matched=0
    while IFS= read -r assertion; do
      [[ -z "$assertion" ]] && continue
      if echo "$rel" | grep -qE "$assertion" 2>/dev/null; then
        matched=1
        break
      fi
    done <"$workdir/structural.txt"
    if [[ "$matched" -eq 0 ]]; then
      extra_unmatched=$((extra_unmatched + 1))
      echo "  EXTRA FAIL: $rel (no structural assertion matches this path)"
    fi
  done

  # Run qualitative checks via judge call, but ONLY if the eval declares any.
  # Evals that omit `### Qualitative` are deterministic-only: structural +
  # bidirectional must-find is all that gets scored.
  if [[ -s "$workdir/qualitative.txt" ]]; then
    # Build a context block of agent-written files for the judge.
    local extra_content=""
    for wf in "${agent_files[@]:-}"; do
      [[ -z "$wf" ]] && continue
      local rel="${wf#$workdir/}"
      extra_content+="
--- FILE: $rel ---
$(head -200 "$wf" 2>/dev/null)
"
    done
    while IFS= read -r criterion; do
      [[ -z "$criterion" ]] && continue
      qual_total=$((qual_total + 1))
      # Run the judge in a way that lets us capture its exit code separately
      # from the `local` assignment (which would otherwise mask it via $?=0).
      local verdict_out
      local judge_rc=0
      verdict_out=$(timeout --kill-after=10 "$EVAL_JUDGE_TIMEOUT" \
        claude --print --dangerously-skip-permissions <<EOF
You are a strict eval judge. Given the model output and any written files below,
evaluate whether the criterion is met. Answer ONLY "PASS" or "FAIL".

Criterion: $criterion

Agent output:
$(cat "$workdir/output.txt")
$extra_content
EOF
      ) || judge_rc=$?
      if [[ "$judge_rc" -eq 124 ]] || [[ "$judge_rc" -eq 137 ]]; then
        echo "  QUAL TIMEOUT (judged FAIL): $criterion"
        verdict_out="FAIL"
      fi
      if [[ "$verdict_out" == *"PASS"* ]]; then
        qual_pass=$((qual_pass + 1))
      else
        echo "  QUAL FAIL: $criterion"
      fi
    done <"$workdir/qualitative.txt"
  fi

  echo "  STRUCTURAL: $struct_pass/$struct_total"
  if [[ "$extra_total" -gt 0 ]]; then
    local matched=$((extra_total - extra_unmatched))
    echo "  COVERAGE:   $matched/$extra_total agent files match a structural pattern"
  fi
  if [[ "$qual_total" -gt 0 ]]; then
    echo "  QUALITATIVE: $qual_pass/$qual_total"
  fi

  # Check pass threshold
  local threshold
  threshold=$(cat "$workdir/threshold.txt")
  echo "  THRESHOLD: $threshold"

  local req_struct req_qual
  req_struct=$(grep -oE "[0-9]+ of [0-9]+ structural" "$workdir/threshold.txt" | grep -oE "^[0-9]+" || true)
  req_qual=$(grep -oE "[0-9]+ of [0-9]+ qualitative" "$workdir/threshold.txt" | grep -oE "^[0-9]+" || echo 0)
  if [[ -z "$req_struct" ]]; then req_struct=$struct_total; fi

  EVAL_TOTAL=$((EVAL_TOTAL + 1))
  if [[ "$struct_pass" -lt "$req_struct" ]] \
      || [[ "$qual_pass" -lt "$req_qual" ]] \
      || [[ "$extra_unmatched" -gt 0 ]]; then
    echo "  RESULT: FAIL $name"
    OVERALL_EXIT=1
  else
    echo "  RESULT: PASS $name"
    EVAL_PASS=$((EVAL_PASS + 1))
  fi
  echo
}

if [[ -d "$SCRIPT_DIR/$TARGET" ]]; then
  for f in "$SCRIPT_DIR/$TARGET"/*.md; do
    [[ -f "$f" ]] || continue
    [[ "$(basename "$f")" == "README.md" ]] && continue
    run_one "$f"
  done
elif [[ -f "$SCRIPT_DIR/$TARGET.md" ]]; then
  run_one "$SCRIPT_DIR/$TARGET.md"
elif [[ -f "$SCRIPT_DIR/$TARGET" ]]; then
  run_one "$SCRIPT_DIR/$TARGET"
else
  echo "Eval not found: $TARGET" >&2
  exit 1
fi

echo "=== Aggregate: $EVAL_PASS/$EVAL_TOTAL evals passed ==="
exit $OVERALL_EXIT
