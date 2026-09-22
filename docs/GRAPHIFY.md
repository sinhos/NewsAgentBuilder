# Would Graphify improve the newsletter?

Researched 22 September 2026. “Graphiphy” appears to mean [Graphify by Graphify-Labs](https://github.com/Graphify-Labs/graphify). This assessment assumes that is the intended tool. No package, skill or graph was installed.

**Recommendation: keep it optional and evaluate it later for archive retrieval. Improve source discovery first.** A graph cannot recover a story the collector never obtained. It would not by itself fix the missed Jev announcement.

## What it adds

Graphify turns code and documents into a graph of entities and relationships that an assistant can query. For a newsletter archive, a possible use is connecting a product's launch, subsequent evaluations and later corrections, then retrieving only the relevant history for a new edition. This is a proposed application, not a feature already integrated or measured here. The project documents graph queries, incremental updates and Markdown support. [Primary README](https://github.com/Graphify-Labs/graphify/blob/20a20d30d8e7eef77675651f0199d87f913bd3e7/README.md)

Its deterministic code parsing needs no model calls. Semantic extraction from articles and documents uses a model; graph construction being described as free does not make the entire news workflow free. It also adds NetworkX, NumPy and many parser dependencies to our currently standard-library-only backend. The inspected package is `graphifyy` version 0.9.65; the repository declares Apache-2.0 and includes additional license/notice files. [Package metadata](https://github.com/Graphify-Labs/graphify/blob/20a20d30d8e7eef77675651f0199d87f913bd3e7/pyproject.toml)

## Does it actually save tokens or improve accuracy?

Its maintainers publish comparisons on conversational memory and code understanding. Results vary: their table shows higher retrieval recall but lower answer accuracy than one competing system on LOCOMO, and a tie with dense retrieval on LongMemEval-S. These are their own experiments, not an independent newsletter benchmark. They do not establish a particular token reduction or accuracy improvement for this project. [Benchmark methods and results](https://github.com/Graphify-Labs/graphify/blob/20a20d30d8e7eef77675651f0199d87f913bd3e7/BENCHMARKS.md)

Our current history already uses SQLite and supplies summaries of seven recent editions. The simpler next improvement is searching that archive for relevant older stories. Graphify becomes more interesting when questions require relationships across many editions, rather than finding one previous mention.

## A useful pilot

1. Keep saved JSON editions and their evidence as the source of truth. Use the new Markdown exports as an optional input corpus in a separate private folder.
2. Compare current recent-history summaries, archive text search and graph retrieval on 20–30 representative questions. Hold the writing model and evidence budget constant.
3. Measure useful-history recall, unsupported claims, duplicate stories, total input/output tokens, extraction cost and elapsed time. Include graph build and update work in the totals.
4. Add an opt-in adapter only if it improves those results. Missing or stale graphs must fall back to normal retrieval. Graph relationships must link back to dated original evidence; an inferred connection is not proof.

Do not index the whole private data directory or commit generated personal graphs. Graphify's code-team documentation encourages sharing graph artifacts, but a personal newsletter corpus needs different handling. Exported briefings contain personalized text and links; sending them to a remote extraction model shares that content with its provider.

The Markdown export is implemented. Archive search and Graphify integration remain proposed work.
