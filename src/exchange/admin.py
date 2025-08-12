from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Q, Count, Sum, Avg
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from unfold.admin import ModelAdmin
from decimal import Decimal
import csv
from django.http import HttpResponse
from django.utils import timezone

from .models import Network, Token, Pool, ExchangeOrder


class TokenInline(admin.TabularInline):
    model = Token
    extra = 0
    fields = ("name", "short_name", "decimals", "is_active", "image_preview")
    readonly_fields = ("image_preview", "created_at")

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, "url"):
            return format_html(
                '<img src="{}" width="25" height="25" style="border-radius: 50%;" />',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Icon"


@admin.register(Network)
class NetworkAdmin(ModelAdmin):
    list_display = (
        "name",
        "short_name",
        "network_type_badge",
        "status_badge",
        "tokens_count",
        "pools_count",
        "health_indicator",
        "created_at",
    )
    list_display_links = ("name", "short_name")
    search_fields = ("name", "short_name")
    list_filter = ("is_active", "is_testnet", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_network_dashboard")

    fieldsets = (
        (
            "🌐 Basic Information",
            {"fields": ("name", "short_name"), "classes": ("wide",)},
        ),
        (
            "⚙️ Configuration",
            {"fields": ("is_active", "is_testnet"), "classes": ("wide",)},
        ),
        (
            "📊 Analytics Dashboard",
            {
                "fields": ("get_network_dashboard",),
                "classes": ("collapse",),
            },
        ),
        (
            "🗂️ Metadata",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [TokenInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("tokens")
            .annotate(
                tokens_count=Count("tokens"),
                active_tokens_count=Count("tokens", filter=Q(tokens__is_active=True)),
            )
        )

    def network_type_badge(self, obj):
        if obj.is_testnet:
            return format_html(
                '<span class="badge" style="background: #ff9800; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">🧪 TESTNET</span>'
            )
        return format_html(
            '<span class="badge" style="background: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">🚀 MAINNET</span>'
        )

    network_type_badge.short_description = "Type"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">🟢 Active</span>'
            )
        return format_html(
            '<span style="color: #f44336; font-weight: bold;">🔴 Inactive</span>'
        )

    status_badge.short_description = "Status"

    def tokens_count(self, obj):
        count = getattr(obj, "tokens_count", 0)
        if count > 0:
            url = reverse(
                "admin:exchange_token_changelist"
            ) + "?network__id__exact={}".format(obj.id)
            return format_html(
                '<a href="{}" style="color: #2196f3; font-weight: bold;">📄 {}</a>',
                url,
                count,
            )
        return "—"

    tokens_count.short_description = "Tokens"

    def pools_count(self, obj):
        pools_count = (
            Pool.objects.filter(Q(token1__network=obj) | Q(token2__network=obj))
            .distinct()
            .count()
        )

        if pools_count > 0:
            return format_html(
                '<span style="color: #673ab7; font-weight: bold;">💧 {}</span>',
                pools_count,
            )
        return "—"

    pools_count.short_description = "Pools"

    def health_indicator(self, obj):
        tokens_count = getattr(obj, "tokens_count", 0)
        active_tokens = getattr(obj, "active_tokens_count", 0)

        if not obj.is_active:
            return format_html('<span style="color: #9e9e9e;">⏸️ Disabled</span>')
        elif active_tokens == 0:
            return format_html('<span style="color: #f44336;">⚠️ No Tokens</span>')
        elif tokens_count > 5:
            return format_html('<span style="color: #4caf50;">💪 Excellent</span>')
        elif tokens_count > 2:
            return format_html('<span style="color: #ff9800;">👍 Good</span>')
        else:
            return format_html('<span style="color: #ffc107;">🔧 Growing</span>')

    health_indicator.short_description = "Health"

    def get_network_dashboard(self, obj):
        if not obj.pk:
            return format_html(
                '<div style="color: #666;">Save network to see dashboard</div>'
            )

        tokens = obj.tokens.all()
        active_tokens = tokens.filter(is_active=True)
        pools = Pool.objects.filter(
            Q(token1__network=obj) | Q(token2__network=obj)
        ).distinct()

        # Calculate network statistics
        total_volume = pools.aggregate(
            total=Sum("token1_amount")
            or Decimal("0") + Sum("token2_amount")
            or Decimal("0")
        )["total"] or Decimal("0")

        add_token_url = reverse("admin:exchange_token_add") + "?network={}".format(
            obj.id
        )
        view_pools_url = reverse(
            "admin:exchange_pool_changelist"
        ) + "?token1__network__id__exact={}".format(obj.id)

        return format_html(
            """
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #333;">📊 Network Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 10px; border-radius: 6px; border-left: 4px solid #2196f3;">
                        <strong style="color: #2196f3;">📄 Tokens</strong><br>
                        Total: {}<br>
                        Active: {}<br>
                        Health: {}
                    </div>

                    <div style="background: white; padding: 10px; border-radius: 6px; border-left: 4px solid #673ab7;">
                        <strong style="color: #673ab7;">💧 Liquidity</strong><br>
                        Pools: {}<br>
                        TVL: ${}<br>
                        Status: {}
                    </div>
                </div>

                <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 6px;">
                    <strong>🎯 Quick Actions:</strong><br>
                    <a href="{}" style="color: #4caf50; text-decoration: none;">➕ Add Token</a> | 
                    <a href="{}" style="color: #2196f3; text-decoration: none;">🔍 View Pools</a>
                </div>
            </div>
        """,
            tokens.count(),
            active_tokens.count(),
            "Good" if active_tokens.count() > 0 else "Needs Tokens",
            pools.count(),
            "{:,.0f}".format(total_volume),
            "Active" if pools.filter(is_active=True).exists() else "Inactive",
            add_token_url,
            view_pools_url,
        )

    get_network_dashboard.short_description = "Network Dashboard"


@admin.register(Token)
class TokenAdmin(ModelAdmin):
    list_display = (
        "token_display",
        "network_badge",
        "decimals",
        "status_badge",
        "pools_count",
        "volume_indicator",
        "image_preview",
        "created_at",
    )
    list_display_links = ("token_display",)
    search_fields = ("name", "short_name", "network__name", "network__short_name")
    list_filter = ("is_active", "network", "decimals", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_token_dashboard")

    fieldsets = (
        (
            "🪙 Token Information",
            {"fields": ("name", "short_name", "network"), "classes": ("wide",)},
        ),
        (
            "🎨 Display & Config",
            {"fields": ("image", "decimals", "is_active"), "classes": ("wide",)},
        ),
        (
            "📈 Token Dashboard",
            {
                "fields": ("get_token_dashboard",),
                "classes": ("collapse",),
            },
        ),
        (
            "🗂️ Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("network")
            .annotate(pools_count=Count("pools_as_token1") + Count("pools_as_token2"))
        )

    def token_display(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<strong style="color: #333;">{}</strong>'
            '<span style="color: #666; margin-left: 8px; font-size: 12px;">({})</span>'
            "</div>",
            obj.name,
            obj.short_name,
        )

    token_display.short_description = "Token"

    def network_badge(self, obj):
        if not obj.network:
            return format_html('<span style="color: #f44336;">❌ No Network</span>')

        url = reverse("admin:exchange_network_change", args=[obj.network.id])
        badge_color = "#4caf50" if obj.network.is_active else "#9e9e9e"
        network_icon = "🧪" if obj.network.is_testnet else "🌐"

        return format_html(
            '<a href="{}" style="text-decoration: none;">'
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px;">'
            "{} {}"
            "</span></a>",
            url,
            badge_color,
            network_icon,
            obj.network.short_name,
        )

    network_badge.short_description = "Network"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">🟢 Active</span>'
            )
        return format_html(
            '<span style="color: #f44336; font-weight: bold;">🔴 Inactive</span>'
        )

    status_badge.short_description = "Status"

    def pools_count(self, obj):
        count = getattr(obj, "pools_count", 0)
        if count > 0:
            return format_html(
                '<span style="color: #673ab7; font-weight: bold;">💧 {}</span>', count
            )
        return "—"

    pools_count.short_description = "Pools"

    def volume_indicator(self, obj):
        # Calculate total volume from pools this token participates in
        pools = Pool.objects.filter(Q(token1=obj) | Q(token2=obj), is_active=True)
        total_volume = Decimal("0")

        for pool in pools:
            if pool.token1_amount and pool.token2_amount:
                total_volume += pool.token1_amount + pool.token2_amount

        if total_volume > 1000000:
            volume_k = total_volume / 1000
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">📈 ${}</span>',
                "{:,.0f}K".format(volume_k),
            )
        elif total_volume > 10000:
            volume_k = total_volume / 1000
            return format_html(
                '<span style="color: #ff9800;">📊 ${}</span>',
                "{:,.0f}K".format(volume_k),
            )
        elif total_volume > 0:
            return format_html(
                '<span style="color: #2196f3;">💹 ${}</span>',
                "{:,.0f}".format(total_volume),
            )
        return "—"

    volume_indicator.short_description = "Volume"

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, "url"):
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%; border: 2px solid #ddd;" />',
                obj.image.url,
            )
        return format_html(
            '<div style="width: 30px; height: 30px; background: #f0f0f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px;">🪙</div>'
        )

    image_preview.short_description = "Icon"

    def get_token_dashboard(self, obj):
        if not obj.pk:
            return format_html(
                '<div style="color: #666;">Save token to see dashboard</div>'
            )

        pools = Pool.objects.filter(Q(token1=obj) | Q(token2=obj))
        active_pools = pools.filter(is_active=True)
        orders = ExchangeOrder.objects.filter(Q(give_token=obj) | Q(receive_token=obj))
        completed_orders = orders.filter(status="completed")

        success_rate = 0
        if orders.count() > 0:
            success_rate = int((completed_orders.count() / orders.count()) * 100)

        return format_html(
            """
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #333;">📈 Token Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 10px; border-radius: 6px; border-left: 4px solid #673ab7;">
                        <strong style="color: #673ab7;">💧 Liquidity</strong><br>
                        Total Pools: {}<br>
                        Active: {}<br>
                        Health: {}
                    </div>

                    <div style="background: white; padding: 10px; border-radius: 6px; border-left: 4px solid #4caf50;">
                        <strong style="color: #4caf50;">📊 Trading</strong><br>
                        Total Orders: {}<br>
                        Completed: {}<br>
                        Success Rate: {}%
                    </div>

                    <div style="background: white; padding: 10px; border-radius: 6px; border-left: 4px solid #ff9800;">
                        <strong style="color: #ff9800;">⚙️ Settings</strong><br>
                        Decimals: {}<br>
                        Network: {}<br>
                        Status: {}
                    </div>
                </div>
            </div>
        """,
            pools.count(),
            active_pools.count(),
            "Good" if active_pools.count() > 0 else "Needs Pools",
            orders.count(),
            completed_orders.count(),
            success_rate,
            obj.decimals,
            obj.network.short_name if obj.network else "None",
            "Active" if obj.is_active else "Inactive",
        )

    get_token_dashboard.short_description = "Token Dashboard"


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
        ("💧 Pool Information", {"fields": ("name",), "classes": ("wide",)}),
        (
            "🪙 Token Configuration",
            {
                "fields": (
                    ("token1", "token1_amount"),
                    ("token2", "token2_amount"),
                ),
                "classes": ("wide",),
            },
        ),
        (
            "⚙️ Pool Settings",
            {"fields": ("fee_percentage", "is_active"), "classes": ("wide",)},
        ),
        (
            "🔗 Smart Contract",
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
            "👨‍💼 Administration",
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
            "📊 Analytics",
            {
                "fields": ("get_pool_dashboard", "get_contract_dashboard"),
                "classes": ("collapse",),
            },
        ),
        (
            "🗂️ Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("token1", "token2", "token1__network", "token2__network")
            .annotate(
                orders_count=Count("orders"),
                completed_orders=Count("orders", filter=Q(orders__status="completed")),
            )
        )

    def pool_display(self, obj):
        if not (obj.token1 and obj.token2):
            return format_html('<span style="color: #f44336;">❌ Incomplete</span>')

        token1_url = reverse("admin:exchange_token_change", args=[obj.token1.id])
        token2_url = reverse("admin:exchange_token_change", args=[obj.token2.id])

        return format_html(
            '<div style="font-weight: bold;">'
            '<a href="{}" style="color: #2196f3; text-decoration: none;">{}</a>'
            '<span style="color: #666; margin: 0 5px;">/</span>'
            '<a href="{}" style="color: #2196f3; text-decoration: none;">{}</a>'
            "</div>",
            token1_url,
            obj.token1.short_name,
            token2_url,
            obj.token2.short_name,
        )

    pool_display.short_description = "Pool Pair"

    def network_info(self, obj):
        if obj.token1 and obj.token1.network:
            network = obj.token1.network
            icon = "🧪" if network.is_testnet else "🌐"
            return format_html(
                '<span style="font-size: 11px; color: #666;">{} {}</span>',
                icon,
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
            return format_html('<span style="color: #f44336;">⚠️ Not Set</span>')

        total_value = obj.token1_amount + obj.token2_amount
        balance_ratio = (
            (obj.token1_amount / total_value * 100) if total_value > 0 else 0
        )

        # Color based on balance (green if well balanced)
        balance_color = (
            "#4caf50"
            if 30 <= balance_ratio <= 70
            else "#ff9800"
            if 20 <= balance_ratio <= 80
            else "#f44336"
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
            "fully_operational": ("🟢", "#4caf50", "Operational"),
            "activated": ("🟡", "#ff9800", "Activated"),
            "deployed": ("🔵", "#2196f3", "Deployed"),
            "failed": ("🔴", "#f44336", "Failed"),
            "pending": ("⏳", "#9e9e9e", "Pending"),
        }

        icon, color, text = status_config.get(status, ("❓", "#000", "Unknown"))

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            text,
        )

    contract_status_badge.short_description = "Contract"

    def liquidity_health(self, obj):
        # Безопасная проверка на None
        if not (obj.token1_amount and obj.token2_amount):
            return format_html('<span style="color: #9e9e9e;">—</span>')

        total_liquidity = obj.token1_amount + obj.token2_amount
        orders_count = getattr(obj, "orders_count", 0) or 0

        # Health calculation based on liquidity and activity
        if total_liquidity > 100000 and orders_count > 10:
            return format_html('<span style="color: #4caf50;">💪 Excellent</span>')
        elif total_liquidity > 10000 and orders_count > 5:
            return format_html('<span style="color: #8bc34a;">👍 Good</span>')
        elif total_liquidity > 1000:
            return format_html('<span style="color: #ff9800;">⚡ Growing</span>')
        else:
            return format_html('<span style="color: #f44336;">🔧 Weak</span>')

    liquidity_health.short_description = "Health"

    def volume_24h(self, obj):
        # Mock 24h volume calculation (you might want to implement actual calculation)
        orders_count = getattr(obj, "completed_orders", 0) or 0
        if orders_count > 50:
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">🔥 High</span>'
            )
        elif orders_count > 10:
            return format_html('<span style="color: #ff9800;">📈 Medium</span>')
        elif orders_count > 0:
            return format_html('<span style="color: #2196f3;">📊 Low</span>')
        return "—"

    volume_24h.short_description = "24h Vol"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">🟢 Active</span>'
            )
        return format_html(
            '<span style="color: #f44336; font-weight: bold;">🔴 Inactive</span>'
        )

    status_badge.short_description = "Status"

    def get_pool_dashboard(self, obj):
        if not obj.pk:
            return format_html(
                '<div style="color: #666;">Save pool to see dashboard</div>'
            )

        orders = ExchangeOrder.objects.filter(pool=obj)
        total_orders = orders.count()
        completed_orders = orders.filter(status="completed").count()
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
                <h3 style="margin-top: 0; color: #333;">💧 Pool Analytics Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #4caf50;">
                        <strong style="color: #4caf50;">📊 Trading Stats</strong><br>
                        Total Orders: {}<br>
                        Completed: {}<br>
                        Success Rate: {}%
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #2196f3;">
                        <strong style="color: #2196f3;">💰 Liquidity</strong><br>
                        TVL: ${}<br>
                        Fee Rate: {}%<br>
                        K Constant: {}
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #ff9800;">
                        <strong style="color: #ff9800;">📈 Performance</strong><br>
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
                <strong style="color: #f44336;">⚠️ Deployment Error:</strong><br>
                <code>{}</code>
            </div>
            """.format(obj.deployment_error)

        return format_html(
            """
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #333;">🔗 Smart Contract Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #673ab7;">
                        <strong style="color: #673ab7;">📋 Contract Status</strong><br>
                        Deployed: {}<br>
                        Activated: {}<br>
                        Liquidity: {}<br>
                        Overall: {}
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #e91e63;">
                        <strong style="color: #e91e63;">🔧 Technical</strong><br>
                        Address: {}<br>
                        Last Sync: {}<br>
                        Admin: {}
                    </div>
                </div>

                {}
            </div>
        """,
            "✅ Yes" if obj.is_contract_deployed else "❌ No",
            "✅ Yes" if obj.is_pool_activated else "❌ No",
            "✅ Yes" if obj.is_liquidity_added else "❌ No",
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

    deploy_contracts.short_description = "🚀 Deploy smart contracts"

    def activate_pools(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            "✅ {} pools activated successfully.".format(updated),
            messages.SUCCESS,
        )

    activate_pools.short_description = "✅ Activate selected pools"

    def sync_from_blockchain(self, request, queryset):
        # Mock sync action - implement actual blockchain sync
        synced_count = queryset.filter(is_contract_deployed=True).count()
        self.message_user(
            request,
            "🔄 {} pools synced from blockchain.".format(synced_count),
            messages.INFO,
        )

    sync_from_blockchain.short_description = "🔄 Sync from blockchain"

    def deactivate_pools(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, "🔴 {} pools deactivated.".format(updated), messages.WARNING
        )

    deactivate_pools.short_description = "🔴 Deactivate selected pools"


@admin.register(ExchangeOrder)
class ExchangeOrderAdmin(ModelAdmin):
    list_display = (
        "order_number_display",
        "status_badge",
        "user_info",
        "exchange_summary",
        "pool_info",
        "financial_summary",
        "time_info",
    )
    list_display_links = ("order_number_display", "exchange_summary")
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
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "order_short_number",
        "created_at",
        "updated_at",
        "get_order_dashboard",
        "get_technical_details",
    )

    fieldsets = (
        (
            "🆔 Order Information",
            {"fields": ("id", "order_short_number", "status"), "classes": ("wide",)},
        ),
        ("👤 User Details", {"fields": ("email",), "classes": ("wide",)}),
        (
            "💱 Exchange Details",
            {
                "fields": (
                    ("give_token", "give_amount"),
                    ("receive_token", "receive_amount"),
                    "pool",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "💰 Financial Details",
            {"fields": ("exchange_rate", "fee_percentage"), "classes": ("wide",)},
        ),
        ("🔗 Transaction", {"fields": ("transaction_hash",), "classes": ("collapse",)}),
        (
            "📊 Analytics",
            {
                "fields": ("get_order_dashboard", "get_technical_details"),
                "classes": ("collapse",),
            },
        ),
        (
            "🗂️ Metadata",
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
        status_color = {
            "pending": "#ff9800",
            "processing": "#2196f3",
            "completed": "#4caf50",
            "cancelled": "#9e9e9e",
            "failed": "#f44336",
        }.get(obj.status, "#000")

        return format_html(
            '<div style="font-weight: bold;">'
            '<span style="color: {};">#{}</span>'
            "</div>",
            status_color,
            obj.order_short_number,
        )

    order_number_display.short_description = "Order #"

    def status_badge(self, obj):
        status_config = {
            "pending": ("⏳", "#ff9800", "Pending"),
            "processing": ("🔄", "#2196f3", "Processing"),
            "completed": ("✅", "#4caf50", "Completed"),
            "cancelled": ("❌", "#9e9e9e", "Cancelled"),
            "failed": ("🚫", "#f44336", "Failed"),
        }

        icon, color, text = status_config.get(obj.status, ("❓", "#000", "Unknown"))

        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 4px 8px; background: {}15; border-radius: 12px; font-size: 11px;">'
            "{} {}"
            "</span>",
            color,
            color,
            icon,
            text,
        )

    status_badge.short_description = "Status"

    def user_info(self, obj):
        return format_html(
            '<div style="font-size: 12px;">'
            '<div style="font-weight: bold; color: #333;">👤 {}</div>'
            "</div>",
            obj.email,
        )

    user_info.short_description = "User"

    def exchange_summary(self, obj):
        return format_html(
            '<div style="text-align: center; font-size: 12px;">'
            '<div style="color: #f44336; font-weight: bold;">- {} {}</div>'
            '<div style="color: #666; margin: 2px 0;">↓</div>'
            '<div style="color: #4caf50; font-weight: bold;">+ {} {}</div>'
            "</div>",
            "{:,.2f}".format(obj.give_amount),
            obj.give_token.short_name,
            "{:,.4f}".format(obj.receive_amount),
            obj.receive_token.short_name,
        )

    exchange_summary.short_description = "Exchange"

    def pool_info(self, obj):
        if not obj.pool:
            return format_html('<span style="color: #f44336;">❌ No Pool</span>')

        url = reverse("admin:exchange_pool_change", args=[obj.pool.id])
        return format_html(
            '<a href="{}" style="color: #673ab7; text-decoration: none; font-size: 12px;">'
            "💧 {}"
            "</a>",
            url,
            obj.pool.name,
        )

    pool_info.short_description = "Pool"

    def financial_summary(self, obj):
        fee_amount = obj.give_amount * (obj.fee_percentage / 100)
        return format_html(
            '<div style="font-size: 11px;">'
            "<div>Rate: {}</div>"
            "<div>Fee: {}% (${})</div>"
            "</div>",
            "{:.4f}".format(obj.exchange_rate),
            "{:.2f}".format(obj.fee_percentage),
            "{:.2f}".format(fee_amount),
        )

    financial_summary.short_description = "Financial"

    def time_info(self, obj):
        if not obj.created_at:
            return "—"

        time_diff = timezone.now() - obj.created_at

        if time_diff.seconds < 60:
            time_str = "{}s ago".format(time_diff.seconds)
        elif time_diff.seconds < 3600:
            time_str = "{}m ago".format(time_diff.seconds // 60)
        elif time_diff.days == 0:
            time_str = "{}h ago".format(time_diff.seconds // 3600)
        else:
            time_str = "{}d ago".format(time_diff.days)

        return format_html(
            '<div style="font-size: 11px; color: #666;">'
            "<div>{}</div>"
            "<div>{}</div>"
            "</div>",
            obj.created_at.strftime("%m/%d %H:%M"),
            time_str,
        )

    time_info.short_description = "Time"

    def get_order_dashboard(self, obj):
        if not obj.pk:
            return format_html(
                '<div style="color: #666;">Save order to see dashboard</div>'
            )

        # Безопасная проверка на None для дат
        if obj.created_at and obj.updated_at:
            processing_time = obj.updated_at - obj.created_at
            processing_time_str = str(processing_time).split(".")[0]
            age_days = (timezone.now() - obj.created_at).days
        else:
            processing_time_str = "Not calculated"
            age_days = 0

        value_usd = float(obj.give_amount) if obj.give_amount else 0
        fee_amount = (
            obj.give_amount * (obj.fee_percentage / 100)
            if obj.give_amount and obj.fee_percentage
            else 0
        )

        created_time = (
            obj.created_at.strftime("%m/%d %H:%M") if obj.created_at else "Not set"
        )

        return format_html(
            """
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #333;">📊 Order Analytics Dashboard</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #2196f3;">
                        <strong style="color: #2196f3;">⏱️ Timing</strong><br>
                        Created: {}<br>
                        Processing: {}<br>
                        Age: {} days
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #4caf50;">
                        <strong style="color: #4caf50;">💰 Financial</strong><br>
                        Value: ${}<br>
                        Fee: ${}<br>
                        Size: {}
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #ff9800;">
                        <strong style="color: #ff9800;">📈 Performance</strong><br>
                        Status: {}<br>
                        Network: {}<br>
                        Health: {}
                    </div>
                </div>
            </div>
        """,
            created_time,
            processing_time_str,
            age_days,
            "{:,.2f}".format(value_usd),
            "{:.4f}".format(fee_amount),
            "Large" if value_usd > 10000 else "Medium" if value_usd > 1000 else "Small",
            obj.get_status_display(),
            obj.give_token.network.short_name
            if obj.give_token and obj.give_token.network
            else "Unknown",
            "Good"
            if obj.status == "completed"
            else "Processing"
            if obj.status in ["pending", "processing"]
            else "Issue",
        )

    get_order_dashboard.short_description = "Order Dashboard"

    def get_technical_details(self, obj):
        """Технические детали заказа"""
        if not obj.pk:
            return format_html(
                '<div style="color: #666;">Save order to see technical details</div>'
            )

        # Расчет слипейджа и других технических параметров
        current_pool_rate = None
        slippage = 0

        if (
            obj.pool
            and obj.pool.token1_amount
            and obj.pool.token2_amount
            and obj.give_token
        ):
            if obj.give_token == obj.pool.token1:
                current_pool_rate = obj.pool.exchange_rate_token1_to_token2
            else:
                current_pool_rate = obj.pool.exchange_rate_token2_to_token1

            if current_pool_rate and current_pool_rate > 0 and obj.exchange_rate:
                slippage = (
                    (obj.exchange_rate - current_pool_rate) / current_pool_rate
                ) * 100

        tx_hash = (
            obj.transaction_hash[:16] + "..." if obj.transaction_hash else "Pending"
        )
        pool_rate = current_pool_rate or 0
        order_rate = obj.exchange_rate or 0
        fee_bps = int((obj.fee_percentage or 0) * 100)  # Convert to basis points

        created_time = (
            obj.created_at.strftime("%Y-%m-%d %H:%M") if obj.created_at else "Not set"
        )

        give_amount = obj.give_amount or 0
        receive_amount = obj.receive_amount or 0
        give_token_name = obj.give_token.short_name if obj.give_token else "Unknown"
        receive_token_name = (
            obj.receive_token.short_name if obj.receive_token else "Unknown"
        )
        pool_name = obj.pool.name if obj.pool else "No Pool"

        return format_html(
            """
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #333;">🔧 Technical Details</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #9c27b0;">
                        <strong style="color: #9c27b0;">📋 Order Specs</strong><br>
                        Order ID: {}<br>
                        Transaction: {}<br>
                        Slippage: {}%<br>
                        Rate Variance: {}
                    </div>

                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #607d8b;">
                        <strong style="color: #607d8b;">🎯 Execution</strong><br>
                        Pool Rate: {}<br>
                        Order Rate: {}<br>
                        Fee Basis: {} bps<br>
                        Gas Estimate: Low
                    </div>
                </div>

                <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 6px; border-left: 4px solid #795548;">
                    <strong style="color: #795548;">🔍 Debug Info:</strong><br>
                    <code style="font-size: 12px; color: #666;">
                        Give: {} {} → Receive: {} {}<br>
                        Pool: {} (Fee: {}%)<br>
                        User: {} | Created: {}
                    </code>
                </div>
            </div>
        """,
            obj.order_short_number,
            tx_hash,
            "{:.3f}".format(slippage),
            "Good"
            if abs(slippage) < 1
            else "High"
            if abs(slippage) < 5
            else "Critical",
            "{:.6f}".format(pool_rate),
            "{:.6f}".format(order_rate),
            fee_bps,
            "{:,.0f}".format(give_amount),
            give_token_name,
            "{:,.4f}".format(receive_amount),
            receive_token_name,
            pool_name,
            obj.fee_percentage or 0,
            obj.email or "No email",
            created_time,
        )

    get_technical_details.short_description = "Technical Details"

    actions = [
        "mark_as_processing",
        "mark_as_completed",
        "mark_as_cancelled",
        "mark_as_failed",
        "export_to_csv",
        "send_status_emails",
    ]

    def mark_as_processing(self, request, queryset):
        updated = queryset.filter(status="pending").update(status="processing")
        self.message_user(
            request, "🔄 {} orders marked as processing.".format(updated), messages.INFO
        )

    mark_as_processing.short_description = "🔄 Mark as processing"

    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status__in=["pending", "processing"]).update(
            status="completed"
        )
        self.message_user(
            request,
            "✅ {} orders marked as completed.".format(updated),
            messages.SUCCESS,
        )

    mark_as_completed.short_description = "✅ Mark as completed"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status__in=["pending", "processing"]).update(
            status="cancelled"
        )
        self.message_user(
            request,
            "❌ {} orders marked as cancelled.".format(updated),
            messages.WARNING,
        )

    mark_as_cancelled.short_description = "❌ Mark as cancelled"

    def mark_as_failed(self, request, queryset):
        updated = queryset.filter(status__in=["pending", "processing"]).update(
            status="failed"
        )
        self.message_user(
            request, "🚫 {} orders marked as failed.".format(updated), messages.ERROR
        )

    mark_as_failed.short_description = "🚫 Mark as failed"

    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="exchange_orders.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Order ID",
                "Status",
                "Email",
                "Give Token",
                "Give Amount",
                "Receive Token",
                "Receive Amount",
                "Exchange Rate",
                "Fee %",
                "Pool",
                "Created At",
                "Transaction Hash",
            ]
        )

        for order in queryset:
            writer.writerow(
                [
                    order.order_short_number,
                    order.get_status_display(),
                    order.email or "",
                    order.give_token.short_name if order.give_token else "",
                    order.give_amount or 0,
                    order.receive_token.short_name if order.receive_token else "",
                    order.receive_amount or 0,
                    order.exchange_rate or 0,
                    order.fee_percentage or 0,
                    order.pool.name if order.pool else "",
                    order.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if order.created_at
                    else "",
                    order.transaction_hash or "",
                ]
            )

        self.message_user(request, "📊 Exported {} orders to CSV.".format(queryset.count()), messages.SUCCESS)
        return response
    export_to_csv.short_description = "📊 Export to CSV"

    def send_status_emails(self, request, queryset):
        # Mock email sending - implement actual email logic
        email_count = queryset.count()
        self.message_user(
            request,
            "📧 {} status emails queued for sending.".format(email_count),
            messages.INFO
        )
    send_status_emails.short_description = "📧 Send status emails"