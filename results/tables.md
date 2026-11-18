## Quality (median per pipeline)

| pipeline   |   ptp_uv |   line_ratio |
|:-----------|---------:|-------------:|
| filtered   |   2.5085 |       0.0041 |
| ica        |   2.2121 |       0.0046 |
| raw        |  16.1746 |     139.265  |

## Identity decoding

| pipeline   | model   | test                       | scheme         |   bal_acc |   chance |
|:-----------|:--------|:---------------------------|:---------------|----------:|---------:|
| raw        | logreg  | pooled                     | window         |     0.975 |     0.05 |
| raw        | logreg  | pooled                     | file           |     0.974 |     0.05 |
| raw        | logreg  | train Arabic -> test Hindi | cross-language |     0.823 |     0.05 |
| raw        | logreg  | train Hindi -> test Arabic | cross-language |     0.906 |     0.05 |
| raw        | rf      | pooled                     | window         |     0.972 |     0.05 |
| raw        | rf      | pooled                     | file           |     0.967 |     0.05 |
| raw        | rf      | train Arabic -> test Hindi | cross-language |     0.813 |     0.05 |
| raw        | rf      | train Hindi -> test Arabic | cross-language |     0.897 |     0.05 |
| filtered   | logreg  | pooled                     | window         |     0.986 |     0.05 |
| filtered   | logreg  | pooled                     | file           |     0.983 |     0.05 |
| filtered   | logreg  | train Arabic -> test Hindi | cross-language |     0.912 |     0.05 |
| filtered   | logreg  | train Hindi -> test Arabic | cross-language |     0.928 |     0.05 |
| filtered   | rf      | pooled                     | window         |     0.983 |     0.05 |
| filtered   | rf      | pooled                     | file           |     0.977 |     0.05 |
| filtered   | rf      | train Arabic -> test Hindi | cross-language |     0.891 |     0.05 |
| filtered   | rf      | train Hindi -> test Arabic | cross-language |     0.925 |     0.05 |
| ica        | logreg  | pooled                     | window         |     0.986 |     0.05 |
| ica        | logreg  | pooled                     | file           |     0.983 |     0.05 |
| ica        | logreg  | train Arabic -> test Hindi | cross-language |     0.913 |     0.05 |
| ica        | logreg  | train Hindi -> test Arabic | cross-language |     0.94  |     0.05 |
| ica        | rf      | pooled                     | window         |     0.982 |     0.05 |
| ica        | rf      | pooled                     | file           |     0.977 |     0.05 |
| ica        | rf      | train Arabic -> test Hindi | cross-language |     0.892 |     0.05 |
| ica        | rf      | train Hindi -> test Arabic | cross-language |     0.929 |     0.05 |

## Language decoding

