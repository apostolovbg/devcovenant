# DevCovenant Data Profile Template

## Table of Contents
- Overview
- Workflow
- Structure

## Overview
This template describes the baseline expectations for a repository that
primarily stores datasets, reports, or other data artifacts. The data
profile keeps documentation consistent so collaborators can understand
what is stored here, how it is updated, and which parts are considered
source-of-truth. Treat this file as the human entry point for data work
and keep it current when datasets or schema definitions change.

## Workflow
1. Add or update data assets inside the data directories.
2. Record a short summary of what changed and why.
3. Update any schema notes or metadata files alongside the data.
4. Validate that file names, formats, and paths follow the documented
   conventions.
5. Run the repository checks so policy enforcement stays in sync.

## Structure
Data repositories commonly include a data folder, a manifest describing
the dataset inventory, and supporting documentation in the root README.
This template expects a data manifest file that lists datasets, their
sources, and any processing requirements. Keep related notes nearby so
reviewers can verify lineage, ownership, and update cadence.
