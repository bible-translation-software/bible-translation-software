const $ = window.jQuery;
const csrf = $("input[type=hidden][name=csrfmiddlewaretoken]").val();
const scriptData = JSON.parse(
  document.getElementById("script-data").textContent
);
import { applyDiff, highlightSpellingErrors, displayError } from "./shared.js";

$(function() {
  $(".js-review-category").on("click", function() {
    let $button = $(this);
    let $count = $(this).find(".js-count");
    $button.prop("disabled", true);
    let currentlyHighlighted = $button.data("highlighted") == "highlighted";

    post(scriptData.urlCategory, {
      verseId: parseInt($button.data("verse-id")),
      category: $button.data("category"),
      register: !currentlyHighlighted
    })
      .then(response => {
        $count.text(response.newCount);
        if (response.currentUserVoted) {
          $button.addClass("saved-category--highlighted");
          $button.data("highlighted", "highlighted");
        } else {
          $button.removeClass("saved-category--highlighted");
          $button.data("highlighted", "");
        }
        $button.toggleClass("saved-category--zero", response.newCount == 0);
        $button.prop("disabled", false);
      })
      .catch(err => {
        displayError(err);
      });
  });

  highlightSpellingErrors($(".js-verse-text"));

  $(".js-claim-verse").on("click", function() {
    let $button = $(this);
    let $step = $button.parents(".js-step").first();
    let $claimers = $step.find(".js-claimers");
    $button.prop("disabled", true);
    post(scriptData.urlClaim, {
      bookCode: scriptData.bookCode,
      chapterNumber: scriptData.chapterNumber,
      verseNumber: scriptData.verseNumber,
      step: "translation"
    })
      .then(response => {
        console.log(response);
        if (response.error == "max_claimers") {
          document.location.reload();
          return;
        }
        $button.hide();
        $claimers.empty();
        response.current_claimers.forEach(claimer => {
          $claimers.append(
            $("<img>")
              .attr("src", claimer.pic)
              .attr("title", claimer.full_name)
              .attr("width", "60")
              .attr("height", 60)
              .attr("crossorigin", "anonymous")
          );
        });
        for (let i = response.current_claimers.length; i < 2; i++) {
          $claimers.append($("<i>").addClass("fas fa-user-slash"));
        }
        $step
          .find(".js-reveal-when-claimed")
          .removeAttr("hidden")
          .fadeIn();
      })
      .catch(err => {
        if (err.responseJSON && err.responseJSON.error === "max_claimers") {
          document.location.reload();
          return;
        } else {
          displayError(err);
        }
      });
  });

  $(".js-new-translation").on("click", function() {
    let $verse = $(this)
      .parents(".js-verse")
      .first();
    let $form = $(".js-review-form");
    let $verseTextElement = $verse.find(".js-verse-text");
    let text = $verseTextElement.data("new") || $verseTextElement.text();
    $form.find(".js-textarea").val(text);
    $form.fadeIn().removeAttr("hidden");
    $form.find(".js-textarea").focus();
    $form[0].scrollIntoView({ behavior: "smooth", block: "center" });
  });

  $(".js-insert-text").on("click", function() {
    const textToInsert = $(this).text();
    const $parent = $(this)
      .parents(".js-step")
      .first();
    const $textarea = $parent.find(".js-textarea");
    const cursorStart = $textarea.prop("selectionStart");
    const v = $textarea.val();
    const textBefore = v.substring(0, cursorStart);
    const textAfter = v.substring(cursorStart, v.length);
    $textarea.val(textBefore + textToInsert + textAfter);
    $textarea.prop("selectionStart", cursorStart + textToInsert.length);
    $textarea.prop("selectionEnd", cursorStart + textToInsert.length);
    $textarea.focus();
  });

  $(".js-review-form").on("submit", function() {
    let $form = $(this);
    let correctionText = $($form[0].elements["correction"]).val();
    let allowSubmit = true;
    $(".js-verse-text").each((i, v) => {
      if ($(v).text() == correctionText) {
        // TODO: translate this
        alert(
          "The correction text is the same as a previous correction or the original."
        );
        allowSubmit = false;
        return false; // break
      }
    });
    return allowSubmit;
  });

  $(".js-show-diff")
    .prop("checked", false)
    .on("change", function() {
      applyDiff($(".js-diff-capable"), this.checked);
    })
    .trigger("changed");

  $(".js-show-comment").on("click", function() {
    let $this = $(this);
    let $commentForm = $this
      .parents(".js-comment")
      .first()
      .find(".js-comment-show-this")
      .removeAttr("hidden");
    $commentForm
      .find(".js-comment-textarea")
      .first()
      .val("")
      .focus();
    $this.hide();
  });

  $(".js-comment-textarea").keydown(function(ev) {
    /* control+enter */
    if ((ev.ctrlKey || ev.metaKey) && (ev.keyCode === 13 || ev.keyCode == 10)) {
      $(this)
        .closest("form")
        .submit();
    }
  });

  $(".js-add-missing-slots").each(function() {
    let $slots = $(this);
    let countExisting = $(this).find(".js-avatar-check").length;
    for (let i = 0; i < 2 - countExisting; i++) {
      $slots.append(
        $("<div>")
          .addClass("avatar-check")
          .append($("<div>").addClass("avatar-check__avatar"))
      );
    }
  });
});

async function post(url, data) {
  return $.post({
    url: url,
    data: JSON.stringify(data),
    contentType: "application/json",
    headers: {
      "X-CSRFToken": csrf
    }
  }).promise();
}
