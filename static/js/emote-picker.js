document.addEventListener('DOMContentLoaded', () => {
    const MAX_EMOTES = 10;
    const catalogNode = document.getElementById('emote-catalog');
    if (!catalogNode) return;
    const catalog = JSON.parse(catalogNode.textContent);

    const createOption = (id) => {
        const option = document.createElement('button');
        option.type = 'button';
        option.className = 'emote-option';
        option.dataset.emoteId = id;
        option.title = `情感动作 ${id}`;
        const image = document.createElement('img');
        image.src = `${catalog.base_url}${id}_hr1.png`;
        image.alt = '';
        image.loading = 'lazy';
        option.append(image);
        return option;
    };

    const populateGrid = (grid, ids) => {
        if (grid.dataset.populated) return;
        grid.append(...ids.map(createOption));
        grid.dataset.populated = 'true';
    };

    document.querySelectorAll('[data-emote-composer]').forEach((composer) => {
        const editor = composer.querySelector('.emote-editor');
        const hidden = composer.querySelector('[data-emote-value]');
        const error = composer.querySelector('.emote-error');
        const trigger = composer.querySelector('.emote-trigger');
        const picker = composer.querySelector('.emote-picker');
        const counter = composer.querySelector('.emote-count');
        const showAll = composer.querySelector('.emote-show-all');
        const allGrid = composer.querySelector('.emote-grid-all');
        let savedRange = null;
        hidden.disabled = false;

        const emoteCount = () => editor.querySelectorAll('.message-emote').length;

        const saveSelection = () => {
            const selection = window.getSelection();
            if (selection.rangeCount && editor.contains(selection.anchorNode)) {
                savedRange = selection.getRangeAt(0).cloneRange();
            }
        };

        const serialize = () => {
            const parts = [];
            const walk = (node) => {
                if (node.nodeType === Node.TEXT_NODE) {
                    parts.push(node.textContent);
                } else if (node.nodeType === Node.ELEMENT_NODE) {
                    if (node.matches('img[data-emote-id]')) {
                        parts.push(`[emote:${node.dataset.emoteId}]`);
                    } else {
                        if (node.tagName === 'BR') parts.push('\n');
                        node.childNodes.forEach(walk);
                        if (node.matches('div, p') && parts.at(-1) !== '\n') parts.push('\n');
                    }
                }
            };
            editor.childNodes.forEach(walk);
            hidden.value = parts.join('').replace(/\n{3,}/g, '\n\n').trim();
            if (hidden.value) {
                editor.classList.remove('is-invalid');
                editor.removeAttribute('aria-invalid');
                error.hidden = true;
            }
            const count = emoteCount();
            counter.textContent = `已用 ${count}/${MAX_EMOTES}`;
            composer.classList.toggle('emote-limit-reached', count >= MAX_EMOTES);
        };

        const insertEmote = (id, src) => {
            if (emoteCount() >= MAX_EMOTES) {
                counter.textContent = '最多使用 10 个动作';
                return;
            }
            editor.focus();
            const selection = window.getSelection();
            const range = savedRange && editor.contains(savedRange.commonAncestorContainer)
                ? savedRange
                : document.createRange();
            if (!savedRange || !editor.contains(savedRange.commonAncestorContainer)) {
                range.selectNodeContents(editor);
                range.collapse(false);
            }
            range.deleteContents();
            const image = document.createElement('img');
            image.className = 'message-emote';
            image.dataset.emoteId = id;
            image.src = src;
            image.alt = `情感动作 ${id}`;
            image.width = 32;
            image.height = 32;
            image.contentEditable = 'false';
            range.insertNode(image);
            range.setStartAfter(image);
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);
            savedRange = range.cloneRange();
            serialize();
        };

        editor.addEventListener('input', serialize);
        editor.addEventListener('keyup', saveSelection);
        editor.addEventListener('mouseup', saveSelection);
        editor.addEventListener('focus', saveSelection);
        editor.addEventListener('paste', (event) => {
            event.preventDefault();
            document.execCommand('insertText', false, event.clipboardData.getData('text/plain'));
        });

        trigger.addEventListener('click', () => {
            const opening = picker.hidden;
            if (opening) populateGrid(composer.querySelector('.emote-grid-common'), catalog.common);
            picker.hidden = !opening;
            trigger.setAttribute('aria-expanded', String(opening));
            if (opening) saveSelection();
        });

        picker.addEventListener('mousedown', (event) => {
            if (event.target.closest('.emote-option')) event.preventDefault();
        });
        picker.addEventListener('click', (event) => {
            const option = event.target.closest('.emote-option');
            if (!option) return;
            const image = option.querySelector('img');
            insertEmote(option.dataset.emoteId, image.src);
        });

        showAll.addEventListener('click', () => {
            const opening = allGrid.hidden;
            if (opening) populateGrid(allGrid, catalog.all);
            allGrid.hidden = !opening;
            showAll.setAttribute('aria-expanded', String(opening));
            showAll.querySelector('span').textContent = opening
                ? '收起全部动作'
                : `查看全部 ${allGrid.children.length} 个动作`;
        });

        composer.closest('form').addEventListener('submit', (event) => {
            serialize();
            if (!hidden.value) {
                event.preventDefault();
                editor.focus();
                editor.classList.add('is-invalid');
                editor.setAttribute('aria-invalid', 'true');
                error.hidden = false;
            }
        });
    });
});
