# Research companion

A static, dependency-free interactive companion to the approved research manuscript. The charts use versioned values in `data/research.json`, sourced from the approved manuscript and machine-readable M8 summary. Task-level endpoint values match Table V at λ = 0.20 and 0.40; the aggregate sweep retains the summary JSON precision, including mean Jaccard against the default. Illustrative walkthroughs are labeled separately from frozen M8 results. The approved paper PDF is included as `paper.pdf`; other artifact links point to specific public GitHub files.

To view locally from the repository root:

```bash
python3 -m http.server 8000 --directory site
```

Then open `http://localhost:8000/`. No build step or package installation is required.

## Measurement and data semantics

`benchmark.harnessWallTimeMs` is the timed eight-task M8 harness interval, including frozen input loading and evaluation; `processPeakRssMiB` is the process-lifetime peak. The `harnessTimingScope`, `offlineExecutionPolicy`, `socketTestCoverage`, and `wholeRunNetworkTelemetryAvailable` fields describe their limits; a configured offline policy is not measured whole-run zero egress. `applicationSeed` is not the unknown historical `PYTHONHASHSEED`. These replace the ambiguous `wallTimeMs`, `memoryMiB`, `zeroEgress`, and `seed` fields.

The ablation bars retain the historical four-decimal display. `storedTaskAggregateContrast` separately records the equal-weight eight-task aggregates 0.441350 and 0.818950 and their +0.377600 difference. The contrast combines eligibility and set-size changes; the estimator assigns gated candidates zero utility. M8's dense rung uses a test-vector encoder, not the M2 MiniLM backend. See the [merged reporting corrections](../docs/PHASE1_REPORTING_CORRECTIONS.md). The approved historical ten-page `paper.pdf` remains unchanged. Phase II remains proposed and unexecuted.
