from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Q
from django.urls import reverse
from unfold.admin import ModelAdmin
from decimal import Decimal

from .models import Network, Token, Pool


class TokenInline(admin.TabularInline):
    model = Token
    extra = 0
    fields = ('name', 'short_name', 'decimals', 'is_active')
    readonly_fields = ('created_at',)


@admin.register(Network)
class NetworkAdmin(ModelAdmin):
    list_display = (
        "name",
        "short_name",
        "is_testnet_display",
        "is_active_display",
        "tokens_count",
        "pools_count",
        "created_at"
    )
    list_display_links = ("name", "short_name")
    search_fields = ("name", "short_name")
    list_filter = ("is_active", "is_testnet", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_stats")

    fieldsets = (
        (None, {
            'fields': ('name', 'short_name')
        }),
        ('Status', {
            'fields': ('is_active', 'is_testnet')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'get_stats'),
            'classes': ('collapse',)
        }),
    )

    inlines = [TokenInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tokens')

    def is_testnet_display(self, obj):
        if obj.is_testnet:
            return format_html('<span style="color: orange;">🧪 Testnet</span>')
        return format_html('<span style="color: green;">🌍 Mainnet</span>')

    is_testnet_display.short_description = "Network Type"

    def is_active_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_active else 'red',
            '✅ Active' if obj.is_active else '❌ Inactive'
        )

    is_active_display.short_description = "Status"

    def tokens_count(self, obj):
        if not obj.pk:
            return "0 tokens"

        count = obj.tokens.count()
        if count > 0:
            url = reverse('admin:exchange_token_changelist') + f'?network__id__exact={obj.id}'
            return format_html('<a href="{}">{} tokens</a>', url, count)
        return "0 tokens"

    tokens_count.short_description = "Tokens"

    def pools_count(self, obj):
        if not obj.pk:
            return "0 pools"

        pools_count = Pool.objects.filter(
            Q(token1__network=obj) | Q(token2__network=obj)
        ).distinct().count()

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
            tokens, active_tokens
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
        "created_at"
    )
    list_display_links = ("name", "short_name")
    search_fields = ("name", "short_name", "network__name", "network__short_name")
    list_filter = ("is_active", "network", "decimals", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "get_pool_info")

    fieldsets = (
        (None, {
            'fields': ('name', 'short_name', 'network')
        }),
        ('Visual & Technical', {
            'fields': ('image', 'decimals')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'get_pool_info'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('network')

    def network_link(self, obj):
        if not obj.network:
            return "No network"

        url = reverse('admin:exchange_network_change', args=[obj.network.id])
        return format_html('<a href="{}">{}</a>', url, obj.network.short_name)

    network_link.short_description = "Network"

    def is_active_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_active else 'red',
            '✅' if obj.is_active else '❌'
        )

    is_active_display.short_description = "Active"

    def pools_count(self, obj):
        if not obj.pk:
            return "0 pools"

        count = Pool.objects.filter(Q(token1=obj) | Q(token2=obj)).count()
        return "{} pools".format(count) if count > 0 else "0 pools"

    pools_count.short_description = "Pools"

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />',
                obj.image.url
            )
        return "No image"

    image_preview.short_description = "Preview"

    def get_pool_info(self, obj):
        if not obj.pk:
            return "Save to see pool information"

        pools = Pool.objects.filter(
            Q(token1=obj) | Q(token2=obj)
        ).select_related('token1', 'token2')

        if not pools.exists():
            return "No pools found"

        pool_list = []
        for pool in pools[:5]:  # Show max 5 pools
            pool_url = reverse('admin:exchange_pool_change', args=[pool.id])
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
        "liquidity_info"
    )
    list_display_links = ("name", "token_pair_display")
    search_fields = (
        "name",
        "token1__name",
        "token1__short_name",
        "token2__name",
        "token2__short_name"
    )
    list_filter = (
        "is_active",
        ("token1__network", admin.RelatedOnlyFieldListFilter),
        ("token2__network", admin.RelatedOnlyFieldListFilter),
        "fee_percentage"
    )
    ordering = ("name",)
    readonly_fields = (
        "id",
        "get_exchange_rates",
        "get_liquidity_analysis",
        "calculate_sample_swaps"
    )

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Token Configuration', {
            'fields': (
                ('token1', 'token1_amount'),
                ('token2', 'token2_amount'),
            )
        }),
        ('Pool Settings', {
            'fields': ('fee_percentage', 'is_active')
        }),
        ('Administration', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': (
                'get_exchange_rates',
                'get_liquidity_analysis',
                'calculate_sample_swaps'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'token1', 'token2', 'token1__network', 'token2__network'
        )

    def token_pair_display(self, obj):
        if not (obj.token1 and obj.token2):
            return "Tokens not set"

        token1_url = reverse('admin:exchange_token_change', args=[obj.token1.id])
        token2_url = reverse('admin:exchange_token_change', args=[obj.token2.id])
        return format_html(
            '<a href="{}">{}</a> / <a href="{}">{}</a>',
            token1_url, obj.token1.short_name,
            token2_url, obj.token2.short_name
        )

    token_pair_display.short_description = "Token Pair"

    def reserves_display(self, obj):
        if not (obj.token1 and obj.token2 and
                obj.token1_amount is not None and obj.token2_amount is not None):
            return "Reserves not set"

        token1_formatted = "{:,.2f}".format(obj.token1_amount)
        token2_formatted = "{:,.2f}".format(obj.token2_amount)

        return format_html(
            '<strong>{}</strong> {} / <strong>{}</strong> {}',
            token1_formatted, obj.token1.short_name,
            token2_formatted, obj.token2.short_name
        )

    reserves_display.short_description = "Reserves"

    def exchange_rate_display(self, obj):
        if not (obj.token1 and obj.token2 and
                obj.token1_amount and obj.token2_amount and
                obj.token1_amount > 0 and obj.token2_amount > 0):
            return "Set reserves to see rates"

        rate1to2 = obj.exchange_rate_token1_to_token2
        rate2to1 = obj.exchange_rate_token2_to_token1
        rate1to2_formatted = "{:.6f}".format(rate1to2)
        rate2to1_formatted = "{:.6f}".format(rate2to1)

        return format_html(
            '1 {} = <strong>{}</strong> {}<br>'
            '1 {} = <strong>{}</strong> {}',
            obj.token1.short_name, rate1to2_formatted, obj.token2.short_name,
            obj.token2.short_name, rate2to1_formatted, obj.token1.short_name
        )

    exchange_rate_display.short_description = "Exchange Rates"

    def is_active_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_active else 'red',
            '✅ Active' if obj.is_active else '❌ Inactive'
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
                formatted_value
            )
        elif total_liquidity > 100000:
            formatted_value = "{:,.0f}K".format(total_liquidity / 1000)
            return format_html(
                '<span style="color: blue; font-weight: bold;">${}</span>',
                formatted_value
            )
        elif total_liquidity > 10000:
            formatted_value = "{:,.0f}K".format(total_liquidity / 1000)
            return format_html('${}', formatted_value)
        else:
            formatted_value = "{:,.0f}".format(total_liquidity)
            return format_html('${}', formatted_value)

    liquidity_info.short_description = "Liquidity"

    def get_exchange_rates(self, obj):
        if not (obj.pk and obj.token1 and obj.token2):
            return "Save and set tokens/amounts to see exchange rates"

        if not (obj.token1_amount and obj.token2_amount and
                obj.token1_amount > 0 and obj.token2_amount > 0):
            return "Set token amounts to see exchange rates"

        rate1to2 = obj.exchange_rate_token1_to_token2
        rate2to1 = obj.exchange_rate_token2_to_token1
        rate1to2_formatted = "{:,.8f}".format(rate1to2)
        rate2to1_formatted = "{:,.8f}".format(rate2to1)
        ratio_formatted = "{:,.2f}".format((obj.token1_amount / (obj.token1_amount + obj.token2_amount)) * 100)

        return format_html(
            "<strong>Current Exchange Rates:</strong><br>"
            "• 1 {} = {} {}<br>"
            "• 1 {} = {} {}<br>"
            "<br><strong>Reserve Ratio:</strong> {}%",
            obj.token1.short_name, rate1to2_formatted, obj.token2.short_name,
            obj.token2.short_name, rate2to1_formatted, obj.token1.short_name,
            ratio_formatted
        )

    get_exchange_rates.short_description = "Exchange Rate Analysis"

    def get_liquidity_analysis(self, obj):
        if not obj.pk:
            return "Save and set amounts to see liquidity analysis"

        if not (obj.token1_amount and obj.token2_amount and
                obj.token1_amount > 0 and obj.token2_amount > 0):
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
            k_formatted, avg_formatted, total_formatted, obj.fee_percentage
        )

    get_liquidity_analysis.short_description = "Liquidity Analysis"

    def calculate_sample_swaps(self, obj):
        if not (obj.pk and obj.token1 and obj.token2):
            return "Save and set tokens/amounts to see sample swap calculations"

        if not (obj.token1_amount and obj.token2_amount and
                obj.token1_amount > 0 and obj.token2_amount > 0):
            return "Set token amounts to see sample swaps"

        # Calculate sample swaps for different amounts
        test_amounts = [Decimal('1'), Decimal('10'), Decimal('100')]
        results = []

        for amount in test_amounts:
            output1to2 = obj.get_output_amount(obj.token1, amount)
            output2to1 = obj.get_output_amount(obj.token2, amount)

            output1to2_formatted = "{:.6f}".format(output1to2)
            output2to1_formatted = "{:.6f}".format(output2to1)

            results.append(
                "• Swap {} {} → {} {}".format(
                    amount, obj.token1.short_name, output1to2_formatted, obj.token2.short_name
                )
            )
            results.append(
                "• Swap {} {} → {} {}".format(
                    amount, obj.token2.short_name, output2to1_formatted, obj.token1.short_name
                )
            )

        results_html = "<br>".join(results)
        return format_html(
            "<strong>Sample Swaps:</strong><br>{}",
            mark_safe(results_html)
        )

    calculate_sample_swaps.short_description = "Sample Swap Calculator"

    actions = ['activate_pools', 'deactivate_pools']

    def activate_pools(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, '{} pools were activated.'.format(updated))

    activate_pools.short_description = "Activate selected pools"

    def deactivate_pools(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} pools were deactivated.')

    deactivate_pools.short_description = "Deactivate selected pools"