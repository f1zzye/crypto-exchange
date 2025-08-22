import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from http import HTTPStatus

from exchange.models import Pool
from exchange.services.deploy_signals import deploy_pool_contract
from exchange.services.liquidity_signals import add_liquidity_to_pool


DEPLOY_CONTRACT: str = "deploy_contract"
SUBMIT_LIQUIDITY: str = "submit_liquidity"


@csrf_exempt
@require_http_methods(["POST"])
def pool_custom_action(request) -> JsonResponse:
    try:
        data = json.loads(request.body)
        pool_id = data["pool_id"]
        action_type = data["action_type"]

        if not pool_id or not action_type:
            return JsonResponse(
                {"status": "error", "message": "Missing pool_id or action_type"},
                status=HTTPStatus.BAD_REQUEST,
            )

        if action_type == DEPLOY_CONTRACT:
            return handle_deploy_contract(pool_id)
        elif action_type == SUBMIT_LIQUIDITY:
            return handle_submit_liquidity(pool_id)

        return JsonResponse(
            {"status": "error", "message": f"Unknown action type: {action_type}"},
            status=HTTPStatus.BAD_REQUEST,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON"},
            status=HTTPStatus.BAD_REQUEST,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


def handle_deploy_contract(pool_id: int) -> JsonResponse:
    try:
        pool = get_object_or_404(Pool, pk=pool_id)

        if pool.is_contract_deployed:
            return JsonResponse(
                {"success": False, "error": "Contract is already deployed"}
            )

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
        return JsonResponse(
            {"success": False, "error": "Pool not found"}, status=HTTPStatus.NOT_FOUND
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR
        )


def handle_submit_liquidity(pool_id: int) -> JsonResponse:
    try:
        pool = get_object_or_404(Pool, pk=pool_id)

        success, message = add_liquidity_to_pool(pool)

        if success:
            return JsonResponse({"status": "success", "message": message})
        else:
            return JsonResponse({"status": "error", "message": message})

    except Pool.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Pool not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
