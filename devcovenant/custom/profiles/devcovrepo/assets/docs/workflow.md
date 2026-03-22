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

- `check` versus `gate --status`

- `gate --start`, `gate --mid`, `test`, and `gate --end`

- why `gate --mid` exists

- run-log inspection order

- recovery rules

- the relationship between local workflow and CI

## Writing Rules
Keep this doc operational.
Do not let unrelated package, config, or architecture detail crowd the main
workflow explanation, and always prefer the next correct action over abstract
workflow philosophy.
