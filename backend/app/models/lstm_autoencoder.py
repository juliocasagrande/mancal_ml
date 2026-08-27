"""LSTM Autoencoder para detecção de anomalia por erro de reconstrução.

Seção 9.3 do blueprint: rede pequena (CPU), treinada apenas com dados
saudáveis (split de treino), score de anomalia = erro de reconstrução
agregado por janela.
"""

import torch
from torch import nn


class LSTMAutoencoder(nn.Module):
    def __init__(self, n_features: int, hidden_size: int = 16, latent_size: int = 8) -> None:
        super().__init__()
        self.n_features = n_features
        self.hidden_size = hidden_size
        self.latent_size = latent_size

        self.encoder_lstm = nn.LSTM(input_size=n_features, hidden_size=hidden_size, batch_first=True)
        self.to_latent = nn.Linear(hidden_size, latent_size)

        self.from_latent = nn.Linear(latent_size, hidden_size)
        self.decoder_lstm = nn.LSTM(input_size=hidden_size, hidden_size=hidden_size, batch_first=True)
        self.output_layer = nn.Linear(hidden_size, n_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, window_size, n_features)
        batch_size, window_size, _ = x.shape

        _, (h_n, _) = self.encoder_lstm(x)
        latent = self.to_latent(h_n[-1])  # (batch, latent_size)

        decoder_input = self.from_latent(latent).unsqueeze(1).repeat(1, window_size, 1)
        decoded, _ = self.decoder_lstm(decoder_input)
        reconstruction = self.output_layer(decoded)
        return reconstruction

    def n_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


def reconstruction_error(x: torch.Tensor, x_hat: torch.Tensor) -> torch.Tensor:
    """Erro de reconstrução por janela (média do MSE sobre tempo e canais)."""
    return ((x - x_hat) ** 2).mean(dim=(1, 2))
