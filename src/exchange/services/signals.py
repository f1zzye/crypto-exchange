import logging
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from exchange.models import Pool

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Pool)
def auto_deploy_pool_contract(sender, instance, created, **kwargs):
    if created and not instance.is_contract_deployed:
        logger.info(f"Starting auto-deployment for pool: {instance}")

        try:
            payload = prepare_deployment_payload(instance)
            success, result = send_deployment_request(payload)

            if success:
                update_pool_with_deployment_result(instance, result)
                logger.info(f"Pool {instance} deployed: {result.get('contract_address')}")
            else:
                handle_deployment_error(instance, result)
                logger.error(f"Pool {instance} deployment failed: {result}")

        except Exception as e:
            handle_deployment_error(instance, str(e))
            logger.exception(f"Deployment error for pool {instance}")


def prepare_deployment_payload(pool_instance):
    token1_symbol = getattr(pool_instance.token1, 'short_name', 'TON')
    token2_symbol = getattr(pool_instance.token2, 'short_name', 'USDT')

    if token1_symbol != 'TON' and token2_symbol == 'TON':
        token1_symbol, token2_symbol = token2_symbol, token1_symbol

    return {
        'token1': token1_symbol,
        'token2': token2_symbol,
        'fee_percentage': float(pool_instance.fee_percentage),
        'admin_address': pool_instance.admin_wallet_address or getattr(settings, 'DEFAULT_ADMIN_WALLET', None),
        'pool_id': str(pool_instance.id),
        'pool_name': pool_instance.name,
    }


def send_deployment_request(payload):
    try:
        nodejs_api_url = getattr(settings, 'NODEJS_API_URL', 'http://localhost:3000')

        response = requests.post(
            f'{nodejs_api_url}/api/deploy-pool',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('success', False), result
        else:
            return False, f'HTTP {response.status_code}: {response.text}'

    except requests.exceptions.Timeout:
        return False, 'Deployment timeout'
    except requests.exceptions.ConnectionError:
        return False, 'Cannot connect to Node.js API'
    except Exception as e:
        return False, str(e)


def update_pool_with_deployment_result(pool_instance, deployment_result):
    try:
        now = timezone.now()
        pool_info = deployment_result.get('pool_info', {})

        update_fields = {
            'contract_address': deployment_result.get('contract_address'),
            'deployment_tx_hash': deployment_result.get('transaction_hash'),
            'is_contract_deployed': True,
            'contract_deployed_at': now,
            'deployment_error': None,
            'last_sync_at': now,
        }

        if pool_info.get('admin') and not pool_instance.admin_wallet_address:
            update_fields['admin_wallet_address'] = pool_info.get('admin')

        if pool_info.get('usdt_master') and not pool_instance.usdt_master_address:
            update_fields['usdt_master_address'] = pool_info.get('usdt_master')

        for field, value in update_fields.items():
            setattr(pool_instance, field, value)

        pool_instance.save(update_fields=list(update_fields.keys()))
        logger.info(f"Pool {pool_instance} updated successfully")

    except Exception as e:
        logger.error(f"Error updating pool {pool_instance}: {e}")
        pool_instance.deployment_error = f"Update failed: {str(e)}"
        pool_instance.save(update_fields=['deployment_error'])


def handle_deployment_error(pool_instance, error_message):
    try:
        pool_instance.deployment_error = str(error_message)[:500]
        pool_instance.is_contract_deployed = False
        pool_instance.contract_deployed_at = None
        pool_instance.save(update_fields=[
            'deployment_error',
            'is_contract_deployed',
            'contract_deployed_at'
        ])
        logger.error(f"Error recorded for pool {pool_instance}: {error_message}")

    except Exception as e:
        logger.error(f"Failed to record error for pool {pool_instance}: {e}")