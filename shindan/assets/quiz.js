import { scoreAnswers } from './core.js';

const intro = document.querySelector('#intro');
const quiz = document.querySelector('#quiz');
const pending = document.querySelector('#pending');
const start = document.querySelector('#start');
const retry = document.querySelector('#retry');
const error = document.querySelector('#load-error');
const heading = document.querySelector('#question');
const counter = document.querySelector('#counter');
const progress = document.querySelector('#progress');
const options = document.querySelector('#choices');
const back = document.querySelector('#back');
let questions = [];
let answers = [];
let current = 0;
let finishing = false;

async function loadQuestions() {
  start.disabled = true;
  retry.hidden = true;
  error.hidden = true;
  try {
    const response = await fetch('/shindan/data/questions.json');
    if (!response.ok) throw new Error('Question data unavailable');
    const data = await response.json();
    scoreAnswers(Array(12).fill(0), data); // Validate the complete dataset.
    questions = data;
    start.disabled = false;
    start.textContent = '診断をはじめる';
  } catch {
    error.hidden = false;
    retry.hidden = false;
    start.textContent = '診断をはじめる';
  }
}

function renderQuestion() {
  const question = questions[current];
  counter.textContent = 'Q' + (current + 1) + ' / 12';
  progress.value = current + 1;
  progress.setAttribute('aria-label', '全12問中' + (current + 1) + '問目');
  heading.textContent = question.text;
  options.replaceChildren();
  question.choices.forEach((choice, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'choice';
    button.textContent = choice.text;
    button.setAttribute('aria-pressed', String(answers[current] === index));
    button.addEventListener('click', event => {
      if (finishing || event.detail > 1) return;
      answers.splice(current, answers.length - current, index);
      if (current === 11) {
        finish();
      } else {
        current += 1;
        renderQuestion();
      }
    });
    options.append(button);
  });
  back.disabled = current === 0;
  heading.focus({ preventScroll: true });
}

function finish() {
  finishing = true;
  const result = scoreAnswers(answers, questions);
  quiz.hidden = true;
  pending.hidden = false;
  document.querySelector('#pending-title').focus({ preventScroll: true });
  const next = '/shindan/result/' + result.code.toLowerCase() +
    '/#p=' + result.percentages.join('-');
  const navigate = () => window.location.assign(next);
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) navigate();
  else window.setTimeout(navigate, 800);
}

start.addEventListener('click', () => {
  answers = [];
  current = 0;
  finishing = false;
  intro.hidden = true;
  quiz.hidden = false;
  renderQuestion();
  window.scrollTo({ top: 0 });
});
back.addEventListener('click', () => {
  if (current > 0 && !finishing) {
    current -= 1;
    renderQuestion();
  }
});
retry.addEventListener('click', loadQuestions);
// Returning with the browser Back button should not restore a frozen judging screen.
window.addEventListener('pageshow', event => {
  if (event.persisted) {
    finishing = false;
    pending.hidden = true;
    quiz.hidden = true;
    intro.hidden = false;
  }
});
loadQuestions();
