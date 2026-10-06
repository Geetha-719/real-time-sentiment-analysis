"""Optional LSTM baseline.

Only used when PyTorch is installed. The dataset (70k+ samples, 4 classes)
justifies a small deep-learning comparison. It is intentionally lightweight
(embedding -> LSTM -> linear) and fully reproducible via a fixed seed.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from ml.config import RANDOM_SEED
from ml.preprocessing import tokenize

try:  # pragma: no cover - environment dependent
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    TORCH_AVAILABLE = False

MAX_LEN = 40
VOCAB_MIN_COUNT = 2
EMBED_DIM = 64
HIDDEN_DIM = 64
BATCH_SIZE = 128
EPOCHS = 3


if TORCH_AVAILABLE:

    class _TextDataset(Dataset):
        def __init__(self, sequences, labels):
            self.x = torch.tensor(sequences, dtype=torch.long)
            self.y = torch.tensor(labels, dtype=torch.long)

        def __len__(self):
            return len(self.y)

        def __getitem__(self, idx):
            return self.x[idx], self.y[idx]

    class _LSTM(nn.Module):
        def __init__(self, vocab_size, n_classes):
            super().__init__()
            self.embed = nn.Embedding(vocab_size, EMBED_DIM, padding_idx=0)
            self.lstm = nn.LSTM(EMBED_DIM, HIDDEN_DIM, batch_first=True, bidirectional=True)
            self.dropout = nn.Dropout(0.3)
            self.fc = nn.Linear(HIDDEN_DIM * 2, n_classes)

        def forward(self, x):
            emb = self.embed(x)
            out, _ = self.lstm(emb)
            pooled = out.max(dim=1).values
            return self.fc(self.dropout(pooled))


def _build_vocab(texts):
    from collections import Counter

    counter: Counter[str] = Counter()
    for t in texts:
        counter.update(tokenize(t, stem=True))
    vocab = {"<pad>": 0, "<unk>": 1}
    for word, cnt in counter.items():
        if cnt >= VOCAB_MIN_COUNT:
            vocab[word] = len(vocab)
    return vocab


def _encode(texts, vocab):
    seqs = np.zeros((len(texts), MAX_LEN), dtype=np.int64)
    for i, t in enumerate(texts):
        ids = [vocab.get(w, 1) for w in tokenize(t, stem=True)][:MAX_LEN]
        seqs[i, : len(ids)] = ids
    return seqs


def train_lstm(X_train, y_train, X_test, y_test, classes):  # pragma: no cover
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch not installed")

    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    vocab = _build_vocab(X_train)
    Xtr = _encode(X_train, vocab)
    Xte = _encode(X_test, vocab)

    model = _LSTM(len(vocab), len(classes))
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    train_loader = DataLoader(_TextDataset(Xtr, y_train), batch_size=BATCH_SIZE, shuffle=True)
    model.train()
    for epoch in range(EPOCHS):
        total = 0.0
        for xb, yb in train_loader:
            opt.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            opt.step()
            total += loss.item() * len(yb)
        print(f"  [lstm] epoch {epoch+1}/{EPOCHS} loss={total/len(Xtr):.4f}")

    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(Xte, dtype=torch.long))
        proba = torch.softmax(logits, dim=1).numpy()
    pred = proba.argmax(axis=1)

    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision_macro": float(precision_score(y_test, pred, average="macro", zero_division=0)),
        "precision_weighted": float(precision_score(y_test, pred, average="weighted", zero_division=0)),
        "recall_macro": float(recall_score(y_test, pred, average="macro", zero_division=0)),
        "recall_weighted": float(recall_score(y_test, pred, average="weighted", zero_division=0)),
        "f1_macro": float(f1_score(y_test, pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_test, pred, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(
            y_test, pred, labels=list(range(len(classes)))
        ).tolist(),
        "classification_report": classification_report(
            y_test, pred, labels=list(range(len(classes))), target_names=classes,
            zero_division=0, output_dict=True,
        ),
        "classes": classes,
        "n_features": len(vocab),
        "roc_auc_ovr_macro": None,
    }
    return metrics, vocab
