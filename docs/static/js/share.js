
// Data from window
const vtuber = window.vtuberData || {};
const videos = window.videosData || [];
const activities = window.activitiesData || [];
const records = window.recordsData || [];

// Active states
let currentTab = 'bio'; // 'bio' is default from HTML
let searchQuery = '';
let currentOtherVideoFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSearch();
    renderAll();
});

function initTabs() {
    window.switchTab = (tabId) => {
        // Update sidebar links
        document.querySelectorAll('.tab-item').forEach(link => {
            link.classList.remove('active');
        });
        const activeLink = document.getElementById(`tab-link-${tabId}`);
        if (activeLink) activeLink.classList.add('active');

        // Update panes
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        const activePane = document.getElementById(`pane-${tabId}`);
        if (activePane) activePane.classList.add('active');

        currentTab = tabId;
        
        // Auto-close sidebar on mobile if open
        const sidebar = document.getElementById('app-sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar && sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
            if (overlay) overlay.classList.remove('active');
        }

        renderCurrentTab(); // re-render or filter
    };
    
    // Toggle sidebar function
    window.toggleSidebar = () => {
        const sidebar = document.getElementById('app-sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar) sidebar.classList.toggle('show');
        if (overlay) overlay.classList.toggle('active');
    };

    // Toggle desktop collapse
    window.toggleDesktopSidebar = () => {
        const layout = document.querySelector('.app-layout');
        if (layout) layout.classList.toggle('collapsed');
    };
}

function initSearch() {
    const searchInput = document.getElementById('share-search-input');
    const clearBtn = document.getElementById('clear-search-btn');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.trim().toLowerCase();
            if (clearBtn) clearBtn.style.display = searchQuery ? 'block' : 'none';
            renderCurrentTab();
        });
    }

    window.clearSearchInput = () => {
        if (searchInput) {
            searchInput.value = '';
            searchQuery = '';
            if (clearBtn) clearBtn.style.display = 'none';
            renderCurrentTab();
        }
    };
}

// YT API
let ytPlayer = null;
window.onYouTubeIframeAPIReady = () => {
    // Player will be created dynamically when a video is played
};

let currentPlaying = { videoId: '', timestamp: 0 };
window.playSong = (videoId, timestamp = 0, title = '', singer = '') => {
    const container = document.getElementById('youtube-player');
    currentPlaying.videoId = videoId;
    currentPlaying.timestamp = timestamp;
    
    // Update player info bar
    document.getElementById('current-song-title').textContent = title || 'Unknown';
    document.getElementById('current-singer-name').innerHTML = `<i class="fa-solid fa-user"></i> ${singer || 'Unknown'}`;

    const onPlayerError = (event) => {
        const vid = currentPlaying.videoId;
        const ts = currentPlaying.timestamp;
        
        if (ytPlayer) {
            try { ytPlayer.destroy(); } catch(e) {}
            ytPlayer = null;
        }
        
        if (event.data === 101 || event.data === 150) {
            container.innerHTML = `
                <div style="background:#000; color:#fff; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding: 20px;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size:24px; color:#f87171; margin-bottom:10px;"></i>
                    <div style="font-size:14px; margin-bottom:12px;">上傳者已停用此影片的嵌入功能</div>
                    <a href="https://www.youtube.com/watch?v=${vid}&t=${ts}s" target="_blank" class="btn-outline btn-sm" style="color:var(--vtuber-active-theme); border-color:var(--vtuber-active-theme); font-weight:600; text-decoration:none;">
                        <i class="fa-brands fa-youtube"></i> 在 YouTube 上完整觀看
                    </a>
                </div>
            `;
        } else {
             container.innerHTML = `
                <div style="background:#000; color:#fff; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;">
                    <i class="fa-solid fa-circle-exclamation" style="font-size:24px; color:#f87171; margin-bottom:10px;"></i>
                    <div style="font-size:14px;">影片無法播放 (錯誤碼: ${event.data})</div>
                </div>
            `;
        }
    };

    if (!ytPlayer) {
        container.innerHTML = `<div id="yt-iframe-placeholder"></div>`;
        ytPlayer = new YT.Player('yt-iframe-placeholder', {
            height: '100%',
            width: '100%',
            videoId: videoId,
            playerVars: {
                'autoplay': 1,
                'start': timestamp
            },
            events: {
                'onReady': (event) => event.target.playVideo(),
                'onError': onPlayerError
            }
        });
    } else {
        try {
            // Remove previous error listener if possible? API doesn't support removeEventListener directly.
            // But since currentPlaying is updated globally, the old onError will read the new values if it triggers.
            ytPlayer.loadVideoById({ videoId: videoId, startSeconds: timestamp });
        } catch(e) {
            // Re-init if destroyed
            container.innerHTML = `<div id="yt-iframe-placeholder"></div>`;
            ytPlayer = new YT.Player('yt-iframe-placeholder', {
                height: '100%',
                width: '100%',
                videoId: videoId,
                playerVars: { 'autoplay': 1, 'start': timestamp },
                events: {
                    'onReady': (event) => event.target.playVideo(),
                    'onError': onPlayerError
                }
            });
        }
    }
};

