jQuery(function (s) {
    var h = {trigger: ".admintable table", interval: 500, min_width: 600};
    s.fn.AdaptiveTable = function (t) {
        var t = s.extend({}, h, t), e = t.trigger, a = t.interval, i = t.min_width;

        function n() {
            s(e).each(function () {
                s(this).hasClass("has_adaptive_wrap") || (s(this).wrap('<div class="adaptive_wrap"></div>'), s(this).addClass("has_adaptive_wrap"));
                var t = s(this).height();
                s(".adaptive_wrap").css({"min-height": t + "px"});
                var e, a, t = parseInt(s(document).width());
                i <= t && ((e = s(this)).removeClass("has_adaptive").addClass("not_adaptive"), s(".not_adaptive_content").show(), s(".has_adaptive_content").hide(), e.find("thead").show(), e.find("tbody tr").removeClass("one_item"), e.find("tbody td").removeClass("one_item_line"), e.find("tbody td .one_item_label").hide()), s(this).parents(".adaptive_wrap").width() < s(this).width() && ((e = s(this)).addClass("has_adaptive").removeClass("not_adaptive"), s(".not_adaptive_content").hide(), s(".has_adaptive_content").show(), e.find("thead").hide(), e.find("tbody tr").addClass("one_item"), e.find("tbody td").addClass("one_item_line"), e.find("tbody td .one_item_label").show(), e.find(".one_item_label").length < 1 && (a = [], e.find("thead:first tr th").each(function (t) {
                    a[t] = s(this).html()
                }), e.find("tbody tr:not(.noitem)").each(function (t) {
                    s(this).find("td").each(function (t) {
                        t = a[t];
                        s(this).wrapInner('<span class="one_item_content">'), s(this).prepend('<span class="one_item_label">' + t + ":</span>")
                    })
                }))), s(".adaptive_wrap").css({"min-height": "100%"})
            })
        }

        var d = "";
        return s(window).on("resize", function () {
            clearTimeout(d), d = setTimeout(n, a)
        }), n(), this
    }
});