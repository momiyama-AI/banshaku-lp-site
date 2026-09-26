/** Pure diagnosis functions. No DOM, storage, network, or random state. */
export const AXES = Object.freeze([
  Object.freeze({ id: 'taste', letters: 'SK', weight: 8 }),
  Object.freeze({ id: 'portion', letters: 'CG', weight: 4 }),
  Object.freeze({ id: 'effort', letters: 'RT', weight: 2 }),
  Object.freeze({ id: 'adventure', letters: 'OA', weight: 1 }),
]);

export function isTypeCode(code) {
  return typeof code === 'string' && /^[SK][CG][RT][OA]$/.test(code);
}

/** Each answer is a choice index (0 or 1), in question order. */
export function scoreAnswers(answers, questions) {
  if (!Array.isArray(answers) || !Array.isArray(questions) ||
      answers.length !== 12 || questions.length !== 12) {
    throw new TypeError('Exactly 12 answers and questions are required.');
  }
  const counts = Object.fromEntries(AXES.flatMap(axis =>
    [...axis.letters].map(letter => [letter, 0])));
  const totals = Object.fromEntries(AXES.map(axis => [axis.id, 0]));
  questions.forEach((question, index) => {
    const axis = AXES.find(item => item.id === question.axis);
    if (!axis || ![0, 1].includes(answers[index]) ||
        question.choices?.length !== 2 ||
        new Set(question.choices.map(choice => choice.letter)).size !== 2 ||
        question.choices.some(choice => !axis.letters.includes(choice.letter))) {
      throw new TypeError('Invalid question or answer.');
    }
    counts[question.choices[answers[index]].letter] += 1;
    totals[axis.id] += 1;
  });
  if (Object.values(totals).some(total => total !== 3)) {
    throw new TypeError('Each axis must have three questions.');
  }
  const winners = AXES.map(axis =>
    counts[axis.letters[0]] > counts[axis.letters[1]] ? axis.letters[0] : axis.letters[1]);
  return {
    code: winners.join(''),
    percentages: winners.map(letter => Math.round(counts[letter] / 3 * 100)),
  };
}

export function oppositeType(code) {
  if (!isTypeCode(code)) throw new TypeError('Invalid type code.');
  return AXES.map((axis, index) =>
    axis.letters[1 - axis.letters.indexOf(code[index])]).join('');
}

/** Stable score ordering: ties retain the recipes.json source order. */
export function recommendRecipes(code, recipes) {
  if (!isTypeCode(code) || !Array.isArray(recipes)) {
    throw new TypeError('Invalid code or recipes.');
  }
  return recipes.map((recipe, index) => {
    if (!isTypeCode(recipe.tags) || typeof recipe.name !== 'string') {
      throw new TypeError('Invalid recipe.');
    }
    const score = AXES.reduce((sum, axis, position) =>
      sum + (recipe.tags[position] === code[position] ? axis.weight : 0), 0);
    return { recipe, index, score };
  }).sort((a, b) => b.score - a.score || a.index - b.index)
    .slice(0, 3).map(item => item.recipe);
}

/** Only the exact public hash format is accepted; no coercion or partial parsing. */
export function parsePercentages(hash) {
  if (typeof hash !== 'string' ||
      !/^#p=(67|100)-(67|100)-(67|100)-(67|100)$/.test(hash)) return null;
  return hash.slice(3).split('-').map(Number);
}

export function shareLinks(name, code, canonical) {
  if (!isTypeCode(code)) throw new TypeError('Invalid type code.');
  const clean = new URL(canonical);
  clean.hash = '';
  clean.search = '';
  const url = clean.href;
  const text = '私は【' + name + '】（' + code + '）でした！あなたの晩酌つまみタイプは？';
  const x = new URL('https://x.com/intent/tweet');
  x.search = new URLSearchParams({ text, url, hashtags: 'つまみ診断,晩酌ラボ', via: 'banshaku_lab' });
  const threads = new URL('https://www.threads.net/intent/post');
  threads.search = new URLSearchParams({ text: text + '\n#つまみ診断\n' + url });
  return { text, url, x: x.href, threads: threads.href };
}
