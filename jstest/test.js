/* eslint-env node */
import { isWordProperlyVowelled } from "../scripturet/static/scripturet/arabic.js";
import fs from "fs";
import path from "path";
import { dirname } from "path";
import { fileURLToPath } from "url";

let success = true;
let dirnamePath = dirname(fileURLToPath(import.meta.url));

let correct = fs.readFileSync(
  path.resolve(dirnamePath, "correctly_vowelled.txt"),
  "utf8"
);

for (let word of correct.split(/\s+/u)) {
  if (word == "") {
    continue;
  }
  if (!isWordProperlyVowelled(word)) {
    success = false;
    console.error(`Word expected to be considered properly vowelled ${word}`);
  }
}

let incorrect = fs.readFileSync(
  path.resolve(dirnamePath, "incorrectly_vowelled.txt"),
  "utf8"
);

for (let word of incorrect.split(/\s+/u)) {
  if (word == "") {
    continue;
  }
  if (isWordProperlyVowelled(word)) {
    success = false;
    console.error(`Word expected to be considered improperly vowelled ${word}`);
  }
}

process.exit(success ? 0 : 1);
