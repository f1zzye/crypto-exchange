document.addEventListener('DOMContentLoaded', function () {
    const config = {
        manifestUrl: `${window.location.origin}/tonconnect-manifest.json`,
        buttonRootId: 'ton-connect-header',
        apiEndpoint: '/api/wallet-balance/'
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
        isManualConnection: false
    };

    const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
        manifestUrl: config.manifestUrl,
        buttonRootId: config.buttonRootId
    });

    window.headerTonConnectUI = tonConnectUI;

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
            const response = await fetch(`${config.apiEndpoint}?address=${encodeURIComponent(address)}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return {
                balance: data.balance || "0.00 TON",
                userFriendlyAddress: data.userFriendlyAddress || address,
                shortAddress: data.shortAddress || address
            };
        } catch (error) {
            showFlashMessage('Ошибка загрузки данных кошелька', 'error');
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

    function updateUnifiedButton(connected) {
        const { unifiedBtn, btnText } = elements.index;
        if (!unifiedBtn || !btnText) return;

        btnText.textContent = connected ? 'Обміняти зараз' : 'Підключити гаманець';
        unifiedBtn.disabled = false;
    }

    function updateAllButtons(connected) {
        const { header, index } = elements;

        if (header.connectBtn) header.connectBtn.style.display = connected ? 'none' : 'inline-flex';
        if (header.walletContainer) header.walletContainer.style.display = connected ? 'block' : 'none';
        if (index.walletField) index.walletField.value = connected && state.currentWallet ? state.currentWallet.account.address : '';
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
            index.btnText.textContent = isLoading ? loadingText : (state.currentWallet ? 'Обміняти зараз' : 'Підключити гаманець');
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

            showFlashMessage(message, messageType);
        } finally {
            setButtonLoading(false);
        }
    }

    async function disconnectWallet() {
        try {
            await tonConnectUI.disconnect();
            closeWalletDropdown();
            showFlashMessage('Кошелек успешно отключен', 'success');
        } catch (error) {
            showFlashMessage('Ошибка отключения кошелька', 'error');
        }
    }

    async function sendTestTransaction() {
        if (!state.currentWallet) {
            showFlashMessage('Сначала подключите кошелек!', 'warning');
            throw new Error('Wallet not connected');
        }

        try {
            setButtonLoading(true, 'Відправка...');

            const transaction = {
                validUntil: Math.floor(Date.now() / 1000) + 360,
                messages: [{
                    address: state.currentWallet.account.address,
                    amount: '1000000'
                }]
            };

            showFlashMessage('Отправка транзакции...', 'info');
            const result = await tonConnectUI.sendTransaction(transaction);
            showFlashMessage('Транзакция успешно отправлена!', 'success');

            return result;
        } catch (error) {
            const isUserRejection = error.message.includes('declined') || error.message.includes('rejected');
            const message = isUserRejection
                ? 'Транзакция отклонена пользователем'
                : `Ошибка отправки транзакции: ${error.message}`;

            showFlashMessage(message, isUserRejection ? 'warning' : 'error');
            throw error;
        } finally {
            setButtonLoading(false);
        }
    }

    async function handleWalletConnection(wallet) {
        state.currentWallet = wallet;

        if (wallet) {
            if (state.isManualConnection && !state.isInitialLoad) {
                showFlashMessage('Кошелек успешно подключен!', 'success');
            }

            state.isManualConnection = false;
            updateAllButtons(true);

            try {
                const walletData = await fetchWalletData(wallet.account.address);
                Object.assign(state.currentWallet, walletData);
                updateUnifiedButton(true);
                displayWallet(walletData.balance, walletData.shortAddress);
            } catch (error) {
                updateUnifiedButton(true);
                displayWallet("0.00 TON", wallet.account.address);
                if (!state.isInitialLoad) {
                    showFlashMessage('Данные кошелька загружены частично', 'warning');
                }
            }
        } else {
            updateAllButtons(false);
            updateUnifiedButton(false);
            displayWallet("0$", "");
            closeWalletDropdown();
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
            } else {
                try {
                    await sendTestTransaction();
                    const form = e.target.closest('form');
                    if (form) form.submit();
                } catch (error) {
                    showFlashMessage('Транзакция не была завершена. Форма не отправлена.', 'error');
                }
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.isDropdownOpen) {
                closeWalletDropdown();
            }
        });
    }

    window.copyWalletAddress = async function() {
        if (!state.currentWallet?.userFriendlyAddress) {
            showFlashMessage('Нет адреса кошелька для копирования', 'error');
            return;
        }

        try {
            await navigator.clipboard.writeText(state.currentWallet.userFriendlyAddress);
            showFlashMessage('Адрес кошелька скопирован!', 'success');
        } catch (error) {
            showFlashMessage('Ошибка копирования адреса', 'error');
            prompt('Скопируйте адрес вручную:', state.currentWallet.userFriendlyAddress);
        }
    };

    window.refreshWalletBalance = utils.debounce(async function() {
        if (!state.currentWallet) {
            showFlashMessage('Кошелек не подключен', 'error');
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
            showFlashMessage('Ошибка обновления баланса', 'error');
        }
    }, 300);

    window.disconnectWalletFromDropdown = disconnectWallet;

    tonConnectUI.onStatusChange(handleWalletConnection);
    tonConnectUI.onError = (error) => showFlashMessage(`Ошибка TON Connect: ${error.message}`, 'error');

    const existingWallet = tonConnectUI.wallet;
    if (existingWallet) {
        tonConnectUI.onStatusChange(existingWallet);
    }

    initEventListeners();
});