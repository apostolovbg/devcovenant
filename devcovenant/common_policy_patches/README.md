# Common Policy Patches
**Last Updated:** 2026-01-11
**Version:** 0.1.1

Patch files override built-in policy metadata without modifying the core
policy scripts. Each patch is a YAML file named after the policy id, e.g.
`line_length_limit.yml`.

Example patch:
```
max_length: 100
exclude_globs: vendor/**
```
