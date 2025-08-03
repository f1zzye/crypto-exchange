jQuery(function($) {
    const $selectGive = $('#select_give');
    const $selectGet = $('#select_get');

    const columnCache = new Map();

    function getColumn(selectElement) {
        const id = selectElement.attr('id');
        if (!columnCache.has(id)) {
            columnCache.set(id, selectElement.closest('.calc__col'));
        }
        return columnCache.get(id);
    }

    function updateCoinUI(selectElement) {
        const column = getColumn(selectElement);
        if (!column.length) return;

        const selectedOption = selectElement.find('option:selected');
        const selectedValue = selectElement.val();
        const imageUrl = selectedOption.data('img') || selectedOption.data('logo');
        const coinName = selectedOption.text().trim();

        const $items = column.find('.calc__item');
        $items.removeClass('active');

        if (selectedValue) {
            $items.filter(`[data-id="${selectedValue}"]`).addClass('active');
        }

        if (imageUrl) column.find('.js-sum-icon').attr('src', imageUrl);
        if (coinName) column.find('.js-sum-name').text(coinName);
    }

    function findNextToken(selectElement, excludeValue) {
        return selectElement.find('option').filter(function() {
            const val = this.value;
            return val && val !== excludeValue;
        }).first();
    }

    function getOtherSelect(select) {
        return select.is($selectGive) ? $selectGet : $selectGive;
    }

    function swapIfDuplicate(changedSelect, newValue) {
        const otherSelect = getOtherSelect(changedSelect);

        if (otherSelect.val() !== newValue) return;

        const nextToken = findNextToken(otherSelect, newValue);
        if (nextToken.length) {
            otherSelect.val(nextToken.val());
            updateCoinUI(otherSelect);
            otherSelect.trigger('change');
        }
    }

    // События
    $(document)
        .on('click', '.calc__item.js-calc-item', function(e) {
            e.preventDefault();

            const tokenId = $(this).data('id');
            if (!tokenId) return;

            const select = $(this).closest('.calc__col').find('select');
            if (!select.length || select.val() === tokenId) return;

            swapIfDuplicate(select, tokenId);
            select.val(tokenId);
            updateCoinUI(select);
            select.trigger('change');
        })

        .on('change', '#select_give, #select_get', function() {
            const $this = $(this);
            swapIfDuplicate($this, $this.val());
            updateCoinUI($this);
        })

        .on('click', '.js-calc-reverse', function(e) {
            e.preventDefault();

            const giveVal = $selectGive.val();
            const getVal = $selectGet.val();

            $selectGive.val(getVal);
            $selectGet.val(giveVal);

            updateCoinUI($selectGive);
            updateCoinUI($selectGet);

            $selectGive.add($selectGet).trigger('change');
        });

    function init() {
        if (!$selectGive.length || !$selectGet.length) {
            setTimeout(init, 200);
            return;
        }

        updateCoinUI($selectGive);
        updateCoinUI($selectGet);

        if ($selectGive.val() === $selectGet.val() && $selectGive.val()) {
            const nextToken = findNextToken($selectGet, $selectGive.val());
            if (nextToken.length) {
                $selectGet.val(nextToken.val());
                updateCoinUI($selectGet);
            }
        }
    }

    $(document).ready(init);
});