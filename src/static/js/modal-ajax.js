document.addEventListener('DOMContentLoaded', function () {
    function handleAjaxForm(formId, modalSelector, successCallback, errorCallback) {
        const form = document.getElementById(formId);
        const modal = modalSelector ? document.querySelector(modalSelector) : null;
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                const formData = new FormData(form);

                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (modal) modal.style.display = "none";
                        form.reset();
                        showFlashMessage(data.message, "success");
                        if (data.redirect_url) {
                            setTimeout(() => {
                                window.location.href = data.redirect_url;
                            }, 1000);
                        }
                        if (typeof successCallback === "function") successCallback(data, form, modal);
                    } else {
                        let errors = "";
                        if (data.errors) {
                            for (let field in data.errors) {
                                errors += data.errors[field].join(" ") + "\n";
                            }
                        } else if (data.message) {
                            errors = data.message;
                        }
                        showFlashMessage(errors, "error");
                        if (typeof errorCallback === "function") errorCallback(data, form, modal);
                    }
                })
                .catch(() => {
                    showFlashMessage("Connection or server error. Please try again later.", "error");
                });
            });
        }
    }

    handleAjaxForm('signupForm', '.pauth[data-popup="reg"]');
    handleAjaxForm('signinForm');
});