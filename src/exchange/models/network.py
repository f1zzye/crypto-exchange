import uuid
from django.db import models

from core.models.basemodel import BaseModel


class Network(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, verbose_name="Network name")
    short_name = models.CharField(
        max_length=10, unique=True, verbose_name="Network shortname"
    )
    is_testnet = models.BooleanField(default=False, verbose_name="Is testnet")
    is_active = models.BooleanField(default=True, verbose_name="Is active")

    class Meta:
        verbose_name = "Network"
        verbose_name_plural = "Networks"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.short_name})"
