// One shared socket is attached to window so page-specific scripts can reuse it.
window.appSocket = io();

// pendingSession stores the challenge being shown in the popup until the user responds.
let pendingSession  = null;
let popdownInterval = null;

// Global toasts are for challenge feedback that can happen on any authenticated page.
function showGlobalToast(message, isError = false) {
  const toast = document.getElementById('global-toast');
  const text  = document.getElementById('global-toast-text');
  text.textContent = message;
  text.className   = isError
    ? 'text-red-400 font-extrabold uppercase tracking-widest text-xs'
    : 'text-amber-400 font-extrabold uppercase tracking-widest text-xs';
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 4000);
}

// The popup auto-declines so pending challenges do not stay open forever.
function showPopup(sessionId) {
  let seconds = 30;
  document.getElementById('popup-countdown').textContent = seconds;
  document.getElementById('challenge-popup').classList.remove('hidden');
  popdownInterval = setInterval(() => {
    seconds--;
    document.getElementById('popup-countdown').textContent = seconds;
    if (seconds <= 0) {
      clearInterval(popdownInterval);
      window.appSocket.emit('decline_challenge', { session_id: sessionId });
      hidePopup();
    }
  }, 1000);
}

function hidePopup() {
  clearInterval(popdownInterval);
  pendingSession = null;
  document.getElementById('challenge-popup').classList.add('hidden');
}

// Incoming server events control the popup and redirect flow.
window.appSocket.on('challenge_received', (data) => {
  pendingSession = data.session_id;
  document.getElementById('popup-title').textContent = data.challenger_name.toUpperCase();
  showPopup(data.session_id);
});

window.appSocket.on('challenge_accepted', (data) => {
  window.location.href = `/challenge/${data.session_id}`;
});

window.appSocket.on('challenge_declined', (data) => {
  showGlobalToast(`${data.opponent_name} declined your challenge.`, true);
});

// Button handlers emit the user's decision back to challenge.py.
document.getElementById('btn-accept').addEventListener('click', () => {
  if (pendingSession === null) return;
  window.appSocket.emit('accept_challenge', { session_id: pendingSession });
  hidePopup();
});

document.getElementById('btn-decline').addEventListener('click', () => {
  if (pendingSession === null) return;
  window.appSocket.emit('decline_challenge', { session_id: pendingSession });
  hidePopup();
});
