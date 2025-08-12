document.addEventListener('DOMContentLoaded', function() {
    const config = {
        manifestUrl: `${window.location.origin}/tonconnect-manifest.json`,
        buttonRootId: 'ton-connect-header',
        apiEndpoint: '/api/wallet-balance/'
    };

    const headerElements = {
        connectBtn: document.getElementById('header-connect-btn'),
        walletContainer: document.getElementById('wallet-button-container'),
        walletInfoBtn: document.getElementById('header-wallet-info'),
        walletDropdown: document.getElementById('wallet-dropdown'),
        balanceEl: document.querySelector('.wallet-balance-display'),
        addressEl: document.querySelector('.wallet-address-display'),
        btnContent: document.querySelector('.wallet-btn-content'),
        dropdownAddress: document.getElementById('dropdown-wallet-address'),
        dropdownBalance: document.getElementById('dropdown-wallet-balance')
    };

    const indexElements = {
        connectBtn: document.getElementById('custom-connect-btn'),
        disconnectBtn: document.getElementById('custom-disconnect-btn'),
        walletField: document.querySelector('input[name="wallet_address"]')
    };

    let currentWallet = null;
    let isDropdownOpen = false;

    const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
        manifestUrl: config.manifestUrl,
        buttonRootId: config.buttonRootId
    });

    window.headerTonConnectUI = tonConnectUI;

    function parseBalance(balanceStr) {
        if (!balanceStr) return 0;
        if (balanceStr.startsWith('<')) return 0.0099;
        return parseFloat(balanceStr.replace(/[^\d.]/g, '')) || 0;
    }

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
        const balValue = parseBalance(balanceStr);
        const isSmallBalance = balValue === 0 || balValue < 0.01;

        if (headerElements.balanceEl) {
            headerElements.balanceEl.textContent = isSmallBalance ? (balValue === 0 ? "0$" : "< 0.01") : balanceStr;
            headerElements.balanceEl.classList.toggle('wallet-balance-small', isSmallBalance);
        }

        const hasValidAddress = userFriendlyAddress && userFriendlyAddress !== '' && userFriendlyAddress !== 'Connecting...';
        if (headerElements.btnContent) {
            headerElements.btnContent.classList.toggle('only-balance', !hasValidAddress);
        }
        if (headerElements.addressEl) {
            headerElements.addressEl.style.display = hasValidAddress ? '' : 'none';
            if (hasValidAddress) headerElements.addressEl.textContent = userFriendlyAddress;
        }

        if (headerElements.dropdownAddress) headerElements.dropdownAddress.textContent = userFriendlyAddress;
        if (headerElements.dropdownBalance) {
            headerElements.dropdownBalance.textContent = isSmallBalance ? "< 0.01" : balanceStr;
            headerElements.dropdownBalance.classList.toggle('wallet-balance-small', isSmallBalance);
        }
    }

    function updateAllButtons(connected) {
        if (headerElements.connectBtn) {
            headerElements.connectBtn.style.display = connected ? 'none' : 'inline-flex';
        }
        if (headerElements.walletContainer) {
            headerElements.walletContainer.style.display = connected ? 'block' : 'none';
        }

        if (indexElements.connectBtn) {
            indexElements.connectBtn.style.display = connected ? 'none' : 'inline-flex';
            indexElements.connectBtn.disabled = false;
            indexElements.connectBtn.innerHTML = '<span>Connect Wallet</span>';
        }
        if (indexElements.disconnectBtn) {
            indexElements.disconnectBtn.style.display = connected ? 'inline-flex' : 'none';
        }

        if (indexElements.walletField) {
            indexElements.walletField.value = connected && currentWallet ? currentWallet.account.address : '';
        }
    }

    function toggleWalletDropdown() {
        isDropdownOpen ? closeWalletDropdown() : openWalletDropdown();
    }

    function openWalletDropdown() {
        if (!headerElements.walletDropdown) return;

        headerElements.walletDropdown.classList.add('show');
        headerElements.walletInfoBtn?.classList.add('active');
        isDropdownOpen = true;

        setTimeout(() => document.addEventListener('click', handleClickOutside), 100);
    }

    function closeWalletDropdown() {
        headerElements.walletDropdown?.classList.remove('show');
        headerElements.walletInfoBtn?.classList.remove('active');
        isDropdownOpen = false;
        document.removeEventListener('click', handleClickOutside);
    }

    function handleClickOutside(e) {
        if (headerElements.walletContainer && !headerElements.walletContainer.contains(e.target)) {
            closeWalletDropdown();
        }
    }

    async function connectWallet() {
        try {
            if (headerElements.connectBtn) {
                headerElements.connectBtn.disabled = true;
                headerElements.connectBtn.querySelector('span').textContent = 'Connecting...';
            }
            if (indexElements.connectBtn) {
                indexElements.connectBtn.disabled = true;
                indexElements.connectBtn.textContent = 'Connecting...';
            }

            await tonConnectUI.connectWallet();

        } catch (error) {
            if (error.message.includes('User rejected')) {
                showFlashMessage('Подключение отклонено пользователем', 'warning');
            } else if (error.message.includes('timeout')) {
                showFlashMessage('Время ожидания истекло. Попробуйте снова', 'error');
            } else {
                showFlashMessage('Ошибка подключения кошелька', 'error');
            }
        } finally {
            if (headerElements.connectBtn) {
                headerElements.connectBtn.disabled = false;
                headerElements.connectBtn.querySelector('span').textContent = 'Connect Wallet';
            }
            if (indexElements.connectBtn) {
                indexElements.connectBtn.disabled = false;
                indexElements.connectBtn.innerHTML = '<span>Connect Wallet</span>';
            }
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

    headerElements.connectBtn?.addEventListener('click', connectWallet);
    headerElements.walletInfoBtn?.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleWalletDropdown();
    });

    indexElements.connectBtn?.addEventListener('click', connectWallet);
    indexElements.disconnectBtn?.addEventListener('click', disconnectWallet);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isDropdownOpen) {
            closeWalletDropdown();
        }
    });

    window.copyWalletAddress = async function() {
        if (!currentWallet?.userFriendlyAddress) {
            showFlashMessage('Нет адреса кошелька для копирования', 'error');
            return;
        }

        try {
            await navigator.clipboard.writeText(currentWallet.userFriendlyAddress);
            showFlashMessage('Адрес кошелька скопирован!', 'success');
        } catch (error) {
            showFlashMessage('Ошибка копирования адреса', 'error');
            prompt('Скопируйте адрес вручную:', currentWallet.userFriendlyAddress);
        }
    };

    window.refreshWalletBalance = async function() {
        if (!currentWallet) {
            showFlashMessage('Кошелек не подключен', 'error');
            return;
        }

        if (headerElements.balanceEl) headerElements.balanceEl.textContent = 'Loading...';
        if (headerElements.dropdownBalance) headerElements.dropdownBalance.textContent = 'Updating...';

        try {
            const walletData = await fetchWalletData(currentWallet.account.address);
            Object.assign(currentWallet, walletData);
            displayWallet(walletData.balance, walletData.shortAddress);
        } catch (error) {
            if (headerElements.balanceEl) headerElements.balanceEl.textContent = '0$';
            if (headerElements.dropdownBalance) {
                headerElements.dropdownBalance.textContent = '0$';
                headerElements.dropdownBalance.classList.add('wallet-balance-small');
            }

            showFlashMessage('Ошибка обновления баланса', 'error');
        }
    };

    window.disconnectWalletFromDropdown = disconnectWallet;

    tonConnectUI.onStatusChange(async wallet => {
        currentWallet = wallet;

        if (wallet) {
            showFlashMessage('Кошелек успешно подключен!', 'success');
            updateAllButtons(true);

            try {
                const walletData = await fetchWalletData(wallet.account.address);
                Object.assign(currentWallet, walletData);
                displayWallet(walletData.balance, walletData.shortAddress);
            } catch (error) {
                displayWallet("0.00 TON", wallet.account.address);
                showFlashMessage('Данные кошелька загружены частично', 'warning');
            }
        } else {
            updateAllButtons(false);
            displayWallet("0$", "");
            closeWalletDropdown();
        }
    });

    const existingWallet = tonConnectUI.wallet;
    if (existingWallet) {
        tonConnectUI.onStatusChange(existingWallet);
    }

    tonConnectUI.onError = (error) => {
        showFlashMessage(`Ошибка TON Connect: ${error.message}`, 'error');
    };
});