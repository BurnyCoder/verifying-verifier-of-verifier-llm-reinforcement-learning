# Dated analysis amendments

## 26 November 2026 · secondary output-format diagnostic

While inspecting the first frozen-solver development replay we observed a correct calculation written with a named assignment on each line. Other responses copied the step names. This motivated a post-hoc development diagnostic. The same diagnostic was specified before any held-out evaluation.

Count otherwise malformed solver responses that give exactly one integer assignment per line, with the original step IDs in order, and all values correct. Reject extra prose, missing steps, repeated IDs and expressions on the right-hand side. Publish the count alongside the strict parse rate and the sample size. The registered reward, primary endpoint, checkpoint choices and held-out decision rule retain their original definitions. The supplemental count describes recoverable serialization errors and cannot establish general mathematical ability.
