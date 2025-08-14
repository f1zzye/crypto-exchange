const changeHeight = () => {
    let vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty("--vh", `${vh}px`);
};
changeHeight();

window.addEventListener("resize", () => {
    changeHeight();
});

function copytext(text) {
    var $tmp = $("<textarea>");
    $("body").append($tmp);
    $tmp.val(text).select();
    document.execCommand("copy");
    $tmp.remove();
}

function initialize_scrollbars(timeout = 0) {
    $(".js-content-scroll").mCustomScrollbar({
        scrollButtons: {
            enable: false,
        },
        scrollInertia: 200,
        horizontalScroll: false,
        autoDraggerLength: true,
        mouseWheel: {
            scrollAmount: 50,
        },
        advanced: {
            autoScrollOnFocus: false,
            autoExpandHorizontalScroll: true,
            updateOnContentResize: true,
        },
        callbacks: {
            onInit: function () {
                const $this = $(this);
                const $activeItem = $this.find(".js-calc-item.active");
                $this.mCustomScrollbar("update"); // Ensure scrollbar is updated
                const scrollToPosition =
                    $activeItem.offset().top - $this.offset().top; // Fine-tune by adjusting -10 if necessary
                if (scrollToPosition > $this.height()) {
                    $(this).mCustomScrollbar(
                        "scrollTo",
                        scrollToPosition - 50,
                        {
                            scrollInertia: 0, // Scroll immediately without inertia
                            timeout: timeout,
                            callbacks: false, // Disable callbacks during scroll
                        }
                    );
                }
            },
        },
    });
}

