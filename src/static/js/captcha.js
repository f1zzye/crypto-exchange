function reloadCaptcha(event) {
    event.preventDefault();

    const reloadBtn = event.target;
    const originalText = reloadBtn.innerHTML;

    fetch(window.location.href, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const img1 = document.querySelector('.captcha1') || document.querySelector('img[class*="captcha"]');
            const img2 = document.querySelector('.captcha2') || document.querySelectorAll('img[class*="captcha"]')[1];
            const operation = document.querySelector('.captcha_sym') || document.querySelector('[class*="captcha_sym"]');
            const input = document.getElementById('captcha-input') || document.querySelector('input[name="number"]');

            if (img1) img1.src = data.img1;
            if (img2) img2.src = data.img2;
            if (operation) operation.textContent = data.operation;
            if (input) input.value = '';

            reloadBtn.innerHTML = originalText;
            reloadBtn.style.animation = '';

            console.log('Капча успешно обновлена');
        })
        .catch(error => {
            console.error('Ошибка при обновлении капчи:', error);

            reloadBtn.innerHTML = originalText;
            reloadBtn.style.animation = '';

            alert('Не удалось обновить капчу. Попробуйте еще раз.');
        });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}