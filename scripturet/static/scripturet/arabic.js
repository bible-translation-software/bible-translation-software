export { isWordProperlyVowelled };

const diacritics = [
  "\u064b", // FATHATAN
  "\u064c", // DAMMATAN
  "\u064d", // KASRATAN
  "\u064e", // FATHA
  "\u064f", // DAMMA
  "\u0650", // KASRA
  "\u0651", // SHADDA
  "\u0652" // SUKUN
];
const WAW = "\u0648";
const ALEF = "\u0627";
const YEH = "\u064a";
const ALEF_MAKSURA = "\u0649";
const TEH_MARBUTA = "\u0629";
const ALEF_WITH_MADDA = "\u0622";
const HAMZA = "\u0621";
const wordsThatNeedNoVowelling = ["في"];
const allah = "\u0627\u0644\u0644\u0647";

function isWordProperlyVowelled(word) {
  if (word.match(/[\s]/u)) {
    throw new Error("Word expected not to contain whitespace");
  }
  // Remove punctuation
  word = word.replace(/[»«"']/gu, "").replace(/[.,،!?؟:]+$/u, "");
  if (word.replace(/[\u064b-\u0652]/gu, "") == allah) {
    return true;
  }
  word = word.replace(/^(ال|بِال|مِال|وْبِال|وِال|وْمِال|لِل)/u, "");

  if (wordsThatNeedNoVowelling.includes(word)) {
    return true;
  }
  if (word.length == 0) {
    return true;
  }
  let split = word.match(/.[\u064b-\u0652]*/gu);
  let letterBefore = null;
  let rv = true;
  for (const [index, letter] of split.entries()) {
    let isLastLetter = index == split.length - 1;
    if ([WAW, ALEF, YEH, ALEF_MAKSURA].includes(letter) && letterBefore) {
      // pass
    } else if (letter == ALEF && !letterBefore) {
      // pass
    } else if ([TEH_MARBUTA, HAMZA].includes(letter) && isLastLetter) {
      // pass
    } else if (letter == ALEF_WITH_MADDA) {
      // pass
    } else if (!letter.match(/[\u064b-\u0650\u0652]/u)) {
      rv = false;
      break;
    } else if (letter.match(/[\u064b\u064c\u064d]/u) && !isLastLetter) {
      rv = false;
      break;
    }
    for (let diacritic of diacritics) {
      let count = (letter.match(new RegExp(escapeRegExp(diacritic), "g")) || [])
        .length;
      if (count > 1) {
        rv = false;
        break;
      }
    }

    letterBefore = letter;
  }
  return rv;
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // $& means the whole matched string
}
