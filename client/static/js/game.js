// Keep these values in one place so timer, scoring, and display stay in sync.
const TOTAL_ROUNDS = 10;
const ROUND_TIME = 10;
const TIMER_INTERVAL_MS = 100;

// state is reset at the start of every game; gameSeq prevents an old API response from overwriting a newer game.
let state = {};
let gameTimer = null;
let gameSeq = 0;

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }

// mode chooses between normal random questions and the daily shared set.
function startGame(mode = 'standard') {
  clearInterval(gameTimer);
  const seq = ++gameSeq;
  const endpoint = mode === 'daily' ? '/api/game/daily' : '/api/game/questions';
  const xhttp = new XMLHttpRequest();
  xhttp.open("GET", endpoint, true);

  xhttp.onload = function() {
    if (seq !== gameSeq) return;
    if (this.status === 200) {
      const response = JSON.parse(this.responseText);

      // The backend sends only the movie pairs; the browser tracks round progress and local scoring.
      state = {
        round: 0,
        score: 0,
        correct: 0,
        roundTimeLeft: ROUND_TIME,
        totalTimeTaken: 0,
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

// Timer ticks frequently for a smooth bar, while display rounds up to whole seconds.
function startTimer() {
  clearInterval(gameTimer);

  state.roundTimeLeft = ROUND_TIME;
  updateTimerDisplay();

  gameTimer = setInterval(() => {
    state.roundTimeLeft = Math.max(0, state.roundTimeLeft - TIMER_INTERVAL_MS / 1000);
    updateTimerDisplay();

    if (state.roundTimeLeft <= 0) {
      clearInterval(gameTimer);
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

// Faster correct answers receive a larger bonus, encouraging quick decisions.
function getTimeBonus(timeTakenThisRound) {
  if (timeTakenThisRound < 1) return 100;
  if (timeTakenThisRound < 2) return 90;
  if (timeTakenThisRound < 3) return 80;
  if (timeTakenThisRound < 4) return 70;
  if (timeTakenThisRound < 5) return 60;
  if (timeTakenThisRound < 6) return 50;
  if (timeTakenThisRound < 7) return 40;
  if (timeTakenThisRound < 8) return 30;
  if (timeTakenThisRound < 9) return 20;
  if (timeTakenThisRound < 10) return 10;
  return 0;
}

// Timeout follows the same reveal flow as a wrong answer but adds the full round time.
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

// Reset every card and feedback element so styles/click handlers do not leak between rounds.
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

  const posterA = document.getElementById('poster-a');
  const posterB = document.getElementById('poster-b');
  posterA.src = movieA.poster_url;
  posterB.src = movieB.poster_url;
  // Fall back to a local image if TMDB poster URLs fail to load.
  posterA.onerror = () => { posterA.src = '/static/img/no-poster.png'; };
  posterB.onerror = () => { posterB.src = '/static/img/no-poster.png'; };
  
  hide('rating-a');
  hide('rating-b');
  hide('feedback');

  document.getElementById('round-display').textContent = state.round + 1;
  document.getElementById('score-display').textContent = state.score;

  startTimer();
}

// Handles a player choice, reveals both ratings, then delays briefly before the next round.
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

  clearInterval(gameTimer);

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

// Results are shown before the POST finishes so the page feels responsive.
function endGame() {
  clearInterval(gameTimer);

  hide('screen-game');
  show('screen-results');

  const accuracy = Math.round((state.correct / TOTAL_ROUNDS) * 100);
  const formattedTimeTaken = state.totalTimeTaken.toFixed(1);

  document.getElementById('result-score').textContent = state.score;
  document.getElementById('result-correct').textContent = `${state.correct}/${TOTAL_ROUNDS}`;
  document.getElementById('result-time').textContent = `${formattedTimeTaken}s`;
  document.getElementById('result-accuracy').textContent = `${accuracy}%`;
  
  submitScore(state.score, state.correct, Number(formattedTimeTaken));

  // Save the completed game so leaderboard/profile pages can include it.
  async function submitScore(score, correctAnswers, timeTaken) {
    try {
      const response = await fetch('/api/game/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          score: score,
          correct_answers: correctAnswers,
          time_taken: timeTaken,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error('Score save failed:', data.error);
        return;
      }

      console.log('Score saved:', data);
    } catch (error) {
      console.error('Score submit error:', error);
    }
  }
}
