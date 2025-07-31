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
    autoHideMessage(messageDiv);
}

function closeFlashMessage(btn) {
    const messageDiv = btn.closest('.flash-message');
    if (messageDiv) {
        hideMessage(messageDiv);
    }
}

function hideMessage(messageDiv) {
    if (messageDiv && messageDiv.parentElement) {
        messageDiv.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            if (messageDiv.parentElement) {
                messageDiv.remove();
            }
        }, 300);
    }
}

function autoHideMessage(messageDiv) {
    setTimeout(() => {
        hideMessage(messageDiv);
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message, index) => {
        const closeBtn = message.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                closeFlashMessage(this);
            });
        }
        setTimeout(() => {
            autoHideMessage(message);
        }, index * 200);
    });
});