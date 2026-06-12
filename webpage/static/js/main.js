/* ═══════════════════════════════════════════════
   ϕ-Noise Project Page — Main JS
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // Active nav link on scroll
  const observedSections = document.querySelectorAll('section[id], div[id="teaser"]');
  const navAnchors = document.querySelectorAll('#navbar a[href^="#"]');

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      navAnchors.forEach(a => a.classList.remove('active'));
      const active = document.querySelector(`#navbar a[href="#${entry.target.id}"]`);
      if (active) active.classList.add('active');
    });
  }, { rootMargin: '-40% 0px -55% 0px' });

  observedSections.forEach(s => sectionObserver.observe(s));

  // Tab switching inside each section
  document.querySelectorAll('.tab-bar').forEach(bar => {
    const btns = bar.querySelectorAll('.tab-btn');
    const section = bar.closest('section');

    btns.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tab;
        btns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (!section) return;
        section.querySelectorAll('.tab-panel').forEach(p => {
          p.classList.toggle('active', p.dataset.panel === target);
        });
      });
    });

    if (btns.length) btns[0].click();
  });

  // BibTeX copy helper
  window.copyBibtex = function () {
    const pre = document.querySelector('#bibtex-code pre');
    const text = pre ? pre.innerText : '';
    navigator.clipboard.writeText(text).then(() => {
      const btn = document.querySelector('.copy-btn');
      if (!btn) return;
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
      setTimeout(() => { btn.innerHTML = orig; }, 2000);
    });
  };

  // Lazy-load videos that use `data-src`
  const lazyVideos = document.querySelectorAll('video[data-src]');
  if (lazyVideos.length) {
    const videoObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const v = entry.target;
        v.src = v.dataset.src;
        v.load();
        videoObserver.unobserve(v);
      });
    }, { rootMargin: '200px' });
    lazyVideos.forEach(v => videoObserver.observe(v));
  }

});
