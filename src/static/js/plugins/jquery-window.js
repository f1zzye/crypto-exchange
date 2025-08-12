jQuery(function (b) {
    var g = {
        id: "",
        window_class: "",
        insert_div: "",
        close_class: "",
        title: "",
        content: "",
        scrollContent: "",
        shadow: 1,
        draggable: 1,
        enable_button: 0,
        out_close: 0,
        button_title: "",
        button_class: "",
        before: function () {
        },
        after: function () {
        },
        close_after: function () {
        }
    };
    b.fn.JsWindow = function (t, n) {
        var i = b.extend({}, g, void 0, n), o = b(this), s = b.trim(i.id);
        s.length < 1 && (s = Math.floor(1e5 * Math.random()) + 1);
        var d = b.trim(i.window_class), e = b.trim(i.insert_div);
        insert_obj = 0 < e.length ? b(e) : b("body");
        var a = b.trim(i.close_class), w = parseInt(b.trim(i.shadow)), r = parseInt(b.trim(i.draggable)),
            l = parseInt(b.trim(i.enable_button)), c = parseInt(b.trim(i.out_close)), _ = b.trim(i.button_title),
            h = b.trim(i.button_class), u = b.trim(i.title), v = b.trim(i.content), m = b.trim(i.scrollContent),
            n = i.before, e = i.after, f = i.close_after;

        function p() {
            var t = b(window).height() - 40, n = Math.ceil((b(window).height() - b(".standart_window").height()) / 2);
            n < 1 && (n = 20);
            var i = Math.ceil((b(window).width() - b(".standart_window").width()) / 2);
            i < 1 && (i = 0), b(".standart_window:not(.dragged)").css({
                top: n,
                left: i
            }), b(".standart_window").css({"max-height": t, "overflow-y": "auto"})
        }

        return "show" == t ? (n.apply(null, [o]), b(".js_techwindow").remove(), 1 == w && (insert_obj.append('<div class="standart_shadow js_techwindow" id="sh_techwindow_' + s + '"></div>'), b(".standart_shadow").show()), w = "", 0 < m.length && (w = '<div class="standart_window_scrollcontent">' + m + "</div>"), _ = '<div class="standart_window ' + d + ' js_techwindow" id="techwindow_' + s + '"><div class="standart_windowins"><div class="standart_window_ins"><div class="standart_window_title"><div class="standart_window_close js_window_close ' + a + '"></div><div class="standart_window_title_ins">' + u + '</div></div><div class="standart_window_content"><div class="standart_window_content_ins">' + v + '<div class="standart_window_clear"></div></div></div>' + w + (1 == l ? '<div class="standart_window_submit"><input type="submit" class="standart_window_button ' + h + '" name="" value="' + _ + '" /></div>' : "") + "</div></div></div>", insert_obj.append(_), b("#techwindow_" + s).show(), p(), 1 == r && "function" == typeof jQuery && "ui" in jQuery && jQuery.ui && "version" in jQuery.ui && b("#techwindow_" + s).draggable({
            handle: ".standart_window_title",
            start: function () {
                b("#techwindow_" + s).addClass("dragged")
            }
        }), 1 == c && b(document).on("click", function (t) {
            b(t.target).closest("#techwindow_" + s).length < 1 && (b("#techwindow_" + s).remove(), b("#sh_techwindow_" + s).remove())
        }), e.apply(null, [o])) : "hide" == t && (n.apply(null, [o]), b(".js_techwindow").remove(), e.apply(null, [o])), b(window).on("scroll", function () {
            p()
        }), b(window).on("resize", function () {
            p()
        }), b(".js_window_close").on("click", function () {
            b(".js_techwindow").remove(), f.apply(null, [b(this)])
        }), this
    }
});