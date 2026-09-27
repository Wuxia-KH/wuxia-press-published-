// The logo intro, as the Wuxia theme plays it whenever the site is opened.
// The timing is all CSS (assets/site.css), ending in a fade, so the cover
// can never stay. This only starts it and lets a click or key skip it.
(function () {
	var d = document.documentElement;
	d.classList.add('intro-play');
	function skip() {
		d.classList.add('intro-skip');
		document.removeEventListener('keydown', skip);
	}
	document.addEventListener('keydown', skip);
	document.addEventListener('click', function (e) {
		if (e.target.closest && e.target.closest('.brand-intro')) {
			skip();
		}
	});
})();
