/**
 * IronDome — Tactical Animation System
 * src/scripts/animations.js
 *
 * ---------------------------------------------------------------
 * SECTION 1: IntersectionObserver scroll reveals
 *   Observes [data-animate] and [data-animate="declassify"] and
 *   [data-declassify-group] elements, adds .visible on viewport
 *   entry. Supports data-animate-delay (ms) and
 *   data-animate-threshold (0-1) overrides.
 *
 * SECTION 2: Terminal typing engine
 *   Observes [data-type-target][data-type-text] elements.
 *   On viewport entry, types out data-type-text one character at
 *   a time. Supports:
 *     data-type-speed (ms per char, default 38)
 *     data-type-loop  (present = loop with 2s pause between runs)
 *     data-no-cursor  (suppress trailing cursor after completion)
 *
 * SECTION 3: Page loader dismissal
 *   If a .page-loader element exists, removes .page-loader--active
 *   on DOMContentLoaded, then removes the node from the DOM after
 *   the fade transition completes.
 * ---------------------------------------------------------------
 */

(function () {
  'use strict';

  /* ============================================================
     UTILITIES
     ============================================================ */

  var prefersReducedMotion = (
    typeof window !== 'undefined' &&
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );

  var supportsIntersectionObserver = typeof IntersectionObserver !== 'undefined';

  /* ============================================================
     SECTION 1: SCROLL REVEAL ANIMATIONS
     ============================================================ */

  /**
   * Supported data-animate values → CSS class that owns the
   * hidden initial state and the .visible trigger:
   *
   *   fade-in-up    (.fade-in-up)
   *   fade-in-left  (.fade-in-left)
   *   fade-in-right (.fade-in-right)
   *   text-reveal   (.text-reveal)
   *   declassify    (.declassify)
   *
   * .declassify-group elements do NOT use data-animate;
   * they are observed separately as groups.
   */

  function applyScrollReveal(el) {
    var animClass = el.getAttribute('data-animate');
    var delay = parseInt(el.getAttribute('data-animate-delay') || '0', 10);

    if (animClass && !el.classList.contains(animClass)) {
      el.classList.add(animClass);
    }

    if (delay > 0) {
      el.style.transitionDelay = delay + 'ms';
      el.style.animationDelay = delay + 'ms';
    }

    if (delay > 0) {
      setTimeout(function () { el.classList.add('visible'); }, delay);
    } else {
      el.classList.add('visible');
    }
  }

  function initScrollReveals() {
    if (prefersReducedMotion) {
      /* Reveal everything immediately for reduced-motion users */
      document.querySelectorAll('[data-animate]').forEach(function (el) {
        var animClass = el.getAttribute('data-animate');
        if (animClass) el.classList.add(animClass);
        el.classList.add('visible');
      });
      document.querySelectorAll('.declassify-group').forEach(function (el) {
        el.classList.add('visible');
      });
      return;
    }

    if (!supportsIntersectionObserver) {
      document.querySelectorAll('[data-animate]').forEach(function (el) {
        el.classList.add('visible');
      });
      document.querySelectorAll('.declassify-group').forEach(function (el) {
        el.classList.add('visible');
      });
      return;
    }

    /* --- IntersectionObserver for [data-animate] elements --- */
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          applyScrollReveal(entry.target);
          revealObserver.unobserve(entry.target);
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    document.querySelectorAll('[data-animate]').forEach(function (el) {
      var animClass = el.getAttribute('data-animate');
      if (animClass) el.classList.add(animClass);

      var rect = el.getBoundingClientRect();
      var alreadyVisible = rect.top < window.innerHeight && rect.bottom > 0;

      if (alreadyVisible) {
        setTimeout(function () { applyScrollReveal(el); }, 120);
      } else {
        revealObserver.observe(el);
      }
    });

    /* --- IntersectionObserver for .declassify-group containers --- */
    var groupObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('visible');
          groupObserver.unobserve(entry.target);
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    document.querySelectorAll('.declassify-group').forEach(function (el) {
      var rect = el.getBoundingClientRect();
      var alreadyVisible = rect.top < window.innerHeight && rect.bottom > 0;

      if (alreadyVisible) {
        setTimeout(function () { el.classList.add('visible'); }, 150);
      } else {
        groupObserver.observe(el);
      }
    });
  }

  /* ============================================================
     SECTION 2: TERMINAL TYPING ENGINE
     ============================================================
     Usage:
       <span
         data-type-target
         data-type-text="pip install IronDome"
         data-type-speed="40"
       ></span>

       Loop: add data-type-loop (no value needed)
       No cursor after completion: add data-no-cursor
  */

  /**
   * Type a string into an element character by character.
   * Returns a cancel function that aborts the sequence.
   *
   * @param {HTMLElement} el
   * @param {string}      text
   * @param {number}      speed  — ms per character
   * @param {Function}    onDone — called when typing completes
   * @returns {Function}         — cancel()
   */
  function typeInto(el, text, speed, onDone) {
    var index = 0;
    var cancelled = false;
    var timerId = null;

    el.textContent = '';
    el.classList.remove('is-typed');
    el.classList.add('is-typing');

    function typeNext() {
      if (cancelled) return;

      if (index < text.length) {
        el.textContent += text[index];
        index++;
        timerId = setTimeout(typeNext, speed);
      } else {
        el.classList.remove('is-typing');
        el.classList.add('is-typed');
        if (typeof onDone === 'function') onDone();
      }
    }

    /* Small initial pause before first character — feels more intentional */
    timerId = setTimeout(typeNext, 200);

    return function cancel() {
      cancelled = true;
      clearTimeout(timerId);
    };
  }

  /**
   * Start (or restart) typing for a single element.
   * Handles looping internally if data-type-loop is present.
   */
  function startTyping(el) {
    var text  = el.getAttribute('data-type-text') || '';
    var speed = parseInt(el.getAttribute('data-type-speed') || '38', 10);
    var loop  = el.hasAttribute('data-type-loop');

    if (!text) return;

    /* If reduced motion, just set the text immediately */
    if (prefersReducedMotion) {
      el.textContent = text;
      el.classList.add('is-typed');
      return;
    }

    function run() {
      typeInto(el, text, speed, function () {
        if (loop) {
          /* 2-second pause between loops */
          setTimeout(function () {
            el.classList.remove('is-typed');
            run();
          }, 2000);
        }
      });
    }

    run();
  }

  function initTypingEffects() {
    if (!supportsIntersectionObserver) {
      document.querySelectorAll('[data-type-target][data-type-text]').forEach(startTyping);
      return;
    }

    var typingObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          typingObserver.unobserve(entry.target);
          startTyping(entry.target);
        });
      },
      {
        threshold: 0.3,
        rootMargin: '0px 0px -20px 0px',
      }
    );

    document.querySelectorAll('[data-type-target][data-type-text]').forEach(function (el) {
      var rect = el.getBoundingClientRect();
      var alreadyVisible = rect.top < window.innerHeight && rect.bottom > 0;

      if (alreadyVisible) {
        /* Already in view: delay slightly so initial paint settles */
        setTimeout(function () { startTyping(el); }, 300);
      } else {
        typingObserver.observe(el);
      }
    });
  }

  /* ============================================================
     SECTION 3: PAGE LOADER DISMISSAL
     ============================================================ */

  function initPageLoader() {
    var loader = document.querySelector('.page-loader');
    if (!loader) return;

    function dismiss() {
      loader.classList.add('page-loader--hidden');
      /* Remove from DOM after CSS fade-out (350ms + 100ms delay = 500ms) */
      setTimeout(function () {
        if (loader.parentNode) loader.parentNode.removeChild(loader);
      }, 500);
    }

    if (document.readyState === 'complete') {
      dismiss();
    } else {
      window.addEventListener('load', dismiss, { once: true });
    }
  }

  /* ============================================================
     BOOT — Initialize everything
     ============================================================ */

  function boot() {
    initScrollReveals();
    initTypingEffects();
    initPageLoader();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  /* Astro View Transitions: re-run after client-side navigation */
  document.addEventListener('astro:page-load', function () {
    initScrollReveals();
    initTypingEffects();
  });

  /* Public API — for dynamic content that arrives after boot */
  window.__ironDomeAnimations = {
    init: boot,
    reveal: applyScrollReveal,
    type: startTyping,
    observe: function (el) {
      var animClass = el.getAttribute('data-animate');
      if (animClass) el.classList.add(animClass);
    },
  };
})();
