from http import HTTPStatus

import httpx
from django.conf import settings
from django.utils import timezone

from exchange.models import Pool

DEFAULT_TIMEOUT: int = 300
MAX_ERROR_LENGTH: int = 500


def add_liquidity_to_pool(pool_instance: Pool, force=False) -> tuple[bool, str]:
    if not pool_instance.is_contract_deployed or not pool_instance.contract_address:
        return False, "Contract must be deployed first"

    if not pool_instance.token1_amount or not pool_instance.token2_amount:
        return False, "Both token1_amount and token2_amount must be set in the pool"

    if pool_instance.token1_amount <= 0 or pool_instance.token2_amount <= 0:
        return False, "Token amounts must be greater than zero"

    if not force and pool_instance.is_liquidity_added:
        return False, "Liquidity already added"

    try:
        payload = prepare_liquidity_payload(pool_instance)

        success, result = send_liquidity_request(payload)

        if success:
            update_pool_with_liquidity_result(pool_instance, result)

            pool_instance.refresh_from_db()

            success_msg = (
                f"Ликвидность добавлена успешно: "
                f"{pool_instance.token1_amount} {pool_instance.token1.short_name} + "
                f"{pool_instance.token2_amount} {pool_instance.token2.short_name}"
            )
            return True, success_msg
        else:
            handle_liquidity_error(pool_instance, result)
            return False, f"Liquidity addition failed: {result}"

    except ValueError as e:
        error_msg = f"Ошибка валидации: {str(e)}"
        handle_liquidity_error(pool_instance, error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {str(e)}"
        handle_liquidity_error(pool_instance, str(e))
        return False, error_msg


def prepare_liquidity_payload(pool_instance: Pool) -> dict:
    if not pool_instance.token1_amount or not pool_instance.token2_amount:
        raise ValueError("Pool must have both token1_amount and token2_amount set")

    if pool_instance.token1.short_name.upper() in ["TON", "TONCOIN"]:
        ton_amount = float(pool_instance.token1_amount)
        token_amount = float(pool_instance.token2_amount)
        token_decimals = pool_instance.token2.decimals
        token_master_address = getattr(pool_instance.token2, "contract_address", None)
    elif pool_instance.token2.short_name.upper() in ["TON", "TONCOIN"]:
        ton_amount = float(pool_instance.token2_amount)
        token_amount = float(pool_instance.token1_amount)
        token_decimals = pool_instance.token1.decimals
        token_master_address = getattr(pool_instance.token1, "contract_address", None)
    else:
        raise ValueError("One token must be TON")

    if token_decimals != 9:
        token_decimals = 9

    if not token_master_address:
        token_master_address = (
            pool_instance.usdt_master_address
            or "kQDF65L0_qkmjO-KMSGoLhfakB3xpRf-AVy8aMjB2u-emUiJ"
        )

    payload = {
        "pool_address": pool_instance.contract_address,
        "ton_amount": ton_amount,
        "token_amount": token_amount,
        "token_decimals": token_decimals,
        "token_master_address": token_master_address,
    }

    return payload


def send_liquidity_request(payload: dict) -> tuple[bool, dict | str]:
    try:
        nodejs_api_url = getattr(settings, "NODEJS_API_URL", "http://localhost:3000")
        api_endpoint = f"{nodejs_api_url}/api/add-liquidity"

        response = httpx.post(
            api_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT,
        )

        if response.status_code == HTTPStatus.OK:
            result = response.json()

            success = (
                result.get("success", False)
                or result.get("status") == "success"
                or result.get("ok", False)
            )

            if success:
                return True, result
            else:
                error_msg = (
                    result["error"] or result["message"] or "Unknown error from API"
                )
                return False, error_msg
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            return False, error_msg

    except httpx.TimeoutException:
        error_msg = "Timeout при добавлении ликвидности"
        return False, error_msg
    except httpx.RequestError as e:
        error_msg = f"Не удалось подключиться к Node.js API: {e}"
        return False, error_msg
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {e}"
        return False, error_msg


def update_pool_with_liquidity_result(pool_instance, liquidity_result) -> None:
    try:
        now = timezone.now()

        update_fields = {
            "last_sync_at": now,
            "is_liquidity_added": True,
            "liquidity_added_at": now,
        }

        if hasattr(pool_instance, "has_liquidity"):
            update_fields["has_liquidity"] = True

        fields_to_update = []
        for field, value in update_fields.items():
            if hasattr(pool_instance, field):
                setattr(pool_instance, field, value)
                fields_to_update.append(field)

        if fields_to_update:
            pool_instance.save(update_fields=fields_to_update)

    except Exception as e:
        if hasattr(pool_instance, "liquidity_error"):
            pool_instance.liquidity_error = f"Update failed: {str(e)}"
            pool_instance.save(update_fields=["liquidity_error"])
        else:
            pool_instance.deployment_error = f"Liquidity update failed: {str(e)}"
            pool_instance.save(update_fields=["deployment_error"])


def handle_liquidity_error(pool_instance, error_message) -> None:
    try:
        error_text = str(error_message)[:MAX_ERROR_LENGTH]

        if hasattr(pool_instance, "liquidity_error"):
            pool_instance.liquidity_error = error_text
            pool_instance.save(update_fields=["liquidity_error"])
        else:
            pool_instance.deployment_error = f"Liquidity error: {error_text}"
            pool_instance.save(update_fields=["deployment_error"])

    except Exception:
        pass
