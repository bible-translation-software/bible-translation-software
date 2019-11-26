(function() {
  "use strict";

  /* We need to check again because of some versions of Safari */
  if (!("noModule" in HTMLScriptElement.prototype)) {
    var message = document
      .getElementById("no-module-script")
      .getAttribute("data-message");
    alert(message);
  }
})();
