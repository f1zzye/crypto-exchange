jQuery(function (a) {
    var r = {key: "", value: "", days: "7", domain: window.location.origin + "/"};
    a.fn.PHPCookie = function (i, t) {
        var e = a.extend({}, r, void 0, t), n = (a(this), a.trim(e.key)), o = e.value, t = a.trim(e.days),
            e = a.trim(e.domain);
        return "set" == i && a.post(e + "request-setc.html", {key: n, value: o, days: t}, function (i) {
        }), this
    }
});