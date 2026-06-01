import pandas as pd

from backend.prediction.models.base import BaseModel

SEQ_LEN = 60


class LSTMModel(BaseModel):
    def __init__(self):
        self._net = None
        self._device = None

    def _get_device(self):
        import torch
        if self._device is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return self._device

    def train(self, df: pd.DataFrame) -> None:
        import numpy as np
        import torch
        import torch.nn as nn

        class _LSTMNet(nn.Module):
            def __init__(self, input_size, hidden=128, layers=2):
                super().__init__()
                self.lstm = nn.LSTM(input_size, hidden, layers, batch_first=True, dropout=0.2)
                self.fc = nn.Linear(hidden, 1)
                self.sigmoid = nn.Sigmoid()

            def forward(self, x):
                out, _ = self.lstm(x)
                return self.sigmoid(self.fc(out[:, -1, :]))

        device = self._get_device()
        X = self._feature_matrix(df).values.astype(np.float32)
        y = (df["Close"].shift(-1) > df["Close"]).astype(float).values

        sequences, labels = [], []
        for i in range(SEQ_LEN, len(X) - 1):
            sequences.append(X[i - SEQ_LEN:i])
            labels.append(y[i])

        X_t = torch.tensor(np.array(sequences), device=device)
        y_t = torch.tensor(np.array(labels), dtype=torch.float32, device=device).unsqueeze(1)

        self._net = _LSTMNet(X_t.shape[2]).to(device)
        optimizer = torch.optim.Adam(self._net.parameters(), lr=1e-3)
        criterion = nn.BCELoss()

        self._net.train()
        for _ in range(20):
            optimizer.zero_grad()
            loss = criterion(self._net(X_t), y_t)
            loss.backward()
            optimizer.step()

    def predict(self, df: pd.DataFrame) -> dict:
        if self._net is None:
            return {"probability": 0.5}
        import numpy as np
        import torch
        device = self._get_device()
        X = self._feature_matrix(df).values.astype(np.float32)
        if len(X) < SEQ_LEN:
            return {"probability": 0.5}
        seq = torch.tensor(X[-SEQ_LEN:].reshape(1, SEQ_LEN, -1), device=device)
        self._net.eval()
        with torch.no_grad():
            prob = float(self._net(seq).item())
        return {"probability": prob}
