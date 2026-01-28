# Virtual Environment

DevCovenant recommends a dedicated `.venv/` directory for python projects.
Create it with:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.in
```

Use `venv.md` to document your repository-specific environment notes if
`requirements.in` is not sufficient.