| pipeline   | task        | model   | scheme   |   bal_acc |   perm_p |
|:-----------|:------------|:--------|:---------|----------:|---------:|
| filtered   | stimulus    | logreg  | window   |     0.682 |  nan     |
| filtered   | stimulus    | logreg  | file     |     0.647 |  nan     |
| filtered   | stimulus    | logreg  | subject  |     0.553 |    0.01  |
| filtered   | stimulus    | rf      | window   |     0.826 |  nan     |
| filtered   | stimulus    | rf      | file     |     0.782 |  nan     |
| filtered   | stimulus    | rf      | subject  |     0.519 |  nan     |
| filtered   | time_ctrl   | logreg  | window   |     0.612 |  nan     |
| filtered   | time_ctrl   | logreg  | file     |     0.521 |  nan     |
| filtered   | time_ctrl   | logreg  | subject  |     0.55  |    0.02  |
| filtered   | time_ctrl   | rf      | window   |     0.675 |  nan     |
| filtered   | time_ctrl   | rf      | file     |     0.536 |  nan     |
| filtered   | time_ctrl   | rf      | subject  |     0.567 |  nan     |
| filtered   | familiarity | logreg  | window   |     0.706 |  nan     |
| filtered   | familiarity | logreg  | file     |     0.674 |  nan     |
| filtered   | familiarity | logreg  | subject  |     0.58  |    0.01  |
| filtered   | familiarity | rf      | window   |     0.844 |  nan     |
| filtered   | familiarity | rf      | file     |     0.795 |  nan     |
| filtered   | familiarity | rf      | subject  |     0.541 |  nan     |
| ica        | stimulus    | logreg  | window   |     0.678 |  nan     |
| ica        | stimulus    | logreg  | file     |     0.65  |  nan     |
| ica        | stimulus    | logreg  | subject  |     0.555 |    0.02  |
| ica        | stimulus    | rf      | window   |     0.837 |  nan     |
| ica        | stimulus    | rf      | file     |     0.784 |  nan     |
| ica        | stimulus    | rf      | subject  |     0.535 |  nan     |
| ica        | time_ctrl   | logreg  | window   |     0.607 |  nan     |
| ica        | time_ctrl   | logreg  | file     |     0.52  |  nan     |
| ica        | time_ctrl   | logreg  | subject  |     0.551 |    0.04  |
| ica        | time_ctrl   | rf      | window   |     0.679 |  nan     |
| ica        | time_ctrl   | rf      | file     |     0.544 |  nan     |
| ica        | time_ctrl   | rf      | subject  |     0.574 |  nan     |
| ica        | familiarity | logreg  | window   |     0.714 |  nan     |
| ica        | familiarity | logreg  | file     |     0.679 |  nan     |
| ica        | familiarity | logreg  | subject  |     0.584 |    0.01  |
| ica        | familiarity | rf      | window   |     0.848 |  nan     |
| ica        | familiarity | rf      | file     |     0.796 |  nan     |
| ica        | familiarity | rf      | subject  |     0.547 |  nan     |
| raw        | stimulus    | logreg  | window   |     0.649 |  nan     |
| raw        | stimulus    | logreg  | file     |     0.613 |  nan     |
| raw        | stimulus    | logreg  | subject  |     0.489 |    0.594 |
| raw        | stimulus    | rf      | window   |     0.8   |  nan     |
| raw        | stimulus    | rf      | file     |     0.753 |  nan     |
| raw        | stimulus    | rf      | subject  |     0.505 |  nan     |
| raw        | time_ctrl   | logreg  | window   |     0.6   |  nan     |
| raw        | time_ctrl   | logreg  | file     |     0.507 |  nan     |
| raw        | time_ctrl   | logreg  | subject  |     0.553 |    0.01  |
| raw        | time_ctrl   | rf      | window   |     0.665 |  nan     |
| raw        | time_ctrl   | rf      | file     |     0.535 |  nan     |
| raw        | time_ctrl   | rf      | subject  |     0.568 |  nan     |
| raw        | familiarity | logreg  | window   |     0.682 |  nan     |
| raw        | familiarity | logreg  | file     |     0.649 |  nan     |
| raw        | familiarity | logreg  | subject  |     0.537 |    0.02  |
| raw        | familiarity | rf      | window   |     0.813 |  nan     |
| raw        | familiarity | rf      | file     |     0.769 |  nan     |
| raw        | familiarity | rf      | subject  |     0.503 |  nan     |

## DiD: features with q<0.05 (count)

| pipeline   |   q_time |   q_familiarity |   q_parallel_trend |
|:-----------|---------:|----------------:|-------------------:|
| filtered   |        0 |               0 |                  0 |
| ica        |        0 |               0 |                  0 |
| raw        |        0 |               0 |                  0 |

## DiD: 10 smallest familiarity p-values (ICA)

| feature      |   familiarity_L2_minus_L1 |   p_familiarity |   q_familiarity |   p_parallel_trend |
|:-------------|--------------------------:|----------------:|----------------:|-------------------:|
| T4_beta_rel  |                    0.0317 |          0.0036 |           0.257 |             0.0376 |
| T4_beta_log  |                    0.1432 |          0.0058 |           0.257 |             0.0376 |
| T5_beta_log  |                    0.0983 |          0.0091 |           0.257 |             0.1041 |
| P3_theta_rel |                   -0.0098 |          0.0113 |           0.257 |             0.4274 |
| T6_beta_log  |                    0.1026 |          0.014  |           0.257 |             0.1212 |
| T4_gamma_log |                    0.144  |          0.014  |           0.257 |             0.089  |
| T4_delta_rel |                   -0.0533 |          0.0173 |           0.257 |             0.3847 |
| O2_beta_log  |                    0.0711 |          0.0173 |           0.257 |             0.0073 |
| T4_theta_rel |                   -0.0091 |          0.0257 |           0.257 |             1      |
| F8_alpha_log |                    0.0719 |          0.0257 |           0.257 |             0.0058 |
