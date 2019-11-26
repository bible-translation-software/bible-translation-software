document.querySelectorAll(".js-choose-email").forEach(element => {
  element.addEventListener("click", () => {
    document.querySelectorAll(".js-step-2").forEach(element => {
      element.removeAttribute("hidden");
      element.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });
});
document.querySelectorAll(".js-choose-sign-in").forEach(element => {
  element.addEventListener("click", () => {
    document.querySelectorAll(".js-step-3").forEach(element => {
      element.removeAttribute("hidden");
      element.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    document.querySelector(".js-step-3 input#id_login").focus();
  });
});
