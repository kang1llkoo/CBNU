# evaluation.py

import numpy as np

from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score
)


def evaluate_model(
        model,
        X_test,
        y_test
):

    pred = model.predict(
        X_test.values
    ).flatten()

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            pred
        )
    )

    mae = mean_absolute_error(
        y_test,
        pred
    )

    r2 = r2_score(
        y_test,
        pred
    )

    return rmse, mae, r2, pred


def print_metrics(
        title,
        rmse,
        mae,
        r2
):

    print()

    print(title)

    print(
        f"RMSE : {rmse:.4f}"
    )

    print(
        f"MAE  : {mae:.4f}"
    )

    print(
        f"R2   : {r2:.4f}"
    )


def analyze_error_distribution(
        y_true,
        y_pred
):

    error = np.abs(
        y_true - y_pred
    )

    print()

    print(
        error.describe()
    )

    return error