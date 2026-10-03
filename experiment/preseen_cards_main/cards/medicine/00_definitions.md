# Definitions used in the profile notes

Each profile note describes one person named in an option, from the OpenAlex 2026-01 snapshot (works, citations,
book citations), PatentsView 2025-12-31 (US patents) and Reliance on Science (patent-to-paper citations). The window
is works published, and patents granted, up to 2021.

- **Research works**: articles, reviews and letters.
- **Impact percentile**: a work's 5-year citation count compared with all OpenAlex works of the same publication year
  and field: 0 = lowest, 0.5 = typical, 1 = highest. "Top 10 %" / "top 1 %" = percentile at least 0.90 / 0.99.
- **Disruption percentile**: the 5-year disruption index (CD) of a work, as a percentile of the same cohort: high
  when the works citing it do not also cite its references. Works without references have no value.
- **Foundation share**: the share of the works citing a work within 5 years that build on the work itself rather
  than on its references.
- **Citing inventions**: distinct inventions (US patents and pre-grant publications) whose front-page or in-text
  references cite the person's works; **own patents**: US utility patents with the person as an inventor.
- **Textbook reach**: citations from books, book chapters and reference entries; "citing books" counts distinct books.
- **Nobel laureate co-authors**: co-authors (works with at most 50 authors) who are Nobel laureates in physics,
  chemistry or physiology or medicine; **people on both sides**: people who are both a co-author and a co-inventor.
- **Reference lines** compare a person's value with the Physiology or Medicine laureates of 2000-2025 measured at the time of
  their prize: only their works published before the prize year, and only patent and book citations dated before
  it (undated works and citations left out). The person's own values cover the whole record up to 2021.

These are descriptive bibliometric measures, not forecasts.
