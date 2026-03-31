/**
 * IronDome — Tactical Animation System
 * src/scripts/animations.js
 *
 * IntersectionObserver-driven entrance animations.
 * Observes all elements with [data-animate] and adds the
 * appropriate CSS class when they enter the viewport.
 *
 * Usage in Astro/HTML:
 *   <div data-animate="fade-in-up">...</div>
 *   <div data-animate="fade-in-left" data-animate-delay="200">...</div>
 *   <h2 data-animate="text-reveal">...</h2>
 *
 * Supported data-animate values:
 *   fade-in-up | fade-in-left | fade-in-right | text-reveal
 *   (all map to CSS classes defined in animations.css)
 *
 * data-animate-delay (ms): optional delay before .visible is added.
 * data-animate-threshold (0-1): optional override for intersection ratio.
 */

(function initAnimations() {
  // Skip if IntersectionObserver is not supported (old browsers)
  if (typeof IntersectionObserver === 'undefined') {
    // Reveal everything immediately — graceful degradation
    document.querySelectorAll('[data-animate]').forEach(function (el) {
      el.classList.add('visible');
    });
    return;
  }

  // Skip for users who prefer reduced motion
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('[data-animate]').forEach(function (el) {
      el.classList.add('visible');
    });
    return;
  }

  /**
   * Apply the animation class to an element.
   * The CSS class matches the data-animate attribute value.
   * The .visible class triggers the transition/animation.
   *
   * @param {Element} el
   */
  function applyAnimation(el) {
    const animationClass = el.getAttribute('data-animate');
    const delay = parseInt(el.getAttribute('data-animate-delay') || '0', 10);

    // Ensure the base animation class is present
    if (animationClass && !el.classList.contains(animationClass)) {
      el.classList.add(animationClass);
    }

    // Apply stagger delay if specified as data attribute
    if (delay > 0) {
      el.style.transitionDelay = delay + 'ms';
      el.style.animationDelay = delay + 'ms';
    }

    // Trigger the transition/animation
    if (delay > 0) {
      setTimeout(function () {
        el.classList.add('visible');
      }, delay);
    } else {
      el.classList.add('visible');
    }
  }

  /**
   * Build observer. Each element can override threshold via
   * data-animate-threshold attribute.
   */
  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;

        var el = entry.target;
        applyAnimation(el);

        // Unobserve after trigger — each animation fires once
        observer.unobserve(el);
      });
    },
    {
      threshold: 0.1,
      rootMargin: '0px 0px -40px 0px',
    }
  );

  /**
   * Observe all [data-animate] elements present at script load.
   * Elements added dynamically after load are not observed
   * unless initAnimations() is called again or a MutationObserver
   * is added (not needed for a static Astro site).
   */
  function observeAll() {
    document.querySelectorAll('[data-animate]').forEach(function (el) {
      var animationClass = el.getAttribute('data-animate');

      // Add the base CSS class immediately so the initial hidden
      // state (opacity:0, transform) is applied before the element
      // enters the viewport. Without this, there's a flash.
      if (animationClass) {
        el.classList.add(animationClass);
      }

      // Elements that are already in viewport on load get a short
      // delay so the page has time to paint before animating.
      var rect = el.getBoundingClientRect();
      var alreadyVisible = rect.top < window.innerHeight && rect.bottom > 0;

      if (alreadyVisible) {
        setTimeout(function () {
          applyAnimation(el);
        }, 120);
      } else {
        observer.observe(el);
      }
    });
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', observeAll);
  } else {
    observeAll();
  }

  // Astro View Transitions: re-run after page navigation
  document.addEventListener('astro:page-load', observeAll);

  // Expose for manual invocation if needed (e.g., after dynamic content)
  window.__ironDomeAnimations = {
    init: observeAll,
    observe: function (el) {
      var animationClass = el.getAttribute('data-animate');
      if (animationClass) el.classList.add(animationClass);
      observer.observe(el);
    },
  };
})();
