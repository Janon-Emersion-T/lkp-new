

document.querySelectorAll('.accordion-toggle').forEach((toggle) => {
  toggle.addEventListener('click', function () {
    const accordion = this.closest('.accordion');
    const content = accordion.querySelector('.accordion-content');
    const icon = this.querySelector('i.fa-chevron-down');
    const accordionGroup = document.querySelector('.accordion-group');
    const allAccordions = accordionGroup.querySelectorAll('.accordion');

    // Close all open accordions except the clicked one
    allAccordions.forEach((acc) => {
      if (acc !== accordion && acc.classList.contains('active')) {
        const otherContent = acc.querySelector('.accordion-content');
        const otherIcon = acc.querySelector('i.fa-chevron-down');
        otherContent.style.height = '0';
        otherIcon.style.transform = 'rotate(0deg)';
        acc.classList.remove('active');
      }
    });

    // Toggle the clicked accordion
    if (accordion.classList.contains('active')) {
      // Close it
      content.style.height = '0';
      icon.style.transform = 'rotate(0deg)';
      accordion.classList.remove('active');
    } else {
      // Open it
      content.style.height = `${content.scrollHeight}px`;
      icon.style.transform = 'rotate(180deg)';
      accordion.classList.add('active');
    }
  });
});
