import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { AXES, scoreAnswers, oppositeType, recommendRecipes, parsePercentages, shareLinks } from '../../shindan/assets/core.js';

const read = name => JSON.parse(readFileSync(new URL('../../shindan/data/' + name + '.json', import.meta.url)));
const questions = read('questions');
const data = read('types');
const recipes = read('recipes');

test('all 4096 answers match an independent majority oracle; all 16 types appear equally', () => {
  const appearances = new Map();
  const before = JSON.stringify(questions);
  for (let mask = 0; mask < 4096; mask++) {
    const answers = Array.from({ length: 12 }, (_, i) => (mask >> i) & 1);
    const selected = questions.map((q, i) => q.choices[answers[i]].letter);
    const expected = ['SK', 'CG', 'RT', 'OA'].map(pair => {
      const first = selected.filter(letter => letter === pair[0]).length;
      return { winner: first >= 2 ? pair[0] : pair[1], percent: first === 0 || first === 3 ? 100 : 67 };
    });
    const result = scoreAnswers(answers, questions);
    assert.deepEqual(result, { code: expected.map(x => x.winner).join(''), percentages: expected.map(x => x.percent) });
    assert.deepEqual(answers, Array.from({ length: 12 }, (_, i) => (mask >> i) & 1));
    appearances.set(result.code, (appearances.get(result.code) || 0) + 1);
  }
  assert.deepEqual([...appearances.keys()].sort(), data.types.map(t => t.code).sort());
  assert.ok([...appearances.values()].every(count => count === 256));
  assert.equal(JSON.stringify(questions), before);
});

test('axis metadata agrees with the data contract', () => {
  assert.deepEqual(AXES.map(a => [a.id, a.letters, a.weight]),
    data.axes.map(a => [a.id, a.letters.join(''), a.weight]));
});

test('reversing all four letters twice returns the original type', () => {
  for (const { code } of data.types) {
    const opposite = oppositeType(code);
    assert.ok([...code].every((char, i) => char !== opposite[i]));
    assert.equal(oppositeType(opposite), code);
  }
  assert.equal(oppositeType('SCRO'), 'KGTA');
});

test('all types get three distinct recipes without mutating the data', () => {
  const before = JSON.stringify(recipes);
  for (const { code } of data.types) {
    const result = recommendRecipes(code, recipes);
    assert.equal(result.length, 3);
    assert.equal(new Set(result.map(r => r.name)).size, 3);
  }
  assert.equal(JSON.stringify(recipes), before);
});

test('axis weights prioritize taste, portion, effort, and adventure in that order', () => {
  const fixture = data.types.map(t => ({ name: t.code, tags: t.code, url: '' }));
  for (const { code } of data.types) {
    assert.deepEqual(recommendRecipes(code, fixture).map(r => r.tags), [
      code,
      code.slice(0, 3) + (code[3] === 'O' ? 'A' : 'O'),
      code.slice(0, 2) + (code[2] === 'R' ? 'T' : 'R') + code[3],
    ]);
  }
});

test('recipe score ties keep JSON order, including ties at the third-place boundary', () => {
  const input = ['first', 'second', 'third', 'fourth'].map(name => ({ name, tags: 'SCRA', url: '' }));
  assert.deepEqual(recommendRecipes('SCRO', input).map(r => r.name), ['first', 'second', 'third']);
});

test('reject invalid/incomplete diagnosis data rather than inventing a result', () => {
  assert.throws(() => scoreAnswers([], questions));
  assert.throws(() => scoreAnswers(Array(12).fill(2), questions));
  assert.throws(() => scoreAnswers(Array(12), questions));
  const malformed = structuredClone(questions);
  malformed[0].choices[1].letter = 'S';
  assert.throws(() => scoreAnswers(Array(12).fill(0), malformed));
  for (const code of ['scro', 'SCROO', '', 'ABCD', null]) {
    assert.throws(() => oppositeType(code));
  }
});

test('only strict 67/100 hashes expose personal percentages', () => {
  assert.deepEqual(parsePercentages('#p=67-100-67-100'), [67, 100, 67, 100]);
  for (const bad of ['', '#', '#p=66-100-67-100', '#p=67-100-67', '#p=067-100-67-100',
    '#p=67-100-67-100&x=1', '#p=67-100-67-100-', '#p=NaN-100-67-100', null]) {
    assert.equal(parsePercentages(bad), null);
  }
});

test('X and Threads share the canonical hash-free result with the exact text', () => {
  const result = shareLinks('冷奴ミニマリスト', 'SCRO', 'https://example.test/shindan/result/scro/?utm=x#p=67-100-67-100');
  assert.equal(result.url, 'https://example.test/shindan/result/scro/');
  assert.equal(result.text, '私は【冷奴ミニマリスト】（SCRO）でした！あなたの晩酌つまみタイプは？');
  const x = new URL(result.x);
  assert.equal(x.origin + x.pathname, 'https://x.com/intent/tweet');
  assert.equal(x.searchParams.get('url'), result.url);
  assert.equal(x.searchParams.get('text'), result.text);
  assert.equal(x.searchParams.get('hashtags'), 'つまみ診断,晩酌ラボ');
  assert.equal(x.searchParams.get('via'), 'banshaku_lab');
  const threads = new URL(result.threads);
  assert.equal(threads.origin + threads.pathname, 'https://www.threads.net/intent/post');
  assert.equal(threads.searchParams.get('text'), result.text + '\n#つまみ診断\n' + result.url);
});
