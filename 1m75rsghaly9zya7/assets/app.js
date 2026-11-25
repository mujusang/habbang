/* 『중경방 임상강좌 각론』 읽기 화면 — 사이드바·목차·진행 표시 */
(function () {
  'use strict';

  var body = document.body;
  var menuBtn = document.getElementById('menuBtn');
  var backdrop = document.getElementById('backdrop');
  var sidebar = document.getElementById('sidebar');

  function closeNav() { body.classList.remove('nav-open'); }

  if (menuBtn) {
    menuBtn.addEventListener('click', function () {
      body.classList.toggle('nav-open');
    });
  }
  if (backdrop) backdrop.addEventListener('click', closeNav);
  if (sidebar) {
    sidebar.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeNav();
    });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeNav();
  });

  /* 소절 펼치기 */
  Array.prototype.forEach.call(document.querySelectorAll('.chev'), function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var li = btn.closest('li');
      var open = li.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.textContent = open ? '▾' : '▸';
    });
  });

  /* 이 문서에서 찾기 */
  var filter = document.getElementById('tocFilter');
  if (filter) {
    filter.addEventListener('input', function () {
      var q = filter.value.trim().toLowerCase();
      Array.prototype.forEach.call(document.querySelectorAll('.sectionlist > li'), function (li) {
        if (!q) { li.style.display = ''; return; }
        var hit = li.textContent.toLowerCase().indexOf(q) !== -1;
        li.style.display = hit ? '' : 'none';
        if (hit) li.classList.add('open');
      });
    });
  }

  /* 진행 막대 · 맨 위로 */
  var bar = document.getElementById('progress');
  var top = document.getElementById('totop');
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var y = h.scrollTop || body.scrollTop;
    if (bar) bar.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';
    if (top) top.classList.toggle('show', y > 600);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();
  if (top) top.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* 지금 읽는 절 표시 */
  var links = {};
  Array.prototype.forEach.call(document.querySelectorAll('.sectionlist a[href^="#"]'), function (a) {
    links[decodeURIComponent(a.getAttribute('href').slice(1))] = a;
  });
  var heads = Array.prototype.slice.call(document.querySelectorAll('article h2[id], article h3[id]'));
  if ('IntersectionObserver' in window && heads.length) {
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var a = links[en.target.id];
        if (!a || a === current) return;
        if (current) current.classList.remove('current');
        current = a;
        a.classList.add('current');
        var li = a.closest('li');
        if (li && li.parentElement.classList.contains('s3')) li.parentElement.parentElement.classList.add('open');
        if (sidebar) {
          var r = a.getBoundingClientRect();
          var sr = sidebar.getBoundingClientRect();
          if (r.top < sr.top || r.bottom > sr.bottom) {
            sidebar.scrollTop += (r.top - sr.top) - (sr.height / 2 - r.height / 2);
          }
        }
      });
    }, { rootMargin: '-64px 0px -70% 0px', threshold: 0 });
    heads.forEach(function (h) { io.observe(h); });
  }
})();
