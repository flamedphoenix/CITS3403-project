const TOTAL_ROUNDS = 10;
const ROUND_TIME = 5;
const TIMER_INTERVAL_MS = 100;

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

function startGame(mode = 'standard') {
  const endpoint = mode === 'daily' ? '/api/game/daily' : '/api/game/questions';
  console.log("Fetching movies from server...");
  const xhttp = new XMLHttpRequest();
  xhttp.open("GET", endpoint, true);
  
  xhttp.onload = function() {
    if (this.status === 200) {
      const response = JSON.parse(this.responseText);
      
  state = {
    round: 0,
    score: 0,
    correct: 0,
    roundTimeLeft: ROUND_TIME,
    totalTimeTaken: 0,
    timer: null,
        pairs: response.pairs,
    picked: false,
  };

  hide('screen-start');
  hide('screen-results');
  show('screen-game');

  loadRound();
    } else {
      alert("Failed to load movies. Ensure your database has enough entries!");
    }
  };
  
  xhttp.send();
}

function startTimer() {
  clearInterval(state.timer);

  state.roundTimeLeft = ROUND_TIME;
  updateTimerDisplay();

  state.timer = setInterval(() => {
    state.roundTimeLeft = Math.max(0, state.roundTimeLeft - TIMER_INTERVAL_MS / 1000);
    updateTimerDisplay();

    if (state.roundTimeLeft <= 0) {
      clearInterval(state.timer);
      handleTimeout();
    }
  }, TIMER_INTERVAL_MS);
}

function updateTimerDisplay() {
  const wholeSeconds = Math.ceil(state.roundTimeLeft);

  document.getElementById('timer-display').textContent = wholeSeconds;
  document.getElementById('timer-bar').style.width = (state.roundTimeLeft / ROUND_TIME * 100) + '%';

  const bar = document.getElementById('timer-bar');
  const timerNum = document.getElementById('timer-display');

  if (state.roundTimeLeft <= 1) {
    bar.classList.replace('bg-amber-400', 'bg-red-500');
    timerNum.classList.replace('text-amber-400', 'text-red-400');
  } else {
    bar.classList.replace('bg-red-500', 'bg-amber-400');
    timerNum.classList.replace('text-red-400', 'text-amber-400');
  }
}

function getTimeBonus(timeTakenThisRound) {
  if (timeTakenThisRound < 1) return 100;
  if (timeTakenThisRound < 2) return 80;
  if (timeTakenThisRound < 3) return 60;
  if (timeTakenThisRound < 4) return 40;
  if (timeTakenThisRound < 5) return 20;
  return 0;
}

function handleTimeout() {
  if (state.picked) return;

  state.picked = true;
  state.totalTimeTaken += ROUND_TIME;

  const [movieA, movieB] = state.pairs[state.round];
  const correctChoice = movieA.rating >= movieB.rating ? 'a' : 'b';
  const correctMovie = correctChoice === 'a' ? movieA : movieB;

  document.getElementById('card-a').onclick = null;
  document.getElementById('card-b').onclick = null;

  document.getElementById('rating-val-a').textContent = movieA.rating.toFixed(1);
  document.getElementById('rating-val-b').textContent = movieB.rating.toFixed(1);
  show('rating-a');
  show('rating-b');

  const correctCard = document.getElementById(`card-${correctChoice}`);
  correctCard.className = 'border-2 border-green-500 w-52 flex flex-col group';
  correctCard.style.boxShadow = '4px 4px 0px #15803d';

  const feedbackText = document.getElementById('feedback-text');
  const feedbackSub = document.getElementById('feedback-sub');

  feedbackText.textContent = 'Time Up!';
  feedbackText.className = 'text-2xl font-extrabold uppercase tracking-widest text-red-400 mb-1';
  feedbackSub.textContent = `${correctMovie.title} had the higher rating (${correctMovie.rating})`;

  show('feedback');

  setTimeout(() => {
    nextRound();
  }, 2000);
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
  document.getElementById('poster-a').src = movieA.poster_url;

  document.getElementById('title-b').textContent = movieB.title;
  document.getElementById('year-b').textContent = movieB.year;
  document.getElementById('poster-b').src = movieB.poster_url;

  document.getElementById('hint-a').textContent = 'Click to pick';
  document.getElementById('hint-b').textContent = 'Click to pick';

  const posterA = document.getElementById('poster-a');
  const posterB = document.getElementById('poster-b');
  posterA.src = movieA.poster_url;
  posterB.src = movieB.poster_url;
  posterA.onerror = () => { posterA.src = '/static/img/no-poster.png'; };
  posterB.onerror = () => { posterB.src = '/static/img/no-poster.png'; };

  hide('rating-a');
  hide('rating-b');
  hide('feedback');

  document.getElementById('round-display').textContent = state.round + 1;
  document.getElementById('score-display').textContent = state.score;

  startTimer();
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


const timeTakenThisRound = ROUND_TIME - state.roundTimeLeft;
state.totalTimeTaken += timeTakenThisRound;

if (isCorrect) {
  const basePoints = 100;
  const speedBonus = getTimeBonus(timeTakenThisRound);
  const roundPoints = basePoints + speedBonus;

  state.correct++;
  state.score += roundPoints;

  document.getElementById('score-display').textContent = state.score;
  feedbackText.textContent = `✓ Correct! +${roundPoints}pts`;

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

  hide('screen-game');
  show('screen-results');

  const accuracy = Math.round((state.correct / TOTAL_ROUNDS) * 100);
  const formattedTimeTaken = state.totalTimeTaken.toFixed(1);

  document.getElementById('result-score').textContent = state.score;
  document.getElementById('result-correct').textContent = `${state.correct}/${TOTAL_ROUNDS}`;
  document.getElementById('result-time').textContent = `${formattedTimeTaken}s`;
  document.getElementById('result-accuracy').textContent = `${accuracy}%`;
}
