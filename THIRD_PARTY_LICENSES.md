# Third-Party Licenses

This file records the third-party dependencies that DevCovenant ships with
and directs reviewers to the corresponding license text stored under
`licenses/`.

## License Report
- `requirements.in`
- `requirements.lock`
- `pyproject.toml`

### PyYAML >= 6.0.2
- License: MIT
- License text: `licenses/PyYAML-6.0.2.txt`
- Reason: YAML parsing helpers used by the installer and tests.

### semver >= 3.0.2
- License: MIT
- License text: `licenses/semver-3.0.2.txt`
- Reason: Version handling utilities consumed by DevFlow gates and sync
  scripts.
