jQuery(function (e) {
    var n = {};
    e.fn.JcheckboxInit = function (c) {
        e.extend({}, n, c);
        return e("label input[type=checkbox]:not(.jcheckbox, .not_jcheckbox)").each(function () {
            var c = e(this);
            c.addClass("jcheckbox"), c.parents("label").wrap('<div class="checkbox">'), e(this).prop("checked") && c.parents(".checkbox").addClass("checked"), c.hide()
        }), this
    };
    var t = {};
    e.fn.Jcheckbox = function (c) {
        e.extend({}, t, c);
        return e(document).on("click", ".checkbox label a", function (c) {
            c.stopPropagation()
        }), e(document).on("click", ".checkbox label", function (c) {
            c.stopPropagation()
        }), e(document).on("change", ".checkbox input", function () {
            var c = e(this).parents(".checkbox");
            c.hasClass("checked") ? c.removeClass("checked") : c.addClass("checked")
        }), e(document).on("click", ".checkbox", function () {
            e(this).find("input").prop("checked") ? e(this).find("input").prop("checked", !1) : e(this).find("input").prop("checked", !0), e(this).find("input").trigger("change")
        }), this
    }
});