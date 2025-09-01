import uuid
from django.db import models

from core.models.basemodel import BaseModel
from exchange.models.network import Network


class Token(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Token name")
    short_name = models.CharField(max_length=20, verbose_name="Token shortname")
    network = models.ForeignKey(
        Network, on_delete=models.CASCADE, related_name="tokens", verbose_name="Network"
    )
    image = models.ImageField(
        upload_to="tokens/", blank=True, null=True, verbose_name="Token image"
    )
    decimals = models.PositiveIntegerField(default=2, verbose_name="Decimal places")
    is_active = models.BooleanField(default=True, verbose_name="Is active")

    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
        unique_together = ["short_name", "network"]
        ordering = ["name"]
        indexes = [
            models.Index(fields=["network", "is_active"]),
            models.Index(fields=["short_name", "network"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.short_name}) - {self.network.name}"