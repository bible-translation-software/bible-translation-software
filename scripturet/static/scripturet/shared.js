const $ = window.jQuery;
const Diff = window.Diff;

export { applyDiff, highlightSpellingErrors, displayError };

import { isWordProperlyVowelled } from "./arabic.js";

$(function() {
  $(".js-alert-title").on("click", function() {
    let title = $(this).attr("title");
    if (title) {
      alert(title);
    }
  });
});

function applyDiff($elements, show) {
  $elements.each(function() {
    let $this = $(this);
    let original = $this.data("original");
    let newText = $this.data("new") || $this.text();
    $this.data("new", newText);
    if (!original) {
      console.error("Could not find original text");
    } else if (show) {
      let diff = Diff.diffWords(original, newText);
      $this.empty();
      let previousSpecial = false;
      diff.forEach(part => {
        if (previousSpecial) {
          $this.append(document.createTextNode(" "));
        }
        if (part.added) {
          let $element = $("<ins>").append(document.createTextNode(part.value));
          $this.append($element);
          $element.addClass("highlight--inserted");
          previousSpecial = true;
        } else if (part.removed) {
          let $element = $("<del>").append(document.createTextNode(part.value));
          $this.append($element);
          $element.addClass("highlight--deleted");
          previousSpecial = true;
        } else {
          let $span = $("<span>").append(document.createTextNode(part.value));
          $this.append($span);
          previousSpecial = false;
        }
      });
    } else {
      // hide diff
      $this.text(newText);
    }
  });
  highlightSpellingErrors($elements);
}

function highlightSpellingErrors($elements) {
  $elements.each(function() {
    let $element = $(this);
    highlightSpellingErrors($element.children());
    $element
      .contents()
      .filter(function() {
        return this.nodeType === 3;
      })
      .each(function() {
        let words = $(this)
          .text()
          .split(/(\s+)/u);
        let newHtml = "";
        for (let word of words) {
          if (word.match(/^\s+$/u)) {
            newHtml = newHtml + escapeHTML(word);
          } else if (isWordProperlyVowelled(word)) {
            newHtml = newHtml + escapeHTML(word);
          } else {
            newHtml =
              newHtml +
              '<span class="highlight-error--spelling">' +
              escapeHTML(word) +
              "</span>";
          }
        }
        $(this).replaceWith(newHtml);
      });
  });
}

function escapeHTML(string) {
  return string
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function displayError(error) {
  console.error(error);
  let string;
  if (typeof error === "string") {
    string = error;
  } else if (
    typeof error === "object" &&
    error.responseJSON &&
    error.responseJSON.error
  ) {
    string = JSON.stringify(error.responseJSON);
  } else if (typeof error === "object" && error.responseText) {
    string = error.responseText;
  } else {
    string = "An error occurred";
  }
  window.UIkit.modal.alert(
    '<h1 style="text-align: center">Error</h1><div dir=auto>' +
      string +
      "</div>"
  );
}
