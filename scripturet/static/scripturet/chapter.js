const $ = window.jQuery;
import { applyDiff, highlightSpellingErrors } from "./shared.js";

$(function() {
  $(".js-show-diff")
    .prop("checked", false)
    .on("change", function() {
      applyDiff($(".js-diff-capable"), this.checked);
    })
    .trigger("changed");

  highlightSpellingErrors($(".js-diff-capable"));
});
