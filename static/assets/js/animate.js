
const Animation = function ({ offset = 10 } = {}) {
  let _elements;

  const windowTop = (offset * window.innerHeight) / 100;
  const windowBottom = window.innerHeight - windowTop;
  const windowLeft = 0;
  const windowRight = window.innerWidth;

  function start(element) {
    element.style.animationDelay = element.dataset.animationDelay || '';
    element.style.animationDuration = element.dataset.animationDuration || '';
    element.classList.add(element.dataset.animation);
    element.dataset.animated = 'true';
  }

  function isElementOnScreen(element) {
    const elementRect = element.getBoundingClientRect();
    const animationOffset = parseInt(element.dataset.animationOffset) || 0;
    const elementTop = elementRect.top + animationOffset;
    const elementBottom = elementRect.bottom - animationOffset;
    const elementLeft = elementRect.left;
    const elementRight = elementRect.right;

    return (
      elementTop <= windowBottom &&
      elementBottom >= windowTop &&
      elementLeft <= windowRight &&
      elementRight >= windowLeft
    );
  }

  function checkElementsOnScreen(els = _elements) {
    if (els) {
      for (let i = 0, len = els.length; i < len; i++) {
        if (els[i].dataset.animated === 'true') continue;

        if (isElementOnScreen(els[i])) {
          start(els[i]);
        }
      }
    }
  }

  function update() {
    _elements = document.querySelectorAll('[data-animation]');
    checkElementsOnScreen(_elements);
  }

  function resetAnimations() {
    if (!_elements) return;

    _elements.forEach((element) => {
      element.classList.remove(element.dataset.animation);
      element.dataset.animated = 'false';
    });
  }

  window.addEventListener('load', update, false);
  window.addEventListener('scroll', () => checkElementsOnScreen(_elements), { passive: true });
  window.addEventListener('resize', () => checkElementsOnScreen(_elements), { passive: true });

  if (document.readyState === 'complete') {
    update();
  }

  return {
    start,
    isElementOnScreen,
    update,
    resetAnimations,
  };
};

// Initialize
const options = {
  offset: 20,
};
const animation = new Animation(options);
