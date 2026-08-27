import torch

from app.models.lstm_autoencoder import LSTMAutoencoder, reconstruction_error


def test_forward_output_shape_matches_input() -> None:
    torch.manual_seed(0)
    model = LSTMAutoencoder(n_features=4, hidden_size=8, latent_size=3)
    x = torch.randn(5, 10, 4)  # batch=5, window=10, features=4

    reconstructed = model(x)

    assert reconstructed.shape == x.shape


def test_reconstruction_error_is_zero_for_perfect_reconstruction() -> None:
    x = torch.randn(3, 6, 2)
    error = reconstruction_error(x, x.clone())

    assert torch.allclose(error, torch.zeros(3))


def test_reconstruction_error_is_per_window() -> None:
    x = torch.zeros(2, 4, 2)
    x_hat = x.clone()
    x_hat[0] += 1.0  # erro só na primeira janela

    error = reconstruction_error(x, x_hat)

    assert error[0] > 0
    assert error[1] == 0


def test_model_is_deterministic_with_fixed_seed() -> None:
    torch.manual_seed(42)
    model_a = LSTMAutoencoder(n_features=3, hidden_size=6, latent_size=2)
    torch.manual_seed(42)
    model_b = LSTMAutoencoder(n_features=3, hidden_size=6, latent_size=2)

    x = torch.randn(2, 5, 3)
    torch.testing.assert_close(model_a(x), model_b(x))


def test_n_parameters_is_positive_and_small_for_cpu() -> None:
    model = LSTMAutoencoder(n_features=11, hidden_size=16, latent_size=8)
    assert 0 < model.n_parameters() < 50_000
