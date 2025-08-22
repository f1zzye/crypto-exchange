# exchange/admin_views.py
import json
import logging
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

from exchange.models import Pool
from exchange.services.deploy_signals import deploy_pool_contract
from exchange.services.liquidity_signals import add_liquidity_to_pool

logger = logging.getLogger(__name__)


@csrf_exempt
@staff_member_required
@require_http_methods(["POST"])
def pool_custom_action(request):
    """
    Обработчик кастомных действий для Pool в админке
    """
    try:
        data = json.loads(request.body)
        pool_id = data.get("pool_id")
        action_type = data.get("action_type")

        if not pool_id or not action_type:
            return JsonResponse(
                {"status": "error", "message": "Missing pool_id or action_type"},
                status=400,
            )

        if action_type == "deploy_contract":
            return handle_deploy_contract(pool_id)
        elif action_type == "submit_liquidity":
            return handle_submit_liquidity(pool_id)

        return JsonResponse(
            {"status": "error", "message": f"Unknown action type: {action_type}"},
            status=400,
        )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.exception(f"Error in pool_custom_action: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def handle_deploy_contract(pool_id):
    """
    Обработка деплоя контракта для конкретного пула
    """
    try:
        pool = get_object_or_404(Pool, pk=pool_id)

        if pool.is_contract_deployed:
            return JsonResponse(
                {"success": False, "error": "Contract is already deployed"}
            )

        logger.info(f"Manual deployment started for pool: {pool}")

        success, message = deploy_pool_contract(pool)

        if success:
            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "contract_address": pool.contract_address,
                }
            )
        else:
            return JsonResponse({"success": False, "error": message})

    except Pool.DoesNotExist:
        return JsonResponse({"success": False, "error": "Pool not found"}, status=404)
    except Exception as e:
        logger.exception(f"Error in handle_deploy_contract for pool {pool_id}: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def handle_submit_liquidity(pool_id):
    """
    Обработка добавления ликвидности для конкретного пула
    """
    try:
        pool = get_object_or_404(Pool, pk=pool_id)

        logger.info(f"Adding liquidity for pool: {pool}")

        # Вызываем функцию добавления ликвидности из сигналов
        success, message = add_liquidity_to_pool(pool)

        if success:
            return JsonResponse({"status": "success", "message": message})
        else:
            return JsonResponse({"status": "error", "message": message})

    except Pool.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Pool not found"}, status=404
        )
    except Exception as e:
        logger.exception(f"Error in handle_submit_liquidity for pool {pool_id}: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
