(() => {
  "use strict";

  document.querySelectorAll(".navbar-collapse .nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      const navbar = document.querySelector(".navbar-collapse.show");
      if (navbar && window.bootstrap) {
        window.bootstrap.Collapse.getOrCreateInstance(navbar).hide();
      }
    });
  });
})();
