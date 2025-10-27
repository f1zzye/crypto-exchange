document.addEventListener('DOMContentLoaded', function () {
    const config = {
        manifestUrl: `${window.location.origin}/tonconnect-manifest.json`,
        buttonRootId: 'ton-connect-header',
        apiEndpoint: '/api/wallet-balance/',
        network: 'testnet'
    };

    const elements = {
        header: {
            connectBtn: document.getElementById('header-connect-btn'),
            walletContainer: document.getElementById('wallet-button-container'),
            walletInfoBtn: document.getElementById('header-wallet-info'),
            walletDropdown: document.getElementById('wallet-dropdown'),
            balanceEl: document.querySelector('.wallet-balance-display'),
            addressEl: document.querySelector('.wallet-address-display'),
            btnContent: document.querySelector('.wallet-btn-content'),
            dropdownAddress: document.getElementById('dropdown-wallet-address'),
            dropdownBalance: document.getElementById('dropdown-wallet-balance')
        },
        index: {
            unifiedBtn: document.getElementById('unified-wallet-btn'),
            btnText: document.getElementById('btn-text'),
            walletStatus: document.getElementById('wallet-status'),
            walletField: document.querySelector('input[name="wallet_address"]')
        }
    };

    const state = {
        currentWallet: null,
        isDropdownOpen: false,
        isInitialLoad: true,
        isManualConnection: false,
        isCaptchaValid: false,
        captchaValidationTimeout: null,
        userJettonWallet: null
    };

    const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
        manifestUrl: config.manifestUrl,
        buttonRootId: config.buttonRootId
    });

    window.headerTonConnectUI = tonConnectUI;

    async function validateCaptcha() {
        const captchaInput = document.querySelector('#captcha-input');
        if (!captchaInput || !captchaInput.value.trim()) {
            state.isCaptchaValid = false;
            return false;
        }

        try {
            const formData = new FormData();
            formData.append('action', 'validate_captcha');
            formData.append('captcha_answer', captchaInput.value);

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                formData.append('csrfmiddlewaretoken', csrfToken.value);
            }

            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            state.isCaptchaValid = data.is_valid;

            if (captchaInput.parentElement) {
                captchaInput.parentElement.classList.toggle('captcha-valid', data.is_valid);
                captchaInput.parentElement.classList.toggle('captcha-invalid', !data.is_valid);
            }

            return data.is_valid;
        } catch (error) {
            state.isCaptchaValid = false;
            return false;
        }
    }

    function isFormValid() {
        const sum1 = document.querySelector('input[name="sum1"]')?.value;
        if (!sum1 || parseFloat(sum1) <= 0) return false;

        const email = document.querySelector('#cf6')?.value;
        if (!email || !email.includes('@')) return false;

        const captcha = document.querySelector('#captcha-input')?.value;
        if (!captcha || captcha.trim() === '' || !state.isCaptchaValid) return false;

        const checkedBoxes = document.querySelectorAll('input[type="checkbox"]:checked[required]');
        if (checkedBoxes.length < 2) return false;

        const giveSelect = document.querySelector('#select_give')?.value;
        const receiveSelect = document.querySelector('#select_get')?.value;
        if (!giveSelect || !receiveSelect || giveSelect === receiveSelect) return false;

        return true;
    }

    function updateUnifiedButton(connected) {
        const { unifiedBtn, btnText } = elements.index;
        if (!unifiedBtn || !btnText) return;

        const hasWallet = !!state.currentWallet;
        const formValid = connected ? isFormValid() : false;

        if (!hasWallet) {
            btnText.textContent = 'Підключити гаманець';
            unifiedBtn.disabled = false;
            unifiedBtn.style.opacity = '1';
            unifiedBtn.style.cursor = 'pointer';
        } else if (formValid) {
            btnText.textContent = 'Обміняти зараз';
            unifiedBtn.disabled = false;
            unifiedBtn.style.opacity = '1';
            unifiedBtn.style.cursor = 'pointer';
        } else {
            btnText.textContent = 'Обміняти зараз';
            unifiedBtn.disabled = true;
            unifiedBtn.style.opacity = '0.5';
            unifiedBtn.style.cursor = 'not-allowed';
        }
    }

    function handleCaptchaChange() {
        const captchaInput = document.querySelector('#captcha-input');
        if (captchaInput) {
            state.isCaptchaValid = false;

            if (captchaInput.parentElement) {
                captchaInput.parentElement.classList.remove('captcha-valid', 'captcha-invalid');
            }

            if (state.currentWallet) updateUnifiedButton(true);

            if (state.captchaValidationTimeout) {
                clearTimeout(state.captchaValidationTimeout);
            }

            state.captchaValidationTimeout = setTimeout(async () => {
                await validateCaptcha();
                if (state.currentWallet) updateUnifiedButton(true);
            }, 500);
        }
    }

    setInterval(() => {
        if (state.currentWallet) {
            updateUnifiedButton(true);
        }
    }, 500);

    document.addEventListener('input', (e) => {
        if (e.target.id === 'captcha-input') {
            handleCaptchaChange();
        } else if (state.currentWallet) {
            updateUnifiedButton(true);
        }
    });

    document.addEventListener('change', () => {
        if (state.currentWallet) updateUnifiedButton(true);
    });

    document.addEventListener('click', function(e) {
        if (e.target.type === 'checkbox' || e.target.closest('label')) {
            setTimeout(() => {
                if (state.currentWallet) updateUnifiedButton(true);
            }, 50);
        }
    });

    const utils = {
        parseBalance(balanceStr) {
            if (!balanceStr) return 0;
            if (balanceStr.startsWith('<')) return 0.0099;
            return parseFloat(balanceStr.replace(/[^\d.]/g, '')) || 0;
        },

        formatBalance(balValue) {
            const isSmallBalance = balValue === 0 || balValue < 0.01;
            return {
                display: isSmallBalance ? (balValue === 0 ? "0$" : "< 0.01") : balValue.toString(),
                isSmall: isSmallBalance
            };
        },

        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };

    async function fetchWalletData(address) {
        try {
            const response = await fetch(`${config.apiEndpoint}?address=${encodeURIComponent(address)}&network=${config.network}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return {
                balance: data.balance || "0.00 TON",
                userFriendlyAddress: data.address || address,
                shortAddress: data.shortAddress || address
            };
        } catch (error) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Ошибка загрузки данных кошелька', 'error');
            }
            return {
                balance: "0.00 TON",
                userFriendlyAddress: address,
                shortAddress: address
            };
        }
    }

    function displayWallet(balanceStr, userFriendlyAddress) {
        const balValue = utils.parseBalance(balanceStr);
        const { display: balanceDisplay, isSmall } = utils.formatBalance(balValue);

        const { header } = elements;

        if (header.balanceEl) {
            header.balanceEl.textContent = balanceDisplay;
            header.balanceEl.classList.toggle('wallet-balance-small', isSmall);
        }

        const hasValidAddress = userFriendlyAddress && userFriendlyAddress !== '' && userFriendlyAddress !== 'Connecting...';

        if (header.btnContent) {
            header.btnContent.classList.toggle('only-balance', !hasValidAddress);
        }

        if (header.addressEl) {
            header.addressEl.style.display = hasValidAddress ? '' : 'none';
            if (hasValidAddress) header.addressEl.textContent = userFriendlyAddress;
        }

        if (header.dropdownAddress) header.dropdownAddress.textContent = userFriendlyAddress;
        if (header.dropdownBalance) {
            header.dropdownBalance.textContent = isSmall ? "< 0.01" : balanceStr;
            header.dropdownBalance.classList.toggle('wallet-balance-small', isSmall);
        }
    }

    function updateAllButtons(connected) {
        const { header, index } = elements;

        if (header.connectBtn) header.connectBtn.style.display = connected ? 'none' : 'inline-flex';
        if (header.walletContainer) header.walletContainer.style.display = connected ? 'block' : 'none';
        if (index.walletField) index.walletField.value = connected && state.currentWallet ? state.currentWallet.account.address : '';

        updateUnifiedButton(connected);
    }

    function toggleWalletDropdown() {
        state.isDropdownOpen ? closeWalletDropdown() : openWalletDropdown();
    }

    function openWalletDropdown() {
        const { walletDropdown, walletInfoBtn } = elements.header;
        if (!walletDropdown) return;

        walletDropdown.classList.add('show');
        walletInfoBtn?.classList.add('active');
        state.isDropdownOpen = true;

        setTimeout(() => document.addEventListener('click', handleClickOutside), 100);
    }

    function closeWalletDropdown() {
        const { walletDropdown, walletInfoBtn } = elements.header;
        walletDropdown?.classList.remove('show');
        walletInfoBtn?.classList.remove('active');
        state.isDropdownOpen = false;
        document.removeEventListener('click', handleClickOutside);
    }

    function handleClickOutside(e) {
        if (elements.header.walletContainer && !elements.header.walletContainer.contains(e.target)) {
            closeWalletDropdown();
        }
    }

    function setButtonLoading(isLoading, loadingText) {
        const { header, index } = elements;

        if (header.connectBtn) {
            header.connectBtn.disabled = isLoading;
            const span = header.connectBtn.querySelector('span');
            if (span) span.textContent = isLoading ? loadingText : 'Connect Wallet';
        }

        if (index.unifiedBtn && index.btnText) {
            index.unifiedBtn.disabled = isLoading;
            if (isLoading) {
                index.btnText.textContent = loadingText;
            } else {
                updateUnifiedButton(!!state.currentWallet);
            }
        }
    }

    async function connectWallet() {
        try {
            state.isManualConnection = true;
            setButtonLoading(true, 'Підключення...');

            await tonConnectUI.connectWallet();
        } catch (error) {
            state.isManualConnection = false;
            updateUnifiedButton(false);

            const errorMessages = {
                'User rejected': 'Подключение отклонено пользователем',
                'timeout': 'Время ожидания истекло. Попробуйте снова'
            };

            const messageType = error.message.includes('User rejected') ? 'warning' : 'error';
            const message = Object.keys(errorMessages).find(key => error.message.includes(key))
                ? errorMessages[Object.keys(errorMessages).find(key => error.message.includes(key))]
                : 'Ошибка подключения кошелька';

            if (typeof showFlashMessage === 'function') {
                showFlashMessage(message, messageType);
            }
        } finally {
            setButtonLoading(false);
        }
    }

    async function disconnectWallet() {
        try {
            await tonConnectUI.disconnect();
            closeWalletDropdown();
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Кошелек успешно отключен', 'success');
            }
        } catch (error) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Ошибка отключения кошелька', 'error');
            }
        }
    }

const TOKEN_CONFIG = {
    'usdt': {
        type: 'usdt',
        aliases: ['usdt', 'tether'],
        isJetton: true,
        masterAddress: {
            testnet: 'kQDF65L0_qkmjO-KMSGoLhfakB3xpRf-AVy8aMjB2u-emUiJ',
            mainnet: 'EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs'
        }
    },
    'ton': {
        type: 'ton',
        aliases: ['ton', 'toncoin'],
        isJetton: false
    },
    // Легко добавить новые токены:
    // 'btc': { type: 'bitcoin', aliases: ['btc', 'bitcoin'] },
    // 'eth': { type: 'ethereum', aliases: ['eth', 'ethereum'] }
};

async function convertRawToUserFriendly(rawAddress, isBounceable = true) {
    try {
        // Если адрес уже в user-friendly формате
        if (!rawAddress.startsWith('0:') && !rawAddress.startsWith('-1:')) {
            return rawAddress;
        }

        const network = config.network === 'mainnet' ? '' : 'testnet.';
        const apiUrl = `https://${network}tonapi.io/v2/address/${encodeURIComponent(rawAddress)}/parse`;

        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': 'Bearer AG2WEUQF7NEZWJQAAAACHFOAPKCD6QL5PJV6KPQI7NDGPRFL6GDW56KFKLGRUM7ONXVUJ3A'
            }
        });

        if (!response.ok) {
            throw new Error(`TonAPI Error: ${response.status}`);
        }

        const data = await response.json();

        // Возвращаем bounceable версию для jetton-транзакций
        return isBounceable ? data.bounceable.b64url : data.non_bounceable.b64url;

    } catch (error) {
        console.error('Error converting address:', error);
        return rawAddress;
    }
}

