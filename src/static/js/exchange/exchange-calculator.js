jQuery(function($) {
    let exchangeTimeout;
    let lastCalculationData = {};

    function calculateExchangeDelayed() {
        clearTimeout(exchangeTimeout);
        exchangeTimeout = setTimeout(calculateExchange, 200);
    }

    function calculateExchange() {
        const giveTokenId = $('#select_give').val();
        const receiveTokenId = $('#select_get').val();
        const amount = parseFloat($('input[name="sum1"]').val()) || 0;

        const currentData = { giveTokenId, receiveTokenId, amount };

        if (JSON.stringify(currentData) === JSON.stringify(lastCalculationData)) return;
        lastCalculationData = currentData;

        const outputField = $('input[name="sum2"], .js_sum2c');
        const courseField = $('.js_course_html');

        if (!giveTokenId || !receiveTokenId) {
            outputField.val('0');
            courseField.text('Выберите токены');
            return;
        }

        if (giveTokenId === receiveTokenId) {
            outputField.val('0');
            courseField.text('Выберите разные токены');
            return;
        }

        if (amount <= 0) {
            outputField.val('0');
            courseField.text('Введите сумму > 0');
            return;
        }

        courseField.text('Расчет...');

        $.ajax({
            url: '/exchange/calculate-exchange/',
            type: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            data: JSON.stringify({
                give_token_id: giveTokenId,
                receive_token_id: receiveTokenId,
                amount: amount
            }),
            success: function(data) {
                if (data.success) {
                    const formattedAmount = parseFloat(data.output_amount).toFixed(6);
                    const effectiveRate = parseFloat(data.effective_rate).toFixed(6);

                    outputField.val(formattedAmount);
                    courseField.text(`1 ${data.give_token_name} = ${effectiveRate} ${data.receive_token_name}`);

                    outputField.addClass('exchange-updated');
                    setTimeout(() => outputField.removeClass('exchange-updated'), 300);
                } else {
                    outputField.val('0');
                    courseField.text(data.error);
                }
            },
            error: function() {
                if (amount > 0) {
                    outputField.val((amount * 0.97).toFixed(6));
                    const giveTokenName = $('#select_give option:selected').text().split(' ')[0];
                    const receiveTokenName = $('#select_get option:selected').text().split(' ')[0];
                    courseField.text(`1 ${giveTokenName} ≈ 0.97 ${receiveTokenName}`);
                } else {
                    outputField.val('0');
                    courseField.text('Ошибка соединения');
                }
            }
        });
    }

    $(document).on('change', '#select_give, #select_get', calculateExchangeDelayed);
    $(document).on('input keyup paste', 'input[name="sum1"]', calculateExchangeDelayed);

    $(document).on('click', '.js-calc-reverse', function(e) {
        e.preventDefault();
        const giveValue = $('#select_give').val();
        const receiveValue = $('#select_get').val();

        $('#select_give').val(receiveValue);
        $('#select_get').val(giveValue);
    });

    $(document).on('click', '.js_min1_val', function(e) {
        e.preventDefault();
        const minVal = $(this).data('min1') || $(this).data('val') || 1;
        $('input[name="sum1"]').val(minVal).trigger('input');
    });

    $(document).on('click', '.js_max1_val', function(e) {
        e.preventDefault();
        const maxVal = $(this).data('max1') || $(this).data('val') || 10000;
        $('input[name="sum1"]').val(maxVal).trigger('input');
    });

    setTimeout(calculateExchange, 500);
});