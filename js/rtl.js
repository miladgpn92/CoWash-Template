(function () {
    "use strict";
    var body = document.body;
    if (!body) {
        return;
    }
    if ((body.getAttribute("dir") || "").toLowerCase() !== "rtl") {
        return;
    }
    document.documentElement.setAttribute("dir", "rtl");
    if (!body.classList.contains("rtl-body")) {
        body.classList.add("rtl-body");
    }
    window.__IS_RTL__ = true;
})();