async function getJettonWalletAddressSimple(ownerAddress, jettonMasterAddress) {
    try {
        const network = config.network === 'mainnet' ? '' : 'testnet.';
        const apiUrl = `https://${network}tonapi.io/v2/accounts/${ownerAddress}/jettons/${jettonMasterAddress}`;

        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': 'Bearer AG2WEUQF7NEZWJQAAAACHFOAPKCD6QL5PJV6KPQI7NDGPRFL6GDW56KFKLGRUM7ONXVUJ3A'
            }
        });

        if (!response.ok) {
            throw new Error(`TonAPI Error: ${response.status}`);
        }

        const data = await response.json();

        if (data && data.wallet_address && data.wallet_address.address) {
            const rawAddress = data.wallet_address.address;

            // Конвертируем в user-friendly формат
            const userFriendlyAddress = await convertRawToUserFriendly(rawAddress, true);

            return userFriendlyAddress;
        }

        throw new Error('Invalid response from TonAPI');
    } catch (error) {
        throw error;
    }
}

// Поддерживаемые пары для свапа
const SUPPORTED_SWAP_PAIRS = {
    'usdt-ton': {
        give: 'usdt',
        receive: 'ton',
        handler: 'usdtToTon'
    },
    'ton-usdt': {
        give: 'ton',
        receive: 'usdt',
        handler: 'tonToUsdt'
    }
    // Легко добавить новые пары:
    // 'btc-ton': { give: 'bitcoin', receive: 'ton', handler: 'btcToTon' }
};

