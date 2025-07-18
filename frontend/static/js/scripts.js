window.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.getElementById('sidebarToggle');
    const mainContent = document.querySelector('main');
  
    if (!sidebar || !toggleButton || !mainContent) return;
  
    // Check saved state
    if (localStorage.getItem('sidebarOpen') === 'true') {
      sidebar.style.left = '0';
      mainContent.style.marginLeft = '220px';
      toggleButton.classList.add('active');
    }
  
    toggleButton.addEventListener('click', () => {
      if (sidebar.style.left === '0px') {
        sidebar.style.left = '-200px';
        mainContent.style.marginLeft = '0';
        toggleButton.classList.remove('active');
        localStorage.setItem('sidebarOpen', 'false');
      } else {
        sidebar.style.left = '0';
        mainContent.style.marginLeft = '220px';
        toggleButton.classList.add('active');
        localStorage.setItem('sidebarOpen', 'true');
      }
    });
  });
  