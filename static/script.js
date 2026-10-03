/**
 * SmartPark AI — Main JavaScript
 * Handles: particles, toast notifications, animations, UI interactions
 */

/* ── Particle System ─────────────────────────────────────────────────────── */
function createParticles() {
  const container = document.getElementById('particles');
  if (!container) return;

  const colors   = ['#00d4ff', '#00ff88', '#b44dff', '#ffd700'];
  const count    = 35;

  for (let i = 0; i < count; i++) {
    const p = document.createElement('div');
    p.className = 'particle';

    const size  = Math.random() * 3 + 1;
    const color = colors[Math.floor(Math.random() * colors.length)];
    const left  = Math.random() * 100;
    const dur   = Math.random() * 12 + 8;
    const delay = Math.random() * 8;

    p.style.cssText = `
      width:  ${size}px;
      height: ${size}px;
      left:   ${left}%;
      bottom: -10px;
      background:    ${color};
      box-shadow:    0 0 ${size * 3}px ${color};
      animation-duration:  ${dur}s;
      animation-delay:     ${delay}s;
    `;
    container.appendChild(p);
  }
}

/* ── Toast Notification ──────────────────────────────────────────────────── */
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;

  const msgEl = document.getElementById('toastMsg');
  if (msgEl) msgEl.textContent = message;

  toast.className = 'toast' + (type === 'error' ? ' error' : '');
  toast.classList.add('show');

  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove('show'), 3500);
}

/* ── Scroll Reveal Animation ─────────────────────────────────────────────── */
function initScrollReveal() {
  const cards = document.querySelectorAll('.glass-card, .stat-card');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, idx) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.style.opacity    = '1';
          entry.target.style.transform  = 'translateY(0)';
        }, idx * 80);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => {
    card.style.opacity   = '0';
    card.style.transform = 'translateY(24px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
  });
}

/* ── Counter Animation ────────────────────────────────────────────────────── */
function animateCounters() {
  document.querySelectorAll('.stat-num').forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;

    let current = 0;
    const step  = Math.max(1, Math.floor(target / 30));
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(timer);
    }, 40);
  });
}

/* ── Neon Cursor Trail ────────────────────────────────────────────────────── */
function initCursorTrail() {
  const trail = [];
  const TRAIL_LENGTH = 8;

  for (let i = 0; i < TRAIL_LENGTH; i++) {
    const dot = document.createElement('div');
    dot.style.cssText = `
      position: fixed;
      pointer-events: none;
      z-index: 9999;
      border-radius: 50%;
      transition: transform 0.1s;
      opacity: ${1 - i / TRAIL_LENGTH};
    `;
    const size = 6 - i * 0.5;
    dot.style.width  = `${size}px`;
    dot.style.height = `${size}px`;
    dot.style.background = `rgba(0,212,255,${0.8 - i * 0.08})`;
    dot.style.boxShadow  = `0 0 ${size * 2}px rgba(0,212,255,0.6)`;
    document.body.appendChild(dot);
    trail.push({ el: dot, x: 0, y: 0 });
  }

  let mouseX = 0, mouseY = 0;
  document.addEventListener('mousemove', e => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  function animateTrail() {
    trail.forEach((dot, i) => {
      const prev = i === 0 ? { x: mouseX, y: mouseY } : trail[i - 1];
      dot.x += (prev.x - dot.x) * 0.35;
      dot.y += (prev.y - dot.y) * 0.35;
      dot.el.style.left = (dot.x - parseInt(dot.el.style.width) / 2) + 'px';
      dot.el.style.top  = (dot.y - parseInt(dot.el.style.height) / 2) + 'px';
    });
    requestAnimationFrame(animateTrail);
  }
  animateTrail();
}

/* ── Slot Hover Ripple ───────────────────────────────────────────────────── */
function initSlotRipples() {
  document.querySelectorAll('.slot').forEach(slot => {
    slot.addEventListener('click', function (e) {
      const ripple = document.createElement('span');
      ripple.className = 'ripple-effect';
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        width: ${size}px; height: ${size}px;
        left: ${e.clientX - rect.left - size / 2}px;
        top:  ${e.clientY - rect.top  - size / 2}px;
        background: rgba(255,255,255,0.15);
        transform: scale(0);
        animation: rippleAnim 0.5s ease-out forwards;
        pointer-events: none;
      `;
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  if (!document.querySelector('#rippleStyle')) {
    const style = document.createElement('style');
    style.id = 'rippleStyle';
    style.textContent = `
      @keyframes rippleAnim {
        to { transform: scale(2); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }
}

/* ── Dynamic Clock in Navbar ─────────────────────────────────────────────── */
function startClock() {
  const el = document.getElementById('navClock');
  if (!el) return;
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  tick();
  setInterval(tick, 1000);
}

/* ── Input Glow on Focus ─────────────────────────────────────────────────── */
function initInputGlow() {
  document.querySelectorAll('input, select').forEach(input => {
    input.addEventListener('focus', () => {
      input.parentElement.classList.add('focused');
    });
    input.addEventListener('blur', () => {
      input.parentElement.classList.remove('focused');
    });
  });
}

/* ── Typewriter Effect for headings ──────────────────────────────────────── */
function typeWriter(el, text, speed = 50) {
  el.textContent = '';
  let i = 0;
  function type() {
    if (i < text.length) {
      el.textContent += text[i++];
      setTimeout(type, speed);
    }
  }
  type();
}

/* ── Button loading state ────────────────────────────────────────────────── */
function setButtonLoading(btn, loading) {
  if (loading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing…';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
    btn.disabled = false;
  }
}

/* ── Smooth scroll to top ────────────────────────────────────────────────── */
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ── Add scroll-to-top button ────────────────────────────────────────────── */
function initScrollTop() {
  const btn = document.createElement('button');
  btn.innerHTML = '<i class="fas fa-arrow-up"></i>';
  btn.style.cssText = `
    position: fixed;
    bottom: 90px;
    right: 32px;
    z-index: 999;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 1px solid rgba(0,212,255,0.3);
    background: rgba(0,212,255,0.08);
    color: #00d4ff;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.3s, transform 0.3s;
    font-size: 0.9rem;
  `;
  document.body.appendChild(btn);
  btn.addEventListener('click', scrollToTop);
  window.addEventListener('scroll', () => {
    btn.style.opacity   = window.scrollY > 300 ? '1' : '0';
    btn.style.transform = window.scrollY > 300 ? 'translateY(0)' : 'translateY(10px)';
  });
}

/* ── Simulated Real-time Notification ────────────────────────────────────── */
function startSimulatedNotifications() {
  const messages = [
    '🟢 Slot A03 is now Available!',
    '🔴 Slot B07 just got Occupied',
    '🟡 Area C has Moderate occupancy',
    '✅ Slot A09 freed up!',
    '🚗 New vehicle entered Area B',
    '📊 Peak hour approaching in 30 min',
  ];

  let idx = 0;
  // Show first notification after 5s, then every 15s
  setTimeout(() => {
    showToast(messages[idx++ % messages.length]);
    setInterval(() => {
      showToast(messages[idx++ % messages.length]);
    }, 15000);
  }, 5000);
}

/* ── Initialize Everything ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initScrollReveal();
  animateCounters();
  initInputGlow();
  initSlotRipples();
  startClock();
  initScrollTop();

  // Only start notifications on dashboard pages
  if (document.querySelector('.parking-grid')) {
    startSimulatedNotifications();
    // Subtle cursor trail only on desktop
    if (window.innerWidth > 768) {
      // initCursorTrail(); // Uncomment if desired
    }
  }
});
