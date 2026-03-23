# Installation and Lifecycle

## Overview
Use this doc for the lifecycle command story.
Keep the install-versus-deploy boundary explicit and practical.

This page should help a maintainer understand what changes in the repository at
each lifecycle step.
It should also explain why DevCovenant separates initial setup, human review,
and full activation instead of treating them as one opaque command.

## What This Doc Should Cover
Explain:

- `install` as setup

- config review as the human checkpoint

- `deploy` as activation

- normal refresh and upgrade behavior

- cleanup, undeploy, and uninstall

- the rule that `clean` may prune older logs but must keep its active run
  folder

- empty-repo, seeded-doc, and existing-repo starting situations

- the first full gate cycle as proof that activation succeeded

## Writing Rules
Prefer direct operational language.
Avoid mixing unrelated package or architecture material into this doc, but do
explain the reason each lifecycle boundary exists so the sequence feels sane.