function initialize_jselect() {
    $(document).Jselect("init", {
        trigger: ".js_my_sel:not(#select_give):not(#select_get)",
        class_ico: "currency_logo",
    });
}
function startDeleteTimer(delete_datetime, delete_text, selector) {
    // Function to pad single digits with leading zero
    function pad(number) {
        return number < 10 ? "0" + number : number;
    }

    // Adjust the date string to ISO 8601 format
    let isoDateString = delete_datetime
        .replace(" GMT", "") // Remove 'GMT'
        .replace(" ", "T") // Replace space between date and time with 'T'
        .replace(/([+-]\d{2})(\d{2})$/, "$1:$2"); // Insert colon in timezone offset

    // Convert to Date object
    let targetDate = new Date(isoDateString);

    // Validate date
    if (isNaN(targetDate.getTime())) {
        console.error("Invalid date format:", delete_datetime);
        return;
    }

    // Use jQuery to select elements using the provided selector
    const $elements = $(selector);

    // Function to update the countdown
    function updateCountdown() {
        let now = new Date();
        let timeDiff = targetDate - now;

        if (timeDiff > 0) {
            // Calculate hours, minutes, and seconds
            let hours = Math.floor(timeDiff / (1000 * 60 * 60));
            let minutes = Math.floor(
                (timeDiff % (1000 * 60 * 60)) / (1000 * 60)
            );
            let seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

            // Format time as HH:MM:SS
            let timeString =
                pad(hours) + ":" + pad(minutes) + ":" + pad(seconds);

            // Update the content of each element
            $elements.each(function () {
                $(this).html(
                    delete_text +
                        ' <span class="time">' +
                        timeString +
                        "</span>"
                );
            });
        } else {
            // Time has expired
            clearInterval(timerInterval);
        }
    }

    // Initial check to see if the date is in the future
    if (targetDate > new Date()) {
        // Update countdown immediately
        updateCountdown();

        // Update countdown every second
        var timerInterval = setInterval(updateCountdown, 1000);
    }
}
$(function () {
    new WOW({ offset: 40 }).init();

    /**************************************************************
     РЎРљР РћР›Р›
     **************************************************************/
    $("body").on("click", "[data-scroll]", function (e) {
        e.preventDefault();
        var hash = "#" + $(this).attr("data-scroll");

        $("html, body")
            .stop()
            .animate(
                {
                    scrollTop: $(hash).offset().top - 100,
                },
                1000
            );
    });

    $(window).scroll(function () {
        var top_scroll =
            window.pageYOffset || document.documentElement.scrollTop;
    });

    /**************************************************************
     РџРћРџРђРџР«
     **************************************************************/
    function openModal(popup_n) {
        $(".popup").fadeOut(800);

        let popup = $('.popup[data-popup="' + popup_n + '"]');
        $(popup).fadeIn(800);
        $("body").addClass("noscroll");
    }

    function closeModal() {
        $(".popup").fadeOut(500);
        $("body").removeClass("noscroll");
    }

    $("body").on("click", "[data-open-popup]", function (e) {
        e.preventDefault();

        openModal($(this).attr("data-open-popup"));
    });
    $(".popup-close").click(function (e) {
        e.preventDefault();

        closeModal();
    });

    $("body").on("click", "[data-open-login]", function (e) {
        e.preventDefault();

        $(".pauth").fadeOut(400);

        let popup = $(
            '.pauth[data-popup="' + $(this).attr("data-open-login") + '"]'
        );
        $(popup).fadeIn(400);
    });
    $("body").on("click", ".js-pauth-close", function (e) {
        e.preventDefault();

        $(".pauth").fadeOut(400);
    });

    $("body").on("click", ".js-open-menu-acc", function (e) {
        $(".js-menu-acc").toggleClass("opened");
    });

    /**************************************************************
     РјРµРЅСЋ
     **************************************************************/
    $(".js-open-nav").click(function (e) {
        $(".pauth").fadeOut(400);
        e.preventDefault();
        $(this).toggleClass("active");
        $(".js-navfix").toggleClass("opened");
        $("body").toggleClass("noscroll");
    });
    $(".js-close-nav").click(function (e) {
        e.preventDefault();
        $(".js-navfix").toggleClass("opened");
        $("body").removeClass("noscroll");
    });

    $(".js-open-nav-acc").click(function (e) {
        $(this).next().fadeToggle();
    });

    /**************************************************************

     **************************************************************/
    const d_now = new Date();
    const d_to = new Date($("#countdown").attr("data-to"));
    const d_locale = $("#countdown").attr("data-locale") || "en";

    if (d_now > d_to) {
        $(".js-countdown").hide();
    } else if ($("#countdown").is(":visible")) {
        $("#countdown").countdown({
            timestamp: d_to,
            locale: d_locale,
        });
    }

    const dm_to = new Date($("#countdown-mobile").attr("data-to"));
    const dm_locale = $("#countdown-mobile").attr("data-locale") || "en";
    if (d_now > dm_to) {
        $(".js-countdown").hide();
    } else if ($("#countdown-mobile").is(":visible")) {
        $("#countdown-mobile").countdown({
            timestamp: dm_to,
            locale: dm_locale,
        });
    }

    new Swiper(".js-reviews-carousel", {
        slidesPerView: 1,
        spaceBetween: 35,
        speed: 400,
        loop: false,
        // simulateTouch: false,

        breakpoints: {
            0: {
                slidesPerView: "auto",
                spaceBetween: 15,
            },
            1024: {
                slidesPerView: "auto",
                spaceBetween: 20,
            },
            1340: {
                slidesPerView: 4,
                spaceBetween: 20,
            },
        },
    });

    /**************************************************************
     CALC
     **************************************************************/
    $(document).on("click", ".calc__amount a", function () {
        const $amount = $(this);
        const value = $amount.data("val");
        const $input = $amount
            .parents(".calc__col")
            .find('.form__input input[type="text"]');
        $input.val(value);
        $amount.removeClass("error");
        $input.parents(".js_wrap_error").removeClass("error");
        $input.trigger("change");
    });

    let leftType = 0;
    let rightType = 0;
    $(document).on("click", ".js-calc-type", function () {
        if ($(this).hasClass("active")) return false;

        const vtype = $(this).attr("data-type");
        const col = $(this).parents(".js-calc-col");

        $(col).find(".js-calc-type").removeClass("active");
        $(this).addClass("active");

        if (vtype == 0) {
            $(col).find(".js-calc-item").removeClass("hide");
        } else {
            $(col).find(".js-calc-item").addClass("hide");
            $(col)
                .find(".js-calc-item-" + vtype)
                .removeClass("hide");
        }

        if ($(this).parents(".js-calc-col-1").length) {
            leftType = vtype;
        } else {
            rightType = vtype;
        }
    });

    $(document).on("click", ".js-calc-table-toggle", function () {
        const col = $(this).parents(".js-calc-col");
        if ($(col).find(".js-calc-table").hasClass("active")) {
            $(col).find(".js-calc-table").removeClass("active");
        } else {
            $(".js-calc-table.active").removeClass("active");
            $(col).find(".js-calc-table").addClass("active");
        }
    });

    window.initializeSelectItems = function () {
        $(".js_my_sel").each(function () {
            const $selectElement = $(this);
            const $itemsContainer = $selectElement.parents(".calc__items");
            const $tagsContainer = $selectElement
                .parents(".calc__col")
                .find(".calc__tags");
            let cTypes = [];

            $selectElement.find("option").each(function () {
                const $option = $(this);
                const value = $option.val();
                const imgSrc = $option.data("img");
                const logoNext = $option.text();
                const isSelected = $option.is(":selected");
                const ctypesData = $option.data("ctypes");
                const curCtypes = ctypesData ? ctypesData.split(" ") : [];
                cTypes = cTypes.concat(curCtypes);

                const $calcItem = $("<div>", {
                    class:
                        "calc__item js-calc-item" +
                        (isSelected ? " active " : " ") +
                        curCtypes
                            .map((type) => `js-calc-item-${type}`)
                            .join(" "),
                    "data-id": value,
                });

                const $iconWrapper = $("<div>", {
                    class: "calc__item-icon",
                });

                const $img = $("<img>", {
                    src: imgSrc,
                    class: "js-calc-item-icon",
                    alt: logoNext,
                });

                $iconWrapper.append($img);
                const $nameDiv = $("<div>", {
                    class: "calc__item-name js-calc-item-name",
                    text: logoNext,
                });

                $calcItem.append($iconWrapper).append($nameDiv);
                $itemsContainer.append($calcItem);
            });

            let uniqueCtypes = [...new Set(cTypes)];
            uniqueCtypes.sort().forEach(function (type, index) {
                let displayType = type.charAt(0).toUpperCase() + type.slice(1);
                $tagsContainer.append(
                    '<div class="calc__tags-btn js-calc-type" data-type="' +
                        type +
                        '">' +
                        displayType +
                        "</div>"
                );
                if (index < uniqueCtypes.length - 1) {
                    $tagsContainer.append('<div class="calc__tags-sep"></div>');
                }
            });

            $itemsContainer.on("click", ".calc__item", function () {
                var $clickedItem = $(this);
                var itemId = $clickedItem.data("id");
                var $option = $selectElement.find(
                    'option[value="' + itemId + '"]'
                );
                if (!$option.prop("selected")) {
                    $option.prop("selected", true);
                    $clickedItem.toggleClass("active");
                    $selectElement.change();
                }
            });
        });

        if (leftType) {
            $(
                '.js-calc-col-1 .js-calc-type[data-type="' + leftType + '"]'
            ).click();
        }
        if (rightType) {
            $(
                '.js-calc-col-2 .js-calc-type[data-type="' + rightType + '"]'
            ).click();
        }
    };

    initializeSelectItems();

    $(".js-calc-search").val("");
    $(document).on("input", ".js-calc-search", function () {
        const col = $(this).parents(".js-calc-col");
        const s = $.trim($(this).val()).toLowerCase();

        $(col)
            .find(".js-calc-item")
            .each(function () {
                if (
                    $(this)
                        .find(".js-calc-item-name")
                        .text()
                        .toLowerCase()
                        .indexOf(s) != -1
                ) {
                    $(this).removeClass("hide");
                } else {
                    $(this).addClass("hide");
                }
            });
    });

    $(".js-copy-buff").click(function (e) {
        e.preventDefault();

        copytext($(this).attr("data-val"));
    });

    $(".js-show-pass").on("click", function (e) {
        e.preventDefault();

        if ($(this).hasClass("view")) {
            $(this).prev().attr("type", "password");
        } else {
            $(this).prev().attr("type", "text");
        }
        $(this).toggleClass("view");
    });

    $(".js-stats-more").click(function (e) {
        e.preventDefault();

        $(this).toggleClass("opened").prev().slideToggle();
    });

    $(".js-profile-val-change").click(function (e) {
        const parent = $(this).parents(".js-profile-val");
        const input = $(parent).find(".js-profile-val-input");
        const t = $(parent).find(".js-profile-val-t");

        if ($(this).attr("data-action") == "edit") {
            $(this).attr("data-action", "save");
            $(parent).addClass("val-change");

            const originalValue = $(input).val();
            $(input).val("");
            $(input).blur().focus().val(originalValue);
        } else {
            $(this).attr("data-action", "edit");
            $(parent).removeClass("val-change");
            $(t).text($(input).val());
        }
    });

    initialize_scrollbars();
    initialize_jselect();
});

