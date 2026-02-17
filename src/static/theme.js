(function () {
    const applyTheme = (light, icon) => {
        document.documentElement.setAttribute('data-theme', light ? 'light' : 'dark');
        if (icon) {
            icon.className = light ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
        }
    };

    const initTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
        let isLight = savedTheme === 'light' || (!savedTheme && systemPrefersLight);

        // Apply theme to document immediately (though the head script should have done this)
        applyTheme(isLight);

        const attachToggle = () => {
            const toggleBtn = document.getElementById('themeToggle');
            const icon = toggleBtn ? toggleBtn.querySelector('i') : null;

            if (toggleBtn) {
                // Update icon to match current state
                applyTheme(isLight, icon);

                toggleBtn.onclick = (e) => {
                    e.preventDefault();
                    isLight = !isLight;
                    localStorage.setItem('theme', isLight ? 'light' : 'dark');
                    applyTheme(isLight, icon);
                };
            } else {
                // If button not found, try again in a bit (for dynamic content or late rendering)
                setTimeout(attachToggle, 100);
            }
        };

        attachToggle();
    };

    // Sync across tabs
    window.addEventListener('storage', (e) => {
        if (e.key === 'theme') {
            initTheme();
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
})();
