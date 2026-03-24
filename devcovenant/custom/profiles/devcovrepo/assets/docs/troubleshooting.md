# Troubleshooting

## Overview
Use this doc for fast recovery paths.
It should help operators and maintainers get from a failed command to the next
correct action quickly.

This is not the place for a second architecture document.
Keep it focused on symptoms, likely causes, the logs to inspect first, and the
next command or file to check.

## What This Doc Should Cover
Explain the most common failure groups:

- gate failures

- changelog coverage failures

- registry drift

- config and metadata mistakes

- installed-CLI and `pipx` path problems

- managed-environment failures

- translator or profile mismatches

- build and publish failures

## Writing Rules
Prefer short recovery sequences over long theory.
Point readers at the right logs and the next command to run, and explain the
smallest useful reason a failure usually happens so the recovery advice does
not feel like ritual.
