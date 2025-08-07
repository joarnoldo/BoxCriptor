document.addEventListener('DOMContentLoaded', () => {
  const observerOptions = { threshold: 0.1 };
  const sections = document.querySelectorAll('section');
  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  }, observerOptions);
  sections.forEach(sec => observer.observe(sec));
});

