function showFlashMessage(text, type="success") {
    let iconHtml = '';
    if (type === 'success') {
        iconHtml = '<i class="fas fa-check-circle"></i>';
    } else if (type === 'error') {
        iconHtml = '<i class="fas fa-times-circle"></i>';
    } else if (type === 'warning') {
        iconHtml = '<i class="fas fa-exclamation-circle"></i>';
    } else if (type === 'info') {
        iconHtml = '<i class="fas fa-info-circle"></i>';
    } else {
        iconHtml = '<i class="fas fa-bell"></i>';
    }

    let html = `
    <div class="flash-message flash-${type}">
        <div class="flash-icon">${iconHtml}</div>
        <span class="flash-text">${text}</span>
        <button class="flash-close" onclick="closeFlashMessage(this)">
            <i class="fas fa-times"></i>
        </button>
    </div>
    `;

    let container = document.querySelector('.flash-messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages-container';
        document.body.appendChild(container);
    }
    container.insertAdjacentHTML('beforeend', html);

    let messageDiv = container.lastElementChild;

    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (messageDiv.parentElement) {
                    messageDiv.remove();
                }
            }, 300);
        }
    }, 5000);
}