
// Set current year in footer
document.getElementById('current-year').textContent = new Date().getFullYear();

// Generate GitHub contribution graph
generateContributionGraph();

function generateContributionGraph() {
  const gridContainer = document.getElementById('contribution-grid');
  if (!gridContainer) return;
  
  // Create 7 rows (days of week) for each of the 53 weeks
  for (let week = 0; week < 53; week++) {
    const weekEl = document.createElement('div');
    weekEl.className = 'contribution-week';
    
    for (let day = 0; day < 7; day++) {
      const contributionDay = document.createElement('div');
      contributionDay.className = 'contribution-day';
      
      // Generate random contribution level
      const isWeekend = day === 0 || day === 6;
      const baseChance = isWeekend ? 0.3 : 0.7;
      const patternBoost = (week % 2 === 0) ? 0.2 : 0;
      
      const rand = Math.random();
      const hasContribution = rand < (baseChance + patternBoost);
      
      let contributionCount = 0;
      if (hasContribution) {
        contributionCount = Math.floor(Math.random() * 4) + 1; // 1-4 contributions
      }
      
      // Date calculation
      const today = new Date();
      const date = new Date(today);
      date.setDate(today.getDate() - ((53 - week) * 7) - (6 - day));
      
      // Set class based on contribution level
      contributionDay.classList.add(`level-${contributionCount}`);
      
      // Set tooltip data
      contributionDay.dataset.date = date.toLocaleDateString();
      contributionDay.dataset.count = contributionCount;
      contributionDay.title = `${contributionCount} contributions on ${date.toLocaleDateString()}`;
      
      weekEl.appendChild(contributionDay);
    }
    
    gridContainer.appendChild(weekEl);
  }
}

// Add animation classes when elements come into view
document.addEventListener('DOMContentLoaded', function() {
  const animatedElements = document.querySelectorAll('.animation-fade-in');
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });
  
  animatedElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
  });
});
