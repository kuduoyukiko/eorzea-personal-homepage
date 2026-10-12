(function () {
    'use strict';

    var group = document.getElementById('themeSwitch');
    if (!group) return;

    var validThemes = ['ffxiv', 'nier', 'blue-pop'];
    var labels = { ffxiv: 'FFXIV 水晶', nier: 'YoRHa 档案', 'blue-pop': '蓝白潮流' };
    var theme = document.documentElement.dataset.theme;
    if (validThemes.indexOf(theme) === -1) theme = 'nier';

    function updateStylesheet(id, href, active) {
        var link = document.getElementById(id);
        if (!active) {
            if (link) link.remove();
            return;
        }
        if (!link) {
            link = document.createElement('link');
            link.id = id;
            link.rel = 'stylesheet';
            link.href = href;
            document.head.appendChild(link);
        }
    }

    function apply(nextTheme) {
        theme = validThemes.indexOf(nextTheme) !== -1 ? nextTheme : 'nier';
        document.documentElement.dataset.theme = theme;
        document.body.dataset.theme = theme;
        document.body.classList.toggle('nier-terminal', theme === 'nier');
        updateStylesheet('nierThemeStylesheet', group.dataset.nierHref, theme === 'nier');
        updateStylesheet('bluePopThemeStylesheet', group.dataset.bluePopHref, theme === 'blue-pop');
        try { localStorage.setItem('yukiko-visual-theme', theme); } catch (error) { /* Keep the choice for this page session. */ }
        group.querySelectorAll('[data-theme-choice]').forEach(function (choice) {
            var selected = choice.dataset.themeChoice === theme;
            choice.setAttribute('aria-pressed', String(selected));
            choice.classList.toggle('is-selected', selected);
            choice.title = selected ? labels[theme] + '（当前主题）' : '切换到 ' + labels[choice.dataset.themeChoice];
        });
    }

    group.addEventListener('click', function (event) {
        var choice = event.target.closest('[data-theme-choice]');
        if (choice && group.contains(choice)) apply(choice.dataset.themeChoice);
    });

    apply(theme);
}());
