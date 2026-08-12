/**
 * FF14 个人主页 — 音乐播放器
 * 支持播放列表、进度控制、音量调节
 * 线性设计风格
 */

class MusicPlayer {
    constructor(options = {}) {
        this.sources = options.sources || [];
        this.defaultSource = options.defaultSource || "local";
        this.currentSource = this.defaultSource;
        this.playlist = options.playlist || [];
        this.currentIndex = 0;
        this.isPlaying = false;
        this.isOpen = false;
        this.showPlaylist = false;
        this.volume = parseFloat(localStorage.getItem("ffxiv_player_volume")) || 0.6;

        // DOM 元素
        this.toggleBtn = document.getElementById("musicToggle");
        this.playerEl = document.getElementById("musicPlayer");
        this.audio = document.getElementById("musicAudio");
        this.coverEl = document.getElementById("playerCover");
        this.titleEl = document.getElementById("playerTitle");
        this.artistEl = document.getElementById("playerArtist");
        this.playBtn = document.getElementById("playerPlayBtn");
        this.playIcon = document.getElementById("playerPlayIcon");
        this.prevBtn = document.getElementById("playerPrev");
        this.nextBtn = document.getElementById("playerNext");
        this.progressBar = document.getElementById("progressBar");
        this.progressFill = document.getElementById("progressFill");
        this.currentTimeEl = document.getElementById("currentTime");
        this.durationEl = document.getElementById("totalTime");
        this.volumeBar = document.getElementById("volumeBar");
        this.volumeFill = document.getElementById("volumeFill");
        this.volumeIcon = document.getElementById("volumeIcon");
        this.playlistEl = document.getElementById("playerPlaylistBody");
        this.playlistToggle = document.getElementById("playlistToggleBtn");
        this.playlistSection = document.getElementById("playerPlaylistSection");
        this.playlistFooter = document.getElementById("playlistFooter");

        this.init();
    }

    cleanText(value, fallback = "") {
        const text = value === null || value === undefined || value === ""
            ? fallback
            : String(value);

        return text
            .replace(/\\r\\n|\\n|\\r/gi, " ")
            .replace(/[\r\n]+/g, " ")
            .replace(/\s{2,}/g, " ")
            .trim();
    }

    init() {
        // 设置初始音量
        this.audio.volume = this.volume;
        this.volumeFill.style.width = (this.volume * 100) + "%";
        this.updateVolumeIcon();

        // 渲染来源标签
        this.renderSourceTabs();
        // 加载播放列表
        this.renderPlaylist();

        // 事件绑定
        this.toggleBtn.addEventListener("click", () => this.togglePlayer());
        this.playBtn.addEventListener("click", () => this.togglePlay());
        this.prevBtn.addEventListener("click", () => this.prev());
        this.nextBtn.addEventListener("click", () => this.next());

        // 进度条
        this.progressBar.addEventListener("click", (e) => this.seek(e));
        this.audio.addEventListener("timeupdate", () => this.updateProgress());
        this.audio.addEventListener("loadedmetadata", () => this.updateDuration());
        this.audio.addEventListener("ended", () => this.next());

        // 音量
        this.volumeBar.addEventListener("click", (e) => this.setVolume(e));

        // 播放列表切换
        this.playlistToggle.addEventListener("click", () => this.togglePlaylist());

        // 键盘快捷键
        document.addEventListener("keydown", (e) => {
            if (e.code === "Space" && this.isOpen) {
                e.preventDefault();
                this.togglePlay();
            }
        });

        // 加载第一首
        this.loadTrack(0);

        // 页面关闭/跳转时保存播放状态
        var self = this;
        window.addEventListener("beforeunload", function() {
            if (self.playlist.length > 0) {
                localStorage.setItem("ffxiv_player_state", JSON.stringify({
                    trackIndex: self.currentIndex,
                    currentTime: self.audio.currentTime,
                    volume: self.volume
                }));
            }
        });

        // 从本地存储恢复状态
        const savedIndex = localStorage.getItem("ffxiv_player_index");
        if (savedIndex !== null) {
            this.loadTrack(parseInt(savedIndex));
        }
    }

    loadTrack(index) {
        if (index < 0 || index >= this.playlist.length) return;
        this.currentIndex = index;
        const track = this.playlist[index];
        this.audio.src = track.file;
        this.titleEl.textContent = this.cleanText(track.title);
        this.artistEl.textContent = this.cleanText(track.artist, "Unknown");
        const cleanTitle = this.cleanText(track.title, "Music");
        this.coverEl.innerHTML = track.cover
            ? `<img src="${track.cover}" alt="${cleanTitle}">`
            : `<i class="fa-solid fa-music"></i>`;
        this.updatePlaylistActive();
        localStorage.setItem("ffxiv_player_index", index);
    }

