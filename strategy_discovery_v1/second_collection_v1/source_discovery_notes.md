# Second-collection source discovery notes

## QuantConnect Research

Official repository URL: https://github.com/QuantConnect/Research

The repository describes itself as a collection of research notebooks and tutorials using the QuantConnect LEAN platform. The visible repository page lists research topics including mean reversion, Kalman filters and pairs trading, stationary processes and z-scores, EMA cross strategies, and pairs trading based on cointegration. The default branch is `master`; the observed head from the GitHub API was `d89cf67bc37bc032f0de47089e16d825bcd8a65f`. The recursive tree contained 27 notebooks, including 5 analysis notebooks and 9 Research2Production notebooks. These are eligible as stable open-quant source records, but each remains subject to the existing deterministic-normalization gate.

Official QuantConnect LEAN repository URL: https://github.com/QuantConnect/Lean

The recursive tree contained 869 C# and 456 Python files beneath `Algorithm.CSharp/` and `Algorithm.Python/`. The tree contained 11 C# and 14 Python alpha files, plus many other algorithm examples. Regression, benchmark, basic-template, and test files must be excluded from strategy-lead collection because they are infrastructure or demonstrations rather than strategy candidates. The stable revision/path locator and blob SHA are retained for any collected record.

## AQR Research

Official research index: https://www.aqr.com/Insights/Research

The public index exposes stable research URLs and describes research content, including an Academic Alpha category. AQR material is an allowed published-quant-research source family, but the existing source registry states that a broad factor narrative without deterministic entry, exit, and sizing rules remains a research reference rather than a candidate. No performance claim is treated as executable rule evidence.

## Man Institute / Man Insights

The source-registry locator `https://www.man.com/maninstitute` redirects to the official Man Insights hub at https://www.man.com/insights. The page exposes stable insight URLs and topic/series filters, but its legal notice explicitly frames the material as informational and not a recommendation. Man material is therefore retained only as an allowed research-reference source family, and exact deterministic disclosure remains required at normalization.

## Collection implication

The second collection will diversify beyond the first run's arXiv-only source distribution by using separate source-class slices: academic/preprint microstructure and systematic-finance records, stable QuantConnect open-code/notebook records, and stable AQR/Man public research pages where sufficient provenance is available. Any source without an actual stable locator and snapshot hash will be rejected or withheld from candidate-lead records. No source-registry, schema, protocol, lifecycle, first-run, L2, Drive, or trial-ledger artifact is changed by these notes.

## Additional browser verification

A direct SSRN search URL tested during this run returned a page-not-found response, so no SSRN records will be synthesized or collected without a stable, accessible SSRN record endpoint. The official AQR research index was successfully inspected. It exposes stable relative research URLs including `Working-Paper/The-Tax-Benefits-of-Pre-Tax-Alpha`, `White-Papers/Academic-Alpha`, and other research pages; the page also exposes pagination indicators. These URLs can be collected as published-quant-research leads with the exact page URL and retrieved-page hash, but the existing source policy still governs normalization.

The AQR page was inspected in the browser and its extracted HTML was saved by the browser under `/home/ubuntu/browser_html/aqr_com_Research_1787721525064.html`; this local browser cache is evidence only and is not a repository artifact.
