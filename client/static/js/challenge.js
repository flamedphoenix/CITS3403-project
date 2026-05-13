const TOTAL_ROUNDS = 10;
const ROUND_TIME = 10;
const TIMER_INTERVAL_MS = 100;

let state = {
  round: 0,
  picked: false,
  roundTimeLeft: ROUND_TIME,
  timer: null,
  pairs: [],
  challenger: null,
  opponent: null,
};

const socket = window.appSocket;

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }

function myKey()  { return state.challenger && state.challenger.user_id === CURRENT_USER_ID ? 'challenger' : 'opponent'; }
function oppKey() { return myKey() === 'challenger' ? 'opponent' : 'challenger'; }

// ---------------------------------------------------------------------------
// SocketIO
// ---------------------------------------------------------------------------

function joinChallenge() {
  socket.emit('join_challenge', { session_id: SESSION_ID });
}
if (socket.connected) {
  joinChallenge();
} else {
  socket.on('connect', joinChallenge);
}

socket.on('game_start', (data) => {
  state.pairs      = data.pairs;
  state.challenger = data.challenger;
  state.opponent   = data.opponent;

  document.getElementById('challenger-name').textContent = data.challenger.username.toUpperCase();
  document.getElementById('opponent-name').textContent   = data.opponent.username.toUpperCase();

  hide('screen-waiting');
  show('screen-game');
  loadRound();
});

socket.on('opponent_answered', () => {
  const el = document.getElementById('opponent-status');
  el.textContent = 'Opponent answered!';
  el.className = 'text-green-400 text-xs uppercase tracking-widest font-bold';
});

socket.on('round_result', (data) => {
  clearInterval(state.timer);

  const myResult  = data[myKey()];
  const oppResult = data[oppKey()];

  // Show ratings
  document.getElementById('rating-val-a').textContent = data.movie_a.rating.toFixed(1);
  document.getElementById('rating-val-b').textContent = data.movie_b.rating.toFixed(1);
  show('rating-a');
  show('rating-b');

  // Colour the correct card green
  const correctCard = document.getElementById(`card-${data.correct_choice}`);
  correctCard.style.cssText = 'width:340px; box-shadow: 4px 4px 0px #15803d;';
  correctCard.className = 'border-2 border-green-500 flex flex-col group';

  // Colour my wrong pick red
  if (myResult.choice && myResult.choice !== data.correct_choice) {
    const wrongCard = document.getElementById(`card-${myResult.choice}`);
    wrongCard.style.cssText = 'width:340px; box-shadow: 4px 4px 0px #b91c1c;';
    wrongCard.className = 'border-2 border-red-500 flex flex-col group';
  }

  // Update live scores
  document.getElementById('challenger-score').textContent = data.challenger.total_score;
  document.getElementById('opponent-score').textContent   = data.opponent.total_score;

  // Correct-answer counters (track locally from cumulative round data)
  document.getElementById('challenger-correct').textContent =
    `${data[myKey() === 'challenger' ? 'challenger' : 'opponent'].is_correct
        ? '↑' : ''}${state.challengerCorrect || 0}/10 correct`;

  // Feedback
  const feedbackText = document.getElementById('feedback-text');
  const feedbackSub  = document.getElementById('feedback-sub');

  if (myResult.is_correct) {
    const tag = myResult.points >= 100 ? ' (first!)' : ' (second)';
    feedbackText.textContent = `✓ Correct! +${myResult.points}pts${tag}`;
    feedbackText.className   = 'text-2xl font-extrabold uppercase tracking-widest text-green-400 mb-1';
  } else if (myResult.choice === null) {
    feedbackText.textContent = 'Time Up! +0pts';
    feedbackText.className   = 'text-2xl font-extrabold uppercase tracking-widest text-red-400 mb-1';
  } else {
    feedbackText.textContent = '✗ Wrong! +0pts';
    feedbackText.className   = 'text-2xl font-extrabold uppercase tracking-widest text-red-400 mb-1';
  }

  feedbackSub.textContent = oppResult.is_correct
    ? `Opponent got it right (+${oppResult.points}pts)`
    : 'Opponent got it wrong (+0pts)';

  show('feedback');

  // Advance local round counter
  state.round = data.round + 1;

  if (state.round < TOTAL_ROUNDS) {
    setTimeout(loadRound, 2500);
  }
  // game_over event handles the results screen when round === 10
});

