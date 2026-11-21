# Focused Literature Review and Novelty Assessment

> **Superseded (2026-11-21).** This document was written under the withdrawn "cross-script EEG identity recognition during reading" framing. The task may have been overt speech, identity is confounded with a single recording session, and script is confounded with time. See the status notice in `README.md`.

Checked 2026-11-13. This is a focused comparison for the current cross-script EEG biometric project, not a systematic review.

## Closest studies

| Study | Dataset / condition | Method and reported result | Relation and limitation for comparison |
|---|---|---|---|
| Sah, Ahirwal, and Tomar, “Deep Learning and EEG Signal Based Biometric System: An Application of Brain Computer Interface,” IEEE SCEECS 2025, DOI 10.1109/SCEECS64059.2025.10940880 | EEG biometrics with native-language songs, non-native-language songs, and neutral music; auditory stimulation | 1-D CNN; IEEE Xplore abstract reports mean sensitivity 0.9666, specificity 0.9982, and EER 0.0318. A publicly available author copy describes comparisons across language and auditory delivery conditions. | **Directly weakens any claim that language-conditioned EEG biometrics have not been studied.** It is auditory/music and does not answer Arabic/Devanagari visual script reading or native/foreign reading transfer. Different cohort, preprocessing, split and metric protocol mean raw accuracy is not comparable. |
| Mota et al., “A deep descriptor for cross-tasking EEG-based recognition,” PeerJ Computer Science, 2021, DOI 10.7717/peerj-cs.549 | PhysioNet EEG Motor Movement/Imagery; 109 participants, 64 channels, motor/imagery tasks | CNN with squeeze-and-excitation descriptors; reports cross-task verification EER around 0.1% under its specified protocol. | Established cross-task EEG biometrics before this project. It is the closest conceptual comparator for task transfer, but not a language/script manipulation and uses a much larger, different acquisition. |
| Del Pozo-Baños et al., “Evidence of a task-independent neural signature in the spectral shape of the electroencephalogram,” International Journal of Neural Systems, 2018, DOI 10.1142/S0129065717500356 | EEG spectral shape across task/condition | Evidence for person-specific spectral-shape information across conditions. | Precludes presenting task-independent EEG identity as a new general idea. The present study needs to motivate the specific visual language/script transfer condition. |
| Aldhaheri et al., “Investigation of brain response to acquisition and learning the second languages based on EEG signals and machine learning techniques,” Cogent Arts & Humanities 11(1), 2416759, 2024, DOI 10.1080/23311983.2024.2416759 | Early Arabic/Hindi L2 dataset analysis; 8 participants in the published paper | Language-related EEG classification; reported accuracy range about 64–75% across classifiers. | Same research line and language pair, but it asks about language-related classification, not person identification transferred across script blocks. Do not treat it as a distinct independent dataset without reconciling release versions. |
| Aldhaheri et al., “Utilizing machine and deep learning algorithms to identify learning-related features in electroencephalography data during second language acquisition,” Cogent Arts & Humanities 12(1), 2025, DOI 10.1080/23311983.2025.2485696 | Arabic/Hindi L2 task; 10 participants in the article | RF, XGBoost, CatBoost, CNN and other classifiers for language/learning-related labels; abstract reports XGBoost 94.95%, CatBoost 94.69%, RF 93.90%. | Same language-acquisition line, different target from biometric identity. Its high within-task classification values are not directly comparable to cross-block identity accuracy. |
| Aldhaheri et al., “Optimizing machine learning models with multi feature selection for EEG analysis in second language acquisition research,” Discover Artificial Intelligence 6, 99 (2026), DOI 10.1007/s44163-025-00801-z | Arabic/Hindi data; 20 participants; paper describes 1,979 data points and 80/20 stratified train/test split | Multiple feature-selection methods plus conventional classifiers; abstract reports up to 97.15% classification accuracy. | Same 20-person language dataset line, but language-related classification rather than subject identification. Report the differing target and split protocol; do not use 97.15% as a directly comparable biometric baseline. |

## Novelty that survives comparison

The defensible contribution is an **exploratory within-session transfer evaluation from one visual script-reading block to the other, on Arabic/Hindi data, with spectral and connectivity representations and participant-level reliability analysis**. This is narrower than “first language-invariant EEG biometric” and should be written that way. The direct auditory-language biometric study makes the broader claim untenable.

The analysis does not establish a neural language-invariant identity mechanism. In the local data, language block and time/order are coupled, both blocks are from one session, and the existing main result originally used ICA fitted on both blocks. The corrected experiment now fits ICA on the enrollment block only, but the order and session limitations remain.

## Implications for the manuscript

- Replace “none, to our knowledge, has asked whether the signature survives a change in language” with a qualified statement that language-conditioned EEG biometrics exist, while cross-script visual reading transfer is a narrower condition not tested by the closest auditory study.
- State that the dataset is reused for a different prediction target; it is not a novel dataset contribution.
- Compare by cohort, modality (auditory vs visual), condition definition, enrollment/test split, and metric. Do not rank the reported accuracies across studies.
- Treat all three Arabic/Hindi acquisition papers as same-data-line comparisons until archive/version history is authoritatively resolved.

## Sources verified

- IEEE Xplore record for Sah et al.: https://ieeexplore.ieee.org/document/10940880/ (DOI 10.1109/SCEECS64059.2025.10940880).
- Mota et al. open full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8157223/.
- Del Pozo-Baños et al. bibliographic record: https://pubmed.ncbi.nlm.nih.gov/28269291/.
- 2024 paper DOI: https://doi.org/10.1080/23311983.2024.2416759.
- 2025 paper DOI: https://doi.org/10.1080/23311983.2025.2485696.
- 2026 paper DOI: https://doi.org/10.1007/s44163-025-00801-z.
- Dataset landing page: https://data.mendeley.com/datasets/7cdyp2r5cz/1.

## IEEE conference targets checked

| Conference | Fit | Verified 2027 requirements/deadline | Recommendation |
|---|---|---|---|
| IEEE EMBS Neural Engineering Conference (NER 2027) | Strongest topic match for neural signals and neural-engineering methods; the work must be framed as a cautious experimental transfer study, not a deployable biometric. | Official site lists a 6-page initial paper deadline of **15 March 2027**, acceptance notification **15 May 2027**, final 6-page submission **2 June 2027**; the submission page states full papers can be 4–7 pages maximum including references and overlength fees apply after page 4. Accepted papers that complete requirements and are presented are eligible for IEEE Xplore/PubMed, not guaranteed. | **Preferred target** if corrected results are stable and the manuscript fits six pages (seven maximum). |
| IEEE EMBS Annual International Conference (EMBC 2027) | Good biomedical signal processing / neural engineering scope. | Official CFP lists full-paper deadline **24 January 2027**, notification **16 April**, final due **30 April**; strict 4 technical pages + reference-only page, maximum 20 references. | Reasonable alternate, but very tight page budget and a shorter timeline. |

Sources: NER official site https://neuro.embs.org/2027/papers/ and https://neuro.embs.org/2027/; EMBC official CFP https://embc.embs.org/2027/papers/ and author guidelines https://embc.embs.org/2027/author-guidelines/. Venue requirements can change; recheck before submission.
