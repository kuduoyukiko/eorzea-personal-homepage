/**
 * FF14 个人主页 — 交互脚本
 */

document.addEventListener('DOMContentLoaded', function () {

    // 首页旅程序章：离开序章后移出滚动路径，仅通过重温按钮重新观看。
    const journeyIntro = document.getElementById('journeyIntro');
    const journeyVideo = document.getElementById('journeyIntroVideo');
    const journeyEnter = document.getElementById('journeyEnter');
    const journeyReplay = document.getElementById('journeyReplay');

    if (journeyIntro) {
        const root = document.documentElement;
        const loadJourneyVideo = function () {
            if (!journeyVideo || journeyVideo.dataset.loaded === 'true') return;
            journeyVideo.querySelectorAll('source[data-src]').forEach(function (source) {
                source.src = source.dataset.src;
            });
            journeyVideo.dataset.loaded = 'true';
            journeyVideo.load();
        };
        const dismissIntro = function () {
            if (root.classList.contains('journey-dismissed')) return;
            root.classList.add('journey-entered', 'journey-dismissed');
            if (journeyVideo) journeyVideo.pause();
            try {
                localStorage.setItem('yukiko-chronicle-intro-seen', '1');
            } catch (error) {
                // 无本地存储权限时仍允许正常浏览。
            }
            requestAnimationFrame(function () {
                window.scrollTo({ top: 0, behavior: 'auto' });
            });
        };

        if (journeyVideo) {
            journeyVideo.addEventListener('error', dismissIntro);
        }

        if (root.classList.contains('journey-returning')) {
            root.classList.add('journey-entered');
            if (journeyVideo) journeyVideo.pause();
        } else if (journeyVideo) {
            loadJourneyVideo();
            journeyVideo.play().catch(function () {
                journeyIntro.classList.add('video-paused');
            });
        }

        if (journeyEnter) {
            journeyEnter.addEventListener('click', function (event) {
                event.preventDefault();
                dismissIntro();
            });
        }

        window.addEventListener('scroll', function () {
            if (window.scrollY >= Math.max(80, window.innerHeight * 0.45)) {
                dismissIntro();
            }
        }, { passive: true });

        if (journeyReplay) {
            journeyReplay.addEventListener('click', function () {
                root.classList.remove('journey-returning', 'journey-entered', 'journey-dismissed');
                root.classList.add('journey-first');
                window.scrollTo({ top: 0, behavior: 'smooth' });
                if (journeyVideo) {
                    loadJourneyVideo();
                    journeyVideo.currentTime = 0;
                    journeyVideo.play().catch(function () {});
                }
            });
        }
    }

    // ========================================
    // 1. 画廊灯箱
    // ========================================
    const lightboxHTML = `
    <div class="lightbox" id="galleryLightbox">
        <span class="lb-close" id="lbClose">&times;</span>
        <img id="lbImage" src="" alt="预览">
    </div>`;

    // 只插入一次
    if (!document.getElementById('galleryLightbox')) {
        document.body.insertAdjacentHTML('beforeend', lightboxHTML);
    }

    const lightbox = document.getElementById('galleryLightbox');
    const lbImage = document.getElementById('lbImage');
    const lbClose = document.getElementById('lbClose');

    // 点击画廊原图链接 → 在灯箱中打开
    document.querySelectorAll('.gallery-item a[href], .gallery-feature a[href]').forEach(function (link) {
        link.addEventListener('click', function (e) {
            // 只对图片使用灯箱
            const href = this.getAttribute('href');
            if (/\.(png|jpg|jpeg|gif|webp|bmp)(\?|#|$)/i.test(href)) {
                e.preventDefault();
                lbImage.setAttribute('src', href);
                lightbox.classList.add('show');
                document.body.style.overflow = 'hidden';
            }
            // 视频保持原样（新标签页打开）
        });
    });

    // 关闭灯箱
    function closeLightbox() {
        lightbox.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (lbClose) lbClose.addEventListener('click', closeLightbox);
    if (lightbox) lightbox.addEventListener('click', function (e) {
        if (e.target === this) closeLightbox();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeLightbox();
    });

    // ========================================
    // 2. 画廊分类切换
    // ========================================
    document.querySelectorAll('.gallery-tab').forEach(function (tab) {
        tab.addEventListener('click', function () {
            // 切换 active 状态
            document.querySelectorAll('.gallery-tab').forEach(function (t) {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');

            const target = this.getAttribute('data-target');
            const galleryGrid = document.getElementById('galleryGrid');
            if (galleryGrid) galleryGrid.dataset.view = target;
            const feature = document.getElementById('galleryFeature');
            if (feature) {
                feature.style.display = target === 'all' ? '' : 'none';
            }
            document.querySelectorAll('.gallery-group').forEach(function (group) {
                group.hidden = target !== 'all' && group.id !== target;
            });
        });
    });

    // ========================================
    // 3. 页面滚动淡入动画
    // ========================================
    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll').forEach(function (el) {
        observer.observe(el);
    });

    // ========================================
    // 4. 导航栏滚动效果
    // ========================================
    const navbar = document.querySelector('.navbar-ff14');
    if (navbar) {
        const updateNavbar = function () {
            navbar.classList.toggle('scrolled', window.scrollY > 50);
        };
        updateNavbar();
        window.addEventListener('scroll', updateNavbar, { passive: true });
    }

    // ========================================
    // 5. 给当前页面的导航项加 active 类
    // ========================================
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-ff14 .nav-link').forEach(function (link) {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });

});
