import logging
from http import HTTPStatus

import httpx
from django.conf import settings
from django.utils import timezone

from exchange.models import Pool

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT: int = 300
MAX_ERROR_LENGTH: int = 500


def add_liquidity_to_pool(pool_instance: Pool, force=False) -> tuple[bool, str]:
    """
    Функция для добавления ликвидности в пул через кнопку в админке.
    """
    logger.info(f"🚀 Начинаем добавление ликвидности для пула: {pool_instance}")

    # Проверяем, что контракт задеплоен
    if not pool_instance.is_contract_deployed or not pool_instance.contract_address:
        logger.error("❌ Контракт не задеплоен или отсутствует адрес")
        return False, "Contract must be deployed first"

    # Проверяем, что установлены суммы токенов
    if not pool_instance.token1_amount or not pool_instance.token2_amount:
        logger.error(
            f"❌ Суммы токенов не установлены: token1_amount={pool_instance.token1_amount}, token2_amount={pool_instance.token2_amount}"
        )
        return False, "Both token1_amount and token2_amount must be set in the pool"

    if pool_instance.token1_amount <= 0 or pool_instance.token2_amount <= 0:
        logger.error(
            f"❌ Суммы токенов должны быть больше нуля: token1_amount={pool_instance.token1_amount}, token2_amount={pool_instance.token2_amount}"
        )
        return False, "Token amounts must be greater than zero"

    # Проверяем текущий статус ликвидности
    logger.info(
        f"📊 Текущий статус ликвидности: is_liquidity_added={pool_instance.is_liquidity_added}"
    )

    if not force and pool_instance.is_liquidity_added:
        logger.warning("⚠️ Ликвидность уже добавлена")
        return False, "Liquidity already added"

    logger.info(
        f"💰 Добавляем ликвидность: "
        f"Token1: {pool_instance.token1_amount} {pool_instance.token1.short_name}, "
        f"Token2: {pool_instance.token2_amount} {pool_instance.token2.short_name}"
    )

    try:
        logger.info("🔄 Подготавливаем payload...")
        payload = prepare_liquidity_payload(pool_instance)

        logger.info("📡 Отправляем запрос к Node.js API...")
        success, result = send_liquidity_request(payload)

        logger.info(f"📥 Получен ответ: success={success}, result={result}")

        if success:
            logger.info("✅ Обновляем статус пула...")
            update_pool_with_liquidity_result(pool_instance, result)

            # Перезагружаем объект из базы, чтобы проверить обновления
            pool_instance.refresh_from_db()
            logger.info(
                f"🔄 После обновления: is_liquidity_added={pool_instance.is_liquidity_added}"
            )

            success_msg = (
                f"Ликвидность добавлена успешно: "
                f"{pool_instance.token1_amount} {pool_instance.token1.short_name} + "
                f"{pool_instance.token2_amount} {pool_instance.token2.short_name}"
            )
            logger.info(f"🎉 {success_msg}")
            return True, success_msg
        else:
            logger.error(f"❌ Ошибка от API: {result}")
            handle_liquidity_error(pool_instance, result)
            return False, f"Liquidity addition failed: {result}"

    except ValueError as e:
        error_msg = f"Ошибка валидации: {str(e)}"
        logger.error(f"❌ {error_msg}")
        handle_liquidity_error(pool_instance, error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {str(e)}"
        logger.exception(f"💥 {error_msg}")
        handle_liquidity_error(pool_instance, str(e))
        return False, error_msg


def prepare_liquidity_payload(pool_instance: Pool) -> dict:
    """
    Формирует payload для Node.js API с фиксированным decimals=9 и правильным token_master_address:
    {
        "pool_address": "...",
        "ton_amount": ...,
        "token_amount": ...,
        "token_decimals": 9,
        "token_master_address": ...
    }
    """
    if not pool_instance.token1_amount or not pool_instance.token2_amount:
        raise ValueError("Pool must have both token1_amount and token2_amount set")

    if pool_instance.token1.short_name.upper() in ["TON", "TONCOIN"]:
        ton_amount = float(pool_instance.token1_amount)
        token_amount = float(pool_instance.token2_amount)  # Человеческий формат
        token_decimals = pool_instance.token2.decimals  # Берем из модели
        token_master_address = getattr(pool_instance.token2, "contract_address", None)
    elif pool_instance.token2.short_name.upper() in ["TON", "TONCOIN"]:
        ton_amount = float(pool_instance.token2_amount)
        token_amount = float(pool_instance.token1_amount)  # Человеческий формат
        token_decimals = pool_instance.token1.decimals  # Берем из модели
        token_master_address = getattr(pool_instance.token1, "contract_address", None)
    else:
        raise ValueError("One token must be TON")

    # Проверяем decimals
    if token_decimals != 9:
        logger.warning(
            f"Token decimals is {token_decimals}, expected 9. Forcing decimals=9."
        )
        token_decimals = 9  # Фиксируем decimals=9 для вашего токена

    # Проверяем token_master_address
    if not token_master_address:
        token_master_address = (
            pool_instance.usdt_master_address
            or "kQDF65L0_qkmjO-KMSGoLhfakB3xpRf-AVy8aMjB2u-emUiJ"
        )
        logger.warning(f"Using fallback token_master_address: {token_master_address}")

    payload = {
        "pool_address": pool_instance.contract_address,
        "ton_amount": ton_amount,
        "token_amount": token_amount,  # Человеческий формат (20)
        "token_decimals": token_decimals,  # Явно указываем 9
        "token_master_address": token_master_address,
    }

    logger.info(f"Prepared liquidity payload: {payload}")
    return payload


def send_liquidity_request(payload: dict) -> tuple[bool, dict | str]:
    """
    Отправляет запрос на добавление ликвидности в Node.js API
    """
    try:
        nodejs_api_url = getattr(settings, "NODEJS_API_URL", "http://localhost:3000")
        api_endpoint = f"{nodejs_api_url}/api/add-liquidity"

        logger.info(f"Отправка запроса на добавление ликвидности: {api_endpoint}")
        logger.info(f"Payload: {payload}")

        response = httpx.post(
            api_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT,
        )

        logger.info(f"Статус ответа: {response.status_code}")
        logger.info(f"Тело ответа: {response.text}")

        if response.status_code == HTTPStatus.OK:
            result = response.json()
            logger.info(f"Распарсенный ответ: {result}")

            # Проверяем несколько возможных форматов ответа
            success = (
                result.get("success", False)
                or result.get("status") == "success"
                or result.get("ok", False)
            )

            if success:
                logger.info("✅ Ликвидность успешно добавлена!")
                return True, result
            else:
                error_msg = (
                    result.get("error")
                    or result.get("message")
                    or "Unknown error from API"
                )
                logger.error(f"❌ API вернул ошибку: {error_msg}")
                return False, error_msg
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"❌ HTTP ошибка: {error_msg}")
            return False, error_msg

    except httpx.TimeoutException:
        error_msg = "Timeout при добавлении ликвидности"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
    except httpx.RequestError as e:
        error_msg = f"Не удалось подключиться к Node.js API: {e}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {e}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg


