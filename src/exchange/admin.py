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
        "is_testnet_display",
        "is_active_display",
        "tokens_count",
        "pools_count",
        "created_at",
    )
    list_display_links = ("name", "short_name")
    search_fields = ("name", "short_name")
    list_filter = ("is_active", "is_testnet", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_stats")

    fieldsets = (
        (None, {"fields": ("name", "short_name")}),
        ("Status", {"fields": ("is_active", "is_testnet")}),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at", "get_stats"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [TokenInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tokens")

    def is_testnet_display(self, obj):
        if obj.is_testnet:
            return format_html('<span style="color: orange;">Testnet</span>')
        return format_html('<span style="color: green;">Mainnet</span>')

    is_testnet_display.short_description = "Network Type"

    def is_active_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if obj.is_active else "red",
            "Active" if obj.is_active else "Inactive",
        )

    is_active_display.short_description = "Status"

    def tokens_count(self, obj):
        if not obj.pk:
            return "0 tokens"

        count = obj.tokens.count()
        if count > 0:
            url = (
                reverse("admin:exchange_token_changelist")
                + f"?network__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{} tokens</a>', url, count)
        return "0 tokens"

    tokens_count.short_description = "Tokens"

    def pools_count(self, obj):
        if not obj.pk:
            return "0 pools"

        pools_count = (
            Pool.objects.filter(Q(token1__network=obj) | Q(token2__network=obj))
            .distinct()
            .count()
        )

        return "{} pools".format(pools_count) if pools_count > 0 else "0 pools"

    pools_count.short_description = "Pools"

    def get_stats(self, obj):
        if not obj.pk:
            return "Save to see statistics"

        tokens = obj.tokens.count()
        active_tokens = obj.tokens.filter(is_active=True).count()
        return format_html(
            "<strong>Statistics:</strong><br>"
            "• Total tokens: {}<br>"
            "• Active tokens: {}<br>",
            tokens,
            active_tokens,
        )

    get_stats.short_description = "Network Statistics"


@admin.register(Token)
class TokenAdmin(ModelAdmin):
    list_display = (
        "name",
        "short_name",
        "network_link",
        "decimals",
        "is_active_display",
        "pools_count",
        "image_preview",
        "created_at",
    )
    list_display_links = ("name", "short_name")
    search_fields = ("name", "short_name", "network__name", "network__short_name")
    list_filter = ("is_active", "network", "decimals", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_pool_info")

    fieldsets = (
        (None, {"fields": ("name", "short_name", "network")}),
        ("Visual & Technical", {"fields": ("image", "decimals")}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at", "get_pool_info"),
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

    def is_active_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if obj.is_active else "red",
            "Active" if obj.is_active else "Inactive",
        )

    is_active_display.short_description = "Active"

    def pools_count(self, obj):
        if not obj.pk:
            return "0 pools"

        count = Pool.objects.filter(Q(token1=obj) | Q(token2=obj)).count()
        return "{} pools".format(count) if count > 0 else "0 pools"

    pools_count.short_description = "Pools"

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, "url"):
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Preview"

    def get_pool_info(self, obj):
        if not obj.pk:
            return "Save to see pool information"

        pools = Pool.objects.filter(Q(token1=obj) | Q(token2=obj)).select_related(
            "token1", "token2"
        )

        if not pools.exists():
            return "No pools found"

        pool_list = []
        for pool in pools[:5]:  # Show max 5 pools
            pool_url = reverse("admin:exchange_pool_change", args=[pool.id])
            pool_list.append(f'<a href="{pool_url}">{pool}</a>')

        result = "<strong>Active Pools:</strong><br>" + "<br>".join(pool_list)
        if pools.count() > 5:
            result += "<br>... and {} more".format(pools.count() - 5)
        return format_html(result)

    get_pool_info.short_description = "Pool Information"


@admin.register(Pool)
class PoolAdmin(ModelAdmin):
    list_display = (
        "name",
        "token_pair_display",
        "reserves_display",
        "exchange_rate_display",
        "fee_percentage",
        "is_active_display",
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
        "get_exchange_rates",
        "get_liquidity_analysis",
        "calculate_sample_swaps",
    )

    fieldsets = (
        (None, {"fields": ("name",)}),
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
                "fields": (
                    "get_exchange_rates",
                    "get_liquidity_analysis",
                    "calculate_sample_swaps",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
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

        token1_formatted = "{:,.2f}".format(obj.token1_amount)
        token2_formatted = "{:,.2f}".format(obj.token2_amount)

        return format_html(
            "<strong>{}</strong> {} / <strong>{}</strong> {}",
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
            return "Set reserves to see rates"

        rate1to2 = obj.exchange_rate_token1_to_token2
        rate2to1 = obj.exchange_rate_token2_to_token1
        rate1to2_formatted = "{:.6f}".format(rate1to2)
        rate2to1_formatted = "{:.6f}".format(rate2to1)

        return format_html(
            "1 {} = <strong>{}</strong> {}<br>" "1 {} = <strong>{}</strong> {}",
            obj.token1.short_name,
            rate1to2_formatted,
            obj.token2.short_name,
            obj.token2.short_name,
            rate2to1_formatted,
            obj.token1.short_name,
        )

    exchange_rate_display.short_description = "Exchange Rates"

    def is_active_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if obj.is_active else "red",
            "Active" if obj.is_active else "Inactive",
        )

    is_active_display.short_description = "Status"

    def liquidity_info(self, obj):
        if obj.token1_amount is None or obj.token2_amount is None:
            return "No liquidity"

        total_liquidity = obj.token1_amount + obj.token2_amount
        if total_liquidity > 1000000:
            formatted_value = "{:,.0f}K+".format(total_liquidity / 1000)
            return format_html(
                '<span style="color: green; font-weight: bold;">${} 🔥</span>',
                formatted_value,
            )
        elif total_liquidity > 100000:
            formatted_value = "{:,.0f}K".format(total_liquidity / 1000)
            return format_html(
                '<span style="color: blue; font-weight: bold;">${}</span>',
                formatted_value,
            )
        elif total_liquidity > 10000:
            formatted_value = "{:,.0f}K".format(total_liquidity / 1000)
            return format_html("${}", formatted_value)
        else:
            formatted_value = "{:,.0f}".format(total_liquidity)
            return format_html("${}", formatted_value)

    liquidity_info.short_description = "Liquidity"

    def get_exchange_rates(self, obj):
        if not (obj.pk and obj.token1 and obj.token2):
            return "Save and set tokens/amounts to see exchange rates"

        if not (
            obj.token1_amount
            and obj.token2_amount
            and obj.token1_amount > 0
            and obj.token2_amount > 0
        ):
            return "Set token amounts to see exchange rates"

        rate1to2 = obj.exchange_rate_token1_to_token2
        rate2to1 = obj.exchange_rate_token2_to_token1
        rate1to2_formatted = "{:,.2f}".format(rate1to2)
        rate2to1_formatted = "{:,.2f}".format(rate2to1)
        ratio_formatted = "{:,.2f}".format(
            (obj.token1_amount / (obj.token1_amount + obj.token2_amount)) * 100
        )

        return format_html(
            "<strong>Current Exchange Rates:</strong><br>"
            "• 1 {} = {} {}<br>"
            "• 1 {} = {} {}<br>"
            "<br><strong>Reserve Ratio:</strong> {}%",
            obj.token1.short_name,
            rate1to2_formatted,
            obj.token2.short_name,
            obj.token2.short_name,
            rate2to1_formatted,
            obj.token1.short_name,
            ratio_formatted,
        )

    get_exchange_rates.short_description = "Exchange Rate Analysis"

    def get_liquidity_analysis(self, obj):
        if not obj.pk:
            return "Save and set amounts to see liquidity analysis"

        if not (
            obj.token1_amount
            and obj.token2_amount
            and obj.token1_amount > 0
            and obj.token2_amount > 0
        ):
            return "Set token amounts to see liquidity analysis"

        k_constant = obj.token1_amount * obj.token2_amount
        avg_liquidity = (obj.token1_amount + obj.token2_amount) / 2
        total_value = obj.token1_amount + obj.token2_amount

        k_formatted = "{:,.2f}".format(k_constant)
        avg_formatted = "{:,.2f}".format(avg_liquidity)
        total_formatted = "{:,.2f}".format(total_value)

        return format_html(
            "<strong>Liquidity Analysis:</strong><br>"
            "• K Constant: {}<br>"
            "• Average Liquidity: {}<br>"
            "• Total Value: {}<br>"
            "• Fee Rate: {}%",
            k_formatted,
            avg_formatted,
            total_formatted,
            obj.fee_percentage,
        )

    get_liquidity_analysis.short_description = "Liquidity Analysis"

    def calculate_sample_swaps(self, obj):
        if not (obj.pk and obj.token1 and obj.token2):
            return "Save and set tokens/amounts to see sample swap calculations"

        if not (
            obj.token1_amount
            and obj.token2_amount
            and obj.token1_amount > 0
            and obj.token2_amount > 0
        ):
            return "Set token amounts to see sample swaps"

        # Calculate sample swaps for different amounts
        test_amounts = [Decimal("1"), Decimal("10"), Decimal("100")]
        results = []

        for amount in test_amounts:
            output1to2 = obj.get_output_amount(obj.token1, amount)
            output2to1 = obj.get_output_amount(obj.token2, amount)

            output1to2_formatted = "{:.6f}".format(output1to2)
            output2to1_formatted = "{:.6f}".format(output2to1)

            results.append(
                "• Swap {} {} → {} {}".format(
                    amount,
                    obj.token1.short_name,
                    output1to2_formatted,
                    obj.token2.short_name,
                )
            )
            results.append(
                "• Swap {} {} → {} {}".format(
                    amount,
                    obj.token2.short_name,
                    output2to1_formatted,
                    obj.token1.short_name,
                )
            )

        results_html = "<br>".join(results)
        return format_html(
            "<strong>Sample Swaps:</strong><br>{}", mark_safe(results_html)
        )

    calculate_sample_swaps.short_description = "Sample Swap Calculator"

    actions = ["activate_pools", "deactivate_pools"]

    def activate_pools(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, "{} pools were activated.".format(updated))

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
        "wallet_address",
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
        "get_exchange_analysis",
        "get_profit_analysis",
        "get_transaction_timeline",
    )

    fieldsets = (
        ("Order Information", {"fields": ("id", "order_short_number", "status")}),
        ("User Details", {"fields": ("email", "wallet_address")}),
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
                "fields": (
                    "get_exchange_analysis",
                    "get_profit_analysis",
                    "get_transaction_timeline",
                ),
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
        give_formatted = "{:,.2f}".format(obj.give_amount)
        receive_formatted = "{:,.2f}".format(obj.receive_amount)

        return format_html(
            '<div style="text-align: center;">'
            "<strong>{} {}</strong><br>"
            "↓<br>"
            "<strong>{} {}</strong>"
            "</div>",
            give_formatted,
            obj.give_token.short_name,
            receive_formatted,
            obj.receive_token.short_name,
        )

    exchange_summary_display.short_description = "Exchange"

    def exchange_rate_display(self, obj):
        rate_formatted = "{:,.6f}".format(obj.exchange_rate)
        return format_html(
            "1 {} = <br>{} {}",
            obj.give_token.short_name,
            rate_formatted,
            obj.receive_token.short_name,
        )

    exchange_rate_display.short_description = "Rate"

    def fee_display(self, obj):
        return format_html("<strong>{}%</strong>", obj.fee_percentage)

    fee_display.short_description = "Fee"

    def pool_link(self, obj):
        if not obj.pool:
            return "No pool"

        url = reverse("admin:exchange_pool_change", args=[obj.pool.id])
        return format_html('<a href="{}">{}</a>', url, obj.pool.name)

    pool_link.short_description = "Pool"

    def get_exchange_analysis(self, obj):
        if not obj.pk:
            return "Save to see exchange analysis"

        total_value_usd = float(obj.give_amount)
        fee_amount = obj.give_amount * (obj.fee_percentage / 100)
        net_receive = obj.receive_amount

        current_pool_rate = (
            obj.pool.exchange_rate_token1_to_token2
            if obj.give_token == obj.pool.token1
            else obj.pool.exchange_rate_token2_to_token1
        )
        rate_difference = (
            (obj.exchange_rate - current_pool_rate) / current_pool_rate
        ) * 100

        return format_html(
            "<strong>Exchange Analysis:</strong><br>"
            "Order Value: ${:,.2f}<br>"
            "Fee Amount: {:.4f} {}<br>"
            "Net Receive: {:.6f} {}<br>"
            "Rate vs Current: {:.2f}%<br>"
            "Order Size: {}",
            total_value_usd,
            fee_amount,
            obj.give_token.short_name,
            net_receive,
            obj.receive_token.short_name,
            rate_difference,
            (
                "Large"
                if total_value_usd > 10000
                else "Medium" if total_value_usd > 1000 else "Small"
            ),
        )

    get_exchange_analysis.short_description = "Exchange Analysis"

    def get_profit_analysis(self, obj):
        if not obj.pk:
            return "Save to see profit analysis"

        fee_revenue = obj.give_amount * (obj.fee_percentage / 100)
        operational_cost = Decimal("0.01")
        net_profit = fee_revenue - operational_cost
        profit_margin = (net_profit / fee_revenue) * 100 if fee_revenue > 0 else 0

        return format_html(
            "<strong>Revenue Analysis:</strong><br>"
            "Fee Revenue: {:.4f} {}<br>"
            "Operational Cost: ${:.2f}<br>"
            "Net Profit: {:.4f} {}<br>"
            "Profit Margin: {:.1f}%<br>"
            "Status: {}",
            fee_revenue,
            obj.give_token.short_name,
            operational_cost,
            net_profit,
            profit_margin,
            "Profitable" if net_profit > 0 else "Loss",
        )

    get_profit_analysis.short_description = "Profit Analysis"

    def get_transaction_timeline(self, obj):
        if not obj.pk:
            return "Save to see timeline"

        from django.utils import timezone
        import datetime

        timeline_events = []
        timeline_events.append(f"Order Created: {obj.created_at.strftime('%H:%M:%S')}")

        if obj.updated_at != obj.created_at:
            timeline_events.append(
                f"Last Updated: {obj.updated_at.strftime('%H:%M:%S')}"
            )

        if obj.transaction_hash:
            timeline_events.append(f"Transaction Hash: {obj.transaction_hash[:20]}...")

        if obj.status == "completed":
            timeline_events.append("Status: Successfully Completed")
        elif obj.status == "pending":
            time_waiting = timezone.now() - obj.created_at
            if time_waiting > datetime.timedelta(hours=1):
                timeline_events.append("Status: Long Wait Time")
            else:
                timeline_events.append("Status: Normal Wait Time")

        timeline_html = "<br>".join(timeline_events)
        return format_html(
            "<strong>Transaction Timeline:</strong><br>{}", mark_safe(timeline_html)
        )

    get_transaction_timeline.short_description = "Transaction Timeline"

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
                    order.wallet_address,
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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        total_orders = ExchangeOrder.objects.count()
        pending_orders = ExchangeOrder.objects.filter(status="pending").count()
        completed_orders = ExchangeOrder.objects.filter(status="completed").count()

        extra_context["total_orders"] = total_orders
        extra_context["pending_orders"] = pending_orders
        extra_context["completed_orders"] = completed_orders

        return super().changelist_view(request, extra_context)