function getTokenType(tokenName) {
    if (!tokenName) return null;

    const normalizedName = tokenName.toLowerCase().trim();

    for (const config of Object.values(TOKEN_CONFIG)) {
        if (config.aliases.some(alias => normalizedName.includes(alias))) {
            return config.type;
        }
    }
    return null;
}

function getSwapPair(giveTokenType, receiveTokenType) {
    const pairKey = `${giveTokenType}-${receiveTokenType}`;
    return SUPPORTED_SWAP_PAIRS[pairKey] || null;
}

function createUsdtToTonTransaction(beginCell, poolAddress, recipientAddress, userJettonWalletAddress, usdtAmount) {

    const usdtAmountValue = BigInt(Math.floor(parseFloat(usdtAmount) * 1e9));

    const swapPayload = beginCell()
        .storeUint(0x4, 32)
        .storeCoins(100000000)
        .storeAddress(recipientAddress)
        .endCell();

    const transferBody = beginCell()
        .storeUint(0xf8a7ea5, 32)
        .storeUint(0, 64)
        .storeCoins(usdtAmountValue)
        .storeAddress(poolAddress)
        .storeAddress(recipientAddress)
        .storeUint(0, 1)
        .storeCoins(100000000)
        .storeUint(1, 1)
        .storeRef(swapPayload)
        .endCell();

    return {
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [{
            address: userJettonWalletAddress,
            amount: '200000000',
            payload: transferBody.toBoc().toString("base64")
        }]
    };
}

