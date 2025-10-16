
(function() {
    const poolContractAddressInput = document.getElementById('pool-contract-address');
    const giveTokenSelect = document.getElementById('select_give');
    const receiveTokenSelect = document.getElementById('select_get');

    async function updatePoolContractAddress() {
        if (!giveTokenSelect || !receiveTokenSelect || !poolContractAddressInput) {
            return;
        }

        const token1Id = giveTokenSelect.value;
        const token2Id = receiveTokenSelect.value;

        if (!token1Id || !token2Id) {
            poolContractAddressInput.value = '';
            return;
        }

        try {
            const params = new URLSearchParams({
                token1: token1Id,
                token2: token2Id
            });

            const response = await fetch(`/pool-contract-address/?${params}`);

            if (response.ok) {
                const data = await response.json();
                poolContractAddressInput.value = data.contract_address || '';
            } else {
                poolContractAddressInput.value = '';
            }
        } catch (error) {
            console.error('Ошибка получения адреса контракта:', error);
            poolContractAddressInput.value = '';
        }
    }

    if (giveTokenSelect) {
        giveTokenSelect.addEventListener('change', updatePoolContractAddress);
    }

    if (receiveTokenSelect) {
        receiveTokenSelect.addEventListener('change', updatePoolContractAddress);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updatePoolContractAddress);
    } else {
        updatePoolContractAddress();
    }

    document.addEventListener('click', function(e) {
        if (e.target.closest('.calc__items') || e.target.classList.contains('js_my_sel')) {
            setTimeout(updatePoolContractAddress, 100);
        }
    });
})();