socket.on('game_over', (data) => {
  clearInterval(state.timer);
  hide('screen-game');
  show('screen-results');

  const winnerText = document.getElementById('winner-text');
  if (data.winner_id === null) {
    winnerText.textContent = "It's a Tie!";
  } else if (data.winner_id === CURRENT_USER_ID) {
    winnerText.textContent = 'You Win!';
    winnerText.className = 'text-5xl font-extrabold text-amber-400 uppercase tracking-tight text-shadow-retro mb-8';
  } else {
    winnerText.textContent = 'You Lose!';
    winnerText.className = 'text-5xl font-extrabold text-red-400 uppercase tracking-tight text-shadow-retro mb-8';
  }

  document.getElementById('result-challenger-name').textContent    = data.challenger.username.toUpperCase();
  document.getElementById('result-challenger-score').textContent   = data.challenger.score;
  document.getElementById('result-challenger-correct').textContent = `${data.challenger.correct}/10 correct`;

  document.getElementById('result-opponent-name').textContent    = data.opponent.username.toUpperCase();
  document.getElementById('result-opponent-score').textContent   = data.opponent.score;
  document.getElementById('result-opponent-correct').textContent = `${data.opponent.correct}/10 correct`;
});

socket.on('challenge_error', (data) => {
  alert(data.message);
});

// ---------------------------------------------------------------------------
// Game rendering
// ---------------------------------------------------------------------------

function loadRound() {
  state.picked = false;

  const [movieA, movieB] = state.pairs[state.round];

  const cardA = document.getElementById('card-a');
  const cardB = document.getElementById('card-b');

  cardA.className = 'border-2 border-zinc-700 hover:border-amber-400 transition cursor-pointer flex flex-col shadow-retro group';
  cardB.className = 'border-2 border-zinc-700 hover:border-amber-400 transition cursor-pointer flex flex-col shadow-retro group';
  cardA.style.cssText = 'width:340px;';
  cardB.style.cssText = 'width:340px;';
  cardA.onclick = () => pick('a');
  cardB.onclick = () => pick('b');

  document.getElementById('title-a').textContent = movieA.title;
  document.getElementById('year-a').textContent  = movieA.year;
  document.getElementById('title-b').textContent = movieB.title;
  document.getElementById('year-b').textContent  = movieB.year;
  document.getElementById('hint-a').textContent  = 'Click to pick';
  document.getElementById('hint-b').textContent  = 'Click to pick';

  const posterA = document.getElementById('poster-a');
  const posterB = document.getElementById('poster-b');
  posterA.src = movieA.poster_url;
  posterB.src = movieB.poster_url;
  posterA.onerror = () => { posterA.src = '/static/img/no-poster.png'; };
  posterB.onerror = () => { posterB.src = '/static/img/no-poster.png'; };

  hide('rating-a');
  hide('rating-b');
  hide('feedback');

  const opponentStatus = document.getElementById('opponent-status');
  opponentStatus.textContent = 'Opponent thinking...';
  opponentStatus.className = 'text-zinc-600 text-xs uppercase tracking-widest font-bold';

  document.getElementById('round-display').textContent = state.round + 1;

  startTimer();
}

function startTimer() {
  clearInterval(state.timer);
  state.roundTimeLeft = ROUND_TIME;
  updateTimerDisplay();

  const roundSnapshot = state.round;

  state.timer = setInterval(() => {
    state.roundTimeLeft = Math.max(0, state.roundTimeLeft - TIMER_INTERVAL_MS / 1000);
    updateTimerDisplay();

    if (state.roundTimeLeft <= 0) {
      clearInterval(state.timer);
      if (!state.picked) {
        state.picked = true;
        document.getElementById('card-a').onclick = null;
        document.getElementById('card-b').onclick = null;
        socket.emit('challenge_timeout', { session_id: SESSION_ID, round: roundSnapshot });
      }
    }
  }, TIMER_INTERVAL_MS);
}

function updateTimerDisplay() {
  const wholeSeconds = Math.ceil(state.roundTimeLeft);
  document.getElementById('timer-display').textContent = wholeSeconds;
  document.getElementById('timer-bar').style.width = (state.roundTimeLeft / ROUND_TIME * 100) + '%';

  const bar      = document.getElementById('timer-bar');
  const timerNum = document.getElementById('timer-display');
  if (state.roundTimeLeft <= 3) {
    bar.classList.replace('bg-amber-400', 'bg-red-500');
    timerNum.classList.replace('text-amber-400', 'text-red-400');
  } else {
    bar.classList.replace('bg-red-500', 'bg-amber-400');
    timerNum.classList.replace('text-red-400', 'text-amber-400');
  }
}

function pick(choice) {
  if (state.picked) return;
  state.picked = true;

  document.getElementById('card-a').onclick = null;
  document.getElementById('card-b').onclick = null;

  const timeTaken = ROUND_TIME - state.roundTimeLeft;

  document.getElementById(`hint-${choice}`).textContent = '✓ Your pick';
  const other = choice === 'a' ? 'b' : 'a';
  document.getElementById(`hint-${other}`).textContent = '';

  socket.emit('challenge_pick', {
    session_id: SESSION_ID,
    round:      state.round,
    choice,
    time_taken: timeTaken,
  });
}
