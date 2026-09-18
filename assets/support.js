/* Support page behaviour: copy-address with a toast. DOM API only, no
 * direct HTML injection, no network, no storage — same discipline as app.js. */
(function () {
  'use strict';
  var addrEl = document.getElementById('dogeAddr');
  var btn = document.getElementById('copyAddr');
  var toast = document.getElementById('toast');
  if (!addrEl || !btn) return;
  var ADDR = (addrEl.textContent || '').trim();
  var hideT = null;

  function say(msg) {
    if (!toast) return;
    while (toast.firstChild) toast.removeChild(toast.firstChild);
    toast.appendChild(document.createTextNode(msg));
    toast.classList.add('show');
    if (hideT) clearTimeout(hideT);
    hideT = setTimeout(function () { toast.classList.remove('show'); }, 2200);
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  /**
   * One copy path for every control on this page.
   *
   * There were two. The first, on the support button, tried the async API and
   * fell back to execCommand; the second, added with the launch offer, tried
   * the async API and gave up. So the same click could succeed on one button
   * and fail on the other in the same browser, and the two reported it in
   * different words. On a page where the thing being copied is a payment
   * address, a copy that quietly does nothing is the worst outcome available.
   *
   * Resolves to true or false; the caller decides what to say.
   */
  function copyText(value) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(value).then(
        function () { return true; },
        function () { return fallbackCopy(value); }
      );
    }
    return Promise.resolve(fallbackCopy(value));
  }

  var COPIED = 'Copied';
  var COPY_FAILED = 'Copy failed — select manually';

  btn.addEventListener('click', function () {
    copyText(ADDR).then(function (ok) { say(ok ? COPIED : COPY_FAILED); });
  });

  // The launch-offer button, which used to carry its own half of this logic.
  // The confirmation lands on the button itself because it sits far from the
  // toast, and both use the same two strings.
  document.addEventListener('click', function (e) {
    var b = e.target && e.target.closest && e.target.closest('[data-copy]');
    if (!b) return;
    var restore = b.textContent;
    copyText(b.getAttribute('data-copy') || '').then(function (ok) {
      b.textContent = ok ? COPIED : COPY_FAILED;
      setTimeout(function () { b.textContent = restore; }, 2200);
    });
  });
})();
