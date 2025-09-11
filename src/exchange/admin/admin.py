from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404
from unfold.admin import ModelAdmin
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from exchange.models import Token, Network, Pool
from exchange.services.deploy_signals import deploy_pool_contract
from orders.models import ExchangeOrder


class TokenInline(admin.TabularInline):
    model = Token
    extra = 0
    fields = ("name", "short_name", "decimals", "is_active")
    readonly_fields = ("created_at",)


@admin.register(Network)
class NetworkAdmin(ModelAdmin):
    list_display = (
        "name",
        "short_name",
        "network_type_display",
        "status_display",
        "tokens_count",
        "pools_count",
        "created_at",
    )
    list_display_links = ("name", "short_name")
    search_fields = ("name", "short_name")
    list_filter = ("is_active", "is_testnet", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_network_stats")

    fieldsets = (
        ("Basic Information", {"fields": ("name", "short_name")}),
        ("Configuration", {"fields": ("is_active", "is_testnet")}),
        (
            "Analytics",
            {
                "fields": ("get_network_stats",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [TokenInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tokens")

    def network_type_display(self, obj):
        if obj.is_testnet:
            return format_html('<span style="color: #ff9800;">Testnet</span>')
        return format_html('<span style="color: #4caf50;">Mainnet</span>')

    network_type_display.short_description = "Type"

    def status_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            "#4caf50" if obj.is_active else "#f44336",
            "Active" if obj.is_active else "Inactive",
        )

    status_display.short_description = "Status"

    def tokens_count(self, obj):
        if not obj.pk:
            return "0"

        count = obj.tokens.count()
        if count > 0:
            url = (
                reverse("admin:exchange_token_changelist")
                + f"?network__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"

    tokens_count.short_description = "Tokens"

    def pools_count(self, obj):
        if not obj.pk:
            return "0"

        pools_count = (
            Pool.objects.filter(Q(token1__network=obj) | Q(token2__network=obj))
            .distinct()
            .count()
        )
        return str(pools_count)

    pools_count.short_description = "Pools"

    def get_network_stats(self, obj):
        if not obj.pk:
            return "Save to see analytics"

        tokens = obj.tokens.count()
        active_tokens = obj.tokens.filter(is_active=True).count()
        pools_count = (
            Pool.objects.filter(Q(token1__network=obj) | Q(token2__network=obj))
            .distinct()
            .count()
        )

        return format_html(
            "<strong>Network Analytics:</strong><br>"
            "Total Tokens: {}<br>"
            "Active Tokens: {}<br>"
            "Associated Pools: {}<br>"
            "Network Health: {}",
            tokens,
            active_tokens,
            pools_count,
            "Good" if active_tokens > 0 else "Needs Tokens",
        )

    get_network_stats.short_description = "Network Analytics"


@admin.register(Token)
class TokenAdmin(ModelAdmin):
    list_display = (
        "name",
        "short_name",
        "network_link",
        "decimals",
        "status_display",
        "pools_count",
        "image_preview",
        "created_at",
    )
    list_display_links = ("name", "short_name")
    search_fields = ("name", "short_name", "network__name", "network__short_name")
    list_filter = ("is_active", "network", "decimals", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_token_analytics")

    fieldsets = (
        ("Basic Information", {"fields": ("name", "short_name", "network")}),
        ("Configuration", {"fields": ("image", "decimals", "is_active")}),
        (
            "Analytics",
            {
                "fields": ("get_token_analytics",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("network")

    def network_link(self, obj):
        if not obj.network:
            return "No network"

        url = reverse("admin:exchange_network_change", args=[obj.network.id])
        return format_html('<a href="{}">{}</a>', url, obj.network.short_name)

    network_link.short_description = "Network"

    def status_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            "#4caf50" if obj.is_active else "#f44336",
            "Active" if obj.is_active else "Inactive",
        )

    status_display.short_description = "Status"

    def pools_count(self, obj):
        if not obj.pk:
            return "0"

        count = Pool.objects.filter(Q(token1=obj) | Q(token2=obj)).count()
        return str(count)

    pools_count.short_description = "Pools"

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, "url"):
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Preview"

    def get_token_analytics(self, obj):
        if not obj.pk:
            return "Save to see analytics"

        pools = Pool.objects.filter(Q(token1=obj) | Q(token2=obj))
        active_pools = pools.filter(is_active=True)

        total_liquidity = sum(
            pool.token1_amount + pool.token2_amount
            for pool in active_pools
            if pool.token1_amount and pool.token2_amount
        )

        pool_list = []
        for pool in active_pools[:3]:
            pool_url = reverse("admin:exchange_pool_change", args=[pool.id])
            pool_list.append(f'<a href="{pool_url}">{pool}</a>')

        result = format_html(
            "<strong>Token Analytics:</strong><br>"
            "Total Pools: {}<br>"
            "Active Pools: {}<br>"
            "Total Liquidity: ${:,.0f}<br>"
            "Token Health: {}",
            pools.count(),
            active_pools.count(),
            total_liquidity,
            "Good" if active_pools.count() > 0 else "Needs Pools",
        )

        if pool_list:
            result += format_html(
                "<br><br><strong>Active Pools:</strong><br>{}", "<br>".join(pool_list)
            )
            if active_pools.count() > 3:
                result += f"<br>... and {active_pools.count() - 3} more"

        return result

    get_token_analytics.short_description = "Token Analytics"


@admin.register(Pool)
class PoolAdmin(ModelAdmin):
    list_display = (
        "pool_display",
        "network_info",
        "reserves_display",
        "contract_status_badge",
        "liquidity_health",
        "fee_percentage",
        "volume_24h",
        "status_badge",
    )
    list_display_links = ("pool_display",)
    search_fields = (
        "name",
        "token1__name",
        "token1__short_name",
        "token2__name",
        "token2__short_name",
        "contract_address",
    )
    list_filter = (
        "is_active",
        "is_contract_deployed",
        "is_pool_activated",
        "is_liquidity_added",
        ("token1__network", admin.RelatedOnlyFieldListFilter),
        "fee_percentage",
        "created_at",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "contract_status_display",
        "get_pool_dashboard",
        "get_contract_dashboard",
        "get_liquidity_submit_button",
        "get_deploy_contract_button",
    )

    fieldsets = (
        ("Pool Information", {"fields": ("name",), "classes": ("wide",)}),
        (
            "Token Configuration",
            {
                "fields": (
                    "token1",
                    "token2",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "Pool Settings",
            {
                "fields": (
                    "fee_percentage",
                    "is_active",
                    "get_deploy_contract_button",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "Adding Liquidity",
            {
                "fields": (
                    "token1_amount",
                    "token2_amount",
                    "get_liquidity_submit_button",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "Smart Contract",
            {
                "fields": (
                    "contract_address",
                    "contract_status_display",
                    ("is_contract_deployed", "contract_deployed_at"),
                    ("is_pool_activated", "pool_activated_at"),
                    ("is_liquidity_added", "liquidity_added_at"),
                    "deployment_error",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Administration",
            {
                "fields": (
                    "admin_wallet_address",
                    "usdt_master_address",
                    "admin_notes",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Analytics Dashboard",
            {
                "fields": ("get_pool_dashboard", "get_contract_dashboard"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("token1", "token2", "token1__network", "token2__network")
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "deploy_contract/",
                self.admin_site.admin_view(csrf_exempt(self.deploy_contract_view)),
                name="pool_custom_action",
            ),
        ]
        return custom_urls + urls

    @staticmethod
    def deploy_contract_view(request):
        if request.method != "POST":
            return HttpResponseBadRequest("Only POST allowed")
        try:
            data = json.loads(request.body)
            pool_id = data.get("pool_id")
            pool = get_object_or_404(Pool, pk=pool_id)
            ok, message = deploy_pool_contract(pool)
            status = "success" if ok else "error"
            return JsonResponse({"status": status, "message": message})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    @method_decorator(csrf_exempt, name="dispatch")
    def custom_action_view(self, request):
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                pool_id = data["pool_id"]
                action_type = data.get("action_type", "unknown")

                if pool_id and pool_id != "new":
                    try:
                        pool = Pool.objects.get(pk=pool_id)
                    except Pool.DoesNotExist:
                        pass

                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Действие выполнено успешно!",
                        "pool_id": pool_id,
                    }
                )
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=400)

        return JsonResponse(
            {"status": "error", "message": "Method not allowed"}, status=405
        )

    def get_liquidity_submit_button(self, obj):
        pool_id = obj.pk if obj and obj.pk else "new"
        action_url = reverse("exchange:pool_custom_action")

        if not obj or not obj.is_contract_deployed:
            return format_html(
                '<span style="color: #6b7280; font-style: italic;">Deploy contract first</span>'
            )

        return format_html(
            """
            <div style="margin: 10px 0;">
                <button 
                    type="button" 
                    id="liquidity-btn-{}"
                    onclick="performLiquidityAction('{}', '{}')"
                    style="
                        background: #8b5cf6; 
                        color: white; 
                        border: none; 
                        padding: 12px 25px; 
                        border-radius: 6px; 
                        font-size: 14px; 
                        font-weight: bold; 
                        cursor: pointer; 
                        transition: all 0.3s ease;
                        width: 100%;
                    "
                    onmouseover="this.style.background='#7c3aed'"
                    onmouseout="this.style.background='#8b5cf6'"
                >
                    Submit Liquidity
                </button>
                <div id="liquidity-result-{}" style="margin-top: 10px; font-size: 12px; color: #a1a1aa;"></div>
            </div>

            <script>
            async function performLiquidityAction(poolId, actionUrl) {{
                console.log('Submit Liquidity нажата для Pool ID:', poolId);

                const btn = document.getElementById('liquidity-btn-' + poolId);
                const resultDiv = document.getElementById('liquidity-result-' + poolId);
                const originalText = btn.innerHTML;

                try {{
                    btn.innerHTML = 'Adding...';
                    btn.disabled = true;
                    btn.style.background = '#6b7280';
                    resultDiv.innerHTML = '<span style="color: #f59e0b;">Adding liquidity...</span>';

                    const response = await fetch(actionUrl, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }},
                        body: JSON.stringify({{
                            pool_id: poolId,
                            action_type: 'submit_liquidity',
                            timestamp: new Date().toISOString()
                        }})
                    }});

                    const data = await response.json();

                    if (data.status === 'success') {{
                        btn.innerHTML = '✓ Added';
                        btn.style.background = '#10b981';
                        resultDiv.innerHTML = '<span style="color: #22c55e;">✓ ' + data.message + '</span>';
                        setTimeout(() => location.reload(), 2000);
                    }} else {{
                        throw new Error(data.message || 'Unknown error');
                    }}
                }} catch (error) {{
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    btn.style.background = '#8b5cf6';
                    resultDiv.innerHTML = '<span style="color: #ef4444;">✗ Error: ' + error.message + '</span>';
                }}
            }}
            </script>
            """,
            pool_id,
            pool_id,
            action_url,
            pool_id,
        )

    get_liquidity_submit_button.short_description = "Submit Liquidity"

    def get_deploy_contract_button(self, obj):
        pool_id = obj.pk if obj and obj.pk else "new"
        action_url = reverse("exchange:pool_custom_action")

        if obj and obj.is_contract_deployed:
            contract_addr = obj.contract_address or "Unknown"
            return format_html(
                f'<span style="color: #10b981; font-weight: bold;">✓ Deployed: {contract_addr[:4]}...{contract_addr[-4:]}</span>'
            )

        return format_html(
            """
            <button
                type="button"
                id="deploy-btn-{}"
                onclick="performDeployContract('{}', '{}')"
                style="background: #a855f7; color: white; border: none; padding: 12px 25px; border-radius: 6px; font-size: 14px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; width: 100%;"
                onmouseover="this.style.background='#9333ea'"
                onmouseout="this.style.background='#a855f7'"
            >Deploy Contract</button>
            <script>
            async function performDeployContract(poolId, actionUrl) {{
                const btn = document.getElementById('deploy-btn-' + poolId);
                const originalText = btn.innerHTML;

                try {{
                    btn.innerHTML = 'Deploying...';
                    btn.disabled = true;
                    btn.style.background = '#6b7280';

                    const response = await fetch(actionUrl, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }},
                        body: JSON.stringify({{
                            pool_id: poolId,
                            action_type: 'deploy_contract',
                            timestamp: new Date().toISOString()
                        }})
                    }});

                    const data = await response.json();

                    if (data.success) {{
                        btn.innerHTML = '✓ Deployed';
                        btn.style.background = '#10b981';
                        setTimeout(() => location.reload(), 2000);
                    }} else {{
                        throw new Error(data.error || 'Unknown error');
                    }}

                }} catch (error) {{
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    btn.style.background = '#a855f7';
                    alert('Ошибка деплоя: ' + error.message);
                }}
            }}
            </script>
            """,
            pool_id,
            pool_id,
            action_url,
        )

    get_deploy_contract_button.short_description = "Deploy Contract"

    def pool_display(self, obj):
        if not (obj.token1 and obj.token2):
            return format_html('<span style="color: #f44336;">Incomplete</span>')

        edit_url = reverse("admin:exchange_pool_change", args=[obj.pk])

        token1_url = reverse("admin:exchange_token_change", args=[obj.token1.id])
        token2_url = reverse("admin:exchange_token_change", args=[obj.token2.id])

        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<strong style="color: #333;">'
            '<a href="{}" style="color: #1976d2; text-decoration: none;">{} / {}</a>'
            "</strong>"
            '<div style="font-size: 11px; color: #666; margin-left: 8px;">'
            '<a href="{}" style="color: #666;">T1</a> | '
            '<a href="{}" style="color: #666;">T2</a>'
            "</div>"
            "</div>",
            edit_url,
            obj.token1.short_name,
            obj.token2.short_name,
            token1_url,
            token2_url,
        )

    pool_display.short_description = "Pool"

    def network_info(self, obj):
        if obj.token1 and obj.token1.network:
            network = obj.token1.network
            url = reverse("admin:exchange_network_change", args=[network.id])
            badge_color = "#4caf50" if network.is_active else "#9e9e9e"
            network_type = "TESTNET" if network.is_testnet else "MAINNET"

            return format_html(
                '<a href="{}" style="text-decoration: none;">'
                '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px;">'
                "{}"
                "</span></a>",
                url,
                badge_color,
                network.short_name,
            )
        return "—"

    network_info.short_description = "Network"

    def reserves_display(self, obj):
        if not (
            obj.token1
            and obj.token2
            and obj.token1_amount is not None
            and obj.token2_amount is not None
        ):
            return format_html('<span style="color: #f44336;">Not Set</span>')

        total_value = obj.token1_amount + obj.token2_amount
        balance_ratio = (
            (obj.token1_amount / total_value * 100) if total_value > 0 else 0
        )

        balance_color = (
            "#4caf50"
            if 30 <= balance_ratio <= 70
            else "#ff9800" if 20 <= balance_ratio <= 80 else "#f44336"
        )

        return format_html(
            '<div style="font-size: 12px;">'
            "<div>{} {}</div>"
            "<div>{} {}</div>"
            '<div style="color: {}; font-weight: bold;">TVL: ${}</div>'
            "</div>",
            "{:,.0f}".format(obj.token1_amount),
            obj.token1.short_name,
            "{:,.0f}".format(obj.token2_amount),
            obj.token2.short_name,
            balance_color,
            "{:,.0f}".format(total_value),
        )

    reserves_display.short_description = "Reserves"

    def contract_status_badge(self, obj):
        status = obj.contract_status
        status_config = {
            "fully_operational": ("#4caf50", "Operational"),
            "activated": ("#ff9800", "Activated"),
            "deployed": ("#2196f3", "Deployed"),
            "failed": ("#f44336", "Failed"),
            "pending": ("#9e9e9e", "Pending"),
        }

        color, text = status_config.get(status, ("#000", "Unknown"))

        if obj.contract_address and obj.is_contract_deployed:
            explorer_url = f"https://testnet.tonviewer.com/{obj.contract_address}"
            return format_html(
                "<div>"
                '<span style="color: {}; font-weight: bold;">{}</span><br>'
                '<a href="{}" target="_blank" style="font-size: 10px; color: #666;">View on TONviewer</a>'
                "</div>",
                color,
                text,
                explorer_url,
            )
        else:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                text,
            )

    contract_status_badge.short_description = "Contract"

    def liquidity_health(self, obj):
        if not (obj.token1_amount and obj.token2_amount):
            return format_html('<span style="color: #9e9e9e;">—</span>')

        total_liquidity = obj.token1_amount + obj.token2_amount

        try:
            orders_count = ExchangeOrder.objects.filter(pool=obj).count()
        except:
            orders_count = 0

        if total_liquidity > 10_000_0 and orders_count > 10:
            return format_html('<span style="color: #4caf50;">Excellent</span>')
        elif total_liquidity > 10_000 and orders_count > 5:
            return format_html('<span style="color: #8bc34a;">Good</span>')
        elif total_liquidity > 1000:
            return format_html('<span style="color: #ff9800;">Growing</span>')
        else:
            return format_html('<span style="color: #f44336;">Weak</span>')

    liquidity_health.short_description = "Health"

    def volume_24h(self, obj):
        try:
            orders_count = ExchangeOrder.objects.filter(
                pool=obj, status="completed"
            ).count()
        except:
            orders_count = 0

        if orders_count > 50:
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">High</span>'
            )
        elif orders_count > 10:
            return format_html('<span style="color: #ff9800;">Medium</span>')
        elif orders_count > 0:
            return format_html('<span style="color: #2196f3;">Low</span>')
        return "—"

    volume_24h.short_description = "24h Vol"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">Active</span>'
            )
        return format_html(
            '<span style="color: #f44336; font-weight: bold;">Inactive</span>'
        )

    status_badge.short_description = "Status"

    def get_pool_dashboard(self, obj):
        if not obj.pk:
            return format_html(
                '<div style="color: #666;">Save pool to see dashboard</div>'
            )

        try:
            orders = ExchangeOrder.objects.filter(pool=obj)
            total_orders = orders.count()
            completed_orders = orders.filter(status="completed").count()
        except:
            total_orders = 0
            completed_orders = 0

        success_rate = (
            (completed_orders / total_orders * 100) if total_orders > 0 else 0
        )

        return format_html(
            """
            <div style="background: #1e293b; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #f1f5f9;">Pool Analytics Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr; gap: 15px;">
                    <div style="background: #0f172a; padding: 12px; border-radius: 6px; border-left: 4px solid #4caf50; color: #e2e8f0;">
                        <strong style="color: #4caf50;">Trading Stats</strong><br>
                        Total Orders: {}<br>
                        Completed: {}<br>
                        Success Rate: {}%
                    </div>
                </div>

                <div style="margin-top: 15px; background: #0f172a; padding: 12px; border-radius: 6px; border-left: 4px solid #9c27b0; color: #e2e8f0;">
                    <strong style="color: #ba68c8;">Liquidity History Summary:</strong><br>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px;">
                        <div style="font-size: 14px;">
                            📈 <strong>Total {} Added:</strong> {}<br>
                            📈 <strong>Total {} Added:</strong> {}
                        </div>
                        <div style="font-size: 14px;">
                            🔄 <strong>Operations:</strong> {}<br>
                            📊 <strong>Avg per Operation:</strong> ${}
                        </div>
                    </div>
                </div>
            </div>
            """,
            total_orders,
            completed_orders,
            "{:.1f}".format(success_rate),
            obj.token1.short_name if obj.token1 else "TOKEN1",
            "{:,.2f}".format(obj.total_token1_added or 0),
            obj.token2.short_name if obj.token2 else "TOKEN2",
            "{:,.2f}".format(obj.total_token2_added or 0),
            obj.total_liquidity_additions or 0,
            "{:,.0f}".format(
                (
                    (
                        float(obj.total_token1_added or 0)
                        + float(obj.total_token2_added or 0)
                    )
                    / (obj.total_liquidity_additions or 1)
                )
            ),
        )

    get_pool_dashboard.short_description = "Pool Dashboard"

    def get_contract_dashboard(self, obj):
        if not obj.pk:
            return format_html(
                '<div style="color: #666;">Save pool to see contract info</div>'
            )

        contract_addr = (
            obj.contract_address[:10] + "..." if obj.contract_address else "Not set"
        )
        last_sync = (
            obj.last_sync_at.strftime("%m/%d %H:%M") if obj.last_sync_at else "Never"
        )
        admin_addr = (
            obj.admin_wallet_address[:10] + "..."
            if obj.admin_wallet_address
            else "Not set"
        )

        error_section = ""
        if obj.deployment_error:
            error_section = """
            <div style="background: #ffebee; padding: 10px; border-radius: 6px; border-left: 4px solid #f44336; margin-top: 15px;">
                <strong style="color: #f44336;">Deployment Error:</strong><br>
                <code>{}</code>
            </div>
            """.format(
                obj.deployment_error
            )

        return format_html(
            """
            <div style="background: #1e293b; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #f1f5f9;">Smart Contract Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: #0f172a; padding: 12px; border-radius: 6px; border-left: 4px solid #673ab7; color: #e2e8f0;">
                        <strong style="color: #c4b5fd;">Contract Status</strong><br>
                        Deployed: {}<br>
                        Activated: {}<br>
                        Liquidity: {}<br>
                        Overall: {}
                    </div>

                    <div style="background: #0f172a; padding: 12px; border-radius: 6px; border-left: 4px solid #e91e63; color: #e2e8f0;">
                        <strong style="color: #f472b6;">Technical</strong><br>
                        Address: {}<br>
                        Last Sync: {}<br>
                        Admin: {}
                    </div>
                </div>

                {}
            </div>
        """,
            "Yes" if obj.is_contract_deployed else "No",
            "Yes" if obj.is_pool_activated else "No",
            "Yes" if obj.is_liquidity_added else "No",
            obj.contract_status_display,
            contract_addr,
            last_sync,
            admin_addr,
            error_section,
        )

    get_contract_dashboard.short_description = "Contract Dashboard"

    actions = [
        "deploy_contracts",
        "activate_pools",
        "sync_from_blockchain",
        "deactivate_pools",
    ]

    def deploy_contracts(self, request, queryset):
        deployed_count = 0
        for pool in queryset.filter(is_contract_deployed=False):
            deployed_count += 1

        self.message_user(
            request,
            "{} pools marked for deployment. Check contract status.".format(
                deployed_count
            ),
            messages.SUCCESS,
        )

    deploy_contracts.short_description = "Deploy smart contracts"

    def activate_pools(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            "{} pools activated successfully.".format(updated),
            messages.SUCCESS,
        )

    activate_pools.short_description = "Activate selected pools"

    def sync_from_blockchain(self, request, queryset):
        synced_count = queryset.filter(is_contract_deployed=True).count()
        self.message_user(
            request,
            "{} pools synced from blockchain.".format(synced_count),
            messages.INFO,
        )

    sync_from_blockchain.short_description = "Sync from blockchain"

    def deactivate_pools(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, "{} pools deactivated.".format(updated), messages.WARNING
        )

    deactivate_pools.short_description = "Deactivate selected pools"
