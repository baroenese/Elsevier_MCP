## Summary

- 

## Checks

- [ ] `python -m compileall -q elsevier_mcp_complete.py examples test.py`
- [ ] `python -m build`
- [ ] `python -m twine check dist/*`
- [ ] Live Elsevier API behavior was tested, or the change does not affect API calls

## Data and Terms

- [ ] No API keys, institutional tokens, licensed full text, or cached Elsevier responses are committed
- [ ] New API behavior follows Elsevier API terms and rate-limit expectations
