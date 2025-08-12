jQuery(function (c) {
    var s = {trigger: ".js_timer"};
    c.fn.JTimer = function (t) {
        var t = c.extend({}, s, t).trigger, a = c(t);

        function j(t, a) {
            return 1 == a && t < 10 && (t = "0" + t), t
        }

        return 0 < a.length && setInterval(function () {
            a.each(function () {
                var t = parseInt(c(this).attr("end-time")), a = c(this).attr("data-y"), s = c(this).attr("data-m"),
                    n = c(this).attr("data-d"), r = c(this).attr("data-h"), e = c(this).attr("data-mi"),
                    p = c(this).attr("data-s"), i = parseInt(c(this).attr("data-zero"));
                isNaN(t) || (t = t - 1, c(this).attr("end-time", t), 0 < t ? c(this).html(function (t, a, s, n, r, e, p, i) {
                    if (0 < t) {
                        var c = 0;
                        31536e3 < t && (t -= 31536e3 * (c = parseInt(t / 31536e3)));
                        var h = 0;
                        2592e3 < t && (t -= 2592e3 * (h = parseInt(t / 2592e3)));
                        var u = 0;
                        86400 < t && (t -= 86400 * (u = parseInt(t / 86400)));
                        var l = 0;
                        3600 < t && (t -= 3600 * (l = parseInt(t / 3600)));
                        var d = 0;
                        60 < t && (t -= 60 * (d = parseInt(t / 60)));
                        a = '<span class="jt_y">' + j(c, i) + '<span class="jt_count">' + a + "</span></span> ", s = '<span class="jt_m">' + j(h, i) + '<span class="jt_count">' + s + "</span></span> ", n = '<span class="jt_d">' + j(u, i) + '<span class="jt_count">' + n + "</span></span> ", r = '<span class="jt_h">' + j(l, i) + '<span class="jt_count">' + r + "</span></span> ", e = '<span class="jt_min">' + j(d, i) + '<span class="jt_count">' + e + "</span></span> ", p = '<span class="jt_s">' + j(t, i) + '<span class="jt_count">' + p + "</span></span> ";
                        return 0 < c ? a + s + n + r : 0 < h ? s + n + r + e : 0 < u ? n + r + e + p : 0 < l ? r + e + p : e + p
                    }
                    return "---"
                }(t, a, s, n, r, e, p, i)) : c(this).addClass("ending").html("---"))
            })
        }, 1e3), this
    }, c(document).JTimer()
});