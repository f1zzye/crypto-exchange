jQuery(function($) {
    function updateCoinDisplay(selectElement, targetImageClass, targetNameClass) {
        const selectedOption = selectElement.find('option:selected');
        const imageUrl = selectedOption.data('img') || selectedOption.data('logo');
        const coinName = selectedOption.text().trim();

        if (imageUrl) {
            $(targetImageClass).attr('src', imageUrl);
        }

        $(targetNameClass).text(coinName);
    }

    $(document).on('change', '#select_give', function() {
        const column = $(this).closest('.calc__col');
        const imageElement = column.find('.js-sum-icon');
        const nameElement = column.find('.js-sum-name');
        updateCoinDisplay($(this), imageElement, nameElement);
    });

    $(document).on('change', '#select_get', function() {
        const column = $(this).closest('.calc__col');
        const imageElement = column.find('.js-sum-icon');
        const nameElement = column.find('.js-sum-name');
        updateCoinDisplay($(this), imageElement, nameElement);
    });

    function initializeCoinDisplay() {
        $('#select_give').each(function() {
            const column = $(this).closest('.calc__col');
            const imageElement = column.find('.js-sum-icon');
            const nameElement = column.find('.js-sum-name');
            updateCoinDisplay($(this), imageElement, nameElement);
        });

        $('#select_get').each(function() {
            const column = $(this).closest('.calc__col');
            const imageElement = column.find('.js-sum-icon');
            const nameElement = column.find('.js-sum-name');
            updateCoinDisplay($(this), imageElement, nameElement);
        });
    }

    initializeCoinDisplay();
});