function createTonToUsdtTransaction(beginCell, poolAddress, recipientAddress, tonAmount, minUsdtOut) {
    // Конвертируем значения в нужный формат
    const tonAmountValue = typeof tonAmount === 'bigint' ? tonAmount : BigInt(Math.floor(parseFloat(tonAmount) * 1e9)); // 9 decimals для TON
    const minUsdtOutValue = typeof minUsdtOut === 'bigint' ? minUsdtOut : BigInt(Math.floor(parseFloat(minUsdtOut) * 1e9)); // 9 decimals для USDT

    const body = beginCell()
        .storeUint(0x3, 32)
        .storeUint(0, 64)
        .storeCoins(minUsdtOutValue)  // ✅ Используем реальное значение минимального USDT
        .storeAddress(recipientAddress)
        .endCell();

    return {
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [{
            address: poolAddress.toString(),
            amount: (tonAmountValue + BigInt(50000000)).toString(),  // ✅ Добавляем tonAmount + 0.05 TON для комиссии
            payload: body.toBoc().toString("base64")
        }]
    };
}

async function sendTestTransaction() {
    if (!state.currentWallet) {
        if (typeof showFlashMessage === 'function') {
            showFlashMessage('Сначала подключите кошелек!', 'warning');
        }
        throw new Error('Wallet not connected');
    }

    try {
        setButtonLoading(true, 'Відправка...');

        const { beginCell, Address } = window.toncore;
        const recipientAddress = Address.parse(state.currentWallet.account.address);
        const poolAddressValue = document.querySelector('#pool-contract-address')?.value;
        const poolAddress = Address.parse(poolAddressValue);

        const giveTokenName = document.querySelector('#select_give option:checked')?.textContent?.trim() || '';
        const receiveTokenName = document.querySelector('#select_get option:checked')?.textContent?.trim() || '';

        // ✅ Получаем значения из полей ввода
        const giveAmount = document.querySelector('input[name="sum1"]')?.value;
        const receiveAmount = document.querySelector('input[name="sum2"]')?.value;

        if (!giveAmount || !receiveAmount) {
            throw new Error('Amount values are missing');
        }

        const giveTokenType = getTokenType(giveTokenName);
        const receiveTokenType = getTokenType(receiveTokenName);

        if (!giveTokenType || !receiveTokenType) {
            throw new Error('Unsupported token selected');
        }

        const swapPair = getSwapPair(giveTokenType, receiveTokenType);

        if (!swapPair) {
            throw new Error(`Swap pair ${giveTokenType}-${receiveTokenType} is not supported`);
        }

        let transaction;

        switch (swapPair.handler) {
            case 'usdtToTon':
                if (!state.userJettonWallet) {
                    throw new Error('Jetton wallet address not found. Please reconnect your wallet.');
                }

                // ✅ Передаем реальные значения из формы
                transaction = createUsdtToTonTransaction(
                    beginCell,
                    poolAddress,
                    recipientAddress,
                    state.userJettonWallet,
                    giveAmount,      // количество USDT которое отдаем
                    receiveAmount    // минимальное количество TON которое получаем
                );
                break;

            case 'tonToUsdt':
                // ✅ Передаем реальные значения из формы
                transaction = createTonToUsdtTransaction(
                    beginCell,
                    poolAddress,
                    recipientAddress,
                    giveAmount,      // количество TON которое отдаем
                    receiveAmount    // минимальное количество USDT которое получаем
                );
                break;

            default:
                throw new Error(`Handler ${swapPair.handler} not implemented`);
        }

        if (typeof showFlashMessage === 'function') {
            showFlashMessage('Отправка транзакции...', 'info');
        }

        const result = await tonConnectUI.sendTransaction(transaction);

        if (typeof showFlashMessage === 'function') {
            showFlashMessage('Транзакция успешно отправлена!', 'success');
        }

        return result;
    } catch (error) {
        const isUserRejection = error.message.includes('declined') || error.message.includes('rejected');
        const message = isUserRejection
            ? 'Транзакция отклонена пользователем'
            : `Ошибка отправки транзакции: ${error.message}`;

        if (typeof showFlashMessage === 'function') {
            showFlashMessage(message, isUserRejection ? 'warning' : 'error');
        }
        throw error;
    } finally {
        setButtonLoading(false);
    }
}

