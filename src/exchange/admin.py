from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Q
from django.urls import reverse
from unfold.admin import ModelAdmin
from decimal import Decimal

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
        "name",
        "token_pair_display",
        "reserves_display",
        "exchange_rate_display",
        "fee_percentage",
        "status_display",
        "liquidity_info",
    )
    list_display_links = ("name", "token_pair_display")
    search_fields = (
        "name",
        "token1__name",
        "token1__short_name",
        "token2__name",
        "token2__short_name",
    )
    list_filter = (
        "is_active",
        ("token1__network", admin.RelatedOnlyFieldListFilter),
        ("token2__network", admin.RelatedOnlyFieldListFilter),
        "fee_percentage",
    )
    ordering = ("name",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "get_pool_analytics",
        "get_trading_analytics",
    )

    fieldsets = (
        ("Basic Information", {"fields": ("name",)}),
        (
            "Token Configuration",
            {
                "fields": (
                    ("token1", "token1_amount"),
                    ("token2", "token2_amount"),
                )
            },
        ),
        ("Pool Settings", {"fields": ("fee_percentage", "is_active")}),
        ("Administration", {"fields": ("admin_notes",), "classes": ("collapse",)}),
        (
            "Analytics",
            {
                "fields": ("get_pool_analytics", "get_trading_analytics"),
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

    def token_pair_display(self, obj):
        if not (obj.token1 and obj.token2):
            return "Tokens not set"

        token1_url = reverse("admin:exchange_token_change", args=[obj.token1.id])
        token2_url = reverse("admin:exchange_token_change", args=[obj.token2.id])
        return format_html(
            '<a href="{}">{}</a> / <a href="{}">{}</a>',
            token1_url,
            obj.token1.short_name,
            token2_url,
            obj.token2.short_name,
        )

    token_pair_display.short_description = "Token Pair"

    def reserves_display(self, obj):
        if not (
            obj.token1
            and obj.token2
            and obj.token1_amount is not None
            and obj.token2_amount is not None
        ):
            return "Reserves not set"

        token1_formatted = "{:,.0f}".format(obj.token1_amount)
        token2_formatted = "{:,.0f}".format(obj.token2_amount)

        return format_html(
            "{} {} / {} {}",
            token1_formatted,
            obj.token1.short_name,
            token2_formatted,
            obj.token2.short_name,
        )

    reserves_display.short_description = "Reserves"

    def exchange_rate_display(self, obj):
        if not (
            obj.token1
            and obj.token2
            and obj.token1_amount
            and obj.token2_amount
            and obj.token1_amount > 0
            and obj.token2_amount > 0
        ):
            return "Set reserves"

        rate1to2 = obj.exchange_rate_token1_to_token2
        rate1to2_formatted = "{:.4f}".format(rate1to2)

        return format_html(
            "1 {} = {} {}",
            obj.token1.short_name,
            rate1to2_formatted,
            obj.token2.short_name,
        )

    exchange_rate_display.short_description = "Rate"

    def status_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            "#4caf50" if obj.is_active else "#f44336",
            "Active" if obj.is_active else "Inactive",
        )

    status_display.short_description = "Status"

    def liquidity_info(self, obj):
        if obj.token1_amount is None or obj.token2_amount is None:
            return "No liquidity"

        total_liquidity = obj.token1_amount + obj.token2_amount
        if total_liquidity > 1000000:
            formatted_value = "{:,.0f}K".format(total_liquidity / 1000)
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">${}</span>',
                formatted_value,
            )
        elif total_liquidity > 100000:
            formatted_value = "{:,.0f}K".format(total_liquidity / 1000)
            return format_html("${}", formatted_value)
        else:
            formatted_value = "{:,.0f}".format(total_liquidity)
            return format_html("${}", formatted_value)

    liquidity_info.short_description = "Liquidity"

    def get_pool_analytics(self, obj):
        if not obj.pk:
            return "Save to see analytics"

        if not (
            obj.token1_amount
            and obj.token2_amount
            and obj.token1_amount > 0
            and obj.token2_amount > 0
        ):
            return "Set token amounts to see analytics"

        k_constant = obj.token1_amount * obj.token2_amount
        total_value = obj.token1_amount + obj.token2_amount
        ratio = (obj.token1_amount / (obj.token1_amount + obj.token2_amount)) * 100

        return format_html(
            "<strong>Pool Analytics:</strong><br>"
            "K Constant: {:,.0f}<br>"
            "Total Value: ${:,.0f}<br>"
            "Token Ratio: {:.1f}% / {:.1f}%<br>"
            "Fee Rate: {}%<br>"
            "Pool Health: {}",
            k_constant,
            total_value,
            ratio,
            100 - ratio,
            obj.fee_percentage,
            "Good" if 30 <= ratio <= 70 else "Imbalanced",
        )

    get_pool_analytics.short_description = "Pool Analytics"

    def get_trading_analytics(self, obj):
        if not (obj.pk and obj.token1 and obj.token2):
            return "Save to see trading analytics"

        if not (
            obj.token1_amount
            and obj.token2_amount
            and obj.token1_amount > 0
            and obj.token2_amount > 0
        ):
            return "Set token amounts to see trading analytics"

        # Sample swap calculations
        test_amounts = [Decimal("1"), Decimal("10"), Decimal("100")]
        results = []

        for amount in test_amounts:
            output = obj.get_output_amount(obj.token1, amount)
            rate = output / amount if amount > 0 else Decimal("0")
            results.append(
                f"Swap {amount} {obj.token1.short_name} → {output:.4f} {obj.token2.short_name}"
            )

        # Count orders using this pool
        orders_count = ExchangeOrder.objects.filter(pool=obj).count()
        pending_orders = ExchangeOrder.objects.filter(
            pool=obj, status="pending"
        ).count()

        results_html = "<br>".join(results[:3])
        return format_html(
            "<strong>Trading Analytics:</strong><br>"
            "Total Orders: {}<br>"
            "Pending Orders: {}<br>"
            "<br><strong>Sample Swaps:</strong><br>{}",
            orders_count,
            pending_orders,
            mark_safe(results_html),
        )

    get_trading_analytics.short_description = "Trading Analytics"

    actions = ["activate_pools", "deactivate_pools"]

    def activate_pools(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} pools were activated.")

    activate_pools.short_description = "Activate selected pools"

    def deactivate_pools(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} pools were deactivated.")

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
