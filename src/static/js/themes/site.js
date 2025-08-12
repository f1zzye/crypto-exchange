jQuery(function ($) {

    /* color */
    $('.changescheme_button').on('click', function () {
        $('.changescheme_ul').show();
    });

    $(document).on('click', function (event) {
        if ($(event.target).closest(".changescheme_button, .changescheme_ul").length) return;
        $('.changescheme_ul').hide();
    });
    /* end color */

    /* fix div */
    function fix_div() {
        var hei = 0;
        if ($('#wpadminbar').length > 0) {
            if ($('#wpadminbar').css('position') == 'fixed') {
                hei = parseInt($('#wpadminbar').height());
            }
        }
        var npos = $(window).scrollTop();
        var wid = $(window).width();

        $('.fix_div').each(function () {
            var one = parseInt($(this).offset().top) - hei;
            var to_fix = $(this).attr('fix-id');
            var plus_fix = parseInt($(this).attr('fix-top'));
            if (wid >= 310) {
                if (npos > one) {
                    $('#' + to_fix).css({'position': 'fixed', 'top': (hei + plus_fix)}).addClass('fix_elem');
                } else {
                    $('#' + to_fix).css({'position': 'absolute', 'top': '0px'}).removeClass('fix_elem');
                }
            } else {
                $('#' + to_fix).css({'position': 'absolute', 'top': '0px'}).removeClass('fix_elem');
            }
        });
    }

    $(window).on('scroll', function () {
        fix_div();
    });
    $(window).on('resize', function () {
        fix_div();
    });
    $(document).ready(function () {
        fix_div();
    });
    fix_div();
    /* end fix div */

    /* social link */
    $('.social_link').on('click', function () {
        var link_url = $(this).attr('href');
        window.open(link_url, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=600,width=600');

        return false;
    });
    /* end social link */

    /* lang */
    $('.langlist_title').on('click', function () {
        $('.langlist_ul').toggle();
    });

    $(document).on('click', function (event) {
        if ($(event.target).closest(".langlist_title, .langlist_ul").length) return;
        $('.langlist_ul').hide();
    });
    /* end lang */

    /* Chat button */
    $('.btn--chat').on('click', function () {
        $ZSIQChatWindow.openChatWindow();
    });

    $('.topbar_icon_tab').on('click', function () {
        $('.topbar_icon_tabul').addClass('open');
    });

    $(document).on('click', function (event) {
        if ($(event.target).closest(".topbar_icon_tab, .topbar_icon_tabul").length) return;
        $('.topbar_icon_tabul').removeClass('open');
    });

    function contacts_menu() {
        $('.topbar_icon_wrap').removeClass('adaptive');
        var hei_start = $('.topbar').height();
        $('.topbar_icon').show();
        var hei_now = $('.topbar_contain').height();
        if (hei_now > hei_start) {
            $('.topbar_icon_wrap').addClass('adaptive');
        }
    }

    $(window).on('scroll', function () {
        contacts_menu();
    });
    $(window).on('resize', function () {
        contacts_menu();
    });
    $(document).ready(function () {
        contacts_menu();
    });
    contacts_menu();

    $(document).on('click', '.js_shwohide_items', function () {
        var par = $(this).parents('.js_shwohide_wrap');
        var title_no = $(this).attr('data-no');
        var title_yes = $(this).attr('data-yes');
        if ($(this).hasClass('active')) {
            par.find('.js_shwohide_item.hide_item').hide();
            $(this).html(title_no);
        } else {
            par.find('.js_shwohide_item.hide_item').show();
            $(this).html(title_yes);
        }
        $(this).toggleClass('active');

        return false;
    });
});