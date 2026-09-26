import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { scoreAnswers } from '../../shindan/assets/core.js';

const questions = JSON.parse(readFileSync(new URL('../../shindan/data/questions.json', import.meta.url)));
const source = readFileSync(new URL('../../shindan/assets/quiz.js', import.meta.url), 'utf8').replace(/^import .*;\n/, '');

class Element {
  constructor() { this.events = {}; this.children = []; this.attributes = {}; this.hidden = true; }
  addEventListener(name, callback) { this.events[name] = callback; }
  setAttribute(name, value) { this.attributes[name] = value; }
  replaceChildren(...children) { this.children = children; }
  append(child) { this.children.push(child); }
  focus() {}
  click() { this.events.click({ detail: 1 }); }
}

async function setup(reduced, failFetch = false) {
  const nodes = new Map();
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, new Element());
    return nodes.get(id);
  };
  const timers = [], locations = [], events = {};
  const context = {
    scoreAnswers,
    document: { querySelector: node, createElement: () => new Element() },
    fetch: async () => ({ ok: !failFetch, json: async () => questions }),
    window: {
      matchMedia: () => ({ matches: reduced }),
      location: { assign: url => locations.push(url) },
      setTimeout: (callback, delay) => timers.push({ callback, delay }),
      addEventListener: (name, callback) => { events[name] = callback; },
      scrollTo() {},
    },
  };
  vm.runInNewContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  return { node, timers, locations, events };
}

test('normal motion shows judging and waits exactly 800ms before routing', async () => {
  const app = await setup(false);
  assert.equal(app.node('#start').disabled, false);
  app.node('#start').click();
  assert.equal(app.node('#back').disabled, true);
  for (let i = 0; i < 12; i++) {
    assert.equal(app.node('#counter').textContent, 'Q' + (i + 1) + ' / 12');
    app.node('#choices').children[0].click();
  }
  assert.equal(app.node('#pending').hidden, false);
  assert.equal(app.node('#quiz').hidden, true);
  assert.equal(app.locations.length, 0);
  assert.equal(app.timers.length, 1);
  assert.equal(app.timers[0].delay, 800);
  app.timers[0].callback();
  assert.deepEqual(app.locations, ['/shindan/result/sgra/#p=67-67-67-67']);
});

test('reduced motion routes immediately, and changing an answer replaces its score', async () => {
  const app = await setup(true);
  app.node('#start').click();
  app.node('#choices').children[0].click();
  app.node('#back').click();
  assert.equal(app.node('#choices').children[0].attributes['aria-pressed'], 'true');
  app.node('#choices').children[1].click();
  for (let i = 1; i < 12; i++) app.node('#choices').children[0].click();
  assert.equal(app.timers.length, 0);
  assert.deepEqual(app.locations, ['/shindan/result/kgra/#p=67-67-67-67']);
  app.events.pageshow({ persisted: true });
  assert.equal(app.node('#intro').hidden, false);
  assert.equal(app.node('#pending').hidden, true);
});

test('failed data load disables the start button and offers retry', async () => {
  const app = await setup(false, true);
  assert.equal(app.node('#start').disabled, true);
  assert.equal(app.node('#load-error').hidden, false);
  assert.equal(app.node('#retry').hidden, false);
});
