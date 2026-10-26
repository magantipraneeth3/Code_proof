# CodeProof Authorship Analysis Technical Validation

**Audit date:** 2026-10-26  
**Scope:** Workspace source, configured runtime path, tests, frontend result presentation, and available local ML/data directories.  
**Deployment conclusion:** Not validated for educational authorship classification. The authorship classifier is disabled and must remain disabled.

## Executive Summary

CodeProof performs Python AST/tokenize analysis and Tree-sitter syntax/structure parsing for Java, C, C++, JavaScript, TypeScript, and TSX. It does not perform AI-authorship classification or provenance verification. Public comparison uses within-language parser leaf tokens, sequence matching, and 3-gram overlap. Similarity is not an authorship method. Professor review notes and status are human workflow records, not provenance evidence.

No dataset or ground-truth labels are present in the inspected workspace. There is no training/evaluation pipeline, estimator artifact, split manifest, calibration code, or model card. Consequently, held-out-author/project/system evaluation and false-positive/false-negative rates cannot be computed. No classifier accuracy or calibration claim is made in this report.

The inference gateway is fail-closed: every analysis reports the model as unavailable, the authorship assessment as inconclusive, and probability as null. Keep this behavior until the data and validation requirements below are met.

## Implemented Methods

| Component | Current behavior | Validation status |
|---|---|---|
| Language handling | Python, Java, C, C++, JavaScript, TypeScript, and TSX have real parsers. Automatic detection accepts only a unique clean parser match; ambiguous snippets require manual selection. Detection is bounded to 128 KB; selected-language parsing uses the configured source size limit. | Analysis tests cover all parser IDs; uniqueness is not a calibrated confidence score. |
| Syntax | Python uses `ast.parse`; Java, C, C++, JavaScript, TypeScript, and TSX use Tree-sitter grammars. Source is never executed. | Exercised by valid/invalid parser tests; Tree-sitter does not validate types or compiler semantics. |
| Structure | Python AST/tokenize and Tree-sitter nodes provide lines/comments, functions/classes, loops/branches, imports/assignments/returns, nesting, approximate cyclomatic complexity, recursion where names are exposed, error handling, and coarse program style. | Descriptive parser metrics; recovered syntax may be partial and is not authorship evidence. |
| Authorship classifier | Fixed unavailable response; no estimator is loaded or invoked. | Disabled. No predictive inference is performed. |
| Code comparison | Public users can compare snippets against same-language original examples or compare two snippets; authenticated users can inspect accessible submissions side by side. | Parser leaf-token sequence matching, comments/whitespace excluded, identifiers/literals retained, `SequenceMatcher`, 3-gram Jaccard, and a normalized metric distance. Not AST equivalence or cross-language comparison. Similarity is not authorship evidence. |
| Provenance | Analysis returns a fixed “No verified provenance evidence available” summary. | No provenance record intake, verification, or chain-of-custody implementation found. |
| Human review | Professors can mark owned submissions reviewed and store reviewer notes. | Implemented workflow; notes are not independently verified provenance. |
| Evidence report | PDF reports include actual analysis status, limitations, human review status, and recorded notes. Similarity and Git history are explicitly reported as not performed. | Covered by report and workflow tests. |

## Dataset, Labels, and Provenance Audit

- The workspace root `ml/` directory contains no ML dataset or artifacts.
- `backend/app/ml/` contains only the inference gateway and package initializer.
- The public similarity service bundles original examples across parser-supported languages with unknown, unverified authoring process, no verified human/AI labels, and no collection date; they are not a model-training dataset.
- No labeled ML dataset, label schema, collection protocol, author/project identifiers, train/test manifest, model artifact, or model card were found in the workspace.
- `requirements.txt` lists NumPy, pandas, scikit-learn, and joblib, but the inspected application path does not use them to train or load a classifier.
- No ML preprocessing, deduplication, train/test split, calibration, or evaluation implementation was found. Similarity excludes comments/whitespace but retains identifiers and literals; this is not ML preprocessing.

These findings describe this workspace only; they do not make claims about data or experiments outside it.

## Leakage and Generalization

Leakage checks between authors, projects, assignments, repositories, and AI systems are **not applicable to the shipped application path** because no model dataset or split exists. There are no group identifiers or split assignments to inspect, and no held-out authors, projects, or AI systems were evaluated. Random row-level splitting must not be treated as adequate if a dataset is added later: exact/near-duplicate code and shared templates can cross splits and inflate results.

## False Positives, False Negatives, and Calibration

No labeled human/AI examples or classifier predictions exist, so false-positive rate, false-negative rate, precision, recall, ROC/PR curves, calibration error, confidence intervals, and operating thresholds are **not measured**. Existing tests verify that the shipped gateway returns unavailable/inconclusive/null probability and that the UI does not present a probability when no available model value exists. Those are guardrail tests, not detector-performance tests.

