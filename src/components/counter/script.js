document.addEventListener('DOMContentLoaded', function() {
  const counters = document.querySelectorAll('.counter-component');
  
  counters.forEach(counter => {
    const decreaseBtn = counter.querySelector('.counter-decrease');
    const increaseBtn = counter.querySelector('.counter-increase');
    const valueDisplay = counter.querySelector('.counter-value');
    
    if (decreaseBtn && increaseBtn && valueDisplay) {
      let value = parseInt(valueDisplay.textContent) || 0;
      const minValue = parseInt(counter.dataset.minValue) || 0;
      const maxValue = parseInt(counter.dataset.maxValue) || 100;
      const step = parseInt(counter.dataset.step) || 1;
      
      decreaseBtn.addEventListener('click', function() {
        if (value > minValue) {
          value -= step;
          valueDisplay.textContent = value;
        }
      });
      
      increaseBtn.addEventListener('click', function() {
        if (value < maxValue) {
          value += step;
          valueDisplay.textContent = value;
        }
      });
    }
  });
});