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

  btn.addEventListener('click', function () {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(ADDR).then(
        function () { say('DOGE address copied — thank you!'); },
        function () { say(fallbackCopy(ADDR) ? 'DOGE address copied — thank you!' : 'Copy failed — select the address manually'); }
      );
    } else {
      say(fallbackCopy(ADDR) ? 'DOGE address copied — thank you!' : 'Copy failed — select the address manually');
    }
  });
})();

  // Copy-to-clipboard for the address, with a visible result.
  //
  // Nothing is assigned as markup anywhere on this page, so the confirmation is a text node on
  // the button itself. If the clipboard API is unavailable — an insecure
  // context, an old browser, a user who blocked it — the button says so rather
  // than silently doing nothing, because a payment address that you think you
  // copied and did not is a worse outcome than no button.
  document.addEventListener('click', function (e) {
    var b = e.target && e.target.closest && e.target.closest('[data-copy]');
    if (!b) return;
    var value = b.getAttribute('data-copy') || '';
    var restore = b.textContent;
    function say(msg) {
      b.textContent = msg;
      setTimeout(function () { b.textContent = restore; }, 2200);
    }
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      say('Select it and copy by hand');
      return;
    }
    navigator.clipboard.writeText(value).then(
      function () { say('Copied'); },
      function () { say('Could not copy — select it by hand'); }
    );
  });