The public comparator produces a same-language token sequence similarity, 3-gram overlap, and parser-metric distance where available, plus matching line regions. It does not decide copying or shared authorship. Similarity must remain separately labeled as code resemblance and must never be mapped to AI-authorship probability.

## Measured Results

- Backend suite after parser-backed language support: **60 passed** (12 parser subtests). This covers application behavior, access controls, public input/rate/privacy contracts, structural analysis statuses, references, and reports; it is not a model benchmark.
- Frontend service/helper suite at audit: **10 passed**. It includes a guard that does not show a prediction when the model is unavailable or probability is null; it is not a model benchmark.
- Public API acceptance suite: **10 passed**. It covers unauthenticated access, non-persistence, rate/size limits, ambiguity, short inputs, all parser/reference languages, and similarity/authorship separation. These are functional checks, not reference-dataset performance results.
- TypeScript check and production frontend build completed successfully during the audit.
- Browser workflow: public route opened with empty session storage; the public analysis request carried no Authorization header; Python metrics and reference results rendered; short/unsupported behavior remained inconclusive with no estimate; network failure displayed an error and retry; report copying succeeded; viewport widths 320, 390, 768, and 1440 had no horizontal page overflow.
- Two manually compared Python snippets returned 100% token similarity and 100% structural-metric similarity. This is a deterministic feature smoke check, not a performance or authorship validation result.
- The demo/reference set contains locally authored examples for Python, Java, C, C++, JavaScript, TypeScript, and TSX. Their authoring process and authorship labels remain unknown and unverified; the set is not a benchmark.
- Classifier performance results: **none**. No training or evaluation was performed because there is no dataset or classifier to evaluate.
- Similarity evaluation beyond deterministic endpoint examples: **none**. The bundled examples are not a benchmark set.
- Held-out author/project/AI-system results: **none**. No such test was run.

The test counts refer to the repository test suites, not independent validation of educational deployment safety.

## Limitations and Deployment Decision

Do not use CodeProof to label a student’s work AI-generated or human-generated. Current output supports syntax/structure inspection only; it provides no authorship prediction. A lack of verified provenance is not evidence that AI was or was not used. Human review notes are not proof of provenance.

Structural analysis can vary with language version, formatting, assignment templates, libraries, and code length. These metrics describe source characteristics and do not establish who wrote code or how it was produced. Side-by-side source inspection likewise does not establish copying or authorship.

## Work Required Before Any Classifier Is Considered

1. Define the intended claim and label taxonomy (human-only, AI-assisted, AI-generated, mixed/unknown), label provenance, annotation protocol, inter-rater agreement, and permitted use. Preserve an explicit unknown/abstain class.
2. Build a rights-cleared, documented dataset with author, project, assignment, language/version, time, tool/model family and version, prompt/process metadata where available, and collection source. Keep personally identifying information access-controlled.
3. Deduplicate exact and near-duplicate files before splitting. Group all files from the same author and project/repository into one partition; prevent assignment templates and derivative variants from leaking across partitions.
4. Freeze train, calibration, and final test manifests. Evaluate on held-out authors and projects, and separately on held-out AI systems, model versions, prompts, and time periods. Do not tune on the final test set.
5. Compare against strong non-ML baselines and report per-class confusion matrices, false-positive/false-negative rates, precision/recall, ROC/PR metrics, confidence intervals, subgroup and language results, and performance by code length and task type.
6. Calibrate probabilities only on held-out calibration data; report calibration curves and proper scoring rules. Set any operating threshold from an explicit educational-risk analysis, with human review and an abstention path. Revalidate after dataset, model, or workflow changes.
7. Run prospective evaluation in a non-punitive setting before any educational deployment. Publish a model card, known failure modes, monitoring and appeal procedures, data-retention policy, and a prohibition on using a score alone for disciplinary action.

Until these gates are independently met and documented, keep the classifier unavailable and continue to present structural analysis, side-by-side source inspection, and human review as distinct, limited evidence sources.

## Code References

- [Inference gateway](../backend/app/ml/inference.py)
- [Python structural analyzer](../backend/app/analyzers/python_analyzer.py)
- [Analysis service and fixed provenance summary](../backend/app/services/analysis_service.py)
- [Analysis API](../backend/app/api/v1/analysis.py)
- [Side-by-side source inspection](../frontend/src/pages/Compare.tsx)
- [Probability display guard](../frontend/src/utils/format.ts)
- [Analysis guardrail tests](../backend/tests/test_analysis.py)
- [Evidence report tests](../backend/tests/test_report.py)