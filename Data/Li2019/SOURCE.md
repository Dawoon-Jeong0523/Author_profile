# Li, Yin, Fortunato & Wang (2019), "A dataset of publication records for Nobel laureates"

Scientific Data 6:33, https://doi.org/10.1038/s41597-019-0033-6
Harvard Dataverse, https://doi.org/10.7910/DVN/6NJ5RN (version 1, released 2018-12-05)

Downloaded 2026-09-30 through the Dataverse access API (`/api/access/datafile/<id>?format=original`):

| file | Dataverse file id |
|---|---|
| Chemistry publication record.tab | 3323577 |
| Medicine publication record.tab | 3323578 |
| Physics publication record.tab | 3323579 |
| Prize-winning paper record.tab | 3323580 |

Comma-separated despite the .tab suffix, CRLF line ends. The Physics and Medicine files contain a few
non-UTF-8 bytes in Journal / Title fields (read with `encoding_errors='replace'`).
Columns: Laureate ID, Laureate name, Prize year, Title, Pub year, Paper ID (MAG), DOI, Journal,
Affiliation, Is prize-winning paper. Laureate ID prefixes: 1xxxx Physics, 2xxxx Chemistry, 3xxxx Medicine.
One ID per prize: double laureates (Bardeen, Sanger) have two IDs.
`../SciSciNet_Link_NobelLaureates.tsv` (LaureateID, PaperID, Type) is the SciSciNet release of the same
links; Type 1 == "Is prize-winning paper" = YES on every shared row (checked 2026-09-30).