window.toggleFloatingPlayerMinimize = () => {
    const wrapper = document.querySelector('.player-card-wrapper');
    if (wrapper) wrapper.classList.toggle('minimized');
};

function renderAll() {
    renderBio();
    // other tabs will render on demand or initial
    renderCurrentTab();
}

function renderCurrentTab() {
    switch(currentTab) {
        case 'bio': renderBio(); break;
        case 'requestable': renderRepertoire(); break;
        case 'singing': renderVideos('singing-grid', ['stream_singing']); break;
        case 'live': renderOtherVideosFiltered(); break;
        case 'history': renderHistory(); break;
        case 'mv': renderVideos('mv-grid', ['cover_mv', 'original_mv']); break;
    }
}

function renderBio() {
    // 1. Top Songs
    const topSongsList = document.getElementById('top-songs-list');
    if (topSongsList) {
        const songCounts = {};
        records.forEach(r => {
            if (!r.song) return;
            const key = r.song.title_main;
            songCounts[key] = (songCounts[key] || 0) + 1;
        });
        const sortedSongs = Object.entries(songCounts).sort((a,b) => b[1] - a[1]).slice(0, 5);
        topSongsList.innerHTML = sortedSongs.map(s => `
            <li style="display:flex; justify-content:space-between; font-size:13px;">
                <span>${s[0]}</span>
                <span style="color:var(--text-muted);">${s[1]} ${_('times')}</span>
            </li>
        `).join('');
    }

    // 1.5 Top Artists
    const topArtistsList = document.getElementById('top-artists-list');
    if (topArtistsList) {
        const artistCounts = {};
        records.forEach(r => {
            if (!r.song || !r.song.artists) return;
            r.song.artists.forEach(a => {
                const key = a.name_main;
                artistCounts[key] = (artistCounts[key] || 0) + 1;
            });
        });
        const sortedArtists = Object.entries(artistCounts).sort((a,b) => b[1] - a[1]).slice(0, 5);
        topArtistsList.innerHTML = sortedArtists.map(s => `
            <li style="display:flex; justify-content:space-between; font-size:13px;">
                <span>${s[0]}</span>
                <span style="color:var(--text-muted);">${s[1]} ${_('times')}</span>
            </li>
        `).join('') || `<li style="color:var(--text-muted); font-size:12px;">${_('No data')}</li>`;
    }

    // 2. Timeline
    const timelineContainer = document.getElementById('timeline-activities-container');
    if (timelineContainer) {
        const acts = activities.filter(a => !searchQuery || a.title.toLowerCase().includes(searchQuery));
        timelineContainer.innerHTML = acts.map(a => `
            <div style="margin-bottom:12px; border-left:2px solid var(--vtuber-active-theme); padding-left:12px; position:relative;">
                <div style="position:absolute; left:-6px; top:4px; width:10px; height:10px; border-radius:50%; background:var(--vtuber-active-theme);"></div>
                <div style="font-size:11px; color:var(--text-muted);">${a.event_date ? a.event_date.split('T')[0] : ''}</div>
                <div style="font-size:13px; font-weight:600;">${a.title}</div>
            </div>
        `).join('') || '<div style="color:var(--text-muted); font-size:12px;">無資料</div>';
    }
    
    // 3. Social Links
    const socialContainer = document.getElementById('social-links-container');
    if (socialContainer && vtuber.social_links) {
        try {
            const links = typeof vtuber.social_links === 'string' ? JSON.parse(vtuber.social_links) : vtuber.social_links;
            socialContainer.innerHTML = links.map(item => {
                const link = typeof item === 'string' ? item : (item && item.url ? item.url : '');
                if (!link) return '';
                
                let iconClass = 'fa-solid fa-link';
                const lowerLink = link.toLowerCase();
                if (lowerLink.includes('youtube.com')) iconClass = 'fa-brands fa-youtube';
                else if (lowerLink.includes('twitter.com') || lowerLink.includes('x.com')) iconClass = 'fa-brands fa-x-twitter';
                else if (lowerLink.includes('facebook.com')) iconClass = 'fa-brands fa-facebook';
                else if (lowerLink.includes('instagram.com')) iconClass = 'fa-brands fa-instagram';
                else if (lowerLink.includes('discord')) iconClass = 'fa-brands fa-discord';
                else if (lowerLink.includes('twitch.tv')) iconClass = 'fa-brands fa-twitch';
                
                return `<a href="${link}" target="_blank" class="social-icon" title="${link}"><i class="${iconClass}"></i></a>`;
            }).join('');
        } catch (e) {
            console.error("Failed to parse social links", e);
        }
    }
    
    // 4. Singing Calendar
    renderCalendar();
}

