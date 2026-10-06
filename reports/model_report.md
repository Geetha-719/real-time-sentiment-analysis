# Model Evaluation Report

- Dataset size: **69,971** samples
- Train / Test: **55,976** / **13,995**
- Classes: Negative, Neutral, Positive, Irrelevant
- Chosen configuration: `Logistic Regression | unigram+bigram+nostem`

## Model comparison

| Model | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | F1 (weighted) | ROC-AUC |
|---|---|---|---|---|---|---|
| Naive Bayes | 92.26% | 93.13% | 91.56% | 92.19% | 92.26% | 99.15% |
| Logistic Regression | 93.11% | 93.44% | 92.73% | 93.05% | 93.11% | 98.80% |
| LSTM | 70.52% | 71.27% | 68.11% | 68.63% | 69.96% | — |

## Cross-validation (f1_macro, 3-fold)

| Configuration | Mean F1 | Std |
|---|---|---|
| Naive Bayes | unigram+stem | 0.7141 | 0.0040 |
| Logistic Regression | unigram+stem | 0.7794 | 0.0007 |
| Naive Bayes | unigram+bigram+stem | 0.8510 | 0.0034 |
| Logistic Regression | unigram+bigram+stem | 0.8805 | 0.0012 |
| Naive Bayes | unigram+bigram+nostem | 0.8542 | 0.0025 |
| Logistic Regression | unigram+bigram+nostem | 0.8837 | 0.0006 |

## Naive Bayes — confusion matrix

| actual \ predicted | Negative | Neutral | Positive | Irrelevant |
|---|---|---|---|---|
| **Negative** | 4080 | 56 | 99 | 17 |
| **Neutral** | 166 | 3116 | 143 | 18 |
| **Positive** | 170 | 50 | 3600 | 20 |
| **Irrelevant** | 154 | 30 | 160 | 2116 |

## Logistic Regression — confusion matrix

| actual \ predicted | Negative | Neutral | Positive | Irrelevant |
|---|---|---|---|---|
| **Negative** | 4068 | 56 | 103 | 25 |
| **Neutral** | 129 | 3179 | 96 | 39 |
| **Positive** | 153 | 60 | 3574 | 53 |
| **Irrelevant** | 104 | 43 | 103 | 2210 |

## LSTM — confusion matrix

| actual \ predicted | Negative | Neutral | Positive | Irrelevant |
|---|---|---|---|---|
| **Negative** | 3566 | 91 | 416 | 179 |
| **Neutral** | 575 | 1992 | 602 | 274 |
| **Positive** | 425 | 181 | 3047 | 187 |
| **Irrelevant** | 433 | 165 | 598 | 1264 |