def update_pool_with_liquidity_result(pool_instance, liquidity_result) -> None:
    """
    Обновляет пул после успешного добавления ликвидности
    """
    try:
        now = timezone.now()

        update_fields = {
            "last_sync_at": now,
            "is_liquidity_added": True,  # Добавляем это поле!
            "liquidity_added_at": now,
        }

        # Дополнительные поля если они есть в модели
        if hasattr(pool_instance, "has_liquidity"):
            update_fields["has_liquidity"] = True

        fields_to_update = []
        for field, value in update_fields.items():
            if hasattr(pool_instance, field):
                setattr(pool_instance, field, value)
                fields_to_update.append(field)

        if fields_to_update:
            pool_instance.save(update_fields=fields_to_update)
            logger.info(f"Pool {pool_instance} updated fields: {fields_to_update}")

        logger.info(f"Pool {pool_instance} liquidity status updated successfully")

    except Exception as e:
        logger.error(f"Error updating pool liquidity status {pool_instance}: {e}")
        # Записываем ошибку
        if hasattr(pool_instance, "liquidity_error"):
            pool_instance.liquidity_error = f"Update failed: {str(e)}"
            pool_instance.save(update_fields=["liquidity_error"])
        else:
            pool_instance.deployment_error = f"Liquidity update failed: {str(e)}"
            pool_instance.save(update_fields=["deployment_error"])


def handle_liquidity_error(pool_instance, error_message) -> None:
    """
    Обрабатывает ошибки при добавлении ликвидности
    """
    try:
        error_text = str(error_message)[:MAX_ERROR_LENGTH]

        # Если есть специальное поле для ошибок ликвидности
        if hasattr(pool_instance, "liquidity_error"):
            pool_instance.liquidity_error = error_text
            pool_instance.save(update_fields=["liquidity_error"])
        else:
            # Используем общее поле для ошибок
            pool_instance.deployment_error = f"Liquidity error: {error_text}"
            pool_instance.save(update_fields=["deployment_error"])

        logger.error(
            f"Liquidity error recorded for pool {pool_instance}: {error_message}"
        )

    except Exception as e:
        logger.error(f"Failed to record liquidity error for pool {pool_instance}: {e}")
