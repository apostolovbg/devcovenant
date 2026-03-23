# Workflow

## Overview
Use this doc for the exact gate sequence and the run-artifact workflow.
It should explain what each command is for and when to rerun part of the
sequence.

The value of this page is operational certainty.
Someone using it should be able to tell which command comes next, what proof it
records, and how to recover when one step mutates files or fails.

## What This Doc Should Cover
Explain:

1. `check` versus `gate --status`

2. `gate --start`, `gate --mid`, `test`, and `gate --end`

3. why `gate --mid` exists

4. run-log inspection order

5. recovery rules

6. the relationship between local workflow and the generated `CI and Tests`
   workflow

7. the rule that the global CI base stays generic while repo-family extras
   can arrive through profile `governance_and_test` fragments

8. managed-environment use in CI as a metadata-driven contract, not a
   hardcoded virtual-environment activation recipe

## Writing Rules
Keep this doc operational.
Do not let unrelated package, config, or architecture detail crowd the main
workflow explanation, and always prefer the next correct action over abstract
workflow philosophy.
