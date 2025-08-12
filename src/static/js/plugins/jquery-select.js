jQuery(function (a) {
    var _ = {trigger: ".js_my_sel", value: "", class_ico: ""};
    a.fn.Jselect = function (s, e) {
        var t = a.extend({}, _, void 0, e), l = (a(this), t.trigger), e = t.value, c = t.class_ico;

        function i(s, e) {
            var t, l;
            0 < s.length && (0 < (t = s.parents(".select_js")).length && (l = t.find('.select_js_ulli[data-value="' + e + '"]').find(".select_js_ulli_ins").html(), s = t.find("select").val(), t.find(".select_js_title_ins").html(l), t.find("select").val(e), t.removeClass("open"), t.find(".select_js_ulli").removeClass("active"), t.find('.select_js_ulli[data-value="' + e + '"]').addClass("active"), t.find(".select_js_ul, .select_js_search").hide(), s != e && t.find("select").trigger("change")))
        }

        return "init" == s && a(l).each(function () {
            var t, s, l, i, e = a(this);
            e.hasClass("jsw") || (e.addClass("jsw"), e.wrap('<div class="select_js">'), t = e.parents(".select_js"), e.css("width"), s = e.css("height"), t.css({height: s}), i = l = "", e.find("option").each(function () {
                var s = a(this).attr("data-img"), e = "";
                void 0 !== s && !1 !== s && (e = '<div class="select_ico ' + c + '" style="background-image: url(' + s + ');"></div>', t.addClass("iselect_js"));
                s = "";
                a(this).prop("selected") && (s = "active", i = e + '<div class="select_txt">' + a(this).html() + '</div><div style="clear: both;"></div>'), l = l + '<div class="select_js_ulli ' + s + '" data-value="' + a(this).val() + '"><div class="select_js_ulli_ins">' + e + '<div class="select_txt">' + a(this).html() + '</div><div class="select_js_abs"></div><div style="clear: both;"></div></div></div>'
            }), e = '<div class="select_js_title"><div class="select_js_title_ins">' + i + '<div class="select_js_abs"></div></div><div style="clear: both;"></div></div><div class="select_js_search"><div class="select_js_search_ins"><input type="search" name="" value="" /></div></div><div class="select_js_ul"><div class="select_js_ul_ins">' + l + "</div></div>", t.find("select").after(e), t.find("select").css({height: s}))
        }), "set" == s && i(l, e), a(document).on("click", ".select_js_title", function () {
            a(".select_js_ul, .select_js_search").hide(), a(".select_js_search input").val(""), a(this).parents(".select_js").find(".select_js_ulli").show(), a(this).parents(".select_js").addClass("open"), a(this).parents(".select_js").find(".select_js_ul, .select_js_search").show(), a(this).parents(".select_js").find(".select_js_search input").focus(), a(this).parents(".select_js").find(".select_js_ul").stop(!0, !0).animate({scrollTop: 0}, 0, function () {
                var s = a(this).parents(".select_js").find(".select_js_ul").find(".select_js_ulli.active").position().top;
                a(this).parents(".select_js").find(".select_js_ul").animate({scrollTop: s}, 500)
            })
        }), a(document).on("click", ".select_js_ulli", function () {
            var s = a(this).attr("data-value");
            i(a(this).parents(".select_js").find("select"), s)
        }), a(document).on("click", function (s) {
            a(s.target).closest(".select_js").length || (a(".select_js_ul, .select_js_search").hide(), a(".select_js").removeClass("open"), s.stopPropagation())
        }), a(document).ChangeInput({
            trigger: ".select_js_search input", success: function (s) {
                var e, t;
                s = (e = s).parents(".select_js"), 0 < (t = a.trim(e.val()).toLowerCase()).length ? (s.find(".select_js_ulli").hide(), s.find(".select_js_ulli").each(function () {
                    a(this).find(".select_txt").html().toLowerCase().indexOf(t) + 1 && a(this).show()
                })) : s.find(".select_js_ulli").show()
            }
        }), this
    }
});