function renderCalendar() {
    const container = document.getElementById('singing-calendar-container');
    if (!container) return;
    
    // Group streams by date
    window.streamDatesGlobal = new Map();
    videos.filter(v => v.video_type === 'stream_singing' || v.video_type === 'stream_other' || v.video_type === 'schedule').forEach(v => {
        if (!v.published_at) return;
        const date = v.published_at.split('T')[0];
        if (!window.streamDatesGlobal.has(date)) window.streamDatesGlobal.set(date, []);
        window.streamDatesGlobal.get(date).push(v);
    });

    // Use current real-world month
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    
    const firstDay = new Date(year, month, 1).getDay(); // 0=Sun, 6=Sat
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    let html = `<div style="text-align:center; font-weight:bold; margin-bottom:12px;"><i class="fa-solid fa-calendar-days"></i> ${year} / ${month + 1} ${_('Live Streams')}</div>`;
    html += `<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:4px; text-align:center; font-size:12px;">`;
    
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(d => {
        html += `<div style="color:var(--text-muted); font-weight:bold;">${d}</div>`;
    });
    
    for (let i = 0; i < firstDay; i++) {
        html += `<div></div>`;
    }
    
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month+1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const streams = window.streamDatesGlobal.get(dateStr);
        const hasStream = streams && streams.length > 0;
        
        let style = `padding:6px; border-radius:4px; border:1px solid var(--border-color); display:flex; align-items:center; justify-content:center;`;
        let titleAttr = '';
        let clickAttr = '';
        if (hasStream) {
            style = `padding:6px; border-radius:4px; background:var(--vtuber-active-theme); color:#fff; cursor:pointer; font-weight:bold; display:flex; align-items:center; justify-content:center;`;
            const titles = streams.map(v => v.title).join('&#10;');
            titleAttr = `title="${titles}"`;
            clickAttr = `onclick="showCalendarVideos('${dateStr}')"`;
        }
        
        html += `<div style="${style}" ${titleAttr} ${clickAttr}>${d}</div>`;
    }
    html += `</div>`;
    container.innerHTML = html;
}

