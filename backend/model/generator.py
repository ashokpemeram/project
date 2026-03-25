"""Generator definition placeholder.

Replace MitsGanGenerator with your real architecture and keep the class name
(or update MODEL_CLASS_PATH in backend/.env).
"""

import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(c, c, 3, 1, 1),
            nn.BatchNorm2d(c),
            nn.ReLU(True),
            nn.Conv2d(c, c, 3, 1, 1),
            nn.BatchNorm2d(c),
        )

    def forward(self, x):
        return x + self.block(x)


class NoiseNet(nn.Module):
    def __init__(self, noise_dim=100):
        super().__init__()
        self.network = nn.Sequential(
            nn.ConvTranspose2d(noise_dim, 512, 4, 1, 0),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            nn.ConvTranspose2d(512, 512, 4, 2, 1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            nn.ConvTranspose2d(512, 256, 4, 2, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            nn.ConvTranspose2d(256, 128, 4, 2, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            nn.ConvTranspose2d(128, 64, 4, 2, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.ConvTranspose2d(64, 64, 4, 2, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.ConvTranspose2d(64, 64, 4, 2, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.ConvTranspose2d(64, 64, 4, 2, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
        )

    def forward(self, z):
        return self.network(z)


class MitsGanGenerator(nn.Module):
    def __init__(self, noise_dim=100):
        super().__init__()
        self.noise_dim = noise_dim
        self.noisenet = NoiseNet(noise_dim)

        self.initial = nn.Sequential(
            nn.Conv2d(65, 64, 7, 1, 3),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
        )

        self.res = nn.Sequential(
            ResidualBlock(64),
            ResidualBlock(64),
            ResidualBlock(64),
        )

        self.final = nn.Sequential(
            nn.Conv2d(64, 1, 7, 1, 3),
            nn.Tanh(),
        )

    def forward(self, img, z=None):
        if img.dim() == 3:
            img = img.unsqueeze(0)
        if img.size(1) == 3:
            r = img[:, 0:1]
            g = img[:, 1:2]
            b = img[:, 2:3]
            img = 0.2989 * r + 0.5870 * g + 0.1140 * b

        if z is None:
            z = torch.randn(img.size(0), self.noise_dim, 1, 1, device=img.device, dtype=img.dtype)
        elif z.dim() == 2:
            z = z[:, :, None, None]
        z = z.to(device=img.device, dtype=img.dtype)

        p = self.noisenet(z)
        x = torch.cat([img, p], 1)
        x = self.initial(x)
        x = self.res(x)
        return self.final(x)


Generator = MitsGanGenerator
