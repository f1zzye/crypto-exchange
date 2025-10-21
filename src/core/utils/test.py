"""Конфигурация TON сетей"""

from decouple import config


class NetworkConfig:
    """Управление настройками TON сетей"""

    MAINNET = "mainnet"
    TESTNET = "testnet"

    CURRENT_NETWORK = config("TON_NETWORK", default=TESTNET)

    API_URLS = {
        MAINNET: config(
            "TON_MAINNET_API_URL",
            default="https://toncenter.com/api/v2"
        ),
        TESTNET: config(
            "TON_TESTNET_API_URL",
            default="https://testnet.toncenter.com/api/v2"
        ),
    }

    @classmethod
    def get_api_url(cls, network: str | None = None) -> str:
        """
        Получает URL API для сети.

        Args:
            network: Название сети (mainnet/testnet)

        Returns:
            URL API для указанной сети
        """
        network = network or cls.CURRENT_NETWORK
        return cls.API_URLS.get(network, cls.API_URLS[cls.CURRENT_NETWORK])

    @classmethod
    def is_testnet(cls, network: str | None = None) -> bool:
        """Проверяет, является ли сеть тестовой"""
        network = network or cls.CURRENT_NETWORK
        return network == cls.TESTNET


"""Сервис для работы с TON адресами"""

import logging
from pytoniq_core import Address

from .network_config import NetworkConfig

logger = logging.getLogger(__name__)


class AddressService:
    """Форматирование и валидация TON адресов"""

    @staticmethod
    def format_address(address: str, network: str | None = None) -> str:
        """
        Форматирует TON адрес в user-friendly формат.

        Args:
            address: Исходный адрес
            network: Сеть (mainnet/testnet)

        Returns:
            Отформатированный адрес
        """
        try:
            addr_obj = Address(address)

            is_testnet = NetworkConfig.is_testnet(network)

            formatted = addr_obj.to_str(
                is_user_friendly=True,
                is_bounceable=False,
                is_url_safe=True,
                is_test_only=is_testnet,
            )

            return formatted

        except Exception as e:
            logger.warning(f"Address formatting error for {address}: {e}")
            return address

    @staticmethod
    def make_short_address(address: str, prefix: int = 4, suffix: int = 4) -> str:
        """
        Создает короткую версию адреса.

        Args:
            address: Полный адрес
            prefix: Количество символов в начале
            suffix: Количество символов в конце

        Returns:
            Сокращенный адрес вида "XXXX...XXXX"
        """
        if len(address) <= prefix + suffix:
            return address
        return f"{address[:prefix]}...{address[-suffix:]}"

    @staticmethod
    def validate_address(address: str) -> bool:
        """
        Проверяет валидность TON адреса.

        Args:
            address: Адрес для проверки

        Returns:
            True если адрес валиден
        """
        try:
            Address(address)
            return True
        except Exception:
            """Сервис для получения балансов TON кошельков"""

            import logging
            from decimal import Decimal

            import httpx

            from .network_config import NetworkConfig

            logger = logging.getLogger(__name__)


            class BalanceService:
                """Получение и форматирование балансов TON"""

                # Константы
                NANOTON_IN_TON = Decimal("1000000000")  # 1e9
                REQUEST_TIMEOUT = 10.0
                MIN_DISPLAY_BALANCE = Decimal("0.01")

                @classmethod
                def get_balance(cls, address: str, network: str | None = None) -> str:
                    """
                    Получает баланс кошелька.

                    Args:
                        address: TON адрес
                        network: Сеть (mainnet/testnet)

                    Returns:
                        Баланс в формате "X.XX TON"
                    """
                    try:
                        balance_nano = cls._fetch_balance_from_api(address, network)
                        return cls.format_balance(balance_nano)

                    except Exception as e:
                        logger.error(f"Balance fetch error for {address}: {e}", exc_info=True)
                        return "0 TON"

                @classmethod
                def _fetch_balance_from_api(cls, address: str, network: str | None) -> int:
                    """
                    Запрашивает баланс из API.

                    Args:
                        address: TON адрес
                        network: Сеть

                    Returns:
                        Баланс в нанотонах

                    Raises:
                        httpx.HTTPError: При ошибке HTTP запроса
                        ValueError: При неверном формате ответа
                    """
                    base_url = NetworkConfig.get_api_url(network)
                    url = f"{base_url}/getAddressBalance?address={address}"

                    with httpx.Client(timeout=cls.REQUEST_TIMEOUT) as client:
                        response = client.get(url)
                        response.raise_for_status()
                        data = response.json()

                    if not data.get("ok"):
                        raise ValueError(f"API returned error: {data}")

                    return int(data.get("result", 0))

                @classmethod
                def format_balance(cls, balance_nano: int) -> str:
                    """
                    Форматирует баланс из нанотонов в читаемый вид.

                    Args:
                        balance_nano: Баланс в нанотонах

                    Returns:
                        Строка вида "X.XX TON"
                    """
                    balance_ton = Decimal(balance_nano) / cls.NANOTON_IN_TON

                    if balance_ton == 0:
                        return "0 TON"
                    elif balance_ton < cls.MIN_DISPLAY_BALANCE:
                        return f"< {cls.MIN_DISPLAY_BALANCE} TON"
                    else:
                        return f"{balance_ton:.2f} TON"
            return False

import logging
from http import HTTPStatus

from django.http import JsonResponse
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from core.services.ton import AddressService, BalanceService, NetworkConfig

logger = logging.getLogger(__name__)


class WalletTonService(View):
    """API для получения информации о TON кошельке"""

    @method_decorator(cache_page(60))  # Кеш на 1 минуту
    def get(self, request) -> JsonResponse:
        """
        Получает информацию о кошельке.

        Query Parameters:
            - address: TON адрес кошелька
            - network: Сеть (mainnet/testnet), опционально

        Returns:
            JSON с балансом и отформатированным адресом
        """
        address = request.GET.get("address")
        network = request.GET.get("network", NetworkConfig.CURRENT_NETWORK)

        # Валидация
        if not address:
            return JsonResponse(
                {"error": "No address provided"},
                status=HTTPStatus.BAD_REQUEST
            )

        if not AddressService.validate_address(address):
            return JsonResponse(
                {"error": "Invalid TON address"},
                status=HTTPStatus.BAD_REQUEST
            )

        try:
            # Форматирование адреса
            formatted_address = AddressService.format_address(address, network)
            short_address = AddressService.make_short_address(formatted_address)

            # Получение баланса
            balance = BalanceService.get_balance(formatted_address, network)

            return JsonResponse(
                {
                    "balance": balance,
                    "address": formatted_address,
                    "shortAddress": short_address,
                    "network": network,
                }
            )

        except Exception as e:
            logger.error(f"Error processing wallet {address}: {e}", exc_info=True)
            return JsonResponse(
                {"error": "Failed to fetch wallet data"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )



