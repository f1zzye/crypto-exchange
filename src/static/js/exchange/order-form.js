jQuery(function($) {
    function updateHiddenFields() {
        $('#hidden_give_token_id').val($('#select_give').val());
        $('#hidden_receive_token_id').val($('#select_get').val());
        $('#hidden_sum2').val($('input[name="sum2"], .js_sum2c').val());
    }

    $(document).on('change', '#select_give, #select_get', updateHiddenFields);
    $(document).on('input', 'input[name="sum1"], input[name="sum2"], .js_sum2c', updateHiddenFields);

    $(document).on('submit', '.ajax_post_bids', function(e) {
        updateHiddenFields();

        const giveTokenId = $('#hidden_give_token_id').val();
        const receiveTokenId = $('#hidden_receive_token_id').val();
        const giveAmount = $('input[name="sum1"]').val();
        const receiveAmount = $('#hidden_sum2').val();
        const email = $('input[name="cf6"]').val();

        if (!giveTokenId || !receiveTokenId || !giveAmount || !receiveAmount) {
            e.preventDefault();
            alert('Выберите токены и введите сумму для обмена');
            return false;
        }

        if (!email) {
            e.preventDefault();
            alert('Введите email');
            return false;
        }

    });

    updateHiddenFields();
});