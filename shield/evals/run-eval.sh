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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:?Usage: run-eval.sh <folder-or-eval-path>}"

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

  # Dispatch the subagent under test
  local prompt
  prompt=$(cat "$workdir/prompt.txt")
  claude --print --dangerously-skip-permissions --add-dir "$workdir" \
    --append-system-prompt "Working directory: $workdir" \
    <<<"$prompt" >"$workdir/output.txt" 2>"$workdir/output.err" || true

  # Run structural checks — first try output.txt, then fall back to any
  # written files in the workdir (e.g. prd.html for render evals).
  local struct_pass=0 struct_total=0 qual_pass=0 qual_total=0
  while IFS= read -r assertion; do
    [[ -z "$assertion" ]] && continue
    struct_total=$((struct_total + 1))
    if grep -qE "$assertion" "$workdir/output.txt"; then
      struct_pass=$((struct_pass + 1))
    else
      # Fallback: search all non-script written files under workdir
      local found=0
      while IFS= read -r wf; do
        if grep -qE "$assertion" "$wf" 2>/dev/null; then
          found=1
          break
        fi
      done < <(find "$workdir" -type f \
                  ! -name "output.txt" ! -name "output.err" \
                  ! -name "setup.sh" ! -name "setup.log" \
                  ! -name "prompt.txt" ! -name "structural.txt" \
                  ! -name "qualitative.txt" ! -name "threshold.txt" \
                  2>/dev/null)
      if [[ "$found" -eq 1 ]]; then
        struct_pass=$((struct_pass + 1))
      else
        echo "  STRUCT FAIL: $assertion"
      fi
    fi
  done <"$workdir/structural.txt"

  # Run qualitative checks via judge call.
  # Collect all written non-script files to give the judge full context.
  local extra_content=""
  while IFS= read -r wf; do
    local rel
    rel="${wf#$workdir/}"
    extra_content+="
--- FILE: $rel ---
$(head -200 "$wf" 2>/dev/null)
"
  done < <(find "$workdir" -type f \
              ! -name "output.txt" ! -name "output.err" \
              ! -name "setup.sh" ! -name "setup.log" \
              ! -name "prompt.txt" ! -name "structural.txt" \
              ! -name "qualitative.txt" ! -name "threshold.txt" \
              2>/dev/null)
  if [[ -s "$workdir/qualitative.txt" ]]; then
    while IFS= read -r criterion; do
      [[ -z "$criterion" ]] && continue
      qual_total=$((qual_total + 1))
      local verdict
      verdict=$(claude --print --dangerously-skip-permissions <<EOF
You are a strict eval judge. Given the model output and any written files below,
evaluate whether the criterion is met. Answer ONLY "PASS" or "FAIL".

Criterion: $criterion

Agent output:
$(cat "$workdir/output.txt")
$extra_content
EOF
      )
      if [[ "$verdict" == *"PASS"* ]]; then
        qual_pass=$((qual_pass + 1))
      else
        echo "  QUAL FAIL: $criterion"
      fi
    done <"$workdir/qualitative.txt"
  fi

  echo "  STRUCTURAL: $struct_pass/$struct_total"
  echo "  QUALITATIVE: $qual_pass/$qual_total"

  # Check pass threshold
  local threshold
  threshold=$(cat "$workdir/threshold.txt")
  echo "  THRESHOLD: $threshold"
  echo "  WORKDIR: $workdir"
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
