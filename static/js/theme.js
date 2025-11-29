document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        body.classList.add(savedTheme);
        updateThemeIcon(savedTheme === 'dark-theme');
    }

    themeToggle.addEventListener('click', () => {
        const isDark = body.classList.toggle('dark-theme');
        body.classList.toggle('light-theme');
        
        // Save theme preference
        localStorage.setItem('theme', isDark ? 'dark-theme' : 'light-theme');
        updateThemeIcon(isDark);
    });

    function updateThemeIcon(isDark) {
        const icon = themeToggle.querySelector('i');
        icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    }
});