    play() {
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.playIcon.className = "fa-solid fa-pause";
            this.toggleBtn.classList.add("playing");
        }).catch(() => {});
    }

    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.playIcon.className = "fa-solid fa-play";
        this.toggleBtn.classList.remove("playing");
    }

    togglePlay() {
        if (this.isPlaying) this.pause();
        else this.play();
    }

    prev() {
        const idx = this.currentIndex > 0 ? this.currentIndex - 1 : this.playlist.length - 1;
        this.loadTrack(idx);
        if (this.isPlaying) this.play();
    }

    next() {
        const idx = this.currentIndex < this.playlist.length - 1 ? this.currentIndex + 1 : 0;
        this.loadTrack(idx);
        if (this.isPlaying) this.play();
    }

    seek(e) {
        const rect = this.progressBar.getBoundingClientRect();
        const ratio = (e.clientX - rect.left) / rect.width;
        this.audio.currentTime = ratio * this.audio.duration;
    }

    setVolume(e) {
        const rect = this.volumeBar.getBoundingClientRect();
        this.volume = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        this.audio.volume = this.volume;
        this.volumeFill.style.width = (this.volume * 100) + "%";
        this.updateVolumeIcon();
        localStorage.setItem("ffxiv_player_volume", this.volume);
    }

    updateVolumeIcon() {
        if (this.volume === 0) this.volumeIcon.className = "fa-solid fa-volume-xmark";
        else if (this.volume < 0.3) this.volumeIcon.className = "fa-solid fa-volume-off";
        else if (this.volume < 0.7) this.volumeIcon.className = "fa-solid fa-volume-low";
        else this.volumeIcon.className = "fa-solid fa-volume-high";
    }

    updateProgress() {
        if (!this.audio.duration) return;
        const pct = (this.audio.currentTime / this.audio.duration) * 100;
        this.progressFill.style.width = pct + "%";
        this.currentTimeEl.textContent = this.cleanText(this.formatTime(this.audio.currentTime));
    }

    updateDuration() {
        this.durationEl.textContent = this.cleanText(this.formatTime(this.audio.duration));
    }

    formatTime(t) {
        const m = Math.floor(t / 60);
        const s = Math.floor(t % 60);
        return m + ":" + (s < 10 ? "0" : "") + s;
    }

    // 自动播放（支持浏览器 autoplay policy + 嵌入播放器）
    autoPlay() {
        var self = this;

        // 尝试自动播放
        function doPlay() {
            if (self.currentSource === "local" && self.playlist.length > 0) {
                // 恢复上次播放位置
                try {
                    var saved = localStorage.getItem("ffxiv_player_state");
                    if (saved) {
                        var state = JSON.parse(saved);
                        if (state.trackIndex !== undefined && state.trackIndex < self.playlist.length) {
                            self.loadTrack(state.trackIndex);
                            self.audio.currentTime = state.currentTime || 0;
                        }
                        if (state.volume !== undefined) {
                            self.volume = state.volume;
                            self.audio.volume = self.volume;
                            self.volumeFill.style.width = (self.volume * 100) + "%";
                            self.updateVolumeIcon();
                        }
                    }
                } catch (e) {}

                var playPromise = self.audio.play();
                if (playPromise !== undefined) {
                    playPromise.then(function() {
                        self.isPlaying = true;
                        self.playIcon.className = "fa-solid fa-pause";
                        self.toggleBtn.classList.add("playing");
                    }).catch(function() {
                        // 浏览器阻止，等用户点击
                        self.waitForClickPlay(doPlay);
                    });
                }
            } else if (self.currentSource !== "local") {
                // 嵌入播放器：重新调用 switchSource 触发 iframe auto=1
                self.switchSource(self.currentSource, false);
            }
        }

        doPlay();
    }

    // 用户点击页面任意位置时触发播放
    waitForClickPlay(playFn) {
        var self = this;
        function onClick() {
            document.removeEventListener("click", onClick);
            if (self.currentSource === "local") {
                self.audio.play().then(function() {
                    self.isPlaying = true;
                    self.playIcon.className = "fa-solid fa-pause";
                    self.toggleBtn.classList.add("playing");
                }).catch(function() {});
            } else {
                // 嵌入播放器
                self.switchSource(self.currentSource, false);
            }
        }
        document.addEventListener("click", onClick, { once: true });
    }

    togglePlayer() {
        this.isOpen = !this.isOpen;
        this.playerEl.classList.toggle("open", this.isOpen);
        if (this.isOpen) this.loadTrack(this.currentIndex);
    }

    togglePlaylist() {
        this.showPlaylist = !this.showPlaylist;
        this.playlistSection.classList.toggle("open", this.showPlaylist);
        this.playlistFooter.classList.toggle("show", this.showPlaylist);
    }

    renderSourceTabs() {
        const tabsEl = document.getElementById("playerSourceTabs");
        if (!tabsEl || !this.sources.length) return;
        tabsEl.innerHTML = "";
        this.sources.forEach((src, i) => {
            const btn = document.createElement("button");
            btn.className = "source-tab" + (src.id === this.currentSource ? " active" : "");
            btn.innerHTML = `<i class="${src.icon}"></i>${this.cleanText(src.name)}`;
            btn.dataset.source = src.id;
            btn.addEventListener("click", () => this.switchSource(src.id));
            tabsEl.appendChild(btn);
        });
        this.switchSource(this.currentSource, true);
    }

    switchSource(sourceId, silent = false) {
        this.currentSource = sourceId;
        // Update tab active states
        document.querySelectorAll(".source-tab").forEach(t => {
            t.classList.toggle("active", t.dataset.source === sourceId);
        });
        // Hide all content panels
        document.querySelectorAll(".player-local-content, .player-embed").forEach(el => {
            el.classList.remove("active");
        });
        const src = this.sources.find(s => s.id === sourceId);
        if (!src) return;
        if (sourceId === "local") {
            // Show local player controls
            document.querySelector(".player-local-content").classList.add("active");
        } else if (src.embedType && src.embedId) {
            // Show embedded player
            const embedId = sourceId === "netease" ? "playerEmbedNetease" : "playerEmbedQQ";
            const embed = document.getElementById(embedId);
            if (embed) {
                embed.classList.add("active");
                if (!silent) {
                    // Build and set iframe
                    let iframe = embed.querySelector("iframe");
                    if (!iframe) {
                        iframe = document.createElement("iframe");
                        embed.appendChild(iframe);
                    }
                    const auto = src.autoPlay ? 1 : 0;
                    let url = "";
                    if (sourceId === "netease") {
                        const type = src.embedType === "playlist" ? "0" : "2";
                        url = "//music.163.com/outchain/player?type=" + type + "&id=" + src.embedId + "&auto=" + auto + "&height=66";
                    } else if (sourceId === "qqmusic") {
                        if (src.embedType === "playlist") {
                            url = "https://i.y.qq.com/n2/m/outchain/player?type=0&id=" + src.embedId + "&auto=" + auto;
                        } else {
                            url = "https://i.y.qq.com/n2/m/outchain/player?songid=" + src.embedId + "&auto=" + auto + "&height=66";
                        }
                    }
                    iframe.src = url;
                }
            }
        }
    }

    renderPlaylist() {
        this.playlistEl.innerHTML = "";
        this.playlist.forEach((track, i) => {
            const item = document.createElement("div");
            item.className = "playlist-item" + (i === this.currentIndex ? " active" : "");
            item.dataset.index = i;
            item.innerHTML = `
                <span class="playlist-item-num">${i + 1}</span>
                <span class="playlist-track-title">${this.cleanText(track.title)}</span>
                <span class="playlist-track-duration">${this.cleanText(track.duration, "--:--")}</span>
            `;
            item.addEventListener("click", () => {
                this.loadTrack(i);
                if (this.isPlaying) this.play();
                else this.play();
            });
            this.playlistEl.appendChild(item);
        });
    }

    updatePlaylistActive() {
        this.playlistEl.querySelectorAll(".playlist-item").forEach((item, i) => {
            item.classList.toggle("active", i === this.currentIndex);
        });
    }
}


// ===== 自动初始化（页面加载时启动，尝试自动播放） =====
async function initPlayer() {
    try {
        const resp = await fetch("/api/music/config");
        const config = await resp.json();
        if (config && config.sources && config.sources.length > 0) {
            const local = config.sources.find(s => s.id === "local");
            const pOpts = {
                playlist: (local && local.playlist) || [],
                sources: config.sources,
                defaultSource: config.defaultSource || "local"
            };
            const player = new MusicPlayer(pOpts);
            window.ffxivPlayer = player;
            // 尝试自动播放
            setTimeout(function() { player.autoPlay(); }, 500);
        }
    } catch (e) {
        console.log("Music player: config not available");
    }
}

if (document.readyState === "complete" || document.readyState === "interactive") {
    initPlayer();
} else {
    document.addEventListener("DOMContentLoaded", initPlayer);
}
