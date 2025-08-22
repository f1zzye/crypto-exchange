import logging
from http import HTTPStatus

import httpx
from django.conf import settings
from django.utils import timezone

from exchange.models import Pool

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT: int = 300
TON_SYMBOL: str = "TON"
USDT_SYMBOL: str = "USDT"
MAX_ERROR_LENGTH: int = 500


def deploy_pool_contract(pool_instance: Pool, force=False) -> tuple[bool, str]:
    if not force and pool_instance.is_contract_deployed:
        return False, "Contract is already deployed"

    logger.info(f"Starting manual deployment for pool: {pool_instance}")

    try:
        payload = prepare_deployment_payload(pool_instance)
        success, result = send_deployment_request(payload)

        if success:
            update_pool_with_deployment_result(pool_instance, result)
            contract_address = result.get("data", {}).get("contractAddress", "Unknown")
            logger.info(f"Pool {pool_instance} deployed manually: {contract_address}")
            return True, f"Successfully deployed: {contract_address}"
        else:
            handle_deployment_error(pool_instance, result)
            logger.error(f"Pool {pool_instance} deployment failed: {result}")
            return False, f"Deployment failed: {result}"

    except Exception as e:
        handle_deployment_error(pool_instance, str(e))
        logger.exception(f"Deployment error for pool {pool_instance}")
        return False, f"Deployment error: {str(e)}"


def prepare_deployment_payload(pool_instance: Pool) -> dict[str, str | float]:
    token1_symbol = getattr(pool_instance.token1, "short_name", TON_SYMBOL)
    token2_symbol = getattr(pool_instance.token2, "short_name", USDT_SYMBOL)

    if token1_symbol != TON_SYMBOL and token2_symbol == TON_SYMBOL:
        token1_symbol, token2_symbol = token2_symbol, token1_symbol

    return {
        "token1": token1_symbol,
        "token2": token2_symbol,
        "fee_percentage": float(pool_instance.fee_percentage),
        "admin_address": pool_instance.admin_wallet_address
        or getattr(settings, "DEFAULT_ADMIN_WALLET", None),
        "pool_id": str(pool_instance.id),
        "pool_name": pool_instance.name,
    }


def send_deployment_request(payload: dict) -> tuple[bool, dict | str]:
    try:
        nodejs_api_url = getattr(settings, "NODEJS_API_URL", "http://localhost:3000")

        response = httpx.post(
            f"{nodejs_api_url}/api/deploy-pool",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT,
        )

        if response.status_code == HTTPStatus.OK:
            result = response.json()
            return result.get("success", False), result
        else:
            return False, f"HTTP {response.status_code}: {response.text}"

    except httpx.TimeoutException:
        return False, "Deployment timeout"
    except httpx.RequestError:
        return False, "Cannot connect to Node.js API"
    except Exception as e:
        return False, str(e)


def update_pool_with_deployment_result(pool_instance, deployment_result) -> None:
    try:
        now = timezone.now()
        data = deployment_result.get("data", {})

        if not data.get("fullyInitialized", False):
            raise Exception("Pool deployment not fully initialized")

        update_fields = {
            "contract_address": data.get("contractAddress"),
            "is_contract_deployed": data.get("deployed", True),
            "contract_deployed_at": now,
            "is_pool_activated": True,
            "pool_activated_at": now,
            "last_sync_at": now,
        }

        admin_address = data.get("adminAddress")
        if admin_address and not pool_instance.admin_wallet_address:
            update_fields["admin_wallet_address"] = admin_address

        token_master_address = data.get("tokenMasterAddress")
        if token_master_address and not pool_instance.usdt_master_address:
            update_fields["usdt_master_address"] = token_master_address

        fields_to_update = []
        for field, value in update_fields.items():
            if value is not None:
                setattr(pool_instance, field, value)
                fields_to_update.append(field)

        pool_instance.save(update_fields=fields_to_update)
        logger.info(f"Pool {pool_instance} deployed and activated successfully")

    except Exception as e:
        logger.error(f"Error updating pool {pool_instance}: {e}")
        pool_instance.deployment_error = f"Update failed: {str(e)}"
        pool_instance.save(update_fields=["deployment_error"])


def handle_deployment_error(pool_instance, error_message) -> None:
    try:
        pool_instance.deployment_error = str(error_message)[:MAX_ERROR_LENGTH]
        pool_instance.is_contract_deployed = False
        pool_instance.contract_deployed_at = None
        pool_instance.is_pool_activated = False
        pool_instance.pool_activated_at = None
        pool_instance.save(
            update_fields=[
                "deployment_error",
                "is_contract_deployed",
                "contract_deployed_at",
                "is_pool_activated",
                "pool_activated_at",
            ]
        )
        logger.error(f"Error recorded for pool {pool_instance}: {error_message}")

    except Exception as e:
        logger.error(f"Failed to record error for pool {pool_instance}: {e}")
