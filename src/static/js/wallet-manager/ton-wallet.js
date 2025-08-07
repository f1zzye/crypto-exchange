document.addEventListener('DOMContentLoaded', function() {
    const config = {
        manifestUrl: 'https://5cc323479e51.ngrok-free.app/tonconnect-manifest.json',
        buttonRootId: 'ton-connect-header',
        apiEndpoint: '/api/wallet-balance/'
    };

    const elements = {
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
            console.error('Error fetching wallet data:', error);
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

        if (elements.balanceEl) {
            elements.balanceEl.textContent = isSmallBalance ? (balValue === 0 ? "0$" : "< 0.01") : balanceStr;
            elements.balanceEl.classList.toggle('wallet-balance-small', isSmallBalance);
        }

        const hasValidAddress = userFriendlyAddress && userFriendlyAddress !== '' && userFriendlyAddress !== 'Connecting...';
        if (elements.btnContent) {
            elements.btnContent.classList.toggle('only-balance', !hasValidAddress);
        }
        if (elements.addressEl) {
            elements.addressEl.style.display = hasValidAddress ? '' : 'none';
            if (hasValidAddress) elements.addressEl.textContent = userFriendlyAddress;
        }

        if (elements.dropdownAddress) elements.dropdownAddress.textContent = userFriendlyAddress;
        if (elements.dropdownBalance) {
            elements.dropdownBalance.textContent = isSmallBalance ? "< 0.01" : balanceStr;
            elements.dropdownBalance.classList.toggle('wallet-balance-small', isSmallBalance);
        }
    }

    function toggleWalletDropdown() {
        isDropdownOpen ? closeWalletDropdown() : openWalletDropdown();
    }

    function openWalletDropdown() {
        if (!elements.walletDropdown) return;

        elements.walletDropdown.classList.add('show');
        elements.walletInfoBtn?.classList.add('active');
        isDropdownOpen = true;

        setTimeout(() => document.addEventListener('click', handleClickOutside), 100);
    }

    function closeWalletDropdown() {
        elements.walletDropdown?.classList.remove('show');
        elements.walletInfoBtn?.classList.remove('active');
        isDropdownOpen = false;
        document.removeEventListener('click', handleClickOutside);
    }

    function handleClickOutside(e) {
        if (elements.walletContainer && !elements.walletContainer.contains(e.target)) {
            closeWalletDropdown();
        }
    }

    async function connectWallet() {
        if (!elements.connectBtn) return;

        try {
            elements.connectBtn.disabled = true;
            elements.connectBtn.querySelector('span').textContent = 'Connecting...';
            await tonConnectUI.connectWallet();
        } catch (error) {
            showFlashMessage('Failed to connect wallet', 'error');
        } finally {
            elements.connectBtn.disabled = false;
            elements.connectBtn.querySelector('span').textContent = 'Connect Wallet';
        }
    }

    elements.connectBtn?.addEventListener('click', connectWallet);
    elements.walletInfoBtn?.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleWalletDropdown();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isDropdownOpen) closeWalletDropdown();
    });

    window.copyWalletAddress = async function() {
        if (!currentWallet?.userFriendlyAddress) {
            showFlashMessage('No wallet address to copy', 'error');
            return;
        }

        try {
            await navigator.clipboard.writeText(currentWallet.userFriendlyAddress);
            showFlashMessage('Address copied to clipboard!', 'success');
        } catch {
            showFlashMessage('Failed to copy address', 'error');
        }
    };

    window.refreshWalletBalance = async function() {
        if (!currentWallet) {
            showFlashMessage('No wallet connected', 'error');
            return;
        }

        if (elements.balanceEl) elements.balanceEl.textContent = 'Loading...';
        if (elements.dropdownBalance) elements.dropdownBalance.textContent = 'Updating...';

        try {
            const walletData = await fetchWalletData(currentWallet.account.address);
            Object.assign(currentWallet, walletData);
            displayWallet(walletData.balance, walletData.shortAddress);
            showFlashMessage('Balance updated successfully!', 'success');
        } catch {
            if (elements.balanceEl) elements.balanceEl.textContent = '0$';
            if (elements.dropdownBalance) {
                elements.dropdownBalance.textContent = '0$';
                elements.dropdownBalance.classList.add('wallet-balance-small');
            }
            showFlashMessage('Failed to update balance', 'error');
        }
    };

    window.disconnectWalletFromDropdown = function() {
        tonConnectUI.disconnect();
        closeWalletDropdown();
        showFlashMessage('Wallet disconnected', 'info');
    };

    tonConnectUI.onStatusChange(async wallet => {
        currentWallet = wallet;

        if (wallet) {
            if (elements.connectBtn) elements.connectBtn.style.display = 'none';
            if (elements.walletContainer) elements.walletContainer.style.display = 'block';

            try {
                const walletData = await fetchWalletData(wallet.account.address);
                Object.assign(currentWallet, walletData);
                displayWallet(walletData.balance, walletData.shortAddress);
            } catch {
                displayWallet("0.00 TON", wallet.account.address);
            }
        } else {
            if (elements.connectBtn) elements.connectBtn.style.display = 'inline-flex';
            if (elements.walletContainer) elements.walletContainer.style.display = 'none';
            displayWallet("0$", "");
            closeWalletDropdown();
        }
    });

    const existingWallet = tonConnectUI.wallet;
    if (existingWallet) {
        tonConnectUI.onStatusChange(existingWallet);
    }
});