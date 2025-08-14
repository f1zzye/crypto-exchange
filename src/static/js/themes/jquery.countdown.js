(function ($) {

    // Number of seconds in every time division
    var days = 24 * 60 * 60,
        hours = 60 * 60,
        minutes = 60;

    // Creating the plugin
    $.fn.countdown = function (prop) {

        var options = $.extend({
            callback: function () {
            },
            timestamp: 0,
            locale: 'en_US',
        }, prop);

        var left, d, h, m, s, positions;

        // Initialize the plugin
        init(this, options);

        positions = this.find('.countdown__position');

        (function tick() {

            // Time left
            left = Math.floor((options.timestamp - (new Date())) / 1000);

            if (left < 0) {
                left = 0;
            }

            // Number of days left
            d = Math.floor(left / days);
            updateDuo(0, 1, d);
            left -= d * days;

            // Number of hours left
            h = Math.floor(left / hours);
            updateDuo(2, 3, h);
            left -= h * hours;

            // Number of minutes left
            m = Math.floor(left / minutes);
            updateDuo(4, 5, m);
            left -= m * minutes;

            // Number of seconds left
            s = left;
            updateDuo(6, 7, s);

            // Calling an optional user supplied callback
            options.callback(d, h, m, s);

            // Scheduling another call of this function in 1s
            setTimeout(tick, 1000);
        })();

        // This function updates two digit positions at once
        function updateDuo(minor, major, value) {
            switchDigit(positions.eq(minor), Math.floor(value / 10) % 10);
            switchDigit(positions.eq(major), value % 10);
        }

        return this;
    };


    function init(elem, options) {
        elem.addClass('countdown');

        const translations = {
            en_US: ['Days', 'Hours', 'Minutes', 'Seconds'],
            ru_RU: ['Р”РЅРµР№', 'Р§Р°СЃРѕРІ', 'РњРёРЅСѓС‚', 'РЎРµРєСѓРЅРґ'],
            ua_UA: ['Р”РЅС–РІ', 'Р“РѕРґРёРЅ', 'РҐРІРёР»РёРЅ', 'РЎРµРєСѓРЅРґ']
        };

        const tt = translations[options.locale] || translations['en_US'];
        // Creating the markup inside the container
        $.each(['Days', 'Hours', 'Minutes', 'Seconds'], function (i) {
            $('<span class="countdown__item count' + this + '">').html(
                '<span class="countdown__position">\
                    <span class="countdown__digit static">0</span>\
                </span>\
                <span class="countdown__position">\
                    <span class="countdown__digit static">0</span>\
                </span>\
                <span class="countdown__suff">' + tt[i] + '</span>'
            ).appendTo(elem);

            if (this != "Seconds") {
                // elem.append('<span class="countDiv countDiv'+i+'"></span>');
            }
        });

    }

    // Creates an animated transition between the two numbers
    function switchDigit(position, number) {

        var digit = position.find('.countdown__digit')

        if (digit.is(':animated')) {
            return false;
        }

        if (position.data('digit') == number) {
            // We are already showing this number
            return false;
        }

        position.data('digit', number);

        var replacement = $('<span>', {
            'class': 'countdown__digit',
            css: {
                // top:'-2.1em',
                opacity: 1
            },
            html: number
        });

        // The .static class is added when the animation
        // completes. This makes it run smoother.

        digit
            .removeClass('static')
            .animate({opacity: 1}, 'fast', function () {
                digit
                    .before(replacement).remove();
            })

        replacement
            .delay(100)
            .animate({top: 0, opacity: 1}, 'fast', function () {
                replacement.addClass('static');
            });
    }
})(jQuery);