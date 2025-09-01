import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from exchange.models.token import Token
from exchange.models.pool import Pool

from core.models.basemodel import BaseModel


class ExchangeOrder(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(max_length=100, verbose_name="User Email")

    give_token = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name="orders_as_give_token",
        verbose_name="Token Given",
    )
    give_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Amount of Token Given",
    )

    receive_token = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name="orders_as_receive_token",
        verbose_name="Token Received",
    )
    receive_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Amount of Token Received",
    )

    exchange_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Exchange Rate",
    )
    fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Fee Percentage (%)",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Order Status",
    )

    pool = models.ForeignKey(
        Pool,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Exchange Pool",
    )

    transaction_hash = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Transaction Hash"
    )

    class Meta:
        verbose_name = "Exchange Order"
        verbose_name_plural = "Exchange Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["email"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Order #{str(self.id)[:8]} - {self.give_amount} {self.give_token.short_name} → {self.receive_amount} {self.receive_token.short_name}"

    @property
    def order_short_number(self):
        return str(self.id)[:8].upper()
