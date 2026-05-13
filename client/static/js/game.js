const TOTAL_ROUNDS = 10;
const ROUND_TIME = 10;
const TIMER_INTERVAL_MS = 100;

let state = {};

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }

function startGame(mode = 'standard', date = null) {
  hide('daily-panel');
  const endpoint = mode === 'daily' ? `/api/game/daily?date=${date ? `${date}` : ''}` : '/api/game/questions';
  if (mode === 'daily') {
    fetch('/api/admin/maintain-cache').catch(() => {});
  }

  console.log("Fetching movies from server...", endpoint);
  const xhttp = new XMLHttpRequest();
  xhttp.open("GET", endpoint, true);
  
  xhttp.onload = function() {
    if (this.status === 200) {
      const response = JSON.parse(this.responseText);
      
      pass_date = response.date;
      if (date == null && response.today_date != null) {
        pass_date = response.today_date;
      }

      state = {
        round: 0,
        score: 0,
        correct: 0,
        roundTimeLeft: ROUND_TIME,
        totalTimeTaken: 0,
        timer: null,
        pairs: response.pairs,
        picked: false,
        mode: mode,
        date: pass_date || null,
      };

      hide('screen-start');
      hide('screen-results');
      show('screen-game');

      const modeTitle = document.getElementById('mode-title');
      const modeSub = document.getElementById('mode-subtitle');

      if (mode === 'daily') {
        const isToday = (date === null && pass_date !== null);
        document.getElementById('mode-title').textContent = isToday ? "Today's RateRace" : 'Previous RateRace';
        document.getElementById('mode-subtitle').textContent = `Daily — ${pass_date}`;
      } else {
        document.getElementById('mode-title').textContent = 'Standard Mode';
        document.getElementById('mode-subtitle').innerHTML = '★ &nbsp; Beat the Clock &nbsp; ★';

      }

      loadRound();
    } else {
      const err = JSON.parse(this.responseText);
      alert(err.error || "Failed to load game.");
    }
  };
  
  xhttp.send();
}

function toggleDailyPanel() {
  const panel = document.getElementById('daily-panel');
  const arrow = document.getElementById('daily-toggle-arrow');

  if (panel.classList.contains('hidden')) {
    show('daily-panel');
    arrow.textContent = '▼';
    loadDailyHistory();
  } else {
    hide('daily-panel');
    arrow.textContent = '▶';
  }
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


function loadDailyHistory() {
  fetch('/api/game/daily/history')
    .then(r => r.json())
    .then(data => {
      const list = document.getElementById('daily-history-list');
      if (!list) return;
      list.innerHTML = '';
      
      data.dates.forEach(entry => {
        const btn = document.createElement('button');

        if (entry.is_today) {          // today's daily
          btn.className = 'w-full text-left px-4 py-2 bg-amber-400 text-black font-extrabold uppercase tracking-widest text-xs border-b border-amber-600 hover:bg-amber-300 transition flex justify-between items-center';
          btn.innerHTML = `<span>★ Today's Daily</span>${entry.played ? `<span>${entry.score}pts · ${entry.correct}/10</span>` : '<span class="opacity-60">Not played</span>'}`;
          btn.onclick = () => startGame('daily');
        }
        else if (entry.played) {      // past daily, already played
          btn.className = 'w-full text-left px-4 py-2 bg-zinc-900 text-zinc-500 font-bold text-xs uppercase tracking-widest border-b border-zinc-800 flex justify-between items-center';
          btn.innerHTML = `<span>${entry.label}</span><span>${entry.score}pts · ${entry.correct}/10</span>`;
          btn.onclick = () => startGame('daily', entry.date);

        } else {                      // past daily, not played
          btn.className = 'w-full text-left px-4 py-2 bg-zinc-900 text-zinc-600 font-bold text-xs uppercase tracking-widest border-b border-zinc-800 hover:bg-zinc-800 transition flex justify-between items-center';
          btn.innerHTML = `<span>${entry.label}</span><span class="text-zinc-700 text-xs">—</span>`;
          btn.onclick = () => startGame('daily', entry.date);
        }
        list.appendChild(btn);
      });
    });
}

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

  document.getElementById('title-b').textContent = movieB.title;
  document.getElementById('year-b').textContent = movieB.year;

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
  
  submitScore(state.score, state.correct, Number(formattedTimeTaken), state.mode, state.date);

  async function submitScore(score, correctAnswers, timeTaken, mode, gameDate) {
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
          mode: mode || 'standard',
          date: gameDate || null,
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
