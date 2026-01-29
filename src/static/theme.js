document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('themeToggle');
    const icon = toggleBtn.querySelector('i');

    // Check saved preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;

    let isLight = savedTheme === 'light' || (!savedTheme && systemPrefersLight);

    // Apply initial state
    if (isLight) {
        document.documentElement.setAttribute('data-theme', 'light');
        icon.className = 'fa-solid fa-moon'; // Inverted: Moon for Light (to switch to Dark)
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        icon.className = 'fa-solid fa-sun'; // Inverted: Sun for Dark (to switch to Light)
    }

    // Toggle Event
    toggleBtn.addEventListener('click', () => {
        isLight = !isLight;

        if (isLight) {
            document.documentElement.setAttribute('data-theme', 'light');
            icon.className = 'fa-solid fa-moon';
            localStorage.setItem('theme', 'light');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            icon.className = 'fa-solid fa-sun';
            localStorage.setItem('theme', 'dark');
        }
    });
});
