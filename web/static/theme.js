(function () {
  const KEY = 'coagent-theme';

  function apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(KEY, theme); } catch (_) {}
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      var isDark = theme === 'dark';
      btn.setAttribute('aria-label', isDark ? '切换到白天模式' : '切换到夜间模式');
      btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
      var label = btn.querySelector('.theme-toggle-label');
      if (label) label.textContent = isDark ? '白天' : '夜间';
    });
  }

  function init() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (_) {}
    var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    apply(saved || (prefersDark ? 'dark' : 'light'));

    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        apply(next);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