function useForm(options) {
    const form = document.querySelector(options.formSelector);
    const resultContainer = document.querySelector(".form_result");

    if (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const actionUrl = form.getAttribute("action");

            const formData = new FormData(form);

            const jsonData = {};
            formData.forEach((value, key) => {
                jsonData[key] = value;
            });

            if (options.onBeforeSubmit) {
                options.onBeforeSubmit();
            }

            fetch(actionUrl, {
                method: options.method,
                body: formData,
            })
                .then((response) => {
                    // resultContainer.textContent = data.message || 'РЈСЃРїРµС€РЅРѕ РѕС‚РїСЂР°РІР»РµРЅРѕ!';
                    // resultContainer.style.color = 'green';

                    if (options.onSuccess) {
                        options.onSuccess(response);
                    }
                })
                .catch((error) => {
                    // console.error('РћС€РёР±РєР°:', error);
                    // resultContainer.textContent = 'РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР° РїСЂРё РѕС‚РїСЂР°РІРєРµ.';
                    // resultContainer.style.color = 'red';

                    if (options.onError) {
                        options.onError();
                    }
                })
                .finally(() => {
                    if (options.onFinally) {
                        options.onFinally();
                    }
                });
        });
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const submitButton = document.querySelector(
        '#create_deposit_form button[type="submit"]'
    );
    const formContainer = document.querySelector(".deposits__form");

    function showMessage(type, message) {
        const oldMessages = formContainer.querySelectorAll(".result-message");
        oldMessages.forEach((el) => el.remove());

        const div = document.createElement("div");
        div.classList.add(
            "result-message",
            type === "success" ? "resulttrue" : "resultfalse"
        );
        div.innerHTML = `<div class="message-text">${message}</div>`;

        formContainer.prepend(div);

        window.scrollTo({
            top: formContainer.offsetTop,
            behavior: "smooth",
        });
    }

    useForm({
        formSelector: "#create_deposit_form",
        method: "POST",
        onBeforeSubmit: () => {
            submitButton.setAttribute("disabled", true);
        },
        onSubmit: () => {
            const oldMessages =
                formContainer.querySelectorAll(".result-message");
            oldMessages.forEach((el) => el.remove());
        },
        onSuccess: async (response) => {
            const data = await response.json();

            if (data.status === "error") {
                showMessage("error", data.status_text || "РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР°");
                submitButton.removeAttribute("disabled");
            } else if (data.status === "success") {
                showMessage(
                    "success",
                    data.status_text || "РћРїРµСЂР°С†РёСЏ РІС‹РїРѕР»РЅРµРЅР° СѓСЃРїРµС€РЅРѕ"
                );
                window.location.href = "/deposits";
            } else {
                showMessage("error", "РќРµРёР·РІРµСЃС‚РЅС‹Р№ СЃС‚Р°С‚СѓСЃ РѕС‚РІРµС‚Р°");
            }
        },
        onError: (error) => {
            submitButton.removeAttribute("disabled");
            showMessage("error", "РћС€РёР±РєР° РїСЂРё РѕС‚РїСЂР°РІРєРµ Р·Р°РїСЂРѕСЃР°");
        },
        onFinally: () => {
            // ...
        },
    });
});