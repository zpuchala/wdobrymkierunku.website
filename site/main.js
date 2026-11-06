(function () {
  var d = document;

  // Menu mobilne
  var toggle = d.querySelector('.nav-toggle');
  var nav = d.getElementById('main-nav');
  function setNav(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Zamknij menu' : 'Otwórz menu');
    d.body.classList.toggle('nav-open', open);
  }
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      setNav(toggle.getAttribute('aria-expanded') !== 'true');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setNav(false);
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setNav(false);
        toggle.focus();
      }
    });
  }

  // Filtr odcinków według pasma
  var filters = d.querySelector('.episode-filters');
  if (filters) {
    var cards = d.querySelectorAll('.episode-card[data-range]');
    filters.hidden = false;
    filters.addEventListener('click', function (e) {
      var btn = e.target.closest('button[data-filter]');
      if (!btn) return;
      var f = btn.getAttribute('data-filter');
      filters.querySelectorAll('button').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === btn));
      });
      cards.forEach(function (c) {
        c.hidden = f !== 'all' && c.getAttribute('data-range') !== f;
      });
    });
  }

  // Odtwarzacz YouTube ładowany dopiero po kliknięciu
  d.querySelectorAll('.video-poster').forEach(function (poster) {
    poster.addEventListener('click', function () {
      var id = poster.getAttribute('data-video-id');
      var iframe = d.createElement('iframe');
      iframe.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1';
      iframe.title = poster.getAttribute('aria-label') || 'Odtwarzacz YouTube';
      iframe.loading = 'eager';
      iframe.referrerPolicy = 'strict-origin-when-cross-origin';
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.allowFullscreen = true;
      poster.replaceWith(iframe);
      iframe.focus();
    });
  });
})();
