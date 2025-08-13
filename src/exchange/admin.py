from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Q
from django.urls import reverse
from unfold.admin import ModelAdmin
from decimal import Decimal
from django.contrib import messages

from .models import Network, Token, Pool, ExchangeOrder


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
    )

    fieldsets = (
        ("Pool Information", {"fields": ("name",), "classes": ("wide",)}),
        (
            "Token Configuration",
            {
                "fields": (
                    ("token1", "token1_amount"),
                    ("token2", "token2_amount"),
                ),
                "classes": ("wide",),
            },
        ),
        (
            "Pool Settings",
            {"fields": ("fee_percentage", "is_active"), "classes": ("wide",)},
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
                    "deployment_tx_hash",
                    "activation_tx_hash",
                    "liquidity_tx_hash",
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

    def pool_display(self, obj):
        if not (obj.token1 and obj.token2):
            return format_html('<span style="color: #f44336;">Incomplete</span>')

        # URL для редактирования этого Pool объекта
        edit_url = reverse("admin:exchange_pool_change", args=[obj.pk])

        # Ссылки на токены
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

        # Color based on balance (green if well balanced)
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

        # Добавляем ссылку на TON explorer если контракт задеплоен
        if obj.contract_address and obj.is_contract_deployed:
            explorer_url = f"https://tonscan.org/address/{obj.contract_address}"
            return format_html(
                "<div>"
                '<span style="color: {}; font-weight: bold;">{}</span><br>'
                '<a href="{}" target="_blank" style="font-size: 10px; color: #666;">View on TONScan</a>'
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
        # Безопасная проверка на None
        if not (obj.token1_amount and obj.token2_amount):
            return format_html('<span style="color: #9e9e9e;">—</span>')

        total_liquidity = obj.token1_amount + obj.token2_amount

        # Попытка получить количество заказов (с обработкой ошибок)
        try:
            orders_count = ExchangeOrder.objects.filter(pool=obj).count()
        except:
            orders_count = 0

        # Health calculation based on liquidity and activity
        if total_liquidity > 100000 and orders_count > 10:
            return format_html('<span style="color: #4caf50;">Excellent</span>')
        elif total_liquidity > 10000 and orders_count > 5:
            return format_html('<span style="color: #8bc34a;">Good</span>')
        elif total_liquidity > 1000:
            return format_html('<span style="color: #ff9800;">Growing</span>')
        else:
            return format_html('<span style="color: #f44336;">Weak</span>')

    liquidity_health.short_description = "Health"

    def volume_24h(self, obj):
        # Mock 24h volume calculation
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

        # Безопасная проверка на None для сумм
        tvl = 0
        k_constant = 0
        exchange_rate = 0

        if obj.token1_amount and obj.token2_amount:
            tvl = obj.token1_amount + obj.token2_amount
            k_constant = obj.token1_amount * obj.token2_amount
            exchange_rate = obj.exchange_rate_token1_to_token2

        return format_html(
            """
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #333;">Pool Analytics Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #4caf50;">
                        <strong style="color: #4caf50;">Trading Stats</strong><br>
                        Total Orders: {}<br>
                        Completed: {}<br>
                        Success Rate: {}%
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #2196f3;">
                        <strong style="color: #2196f3;">Liquidity</strong><br>
                        TVL: ${}<br>
                        Fee Rate: {}%<br>
                        K Constant: {}
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #ff9800;">
                        <strong style="color: #ff9800;">Performance</strong><br>
                        Exchange Rate: {}<br>
                        Pool Health: {}<br>
                        Volume Rank: {}
                    </div>
                </div>
            </div>
        """,
            total_orders,
            completed_orders,
            "{:.1f}".format(success_rate),
            "{:,.0f}".format(tvl),
            obj.fee_percentage or 0,
            "{:,.0f}".format(k_constant),
            "{:.4f}".format(exchange_rate),
            "Good" if success_rate > 80 else "Average" if success_rate > 50 else "Poor",
            "High" if total_orders > 100 else "Medium" if total_orders > 10 else "Low",
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
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #333;">Smart Contract Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #673ab7;">
                        <strong style="color: #673ab7;">Contract Status</strong><br>
                        Deployed: {}<br>
                        Activated: {}<br>
                        Liquidity: {}<br>
                        Overall: {}
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #e91e63;">
                        <strong style="color: #e91e63;">Technical</strong><br>
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
        # Mock deployment action - implement actual deployment logic
        deployed_count = 0
        for pool in queryset.filter(is_contract_deployed=False):
            # Add your deployment logic here
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
        # Mock sync action - implement actual blockchain sync
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


@admin.register(ExchangeOrder)
class ExchangeOrderAdmin(ModelAdmin):
    list_display = (
        "order_number_display",
        "status_display",
        "user_email",
        "exchange_summary_display",
        "exchange_rate_display",
        "fee_display",
        "pool_link",
        "created_at",
    )
    list_display_links = ("order_number_display", "exchange_summary_display")
    search_fields = (
        "email",
        "transaction_hash",
        "give_token__name",
        "give_token__short_name",
        "receive_token__name",
        "receive_token__short_name",
    )
    list_filter = (
        "status",
        ("give_token", admin.RelatedOnlyFieldListFilter),
        ("receive_token", admin.RelatedOnlyFieldListFilter),
        ("pool", admin.RelatedOnlyFieldListFilter),
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "order_short_number",
        "created_at",
        "updated_at",
        "get_order_analytics",
        "get_financial_analytics",
    )

    fieldsets = (
        ("Basic Information", {"fields": ("id", "order_short_number", "status")}),
        ("User Details", {"fields": ("email",)}),
        (
            "Exchange Details",
            {
                "fields": (
                    ("give_token", "give_amount"),
                    ("receive_token", "receive_amount"),
                    "pool",
                )
            },
        ),
        ("Financial Details", {"fields": ("exchange_rate", "fee_percentage")}),
        ("Transaction", {"fields": ("transaction_hash",), "classes": ("collapse",)}),
        (
            "Analytics",
            {
                "fields": ("get_order_analytics", "get_financial_analytics"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "give_token",
                "receive_token",
                "pool",
                "give_token__network",
                "receive_token__network",
            )
        )

    def order_number_display(self, obj):
        return format_html("<strong>#{}</strong>", obj.order_short_number)

    order_number_display.short_description = "Order #"

    def status_display(self, obj):
        status_colors = {
            "pending": "#ff9800",
            "processing": "#2196f3",
            "completed": "#4caf50",
            "cancelled": "#9e9e9e",
            "failed": "#f44336",
        }

        color = status_colors.get(obj.status, "#000000")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Status"

    def user_email(self, obj):
        return obj.email

    user_email.short_description = "Email"

    def exchange_summary_display(self, obj):
        give_formatted = "{:,.0f}".format(obj.give_amount)
        receive_formatted = "{:,.4f}".format(obj.receive_amount)

        return format_html(
            '<div style="text-align: center;">' "{} {}<br>" "↓<br>" "{} {}" "</div>",
            give_formatted,
            obj.give_token.short_name,
            receive_formatted,
            obj.receive_token.short_name,
        )

    exchange_summary_display.short_description = "Exchange"

    def exchange_rate_display(self, obj):
        rate_formatted = "{:,.4f}".format(obj.exchange_rate)
        return format_html(
            "1 {} = {} {}",
            obj.give_token.short_name,
            rate_formatted,
            obj.receive_token.short_name,
        )

    exchange_rate_display.short_description = "Rate"

    def fee_display(self, obj):
        return format_html("{}%", obj.fee_percentage)

    fee_display.short_description = "Fee"

    def pool_link(self, obj):
        if not obj.pool:
            return "No pool"

        url = reverse("admin:exchange_pool_change", args=[obj.pool.id])
        return format_html('<a href="{}">{}</a>', url, obj.pool.name)

    pool_link.short_description = "Pool"

    def get_order_analytics(self, obj):
        if not obj.pk:
            return "Save to see analytics"

        from django.utils import timezone
        import datetime

        # Time analysis
        processing_time = obj.updated_at - obj.created_at
        time_waiting = timezone.now() - obj.created_at

        # Size analysis
        total_value_usd = float(obj.give_amount)
        size_category = (
            "Large"
            if total_value_usd > 10000
            else "Medium" if total_value_usd > 1000 else "Small"
        )

        # Rate analysis
        current_pool_rate = (
            obj.pool.exchange_rate_token1_to_token2
            if obj.give_token == obj.pool.token1
            else obj.pool.exchange_rate_token2_to_token1
        )
        rate_difference = (
            (obj.exchange_rate - current_pool_rate) / current_pool_rate
        ) * 100

        return format_html(
            "<strong>Order Analytics:</strong><br>"
            "Order Value: ${:,.0f}<br>"
            "Order Size: {}<br>"
            "Processing Time: {}<br>"
            "Rate vs Current: {:.2f}%<br>"
            "Order Health: {}",
            total_value_usd,
            size_category,
            processing_time,
            rate_difference,
            (
                "Good"
                if obj.status == "completed"
                else "Pending" if obj.status == "pending" else "Issue"
            ),
        )

    get_order_analytics.short_description = "Order Analytics"

    def get_financial_analytics(self, obj):
        if not obj.pk:
            return "Save to see analytics"

        # Revenue calculation
        fee_revenue = obj.give_amount * (obj.fee_percentage / 100)
        operational_cost = Decimal("0.01")
        net_profit = fee_revenue - operational_cost
        profit_margin = (net_profit / fee_revenue) * 100 if fee_revenue > 0 else 0

        return format_html(
            "<strong>Financial Analytics:</strong><br>"
            "Fee Revenue: {:.4f} {}<br>"
            "Operational Cost: ${:.2f}<br>"
            "Net Profit: {:.4f} {}<br>"
            "Profit Margin: {:.1f}%<br>"
            "Financial Health: {}",
            fee_revenue,
            obj.give_token.short_name,
            operational_cost,
            net_profit,
            profit_margin,
            "Profitable" if net_profit > 0 else "Loss",
        )

    get_financial_analytics.short_description = "Financial Analytics"

    actions = [
        "mark_as_processing",
        "mark_as_completed",
        "mark_as_cancelled",
        "mark_as_failed",
        "export_selected_orders",
    ]

    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status="processing")
        self.message_user(request, f"{updated} orders marked as processing.")

    mark_as_processing.short_description = "Mark selected orders as processing"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status="completed")
        self.message_user(request, f"{updated} orders marked as completed.")

    mark_as_completed.short_description = "Mark selected orders as completed"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"{updated} orders marked as cancelled.")

    mark_as_cancelled.short_description = "Mark selected orders as cancelled"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status="failed")
        self.message_user(request, f"{updated} orders marked as failed.")

    mark_as_failed.short_description = "Mark selected orders as failed"

    def export_selected_orders(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="exchange_orders.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Order ID",
                "Status",
                "Email",
                "Wallet",
                "Give Token",
                "Give Amount",
                "Receive Token",
                "Receive Amount",
                "Exchange Rate",
                "Fee %",
                "Created At",
                "Transaction Hash",
            ]
        )

        for order in queryset:
            writer.writerow(
                [
                    order.order_short_number,
                    order.get_status_display(),
                    order.email,
                    order.give_token.short_name,
                    order.give_amount,
                    order.receive_token.short_name,
                    order.receive_amount,
                    order.exchange_rate,
                    order.fee_percentage,
                    order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    order.transaction_hash or "N/A",
                ]
            )

        self.message_user(request, f"Exported {queryset.count()} orders to CSV.")
        return response

    export_selected_orders.short_description = "Export selected orders to CSV"
