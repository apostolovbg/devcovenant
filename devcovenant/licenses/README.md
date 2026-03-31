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
- `LICENSE` is DevCovenant's packaged project license.
- `THIRD_PARTY_LICENSES.md` lists the direct dependencies represented in the
  packaged lock and points to their bundled license texts.
- `*.txt` files store the bundled third-party license texts that match the
  packaged dependency surface.

## Why It Ships
DevCovenant ships these files with the package so the package comes with its
own license files.
That lets package users read DevCovenant's project license, inspect the
packaged dependency report, and review the bundled third-party license texts
that match the packaged dependency surface without needing the repository
checkout.
