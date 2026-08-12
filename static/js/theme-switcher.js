(function () {
    'use strict';

    var button = document.getElementById('themeSwitch');
    var label = document.getElementById('themeSwitchLabel');
    if (!button || !label) return;

    var theme = document.documentElement.dataset.theme === 'ffxiv' ? 'ffxiv' : 'nier';

    function render() {
        var isNier = theme === 'nier';
        label.textContent = isNier ? 'YoRHa 档案' : 'FFXIV 水晶';
        button.title = isNier ? '切换到 FFXIV 蓝金风格' : '切换到 YoRHa 档案风格';
        button.setAttribute('aria-pressed', String(isNier));
    }

    button.addEventListener('click', function () {
        theme = theme === 'nier' ? 'ffxiv' : 'nier';
        localStorage.setItem('yukiko-visual-theme', theme);
        document.documentElement.dataset.theme = theme;
        render();
        window.location.reload();
    });

    render();
}());
