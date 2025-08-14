import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        abstract = True


class Network(TimestampMixin):
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


class Token(TimestampMixin):
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


class Pool(TimestampMixin):
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

    deployment_tx_hash = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Deployment Transaction Hash",
        help_text="Transaction hash of the contract deployment",
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

    activation_tx_hash = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Pool Activation Transaction Hash",
        help_text="Transaction hash of the pool activation",
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

    liquidity_tx_hash = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Liquidity Transaction Hash",
        help_text="Transaction hash of the liquidity addition",
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
        self.name = f"{self.token1.symbol}/{self.token2.symbol}"

    @property
    def fee_basis_points(self):
        """Конвертация процентов в базисные пункты для контракта"""
        return int(self.fee_percentage * 100)

    @property
    def contract_status(self):
        """Текстовый статус контракта"""
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
        """Человекочитаемый статус контракта"""
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
        """Курс: сколько token2 за 1 token1"""
        if self.token1_amount > 0:
            return self.token2_amount / self.token1_amount
        return Decimal("0")

    @property
    def exchange_rate_token2_to_token1(self):
        """Курс: сколько token1 за 1 token2"""
        if self.token2_amount > 0:
            return self.token1_amount / self.token2_amount
        return Decimal("0")

    def get_output_amount(self, input_token, input_amount):
        """
        Рассчитать количество выходного токена для обмена
        Использует формула AMM (Automated Market Maker)
        """
        input_amount = Decimal(str(input_amount))

        if input_token == self.token1:
            input_reserve = self.token1_amount
            output_reserve = self.token2_amount
        elif input_token == self.token2:
            input_reserve = self.token2_amount
            output_reserve = self.token1_amount
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

    def mark_contract_deployed(self, contract_address, tx_hash):
        """Отметить контракт как задеплоенный"""
        self.contract_address = contract_address
        self.is_contract_deployed = True
        self.contract_deployed_at = timezone.now()
        self.deployment_tx_hash = tx_hash
        self.deployment_error = None
        self.save(
            update_fields=[
                "contract_address",
                "is_contract_deployed",
                "contract_deployed_at",
                "deployment_tx_hash",
                "deployment_error",
            ]
        )

    def mark_pool_activated(self, tx_hash):
        """Отметить пул как активированный"""
        self.is_pool_activated = True
        self.pool_activated_at = timezone.now()
        self.activation_tx_hash = tx_hash
        self.save(
            update_fields=[
                "is_pool_activated",
                "pool_activated_at",
                "activation_tx_hash",
            ]
        )

    def mark_liquidity_added(self, tx_hash):
        """Отметить ликвидность как добавленную"""
        self.is_liquidity_added = True
        self.liquidity_added_at = timezone.now()
        self.liquidity_tx_hash = tx_hash
        self.save(
            update_fields=[
                "is_liquidity_added",
                "liquidity_added_at",
                "liquidity_tx_hash",
            ]
        )

    def sync_reserves_from_contract(self, ton_reserve_nano, usdt_reserve_micro):
        """
        Синхронизировать резервы из контракта в token1_amount и token2_amount
        """
        # Конвертируем из blockchain единиц в обычные
        self.token1_amount = Decimal(str(ton_reserve_nano)) / Decimal(
            "1000000000"
        )  # из nanotons
        self.token2_amount = Decimal(str(usdt_reserve_micro)) / Decimal(
            "1000000"
        )  # из micro USDT
        self.last_sync_at = timezone.now()

        self.save(update_fields=["token1_amount", "token2_amount", "last_sync_at"])

    def get_contract_amounts(self):
        """
        Получить суммы в единицах контракта (nanotons и micro USDT)
        """
        ton_nano = int(self.token1_amount * Decimal("1000000000"))  # в nanotons
        usdt_micro = int(self.token2_amount * Decimal("1000000"))  # в micro USDT
        return ton_nano, usdt_micro


class ExchangeOrder(TimestampMixin):
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
        "Token",
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
        "Token",
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
        "Pool",
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
