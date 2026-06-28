(function () {
  'use strict';

  // Mobile nav toggle
  const toggle = document.querySelector('.nav-toggle');
  const mobileNav = document.getElementById('mobile-nav');

  if (toggle && mobileNav) {
    toggle.addEventListener('click', () => {
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      mobileNav.hidden = expanded;
    });

    mobileNav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        toggle.setAttribute('aria-expanded', 'false');
        mobileNav.hidden = true;
      });
    });
  }

  // Scroll reveal
  const revealEls = document.querySelectorAll('.reveal');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (reducedMotion) {
    revealEls.forEach((el) => el.classList.add('visible'));
  } else {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    revealEls.forEach((el) => revealObserver.observe(el));
  }

  // Animate bar fills when confidence section enters view
  const barFills = document.querySelectorAll('.bar .fill');
  if (barFills.length && !reducedMotion) {
    const barObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            barFills.forEach((fill, i) => {
              setTimeout(() => fill.classList.add('animated'), i * 80);
            });
            barObserver.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );
    const chart = document.querySelector('.confidence-chart');
    if (chart) barObserver.observe(chart);
  } else {
    barFills.forEach((fill) => fill.classList.add('animated'));
  }

  // Count-up animation for stat numbers
  function animateCount(el, target, duration) {
    const start = performance.now();
    const isDecimal = String(target).includes('.');
    const numericTarget = parseFloat(target);

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = numericTarget * eased;

      if (isDecimal) {
        el.textContent = current.toFixed(1);
      } else {
        el.textContent = Math.round(current);
      }

      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }

  const statNums = document.querySelectorAll('.stat-num');
  if (statNums.length && !reducedMotion) {
    const statObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const target = el.dataset.target;
            if (target && !el.dataset.counted) {
              el.dataset.counted = 'true';
              animateCount(el, target, 1200);
            }
            statObserver.unobserve(el);
          }
        });
      },
      { threshold: 0.5 }
    );
    statNums.forEach((el) => statObserver.observe(el));
  } else {
    statNums.forEach((el) => {
      if (el.dataset.target) el.textContent = el.dataset.target;
    });
  }

  // Pipeline step progression animation
  const steps = document.querySelectorAll('.pipeline-steps .step');
  if (steps.length >= 5 && !reducedMotion) {
    let current = 2; // start at step 3 (index 2) as "active"

    setInterval(() => {
      steps.forEach((s) => s.classList.remove('active'));
      steps[current].classList.add('active');

      for (let i = 0; i < current; i++) steps[i].classList.add('done');
      for (let i = current + 1; i < steps.length; i++) steps[i].classList.remove('done');

      current = (current + 1) % steps.length;
    }, 2400);
  }

  // Header shadow on scroll
  const header = document.querySelector('.site-header');
  if (header) {
    window.addEventListener(
      'scroll',
      () => {
        header.style.boxShadow = window.scrollY > 8 ? 'var(--shadow-sm)' : 'none';
      },
      { passive: true }
    );
  }
})();
