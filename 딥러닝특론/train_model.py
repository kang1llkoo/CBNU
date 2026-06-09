import torch

from pytorch_tabnet.tab_model import TabNetRegressor


def train_tabnet_model(
        X_train,
        y_train,
        cat_idxs,
        cat_dims
):

    device_opt = (
        'cuda'
        if torch.cuda.is_available()
        else 'auto'
    )

    model = TabNetRegressor(
        cat_idxs=cat_idxs,
        cat_dims=cat_dims,
        cat_emb_dim=2,
        optimizer_fn=torch.optim.Adam,
        optimizer_params=dict(
            lr=1e-2
        ),
        device_name=device_opt
    )

    model.fit(
        X_train.values,
        y_train.values.reshape(-1, 1),
        max_epochs=20,
        patience=5,
        batch_size=256,
        virtual_batch_size=64
    )

    return model