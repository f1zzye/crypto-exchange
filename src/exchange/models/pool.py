import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models.basemodel import BaseModel
from exchange.models.token import Token


class Pool(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Pool name")

    token1 = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name="pools_as_token1",
        verbose_name="Token A",
    )
    token1_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Token A reserve",
    )

    token2 = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name="pools_as_token2",
        verbose_name="Token B",
    )
    token2_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Token B reserve",
    )

    fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("1.3"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Fee rate (%)",
        help_text="Trading fee percentage (e.g., 0.3000 for 0.3%)",
    )

    contract_address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name="TON Contract Address",
        help_text="Deployed smart contract address in TON blockchain",
    )

    is_contract_deployed = models.BooleanField(
        default=False,
        verbose_name="Contract Deployed",
        help_text="Whether the TON smart contract has been successfully deployed",
    )

    contract_deployed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Contract Deployed At",
        help_text="Timestamp when the contract was deployed",
    )

    deployment_error = models.TextField(
        blank=True,
        null=True,
        verbose_name="Deployment Error",
        help_text="Error message if contract deployment failed",
    )

    is_pool_activated = models.BooleanField(
        default=False,
        verbose_name="Pool Activated",
        help_text="Whether the pool has been activated (OP_DEPLOY_POOL called)",
    )

    pool_activated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Pool Activated At",
        help_text="Timestamp when the pool was activated",
    )

    is_liquidity_added = models.BooleanField(
        default=False,
        verbose_name="Initial Liquidity Added",
        help_text="Whether initial liquidity has been added to the contract",
    )

    liquidity_added_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Liquidity Added At",
        help_text="Timestamp when initial liquidity was added",
    )

    last_sync_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last Sync At",
        help_text="Last time contract state was synchronized with blockchain",
    )

    admin_wallet_address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Admin Wallet Address",
        help_text="TON wallet address of the pool administrator",
    )

    usdt_master_address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="USDT Master Contract Address",
        help_text="Address of the USDT jetton master contract",
    )

    total_liquidity_additions = models.IntegerField(
        default=0, verbose_name="Total Liquidity Operations"
    )

    total_token1_added = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal("0"),
        verbose_name="Total Token1 Added",
    )

    total_token2_added = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal("0"),
        verbose_name="Total Token2 Added",
    )

    first_liquidity_added_at = models.DateTimeField(
        blank=True, null=True, verbose_name="First Liquidity Added At"
    )

    admin_notes = models.TextField(blank=True, null=True, verbose_name="Admin notes")

    is_active = models.BooleanField(default=True, verbose_name="Is active")

    class Meta:
        verbose_name = "Pool"
        verbose_name_plural = "Pools"
        unique_together = ["token1", "token2"]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["token1", "token2"]),
        ]

    def __str__(self):
        return f"{self.token1.short_name}/{self.token2.short_name}"

    def clean(self):
        if self.token1 == self.token2:
            raise ValidationError("Tokens in the pool cannot be the same")

    def save(self, *args, **kwargs):
        if not self.name:
            self.generate_pool_name()
        super().save(*args, **kwargs)

    def generate_pool_name(self):
        self.name = f"{self.token1.short_name}/{self.token2.short_name}"

    @property
    def fee_basis_points(self):
        return int(self.fee_percentage * 100)

    @property
    def contract_status(self):
        if self.is_liquidity_added:
            return "fully_operational"
        elif self.is_pool_activated:
            return "activated"
        elif self.is_contract_deployed:
            return "deployed"
        elif self.deployment_error:
            return "failed"
        else:
            return "pending"

    @property
    def contract_status_display(self):
        status_map = {
            "fully_operational": "🟢 Fully Operational",
            "activated": "🟡 Pool Activated",
            "deployed": "🔵 Contract Deployed",
            "failed": "🔴 Deployment Failed",
            "pending": "⏳ Pending Deployment",
        }
        return status_map.get(self.contract_status, "❓ Unknown")

    @property
    def exchange_rate_token1_to_token2(self):
        if self.token1_amount > 0:
            return self.token2_amount / self.token1_amount
        return Decimal("0")

    @property
    def exchange_rate_token2_to_token1(self):
        if self.token2_amount > 0:
            return self.token1_amount / self.token2_amount
        return Decimal("0")

    def get_output_amount(self, input_token, input_amount):
        input_amount = Decimal(str(input_amount))

        total_token1_liquidity = self.get_total_token1_liquidity()
        total_token2_liquidity = self.get_total_token2_liquidity()

        if input_token == self.token1:
            input_reserve = total_token1_liquidity
            output_reserve = total_token2_liquidity
        elif input_token == self.token2:
            input_reserve = total_token2_liquidity
            output_reserve = total_token1_liquidity
        else:
            raise ValueError("Токен не принадлежит этому пулу")

        if input_reserve <= 0 or output_reserve <= 0:
            return Decimal("0")

        fee_multiplier = Decimal("100") - self.fee_percentage
        numerator = input_amount * fee_multiplier * output_reserve
        denominator = (input_reserve * Decimal("100")) + (input_amount * fee_multiplier)

        if denominator <= 0:
            return Decimal("0")

        return numerator / denominator

    def get_total_token1_liquidity(self):
        return self.total_token1_added or Decimal("0")

    def get_total_token2_liquidity(self):
        return self.total_token2_added or Decimal("0")

    def add_liquidity(self, token1_amount, token2_amount):
        token1_amount = Decimal(str(token1_amount))
        token2_amount = Decimal(str(token2_amount))

        self.token1_amount = token1_amount
        self.token2_amount = token2_amount

        self.total_token1_added = (
            self.total_token1_added or Decimal("0")
        ) + token1_amount
        self.total_token2_added = (self.total_token2_added or Decimal("0")) + token2_amount
        self.total_liquidity_additions = (self.total_liquidity_additions or 0) + 1

        self.save()

        return True

    def mark_contract_deployed(self, contract_address):
        self.contract_address = contract_address
        self.is_contract_deployed = True
        self.contract_deployed_at = timezone.now()
        self.deployment_error = None
        self.save(
            update_fields=[
                "contract_address",
                "is_contract_deployed",
                "contract_deployed_at",
                "deployment_error",
            ]
        )

    def mark_pool_activated(self):
        self.is_pool_activated = True
        self.pool_activated_at = timezone.now()
        self.save(
            update_fields=[
                "is_pool_activated",
                "pool_activated_at",
            ]
        )

    def mark_liquidity_added(self):
        self.is_liquidity_added = True
        self.liquidity_added_at = timezone.now()
        self.save(
            update_fields=[
                "is_liquidity_added",
                "liquidity_added_at",
            ]
        )

    def sync_reserves_from_contract(self, ton_reserve_nano, usdt_reserve_micro):
        self.token1_amount = Decimal(str(ton_reserve_nano)) / Decimal("1000000000")
        self.token2_amount = Decimal(str(usdt_reserve_micro)) / Decimal("1000000")
        self.last_sync_at = timezone.now()

        self.save(update_fields=["token1_amount", "token2_amount", "last_sync_at"])

    def get_contract_amounts(self):
        ton_nano = int(self.token1_amount * Decimal("1000000000"))
        usdt_micro = int(self.token2_amount * Decimal("1000000"))
        return ton_nano, usdt_micro
