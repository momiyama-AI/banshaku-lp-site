import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import * as core from '../../shindan/assets/core.js';

const data = JSON.parse(readFileSync(new URL('../../shindan/data/types.json', import.meta.url)));
const recipes = JSON.parse(readFileSync(new URL('../../shindan/data/recipes.json', import.meta.url)));
const source = readFileSync(new URL('../../shindan/assets/result.js', import.meta.url), 'utf8')
  .replace(/^import .*;\r?\n/, '');

class Element {
  constructor() {
    this.events = {};
    this.children = [];
    this.textContent = '';
    this.hidden = true;
    this.classList = { toggle() {} };
  }
  addEventListener(name, callback) { this.events[name] = callback; }
  append(child) { this.children.push(child); }
  replaceChildren(...children) { this.children = children; }
  setAttribute() {}
  focus() {}
  select() {}
  querySelector() { return this.children[0]; }
  click() { return this.events.click(); }
}

async function setup(type, origin, clipboardWorks = true) {
  const nodes = new Map();
  const node = selector => {
    if (!nodes.has(selector)) nodes.set(selector, new Element());
    return nodes.get(selector);
  };
  const path = '/shindan/result/' + type.code.toLowerCase() + '/';
  node('#type-name').textContent = type.name;
  // Production canonical intentionally differs from the preview's page URL.
  node('link[rel="canonical"]').href = 'https://banshaku-lp-site.pages.dev' + path;
  node('#copy-fallback').append(new Element());
  const copied = [], nativeShares = [];
  const location = new URL(origin + path + '?utm_source=test#p=67-100-67-100');
  const context = {
    ...core, URL,
    document: {
      body: { dataset: { code: type.code } },
      querySelector: node,
      querySelectorAll: () => [],
      createElement: () => new Element(),
    },
    window: { location, addEventListener() {} },
    navigator: {
      clipboard: { writeText: async url => {
        if (!clipboardWorks) throw new Error('Clipboard unavailable');
        copied.push(url);
      } },
      share: async value => nativeShares.push(value),
    },
    fetch: async () => ({ ok: true, json: async () => recipes }),
  };
  vm.runInNewContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  return { node, copied, nativeShares, expected: origin + path };
}

test('all sharing controls use the viewed deployment for every type, including an unpublished production canonical', async () => {
  const origins = [
    'https://banshaku-lp-site.pages.dev',
    'https://feature-shindan.banshaku-lp-site.pages.dev',
    'https://0dcd74b8.banshaku-lp-site.pages.dev',
  ];
  for (const origin of origins) {
    for (const type of data.types) {
      const app = await setup(type, origin);
      const x = new URL(app.node('#share-x').href);
      assert.equal(x.searchParams.get('url'), app.expected);
      const threads = new URL(app.node('#share-threads').href);
      assert.ok(threads.searchParams.get('text').endsWith('\n' + app.expected));
      await app.node('#copy-link').click();
      assert.deepEqual(app.copied, [app.expected]);
      assert.equal(app.node('#share-more').hidden, false);
      await app.node('#share-more').click();
      assert.equal(app.nativeShares[0].url, app.expected);
      assert.equal(app.nativeShares[0].title, type.name + '（' + type.code + '）');
      assert.equal(app.nativeShares[0].text, x.searchParams.get('text'));
    }
  }
});

test('manual copy fallback also keeps the working preview URL and strips query/hash', async () => {
  const app = await setup(data.types.find(type => type.code === 'KCTO'),
    'https://feature-shindan.banshaku-lp-site.pages.dev', false);
  await app.node('#copy-link').click();
  assert.equal(app.node('#copy-fallback').hidden, false);
  assert.equal(app.node('#copy-fallback').children[0].value, app.expected);
});
