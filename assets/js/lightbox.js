(function () {
  "use strict";

  var dialog = document.getElementById("lightbox");
  if (!dialog || typeof dialog.showModal !== "function") return;

  var image = dialog.querySelector(".lightbox-img");
  var caption = dialog.querySelector(".lightbox-caption");
  var closeButton = dialog.querySelector(".lightbox-close");

  document.querySelectorAll(".project-gallery a").forEach(function (link) {
    link.addEventListener("click", function (event) {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      ) {
        return;
      }

      var thumb = link.querySelector("img");
      if (!thumb) return;

      event.preventDefault();
      image.src = link.href;
      image.alt = thumb.alt;

      var figure = link.closest("figure");
      var source = figure && figure.querySelector("figcaption");
      var text = source ? source.textContent.trim() : "";
      caption.textContent = text;
      caption.hidden = text === "";

      dialog.showModal();
      document.body.classList.add("lightbox-open");
    });
  });

  closeButton.addEventListener("click", function () {
    dialog.close();
  });

  dialog.addEventListener("click", function (event) {
    if (!(event.target instanceof Element) || !event.target.closest(".lightbox-inner")) {
      dialog.close();
    }
  });

  dialog.addEventListener("close", function () {
    image.removeAttribute("src");
    image.alt = "";
    caption.textContent = "";
    caption.hidden = true;
    document.body.classList.remove("lightbox-open");
  });
})();
