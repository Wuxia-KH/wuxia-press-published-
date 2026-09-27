// deploy.html: copy buttons on command blocks, and the table of contents
// marking the section being read.
document.querySelectorAll('.code').forEach((block) => {
  const button = block.querySelector('.copy');
  const text = block.querySelector('pre').innerText;
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = 'Copied';
      button.classList.add('done');
    } catch {
      button.textContent = 'Select';
      getSelection().selectAllChildren(block.querySelector('pre'));
    }
    setTimeout(() => { button.textContent = 'Copy'; button.classList.remove('done'); }, 1800);
  });
});

// The section under the reading line (just below the header) is the one lit;
// whole sections are watched, so a long one stays lit all the way down.
const links = new Map([...document.querySelectorAll('.toc a')].map((a) => [a.hash.slice(1), a]));
const sections = [...links.keys()].map((id) => document.getElementById(id)?.closest('section')).filter(Boolean);
const visible = new Set();
function mark() {
  // At the very bottom the last, short section can never reach the reading line.
  const atEnd = innerHeight + scrollY >= document.documentElement.scrollHeight - 4;
  const current = atEnd ? sections[sections.length - 1] : sections.find((s) => visible.has(s));
  links.forEach((a) => a.classList.remove('on'));
  if (current) links.get(current.querySelector('h2').id)?.classList.add('on');
}
const seen = new IntersectionObserver((entries) => {
  for (const e of entries) e.isIntersecting ? visible.add(e.target) : visible.delete(e.target);
  mark();
}, { rootMargin: '-90px 0px -85% 0px' });
sections.forEach((s) => seen.observe(s));
addEventListener('scroll', mark, { passive: true });
