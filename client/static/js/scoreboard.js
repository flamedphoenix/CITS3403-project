// ---------------------------------------------------------------------------
// Leaderboard
// ---------------------------------------------------------------------------

async function loadLeaderboard() {
  try {
    const res  = await fetch('/api/scores/leaderboard');
    const data = await res.json();
    renderLeaderboard(data.leaderboard);
    populateUserStats(data.leaderboard);
  } catch (e) {
    console.error('Leaderboard load error:', e);
    document.getElementById('leaderboard-body').innerHTML = `
      <tr>
        <td colspan="6" class="px-5 py-8 text-center text-red-400 uppercase tracking-widest text-xs">
          Failed to load leaderboard.
        </td>
      </tr>`;
  }
}

function renderLeaderboard(entries) {
  const tbody = document.getElementById('leaderboard-body');
  if (!entries || !entries.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="px-5 py-8 text-center text-zinc-600 uppercase tracking-widest text-xs">
          No scores yet — be the first to play!
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = entries.map(row => {
    const isMe     = IS_AUTHENTICATED && row.username === CURRENT_USERNAME;
    const rowClass = isMe
      ? 'border-b border-zinc-700 bg-zinc-900'
      : 'border-b border-zinc-800 hover:bg-zinc-900 transition';
    const medal    = row.rank === 1 ? '🥇' : row.rank === 2 ? '🥈' : row.rank === 3 ? '🥉' : '';

    let challengeCell = '';
    if (IS_AUTHENTICATED) {
      challengeCell = isMe
        ? '<td class="px-5 py-4 text-zinc-600 text-xs uppercase tracking-widest">You</td>'
        : `<td class="px-5 py-4">
             <button data-id="${row.user_id}" data-name="${row.username}"
               class="challenge-btn text-xs font-extrabold uppercase tracking-widest px-3 py-1
                      border border-amber-400 text-amber-400 hover:bg-amber-400 hover:text-black transition">
               ⚔ Challenge
             </button>
           </td>`;
    }

    return `
      <tr class="${rowClass}">
        <td class="px-5 py-4 text-amber-400 font-bold">${medal} #${row.rank}</td>
        <td class="px-5 py-4 font-bold uppercase ${isMe ? 'text-amber-400' : ''}">
          <a href="${row.profile_url}" class="hover:text-amber-400 underline underline-offset-4">
            ${row.username}
          </a>
        </td>
        <td class="px-5 py-4">${row.best_score}</td>
        <td class="px-5 py-4">${row.best_time}s</td>
        <td class="px-5 py-4">${row.avg_accuracy}</td>
        ${challengeCell}
      </tr>`;
  }).join('');

  document.querySelectorAll('.challenge-btn').forEach(btn => {
    btn.addEventListener('click', () =>
      sendChallenge(parseInt(btn.dataset.id))
    );
  });
}

function populateUserStats(entries) {
  if (!IS_AUTHENTICATED || !entries) return;
  const me = entries.find(r => r.username === CURRENT_USERNAME);
  if (!me) return;
  document.getElementById('stat-rank').textContent     = `#${me.rank}`;
  document.getElementById('stat-score').textContent    = me.best_score;
  document.getElementById('stat-time').textContent     = `${me.best_time}s`;
  document.getElementById('stat-accuracy').textContent = me.avg_accuracy;
}

loadLeaderboard();

// ---------------------------------------------------------------------------
// Challenge — scoreboard-page specific
// ---------------------------------------------------------------------------

function sendChallenge(opponentId) {
  if (!window.appSocket) return;
  window.appSocket.emit('send_challenge', { opponent_id: opponentId });
}

function showToast(message, isError = false) {
  const toast = document.getElementById('toast-sent');
  const text  = document.getElementById('toast-sent-text');
  text.textContent = message;
  text.className   = isError
    ? 'text-red-400 font-extrabold uppercase tracking-widest text-xs'
    : 'text-amber-400 font-extrabold uppercase tracking-widest text-xs';
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 4000);
}

if (IS_AUTHENTICATED) {
  window.appSocket.on('challenge_sent', (data) => {
    showToast(`Challenge sent to ${data.opponent_name}!`);
  });

  window.appSocket.on('challenge_error', (data) => {
    showToast(data.message, true);
  });
}
