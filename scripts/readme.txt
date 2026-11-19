uv run scripts/check_hubspot.py
uv run scripts/try_search.py
uv run scripts/run_evals.py 2>&1 | tee eval.log 
grep -E "MISMATCH|/3" eval.log