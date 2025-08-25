from decimal import Decimal
import csv
from django.utils import timezone
from datetime import timezone

from django.http import HttpResponse
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ExchangeOrder
from django.utils.html import format_html
from django.urls import path, reverse


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
        if (
            not obj.pk
            or not obj.created_at
            or not obj.updated_at
            or obj.give_amount is None
            or obj.exchange_rate is None
            or obj.give_token is None
            or obj.pool is None
        ):
            return "Save to see analytics"

        processing_time = obj.updated_at - obj.created_at
        total_value_usd = float(obj.give_amount)
        size_category = (
            "Large"
            if total_value_usd > 10_000
            else "Medium" if total_value_usd > 1000 else "Small"
        )

        current_pool_rate = None
        if obj.pool:
            if obj.give_token == obj.pool.token1:
                current_pool_rate = obj.pool.exchange_rate_token1_to_token2
            else:
                current_pool_rate = obj.pool.exchange_rate_token2_to_token1

        if (
            current_pool_rate is None
            or current_pool_rate == 0
            or obj.exchange_rate is None
        ):
            rate_difference = "N/A"
        else:
            rate_difference = (
                (obj.exchange_rate - current_pool_rate) / current_pool_rate
            ) * 100

        return format_html(
            "<strong>Order Analytics:</strong><br>"
            "Order Value: ${:,.0f}<br>"
            "Order Size: {}<br>"
            "Processing Time: {}<br>"
            "Rate vs Current: {}%<br>"
            "Order Health: {}",
            total_value_usd,
            size_category,
            processing_time,
            (
                rate_difference
                if rate_difference == "N/A"
                else "{:.2f}".format(rate_difference)
            ),
            (
                "Good"
                if obj.status == "completed"
                else "Pending" if obj.status == "pending" else "Issue"
            ),
        )

    get_order_analytics.short_description = "Order Analytics"

    def get_financial_analytics(self, obj):
        if (
            not obj.pk
            or obj.give_amount is None
            or obj.fee_percentage is None
            or obj.give_token is None
        ):
            return "Save to see analytics"

        fee_revenue = (
            obj.give_amount * (obj.fee_percentage / 100)
            if obj.give_amount is not None and obj.fee_percentage is not None
            else Decimal("0.00")
        )
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
            obj.give_token.short_name if obj.give_token else "",
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