window.showCalendarVideos = (dateStr) => {
    const streams = window.streamDatesGlobal.get(dateStr);
    if (!streams || streams.length === 0) return;
    
    if (streams.length === 1) {
        // Just play it directly if there's only 1
        const v = streams[0];
        const safeTitle = v.title.replace(/'/g, "\\'");
        const safeSinger = (vtuber.name_main || '').replace(/'/g, "\\'");
        playSong(v.video_id, 0, safeTitle, safeSinger);
        return;
    }
    
    // Multiple videos: show modal
    const modal = document.getElementById('calendar-videos-modal');
    document.getElementById('calendar-modal-title').textContent = `${dateStr} ${_('Live Streams')}`;
    const list = document.getElementById('calendar-modal-list');
    
    list.innerHTML = streams.map(v => {
        const safeTitle = v.title.replace(/'/g, "\\'");
        const safeSinger = (vtuber.name_main || '').replace(/'/g, "\\'");
        return `
            <div class="history-item" style="cursor:pointer; border-radius:8px; margin-bottom:8px; background:var(--bg-color); border:1px solid var(--border-color);" onclick="playSong('${v.video_id}', 0, '${safeTitle}', '${safeSinger}'); document.getElementById('calendar-videos-modal').style.display='none';">
                <div style="flex:1; min-width:0;">
                    <div style="font-size:14px; font-weight:600; color:var(--text-bright);">${v.title}</div>
                    <div style="font-size:12px; color:var(--text-muted);"><i class="fa-brands fa-youtube"></i> YouTube</div>
                </div>
                <div style="color:var(--vtuber-active-theme);"><i class="fa-solid fa-play"></i></div>
            </div>
        `;
    }).join('');
    
    modal.style.display = 'flex';
};

function renderRepertoire() {
    const grid = document.getElementById('repertoire-list');
    if (!grid) return;

    // Extract distinct songs
    const uniqueSongs = new Map();
    records.forEach(r => {
        if (!r.song) return;
        if (!uniqueSongs.has(r.song.id)) {
            uniqueSongs.set(r.song.id, r.song);
        }
    });

    let songs = Array.from(uniqueSongs.values());
    if (searchQuery) {
        songs = songs.filter(s => 
            (s.title_main && s.title_main.toLowerCase().includes(searchQuery)) ||
            (s.artists && s.artists.some(a => a.name_main.toLowerCase().includes(searchQuery)))
        );
    }

    grid.innerHTML = songs.map((song, idx) => {
        const artists = song.artists && song.artists.length > 0 
            ? song.artists.map(a => a.name_main).join(', ') 
            : _('Unknown');
        const songRecord = records.find(r => r.song && r.song.id === song.id);
        const videoId = songRecord && songRecord.video_id ? songRecord.video_id : '';
        const timestamp = songRecord ? songRecord.timestamp_seconds : 0;
        
        return `
            <div class="track-item" onclick="playSong('${videoId}', ${timestamp}, '${song.title_main.replace(/'/g, "\\'")}', '${artists.replace(/'/g, "\\'")}')">
                <div class="track-index-wrapper">
                    <span class="track-index">${idx + 1}</span>
                    <span class="track-play-btn"><i class="fa-solid fa-play"></i></span>
                </div>
                <div class="track-info">
                    <div style="font-size:15px; font-weight:500; color:var(--text-bright);">${song.title_main}</div>
                    <div style="font-size:13px; color:var(--text-muted);">${artists}</div>
                </div>
                <div style="text-align:right;">
                    <span class="badge" style="background:rgba(255,255,255,0.1); font-size:11px;">${song.song_type || 'cover'}</span>
                </div>
            </div>
        `;
    }).join('') || `<div style="text-align:center; padding:40px; color:var(--text-muted);"><i class="fa-solid fa-music fa-3x" style="margin-bottom:16px; opacity:0.5;"></i><br>${_('No related songs yet!')}</div>`;
}

function renderVideos(gridId, types) {
    const grid = document.getElementById(gridId);
    if (!grid) return;

    let vids = videos.filter(v => Array.isArray(types) ? types.includes(v.video_type) : v.video_type === types);
    if (searchQuery) {
        vids = vids.filter(v => v.title.toLowerCase().includes(searchQuery));
    }

    grid.innerHTML = vids.map(v => {
        const dateStr = v.published_at ? v.published_at.split('T')[0] : '';
        const thumb = v.thumbnail_url || `https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg`;
        return `
            <div class="card album-card" style="cursor:pointer; overflow:hidden; border-radius:12px; padding: 12px;" onclick="playSong('${v.video_id}', 0, '${v.title.replace(/'/g, "\\'")}', '${(vtuber.name_main || '').replace(/'/g, "\\'")}')">
                <div class="album-img-wrapper">
                    <img src="${thumb}" style="width:100%; aspect-ratio:16/9; object-fit:cover; display:block; border-radius: 8px;">
                    <div class="album-play-btn"><i class="fa-solid fa-play"></i></div>
                </div>
                <div>
                    <h4 style="margin:0 0 4px; font-size:14px; font-weight:600; color:var(--text-bright); display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">${v.title}</h4>
                    <div style="font-size: 12px; color: var(--text-muted);">${dateStr}</div>
                </div>
            </div>
        `;
    }).join('') || `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-muted);"><i class="fa-solid fa-video-slash fa-3x" style="margin-bottom:16px; opacity:0.5;"></i><br>${_('No videos here yet!')}</div>`;
}

function renderHistory() {
    const list = document.getElementById('history-list');
    if (!list) return;

    let recs = records;
    if (searchQuery) {
        recs = recs.filter(r => 
            (r.song && r.song.title_main.toLowerCase().includes(searchQuery)) ||
            (r.video && r.video.title.toLowerCase().includes(searchQuery))
        );
    }

    list.innerHTML = recs.map((r, idx) => {
        const songTitle = r.song ? r.song.title_main : 'Unknown Song';
        const artists = r.song && r.song.artists && r.song.artists.length > 0 ? r.song.artists.map(a => a.name_main).join(', ') : 'Unknown Artist';
        const videoTitle = r.video ? r.video.title : 'Unknown Video';
        const dateStr = r.video && r.video.published_at ? r.video.published_at.split('T')[0] : '';
        
        return `
            <div class="track-item" onclick="playSong('${r.video_id}', ${r.timestamp_seconds}, '${songTitle.replace(/'/g, "\\'")}', '${artists.replace(/'/g, "\\'")}')">
                <div class="track-index-wrapper">
                    <span class="track-index">${idx + 1}</span>
                    <span class="track-play-btn"><i class="fa-solid fa-play"></i></span>
                </div>
                <div class="track-info">
                    <div style="font-size:15px; font-weight:500; color:var(--text-bright); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${songTitle}</div>
                    <div style="font-size:13px; color:var(--text-muted); display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                        <span>${artists}</span>
                        <span>•</span>
                        <span style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px;">${videoTitle}</span>
                        <span>•</span>
                        <span>${dateStr}</span>
                    </div>
                </div>
                <div style="color: var(--text-muted); font-variant-numeric: tabular-nums;">
                    ${formatSeconds(r.timestamp_seconds)}
                </div>
            </div>
        `;
    }).join('') || '<div style="text-align:center; padding:40px; color:var(--text-muted);"><i class="fa-solid fa-clock-rotate-left fa-3x" style="margin-bottom:16px; opacity:0.5;"></i><br>還沒有任何歷史歌回紀錄呢！</div>';
}

// UI Helpers (Lightbox, Export)
window.openLightbox = (url, caption) => {
    const modal = document.getElementById('image-lightbox-modal');
    const img = document.getElementById('lightbox-img');
    const cap = document.getElementById('lightbox-caption');
    if (modal && img) {
        img.src = url;
        img.style.transform = 'scale(1)';
        if (cap) cap.textContent = caption || '';
        modal.classList.add('active');
    }
};

window.closeLightbox = () => {
    const modal = document.getElementById('image-lightbox-modal');
    if (modal) modal.classList.remove('active');
};

window.toggleLightboxZoom = (event) => {
    const img = event.target;
    if (img.style.transform === 'scale(1)') {
        img.style.transform = 'scale(1.5)';
        img.style.cursor = 'zoom-out';
    } else {
        img.style.transform = 'scale(1)';
        img.style.cursor = 'zoom-in';
    }
};

window.exportToExcel = () => {
    showToast('匯出功能即將推出', 'warning');
};

window.filterOtherVideos = (filterType, btn) => {
    const bar = btn.parentElement;
    bar.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    currentOtherVideoFilter = filterType;
    renderOtherVideosFiltered();
};

function renderOtherVideosFiltered() {
    const grid = document.getElementById('live-grid');
    if (!grid) return;

    let vids = videos.filter(v => ['stream_other', 'other', 'short', 'shorts'].includes(v.video_type));
    
    if (searchQuery) {
        vids = vids.filter(v => v.title.toLowerCase().includes(searchQuery));
    }

    if (currentOtherVideoFilter === 'talk') {
        vids = vids.filter(v => !isCollabTitle(v.title));
    } else if (currentOtherVideoFilter === 'collab') {
        vids = vids.filter(v => isCollabTitle(v.title));
    } else if (currentOtherVideoFilter === 'shorts') {
        vids = vids.filter(v => v.title.toLowerCase().includes('shorts') || v.video_type === 'short' || v.video_type === 'shorts');
    }

    grid.innerHTML = vids.map(v => {
        const dateStr = v.published_at ? v.published_at.split('T')[0] : '';
        const thumb = v.thumbnail_url || `https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg`;
        return `
            <div class="card album-card" style="cursor:pointer; overflow:hidden; border-radius:12px; padding: 12px;" onclick="playSong('${v.video_id}', 0, '${v.title.replace(/'/g, "\\'")}', '${(vtuber.name_main || '').replace(/'/g, "\\'")}')">
                <div class="album-img-wrapper">
                    <img src="${thumb}" style="width:100%; aspect-ratio:16/9; object-fit:cover; display:block; border-radius: 8px;">
                    <div class="album-play-btn"><i class="fa-solid fa-play"></i></div>
                </div>
                <div>
                    <h4 style="margin:0 0 4px; font-size:14px; font-weight:600; color:var(--text-bright); display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">${v.title}</h4>
                    <div style="font-size: 12px; color: var(--text-muted);">${dateStr}</div>
                </div>
            </div>
        `;
    }).join('') || `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-muted);"><i class="fa-solid fa-video-slash fa-3x" style="margin-bottom:16px; opacity:0.5;"></i><br>${_('No videos here yet!')}</div>`;
}

function isCollabTitle(title) {
    const t = title.toLowerCase();
    return t.includes('連動') || t.includes('合作') || t.includes('collab') || t.includes('連同') || t.includes('w/') || t.includes('feat') || t.includes('ft.');
}