async function handleWalletConnection(wallet) {
    state.currentWallet = wallet;

    if (wallet) {
        if (state.isManualConnection && !state.isInitialLoad) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Кошелек успешно подключен!', 'success');
            }
        }

        state.isManualConnection = false;
        updateAllButtons(true);

        try {
            const walletData = await fetchWalletData(wallet.account.address);
            Object.assign(state.currentWallet, walletData);
            displayWallet(walletData.balance, walletData.shortAddress);

            try {
                const userWalletAddress = wallet.account.address;
                const usdtMasterAddress = TOKEN_CONFIG.usdt.masterAddress[config.network];

                const jettonWalletAddress = await getJettonWalletAddressSimple(
                    userWalletAddress,
                    usdtMasterAddress
                );

                state.userJettonWallet = jettonWalletAddress;

            } catch (jettonError) {
                console.error('Error fetching jetton wallet:', jettonError);
            }

        } catch (error) {
            displayWallet("0.00 TON", wallet.account.address);
            if (!state.isInitialLoad) {
                if (typeof showFlashMessage === 'function') {
                    showFlashMessage('Данные кошелька загружены частично', 'warning');
                }
            }
        }
    } else {
        updateAllButtons(false);
        displayWallet("0$", "");
        closeWalletDropdown();
        state.userJettonWallet = null;
    }

    if (state.isInitialLoad) state.isInitialLoad = false;
}

    function initEventListeners() {
        elements.header.connectBtn?.addEventListener('click', connectWallet);

        elements.header.walletInfoBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleWalletDropdown();
        });

        elements.index.unifiedBtn?.addEventListener('click', async function(e) {
            e.preventDefault();

            if (!state.currentWallet) {
                await connectWallet();
            } else if (isFormValid()) {
                try {
                    const hiddenGiveTokenId = document.querySelector('#hidden_give_token_id');
                    const hiddenReceiveTokenId = document.querySelector('#hidden_receive_token_id');
                    const hiddenSum2 = document.querySelector('#hidden_sum2');

                    if (hiddenGiveTokenId) {
                        hiddenGiveTokenId.value = document.querySelector('#select_give')?.value || '';
                    }
                    if (hiddenReceiveTokenId) {
                        hiddenReceiveTokenId.value = document.querySelector('#select_get')?.value || '';
                    }

                    await sendTestTransaction();

                    const form = e.target.closest('form');
                    if (form) {
                        form.submit();
                    }
                } catch (error) {
                    if (typeof showFlashMessage === 'function') {
                        showFlashMessage('Транзакция не была завершена. Форма не отправлена.', 'error');
                    }
                }
            } else {
                if (!state.isCaptchaValid) {
                    if (typeof showFlashMessage === 'function') {
                        showFlashMessage('Неверный ответ на капчу', 'error');
                    }
                } else {
                    if (typeof showFlashMessage === 'function') {
                        showFlashMessage('Заполните все обязательные поля корректно', 'warning');
                    }
                }
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.isDropdownOpen) {
                closeWalletDropdown();
            }
        });
    }

    window.switchNetwork = function(network) {
        if (network !== 'mainnet' && network !== 'testnet') {
            return;
        }

        config.network = network;

        if (state.currentWallet) {
            window.refreshWalletBalance();
        }
    };

    window.copyWalletAddress = async function() {
        if (!state.currentWallet?.userFriendlyAddress) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Нет адреса кошелька для копирования', 'error');
            }
            return;
        }

        try {
            await navigator.clipboard.writeText(state.currentWallet.userFriendlyAddress);
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Адрес кошелька скопирован!', 'success');
            }
        } catch (error) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Ошибка копирования адреса', 'error');
            }
            prompt('Скопируйте адрес вручную:', state.currentWallet.userFriendlyAddress);
        }
    };

    window.refreshWalletBalance = utils.debounce(async function() {
        if (!state.currentWallet) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Кошелек не подключен', 'error');
            }
            return;
        }

        const { header } = elements;
        if (header.balanceEl) header.balanceEl.textContent = 'Loading...';
        if (header.dropdownBalance) header.dropdownBalance.textContent = 'Updating...';

        try {
            const walletData = await fetchWalletData(state.currentWallet.account.address);
            Object.assign(state.currentWallet, walletData);
            displayWallet(walletData.balance, walletData.shortAddress);
        } catch (error) {
            if (header.balanceEl) header.balanceEl.textContent = '0$';
            if (header.dropdownBalance) {
                header.dropdownBalance.textContent = '0$';
                header.dropdownBalance.classList.add('wallet-balance-small');
            }
            if (typeof showFlashMessage === 'function') {
                showFlashMessage('Ошибка обновления баланса', 'error');
            }
        }
    }, 300);

    window.disconnectWalletFromDropdown = disconnectWallet;

    tonConnectUI.onStatusChange(handleWalletConnection);
    tonConnectUI.onError = (error) => {
        if (typeof showFlashMessage === 'function') {
            showFlashMessage(`Ошибка TON Connect: ${error.message}`, 'error');
        }
    };

    const existingWallet = tonConnectUI.wallet;
    if (existingWallet) {
        tonConnectUI.onStatusChange(existingWallet);
    }

    initEventListeners();

    setTimeout(() => updateUnifiedButton(!!state.currentWallet), 1000);
});