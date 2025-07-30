document.addEventListener('DOMContentLoaded', function () {
    const signupForm = document.getElementById('signupForm');
    const modal = document.querySelector('.pauth[data-popup="reg"]');
    if (signupForm && modal) {
        signupForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(signupForm);

            fetch(signupForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    modal.style.display = "none";
                    signupForm.reset();
                    showFlashMessage(data.message, "success");
                } else {
                    let errors = "";
                    for (let field in data.errors) {
                        errors += data.errors[field].join(" ") + "\n";
                    }
                    showFlashMessage(errors, "error");
                }
            })
            .catch(err => {
                showFlashMessage("Ошибка соединения или сервера. Попробуйте позже.", "error");
            });
        });
    }
});

