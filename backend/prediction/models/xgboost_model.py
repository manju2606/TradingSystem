import pandas as pd

from backend.prediction.models.base import BaseModel


class XGBoostModel(BaseModel):
    def __init__(self):
        self._model = None

    def train(self, df: pd.DataFrame) -> None:
        import xgboost as xgb
        X = self._feature_matrix(df)
        y = (df["Close"].shift(-1) > df["Close"]).astype(int).loc[X.index]
        self._model = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05, use_label_encoder=False, eval_metric="logloss")
        self._model.fit(X[:-1], y[:-1])

    def predict(self, df: pd.DataFrame) -> dict:
        if self._model is None:
            # Return neutral until model is trained
            return {"probability": 0.5}
        X = self._feature_matrix(df)
        prob = float(self._model.predict_proba(X.iloc[[-1]])[0][1])
        return {"probability": prob}
