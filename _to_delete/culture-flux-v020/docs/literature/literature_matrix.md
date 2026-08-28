# Literature Matrix

**Status: bibliographic metadata verified; substantive content NOT YET EXTRACTED.**

None of the six core papers is present in this repository. Verifying a citation
is not reading a paper, so every column below that describes what a paper *did*
or *found* reads `NOT YET EXTRACTED`. Nothing in this file was inferred from an
abstract, a secondary source, or prior knowledge, and no number appearing
anywhere in this codebase was taken from any of these papers.

Extraction procedure: [extraction_protocol.md](extraction_protocol.md).

---

## Core corpus — verified bibliographic details

| # | Citation | Verified against | DOI |
|---|---|---|---|
| P1 | Mesoudi, A. (2018). Migration, acculturation, and the maintenance of between-group cultural variation. *PLOS ONE*, 13(10), e0205573. | PLOS ONE article page | [10.1371/journal.pone.0205573](https://doi.org/10.1371/journal.pone.0205573) |
| P2 | Paolillo, R., & Jager, W. (2020). Simulating Acculturation Dynamics Between Migrants and Locals in Relation to Network Formation. *Social Science Computer Review*, 38(4), 365–386. | University of Groningen research portal | [10.1177/0894439318821678](https://doi.org/10.1177/0894439318821678) |
| P3 | Axelrod, R. (1997). The Dissemination of Culture: A Model with Local Convergence and Global Polarization. *Journal of Conflict Resolution*, 41(2), 203–226. | SAGE journal page | [10.1177/0022002797041002001](https://doi.org/10.1177/0022002797041002001) |
| P4 | Erten, E. Y., van den Berg, P., & Weissing, F. J. (2018). Acculturation orientations affect the evolution of a multicultural society. *Nature Communications*, 9, 58. | Nature Communications article page | [10.1038/s41467-017-02513-0](https://doi.org/10.1038/s41467-017-02513-0) |
| P5 | Chuang, Y.-L., Chou, T., & D'Orsogna, M. R. (2019). A network model of immigration: Enclave formation vs. cultural integration. *Networks and Heterogeneous Media*. Volume, issue and pages NOT VERIFIED. | AIMS Sciences article page (title/DOI only) | [10.3934/nhm.2019004](https://doi.org/10.3934/nhm.2019004) |
| P6 | Kunst, J. R., & Mesoudi, A. (2025). Decoding the Dynamics of Cultural Change: A Cultural Evolution Approach to the Psychology of Acculturation. *Personality and Social Psychology Review*, 29(2). Pages NOT VERIFIED. First published online 26 July 2024. | SAGE journal page | [10.1177/10888683241258406](https://doi.org/10.1177/10888683241258406) |

Notes on partial verification:

- **P1** has a published correction (*PLOS ONE*, [10.1371/journal.pone.0216316](https://doi.org/10.1371/journal.pone.0216316)). Extraction must read the correction alongside the original and record what it changed.
- **P2** and **P5** have preprint versions on arXiv (1810.02650 and 1901.09396). Extract from the **published** version; note any differences if the preprint is used for access.
- **P6** carries a 2024 online-first date and a 2025 issue date. This matrix cites the issue year; use whichever the target venue requires and stay consistent.

---

## Extraction matrix

`NYE` = NOT YET EXTRACTED. A cell is filled only from the full text of the paper
named in its row.

| Column | P1 Mesoudi 2018 | P2 Paolillo & Jager 2020 | P3 Axelrod 1997 | P4 Erten et al. 2018 | P5 Chuang et al. 2019 | P6 Kunst & Mesoudi 2025 |
|---|---|---|---|---|---|---|
| Research question | NYE | NYE | NYE | NYE | NYE | NYE |
| Model type | NYE | NYE | NYE | NYE | NYE | NYE |
| Population structure | NYE | NYE | NYE | NYE | NYE | NYE |
| Agent definition | NYE | NYE | NYE | NYE | NYE | NYE |
| Culture representation | NYE | NYE | NYE | NYE | NYE | NYE |
| Migration mechanism | NYE | NYE | NYE | NYE | NYE | NYE |
| Interaction mechanism | NYE | NYE | NYE | NYE | NYE | NYE |
| Network structure | NYE | NYE | NYE | NYE | NYE | NYE |
| Cultural transmission mechanism | NYE | NYE | NYE | NYE | NYE | NYE |
| Independent variables | NYE | NYE | NYE | NYE | NYE | NYE |
| Dependent variables | NYE | NYE | NYE | NYE | NYE | NYE |
| Parameter ranges | NYE | NYE | NYE | NYE | NYE | NYE |
| Number of runs / replicates | NYE | NYE | NYE | NYE | NYE | NYE |
| Sensitivity analysis | NYE | NYE | NYE | NYE | NYE | NYE |
| Principal findings | NYE | NYE | NYE | NYE | NYE | NYE |
| Limitations stated by authors | NYE | NYE | NYE | NYE | NYE | NYE |
| Future research proposed | NYE | NYE | NYE | NYE | NYE | NYE |
| Source code availability | NYE | NYE | NYE | NYE | NYE | NYE |
| Data availability | NYE | NYE | NYE | NYE | NYE | NYE |
| Mechanisms potentially reusable here | NYE | NYE | NYE | NYE | NYE | NYE |
| Differences from our proposed model | NYE | NYE | NYE | NYE | NYE | NYE |

---

## Open questions for the corpus

These are the decisions currently blocked on reading. Each is registered as a
provisional assumption in
[../research/assumption_registry.md](../research/assumption_registry.md); the ID
in brackets is the assumption the answer would settle.

| ID | Question | Blocks | Likely source |
|---|---|---|---|
| L-Q1 | How is culture represented — categorical feature/trait vectors, continuous positions, orientation profiles — and on what grounds? | culture representation, A-001 | P3, P1, P4 |
| L-Q2 | What values of F (features) and Q (traits per feature) are used, and does the qualitative behaviour depend on them? | A-013 | P3, P1 |
| L-Q3 | Which transmission rule does each model use, and what is the stated justification? | the entire dynamics layer | P1, P2, P3, P4 |
| L-Q4 | How is cultural distance defined and measured? | A-003 | P1, P3, P4 |
| L-Q5 | How is migration operationalised — replacement, addition, flow rate, one-off pulse? | A-008 | P1, P2, P5 |
| L-Q6 | Do any of these models vary the NUMBER of source populations at fixed total migration? If none does, that gap is the paper's contribution and must be stated as such. | the whole research programme | all six |
| L-Q7 | How is within-group cultural variation initialised? | A-004 | P1, P4 |
| L-Q8 | What network structures are used, and how are ties formed and rewired? | the network layer | P2, P5 |
| L-Q9 | Are acculturation orientations (integration / assimilation / separation / marginalisation) modelled as agent strategies, and if so how do they evolve? | the agent model | P4, P6 |
| L-Q10 | What outcome measures are reported, and how are qualitative regimes (enclave, integration, polarisation) identified from them? | the metrics layer, RQ7 | P3, P5, P1 |
| L-Q11 | How many replicates per condition, and how is stochastic variation handled in the analysis? | the experimental design | all six |
| L-Q12 | Is majority-group (resident) cultural change modelled, or is acculturation treated as something only migrants do? | the influence layer | P6, P1 |

---

## Secondary corpus — not yet started

Named in the project brief, no entries created: homophily, phase transitions in
opinion and culture dynamics, minority cultural persistence, majority-group
acculturation, cultural drift, prestige bias, super-diversity.

Add a row here only once a specific work has been identified and its
bibliographic details verified.
