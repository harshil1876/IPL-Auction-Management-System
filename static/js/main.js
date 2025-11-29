document.addEventListener('DOMContentLoaded', () => {
    // Player selection handling
    const playerCategory = document.getElementById('playerCategory');
    if (playerCategory) {
        playerCategory.addEventListener('change', (e) => {
            // Handle player category change
            console.log('Selected category:', e.target.value);
            // TODO: Update available players list based on category
        });
    }

    // Tab handling for players page
    const playerTabs = document.getElementById('playerTabs');
    if (playerTabs) {
        const tabs = playerTabs.querySelectorAll('.nav-link');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const target = document.querySelector(tab.getAttribute('href'));
                document.querySelectorAll('.tab-pane').forEach(p => {
                    p.classList.remove('show', 'active');
                });
                target.classList.add('show', 'active');
            });
        });
    }
});
