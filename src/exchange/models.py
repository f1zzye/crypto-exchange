from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid



class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        abstract = True

class Network(TimestampMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, verbose_name="Network name")
    short_name = models.CharField(max_length=10, unique=True, verbose_name="Network shortname")
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
    decimals = models.PositiveIntegerField(
        default=2, verbose_name="Decimal places"
    )
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
        help_text="Trading fee percentage (e.g., 0.3000 for 0.3%)"
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
            # Обмен token1 -> token2
            input_reserve = self.token1_amount
            output_reserve = self.token2_amount
        elif input_token == self.token2:
            # Обмен token2 -> token1
            input_reserve = self.token2_amount
            output_reserve = self.token1_amount
        else:
            raise ValueError("Токен не принадлежит этому пулу")

        if input_reserve <= 0 or output_reserve <= 0:
            return Decimal("0")

        # Формула AMM с комиссией: (input_amount * (100 - fee) * output_reserve) / (input_reserve * 100 + input_amount * (100 - fee))
        fee_multiplier = Decimal("100") - self.fee_percentage
        numerator = input_amount * fee_multiplier * output_reserve
        denominator = (input_reserve * Decimal("100")) + (input_amount * fee_multiplier)

        if denominator <= 0:
            return Decimal("0")

        return numerator / denominator


# class Exchange(models.Model):
#     """Модель для записи обменов"""
#     pool = models.ForeignKey(
#         Pool,
#         on_delete=models.CASCADE,
#         related_name='exchanges',
#         verbose_name="Пул"
#     )
#     user = models.ForeignKey(
#         'auth.User',  # или ваша кастомная модель пользователя
#         on_delete=models.CASCADE,
#         related_name='exchanges',
#         verbose_name="Пользователь"
#     )
#
#     input_token = models.ForeignKey(
#         Token,
#         on_delete=models.CASCADE,
#         related_name='input_exchanges',
#         verbose_name="Входящий токен"
#     )
#     input_amount = models.DecimalField(
#         max_digits=30,
#         decimal_places=18,
#         verbose_name="Количество входящего токена"
#     )
#
#     output_token = models.ForeignKey(
#         Token,
#         on_delete=models.CASCADE,
#         related_name='output_exchanges',
#         verbose_name="Исходящий токен"
#     )
#     output_amount = models.DecimalField(
#         max_digits=30,
#         decimal_places=18,
#         verbose_name="Количество исходящего токена"
#     )
#
#     exchange_rate = models.DecimalField(
#         max_digits=30,
#         decimal_places=18,
#         verbose_name="Курс обмена"
#     )
#     fee_amount = models.DecimalField(
#         max_digits=30,
#         decimal_places=18,
#         verbose_name="Размер комиссии"
#     )
#
#     transaction_hash = models.CharField(
#         max_length=255,
#         blank=True,
#         null=True,
#         verbose_name="Хэш транзакции"
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=[
#             ('pending', 'Ожидает'),
#             ('completed', 'Завершен'),
#             ('failed', 'Неудачен'),
#         ],
#         default='pending',
#         verbose_name="Статус"
#     )
#
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
#
#     class Meta:
#         verbose_name = "Обмен"
#         verbose_name_plural = "Обмены"
#         ordering = ['-created_at']
#
#     def __str__(self):
#         return f"{self.input_amount} {self.input_token.symbol} -> {self.output_amount} {self.output_token.symbol}"
