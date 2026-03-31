# License Assets

## Table of Contents
- [Overview](#overview)
- [Contents](#contents)
- [Why It Ships](#why-it-ships)

## Overview
This packaged directory ships the license artifacts that travel with the
published DevCovenant distribution.
It is meant to tell package users what these files are, not to instruct
repository maintainers how to regenerate them.

## Contents
- `LICENSE` is the packaged mirror of the project license from the repo root.
- `THIRD_PARTY_LICENSES.md` lists the direct dependencies represented in the
  packaged lock and points to their bundled license texts.
- `*.txt` files store the bundled third-party license texts that match the
  packaged dependency surface.

## Why It Ships
DevCovenant ships these files with the package so the project license, the
dependency report, and the bundled third-party license texts stay together in
one installed artifact.
