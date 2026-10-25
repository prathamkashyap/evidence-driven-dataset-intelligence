# Research companion

A static, dependency-free interactive companion to the approved research manuscript. The charts use versioned values in `data/research.json`, sourced from the approved manuscript and machine-readable M8 summary. Task-level endpoint values match Table V at λ = 0.20 and 0.40; the aggregate sweep retains the summary JSON precision, including mean Jaccard against the default. Illustrative walkthroughs are labeled separately from frozen M8 results. The approved paper PDF is included as `paper.pdf`; other artifact links point to specific public GitHub files.

To view locally from the repository root:

```bash
python3 -m http.server 8000 --directory site
```

Then open `http://localhost:8000/`. No build step or package installation is required.
