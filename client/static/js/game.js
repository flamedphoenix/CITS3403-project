const TOTAL_ROUNDS = 10;
const TOTAL_TIME = 60;

const MOVIES = [
  { title: "The Shawshank Redemption", year: "1994", rating: 9.3 },
  { title: "The Godfather",            year: "1972", rating: 9.2 },
  { title: "The Dark Knight",          year: "2008", rating: 9.0 },
  { title: "Schindler's List",         year: "1993", rating: 9.0 },
  { title: "The Lord of the Rings",    year: "2003", rating: 9.0 },
  { title: "Pulp Fiction",             year: "1994", rating: 8.9 },
  { title: "Forrest Gump",             year: "1994", rating: 8.8 },
  { title: "Inception",                year: "2010", rating: 8.8 },
  { title: "Fight Club",               year: "1999", rating: 8.8 },
  { title: "The Matrix",               year: "1999", rating: 8.7 },
  { title: "GoodFellas",               year: "1990", rating: 8.7 },
  { title: "Interstellar",             year: "2014", rating: 8.7 },
  { title: "Se7en",                    year: "1995", rating: 8.6 },
  { title: "The Silence of the Lambs", year: "1991", rating: 8.6 },
  { title: "Saving Private Ryan",      year: "1998", rating: 8.6 },
  { title: "The Prestige",             year: "2006", rating: 8.5 },
  { title: "The Departed",             year: "2006", rating: 8.5 },
  { title: "Parasite",                 year: "2019", rating: 8.5 },
  { title: "Gladiator",                year: "2000", rating: 8.5 },
  { title: "Whiplash",                 year: "2014", rating: 8.5 },
  { title: "Django Unchained",         year: "2012", rating: 8.4 },
  { title: "The Lion King",            year: "1994", rating: 8.5 },
];

let state = {};

function shuffle(arr) {
  return [...arr].sort(() => Math.random() - 0.5);
}

function generatePairs() {
  const available = shuffle(MOVIES);
  const pairs = [];
  while (pairs.length < TOTAL_ROUNDS && available.length >= 2) {
    const a = available.shift();
    const bIndex = available.findIndex(m => m.rating !== a.rating);
    if (bIndex === -1) break;
    const [b] = available.splice(bIndex, 1);
    pairs.push([a, b]);
  }
  return pairs;
}

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }

function startGame() {
  state = {
    round: 0,
    score: 0,
    correct: 0,
    timeLeft: TOTAL_TIME,
    timer: null,
    pairs: generatePairs(),
    picked: false,
  };

  hide('screen-start');
  hide('screen-results');
  show('screen-game');

  startTimer();
  loadRound();
}

function startTimer() {
  updateTimerDisplay();
  state.timer = setInterval(() => {
    state.timeLeft--;
    updateTimerDisplay();
    if (state.timeLeft <= 0) {
      clearInterval(state.timer);
      endGame();
    }
  }, 1000);
}

function updateTimerDisplay() {
  document.getElementById('timer-display').textContent = state.timeLeft;
  document.getElementById('timer-bar').style.width = (state.timeLeft / TOTAL_TIME * 100) + '%';

  const bar = document.getElementById('timer-bar');
  const timerNum = document.getElementById('timer-display');
  if (state.timeLeft <= 10) {
    bar.classList.replace('bg-amber-400', 'bg-red-500');
    timerNum.classList.replace('text-amber-400', 'text-red-400');
  } else {
    bar.classList.replace('bg-red-500', 'bg-amber-400');
    timerNum.classList.replace('text-red-400', 'text-amber-400');
  }
}

function loadRound() {
  const [movieA, movieB] = state.pairs[state.round];
  state.picked = false;

  const cardA = document.getElementById('card-a');
  const cardB = document.getElementById('card-b');
  cardA.className = 'border-2 border-zinc-700 hover:border-amber-400 transition cursor-pointer w-52 flex flex-col shadow-retro group';
  cardB.className = 'border-2 border-zinc-700 hover:border-amber-400 transition cursor-pointer w-52 flex flex-col shadow-retro group';
  cardA.style.boxShadow = '';
  cardB.style.boxShadow = '';
  cardA.onclick = () => pick('a');
  cardB.onclick = () => pick('b');

  document.getElementById('title-a').textContent = movieA.title;
  document.getElementById('year-a').textContent = movieA.year;
  document.getElementById('title-b').textContent = movieB.title;
  document.getElementById('year-b').textContent = movieB.year;
  document.getElementById('hint-a').textContent = 'Click to pick';
  document.getElementById('hint-b').textContent = 'Click to pick';

  hide('rating-a');
  hide('rating-b');
  hide('feedback');

  document.getElementById('round-display').textContent = state.round + 1;
  document.getElementById('score-display').textContent = state.score;
}

function pick(choice) {
  if (state.picked) return;
  state.picked = true;

  const [movieA, movieB] = state.pairs[state.round];
  const correctChoice = movieA.rating >= movieB.rating ? 'a' : 'b';
  const isCorrect = choice === correctChoice;

  document.getElementById('card-a').onclick = null;
  document.getElementById('card-b').onclick = null;

  document.getElementById('rating-val-a').textContent = movieA.rating.toFixed(1);
  document.getElementById('rating-val-b').textContent = movieB.rating.toFixed(1);
  show('rating-a');
  show('rating-b');
  document.getElementById('hint-a').textContent = '';
  document.getElementById('hint-b').textContent = '';

  const pickedCard  = document.getElementById(`card-${choice}`);
  const correctCard = document.getElementById(`card-${correctChoice}`);

  correctCard.className = 'border-2 border-green-500 w-52 flex flex-col group';
  correctCard.style.boxShadow = '4px 4px 0px #15803d';

  if (!isCorrect) {
    pickedCard.className = 'border-2 border-red-500 w-52 flex flex-col group';
    pickedCard.style.boxShadow = '4px 4px 0px #b91c1c';
  }

  const feedbackText = document.getElementById('feedback-text');
  const feedbackSub  = document.getElementById('feedback-sub');

  if (isCorrect) {
    state.correct++;
    state.score += 100;
    document.getElementById('score-display').textContent = state.score;
    feedbackText.textContent = '✓ Correct! +100pts';
    feedbackText.className = 'text-2xl font-extrabold uppercase tracking-widest text-green-400 mb-1';
    feedbackSub.textContent = `${movieA.title} (${movieA.rating}) vs ${movieB.title} (${movieB.rating})`;
  } else {
    const correctMovie = correctChoice === 'a' ? movieA : movieB;
    feedbackText.textContent = '✗ Wrong!';
    feedbackText.className = 'text-2xl font-extrabold uppercase tracking-widest text-red-400 mb-1';
    feedbackSub.textContent = `${correctMovie.title} had the higher rating (${correctMovie.rating})`;
  }

  show('feedback');

  clearInterval(state.timer);
  setTimeout(() => {
    startTimer();
    nextRound();
  }, 2000);
}

function nextRound() {
  state.round++;
  if (state.round >= TOTAL_ROUNDS) {
    endGame();
  } else {
    loadRound();
  }
}

function endGame() {
  clearInterval(state.timer);

  const timeBonus = state.timeLeft * 5;
  state.score += timeBonus;

  hide('screen-game');
  show('screen-results');

  document.getElementById('result-score').textContent    = state.score;
  document.getElementById('result-correct').textContent  = `${state.correct}/10`;
  document.getElementById('result-time').textContent     = `${state.timeLeft}s`;
  document.getElementById('result-accuracy').textContent = `${state.correct * 10}%`;
}
