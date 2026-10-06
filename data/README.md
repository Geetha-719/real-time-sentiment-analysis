# Data Folder

## Where to place the dataset

Put your labeled sentiment dataset CSV in:

```
data/raw/
```

Currently the project uses:

```
data/raw/twitter_training.csv
```

## Expected columns

The CSV should contain (column names are case-insensitive):

| Column    | Description                                  |
|-----------|----------------------------------------------|
| ID        | Unique identifier                            |
| Entity    | Topic/brand the tweet is about               |
| Sentiment | Label: Positive/Negative/Neutral/Irrelevant  |
| Tweet     | The text to classify                         |

If your dataset uses different column names, adjust `load_dataset()` /
`remove_unnecessary_columns()` in `src/data_preprocessing.py`.

Do NOT commit a dataset that you do not have rights to redistribute.
