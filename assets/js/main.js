/* Northline Studio — site behaviour. No dependencies, no external requests. */
(function () {
  'use strict';

  /* ---- mobile nav ------------------------------------------------------- */
  var burger = document.querySelector('.burger');
  var nav = document.getElementById('nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.hasAttribute('data-open');
      if (open) { nav.removeAttribute('data-open'); } else { nav.setAttribute('data-open', ''); }
      burger.setAttribute('aria-expanded', String(!open));
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') { nav.removeAttribute('data-open'); burger.setAttribute('aria-expanded', 'false'); }
    });
  }

  /* ---- scroll reveal ---------------------------------------------------- */
  var rising = document.querySelectorAll('[data-rise]');
  if ('IntersectionObserver' in window && rising.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    rising.forEach(function (el) { io.observe(el); });
  } else {
    rising.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* ---- lightweight analytics ------------------------------------------- *
   * Every interesting click is pushed to window.dataLayer. That means the
   * same markup works with GA4, Plausible or nothing at all — swap the
   * snippet in <head> and the events keep flowing.
   * ---------------------------------------------------------------------- */
  window.dataLayer = window.dataLayer || [];

  function track(name, params) {
    var payload = Object.assign({ event: name }, params || {});
    window.dataLayer.push(payload);
    if (typeof window.gtag === 'function') { window.gtag('event', name, params || {}); }
    if (window.plausible) { window.plausible(name, { props: params || {} }); }
  }

  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-track]');
    if (!el) return;
    track(el.getAttribute('data-track'), {
      package_name: el.getAttribute('data-package') || undefined,
      package_price: el.getAttribute('data-price') || undefined,
      location: el.getAttribute('data-where') || undefined
    });
  });

  /* which packages get looked at — fires once per card per page view */
  var seen = {};
  var cards = document.querySelectorAll('[data-package-view]');
  if ('IntersectionObserver' in window && cards.length) {
    var vio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var key = en.target.getAttribute('data-package-view');
        if (en.isIntersecting && !seen[key]) {
          seen[key] = 1;
          track('view_package_card', { package_name: key });
        }
      });
    }, { threshold: 0.6 });
    cards.forEach(function (c) { vio.observe(c); });
  }

  /* ---- footer year ----------------------------------------------------- */
  var y = document.getElementById('year');
  if (y) { y.textContent = new Date().getFullYear(); }
})();
