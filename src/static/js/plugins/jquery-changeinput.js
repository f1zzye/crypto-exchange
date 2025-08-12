jQuery(function (p) {
    var l = {
        trigger: ".changeinput", changetime: 800, success: function () {
        }
    };
    p.fn.ChangeInput = function (n) {
        var t = p.extend({}, l, n), i = (p(this), t.trigger), u = parseInt(t.changetime), e = t.success, c = [], s = [],
            h = "", a = "", o = 0;

        function r(n) {
            return void 0 !== n.attr("js-change-input-uniq") ? n.attr("js-change-input-uniq") : (o += 1, n.attr("js-change-input-uniq", o), o)
        }

        function g(n) {
            e.apply(null, [n])
        }

        function f(n, t, i) {
            c[n] == t && c[n] !== s[n] && (g(i), s[n] = t)
        }

        return p(document).on("search", i, function () {
            h = r(p(this)), a = p(this).val(), c[h] !== a && (g(p(this)), s[h] = a), c[h] = a
        }), p(document).on("change", i, function () {
            h = r(p(this)), a = p(this).val(), c[h] !== a && (g(p(this)), s[h] = a), c[h] = a
        }), p(document).on("keyup", i, function (n) {
            h = r(p(this)), a = p(this).val(), c[h] = a, setTimeout(f, u, h, a, p(this))
        }), this
    }
});