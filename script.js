// Retro Pi Portfolio - JavaScript
// Lightweight theme switcher and custom audio player logic

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initAudioPlayer();
});

// ==========================================
// 1. Theme Switcher Logic
// ==========================================
function initTheme() {
  const themeBtns = document.querySelectorAll('.theme-btn');
  const savedTheme = localStorage.getItem('site-theme') || 'paper';

  // Apply saved theme
  setTheme(savedTheme);

  themeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const theme = btn.getAttribute('data-set-theme');
      setTheme(theme);
    });
  });
}

function setTheme(theme) {
  if (theme === 'paper') {
    document.documentElement.removeAttribute('data-theme');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }
  localStorage.setItem('site-theme', theme);

  // Update active buttons styling
  document.querySelectorAll('.theme-btn').forEach(btn => {
    if (btn.getAttribute('data-set-theme') === theme) {
      btn.style.textDecoration = 'underline';
      btn.style.fontWeight = 'bold';
    } else {
      btn.style.textDecoration = 'none';
      btn.style.fontWeight = 'normal';
    }
  });
}

// ==========================================
// 2. Custom Retro Audio Player Logic
// ==========================================
function initAudioPlayer() {
  const audio = document.getElementById('main-audio');
  if (!audio) return; // Only run on page with audio player

  const playPauseBtn = document.getElementById('btn-play-pause');
  const stopBtn = document.getElementById('btn-stop');
  const prevBtn = document.getElementById('btn-prev');
  const nextBtn = document.getElementById('btn-next');
  const progressSlider = document.getElementById('player-progress');
  const trackNameDisplay = document.getElementById('display-track-name');
  const timeDisplay = document.getElementById('display-time');
  const playlistItems = document.querySelectorAll('.playlist-item');

  let currentTrackIndex = 0;
  const tracks = [];

  // Parse tracks from the HTML playlist
  playlistItems.forEach((item, index) => {
    const fileUrl = item.getAttribute('data-src');
    const title = item.querySelector('.track-title').textContent;
    tracks.push({ url: fileUrl, title: title, element: item });

    item.addEventListener('click', (e) => {
      // Prevent triggering if clicked directly on an absolute download link
      if (e.target.tagName === 'A' && e.target.hasAttribute('download')) {
        return;
      }
      playTrack(index);
    });
  });

  // Track state
  let isPlaying = false;

  function playTrack(index) {
    if (index < 0 || index >= tracks.length) return;
    
    // Update active playlist styling
    tracks.forEach(t => t.element.classList.remove('active'));
    tracks[index].element.classList.add('active');
    
    currentTrackIndex = index;
    audio.src = tracks[index].url;
    trackNameDisplay.textContent = `[PLAYING] ${tracks[index].title}`;
    
    audio.play()
      .then(() => {
        isPlaying = true;
        updatePlayButtonState();
      })
      .catch(err => {
        console.warn('Audio play failed: ', err);
        trackNameDisplay.textContent = `[ERROR LOADING] ${tracks[index].title}`;
      });
  }

  function togglePlay() {
    if (tracks.length === 0) return;

    if (isPlaying) {
      audio.pause();
      isPlaying = false;
      trackNameDisplay.textContent = `[PAUSED] ${tracks[currentTrackIndex].title}`;
    } else {
      // If src is empty, load the first track
      if (!audio.src || audio.src === window.location.href) {
        playTrack(0);
        return;
      }
      audio.play().then(() => {
        isPlaying = true;
        trackNameDisplay.textContent = `[PLAYING] ${tracks[currentTrackIndex].title}`;
      });
    }
    updatePlayButtonState();
  }

  function updatePlayButtonState() {
    playPauseBtn.textContent = isPlaying ? '[PAUSE]' : '[PLAY]';
  }

  function stopTrack() {
    audio.pause();
    audio.currentTime = 0;
    isPlaying = false;
    updatePlayButtonState();
    trackNameDisplay.textContent = `[STOPPED] ${tracks[currentTrackIndex].title}`;
    progressSlider.value = 0;
    updateTimeDisplay(0, audio.duration || 0);
  }

  function nextTrack() {
    let nextIndex = currentTrackIndex + 1;
    if (nextIndex >= tracks.length) nextIndex = 0; // Loop to start
    playTrack(nextIndex);
  }

  function prevTrack() {
    let prevIndex = currentTrackIndex - 1;
    if (prevIndex < 0) prevIndex = tracks.length - 1; // Loop to end
    playTrack(prevIndex);
  }

  // Audio Event Listeners
  audio.addEventListener('timeupdate', () => {
    if (audio.duration) {
      const percentage = (audio.currentTime / audio.duration) * 100;
      progressSlider.value = percentage;
      updateTimeDisplay(audio.currentTime, audio.duration);
    }
  });

  audio.addEventListener('loadedmetadata', () => {
    updateTimeDisplay(audio.currentTime, audio.duration);
  });

  audio.addEventListener('ended', () => {
    nextTrack();
  });

  // Controls Event Listeners
  playPauseBtn.addEventListener('click', togglePlay);
  stopBtn.addEventListener('click', stopTrack);
  prevBtn.addEventListener('click', prevTrack);
  nextBtn.addEventListener('click', nextTrack);

  // Dragging progress bar
  progressSlider.addEventListener('input', () => {
    if (audio.duration) {
      const newTime = (progressSlider.value / 100) * audio.duration;
      audio.currentTime = newTime;
    }
  });

  // Time Formatter (mm:ss)
  function formatTime(seconds) {
    if (isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  function updateTimeDisplay(current, duration) {
    timeDisplay.textContent = `${formatTime(current)} / ${formatTime(duration)}`;
  }

  // Initialize display with first track
  if (tracks.length > 0) {
    trackNameDisplay.textContent = `[READY] ${tracks[0].title}`;
    tracks[0].element.classList.add('active');
  }
}
