// AI·MPS — small progressive enhancements (works fine if JS is disabled).

document.addEventListener('DOMContentLoaded', function () {
  // Animated count-up for telemetry / metric figures.
  var nums = document.querySelectorAll('[data-count]');
  nums.forEach(function (el) {
    var target = parseFloat(el.dataset.count) || 0;
    var decimals = (el.dataset.decimals ? parseInt(el.dataset.decimals, 10) : 0);
    if (target === 0) { el.textContent = target.toFixed(decimals); return; }
    var dur = 900, start = null;
    function tick(ts) {
      if (start === null) start = ts;
      var p = Math.min(1, (ts - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
});
