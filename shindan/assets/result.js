import { AXES, parsePercentages, recommendRecipes, shareLinks } from './core.js';

// Set only when the official Threads profile URL is confirmed.
const THREADS_PROFILE_URL = '';
const code = document.body.dataset.code;
const name = document.querySelector('#type-name').textContent;
const canonical = document.querySelector('link[rel="canonical"]').href;
const links = shareLinks(name, code, canonical);
const status = document.querySelector('#share-status');

document.querySelector('.skip').addEventListener('click', event => {
  // Keyboard navigation must not replace the personal-result hash.
  event.preventDefault();
  const main = document.querySelector('#main');
  main.focus();
  main.scrollIntoView();
});

function showPercentages() {
  const percentages = parsePercentages(window.location.hash);
  document.querySelector('#personal-result').hidden = !percentages;
  const cta = document.querySelector('#diagnose-cta');
  cta.classList.toggle('secondary', Boolean(percentages));
  cta.textContent = percentages ? 'もう一度診断する' : 'あなたも診断する';
  document.querySelector('#result-label').textContent = percentages ? 'あなたのつまみタイプ' : 'こんなつまみタイプも';
  if (!percentages) return;
  document.querySelectorAll('.axis').forEach((row, index) => {
    const isLeft = code[index] === AXES[index].letters[0];
    const percent = percentages[index];
    const left = isLeft ? percent : 100 - percent;
    const labels = row.querySelectorAll('.axis-label');
    const picked = (isLeft ? labels[0] : labels[1]).textContent + ' ' + percent + '%';
    row.querySelector('.axis-picked').textContent = picked;
    labels[0].classList.toggle('selected', isLeft);
    labels[1].classList.toggle('selected', !isLeft);
    const meter = row.querySelector('[role="meter"]');
    meter.style.setProperty('--left-share', left + '%');
    meter.dataset.side = isLeft ? 'left' : 'right';
    meter.setAttribute('aria-valuenow', String(left));
    meter.setAttribute('aria-valuetext', picked);
  });
}

async function loadRecipes() {
  try {
    const response = await fetch('/shindan/data/recipes.json');
    if (!response.ok) throw new Error('Recipes unavailable');
    const recommendations = recommendRecipes(code, await response.json());
    const items = recommendations.map(recipe => {
      const item = document.createElement('li');
      const title = document.createElement('span');
      title.textContent = recipe.name;
      item.append(title);
      if (recipe.url) {
        const url = new URL(recipe.url);
        if (url.protocol !== 'https:') throw new Error('Only HTTPS recipe URLs are supported');
        const link = document.createElement('a');
        link.href = url.href;
        link.textContent = 'レシピを見る';
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.setAttribute('aria-label', recipe.name + 'のレシピを見る（新しいタブ）');
        item.append(link);
      }
      return item;
    });
    document.querySelector('#recipes').replaceChildren(...items);
  } catch {
    // Generated fallback recommendations remain useful offline.
    document.querySelector('#recipe-note').hidden = false;
  }
}

document.querySelector('#share-x').href = links.x;
document.querySelector('#share-threads').href = links.threads;
document.querySelector('#copy-link').addEventListener('click', async () => {
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(links.url);
    status.textContent = 'リンクをコピーしました。';
  } catch {
    const fallback = document.querySelector('#copy-fallback');
    fallback.hidden = false;
    const input = fallback.querySelector('input');
    input.value = links.url;
    input.focus();
    input.select();
    status.textContent = '下のURLを選択してコピーしてください。';
  }
});
if (typeof navigator.share === 'function') {
  const more = document.querySelector('#share-more');
  more.hidden = false;
  more.addEventListener('click', async () => {
    try {
      await navigator.share({ title: name + '（' + code + '）', text: links.text, url: links.url });
    } catch (error) {
      if (error.name !== 'AbortError') status.textContent = '共有できませんでした。リンクをコピーしてお使いください。';
    }
  });
}
if (THREADS_PROFILE_URL) {
  const profile = document.querySelector('#threads-profile');
  profile.href = THREADS_PROFILE_URL;
  profile.hidden = false;
}
window.addEventListener('hashchange', showPercentages);
showPercentages();
loadRecipes();
