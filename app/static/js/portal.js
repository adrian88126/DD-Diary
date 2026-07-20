// 前台訪客視圖與渲染模組
import { API_BASE } from './config.js';
import { state } from './state.js';
import { showToast, formatSeconds, playRecord } from './ui.js';

export function switchView(viewName, title = '') {
    document.querySelectorAll('.content-view').forEach(el => el.classList.remove('active'));
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) targetView.classList.add('active');
    
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('data-view') === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) {
        if (title) {
            pageTitle.textContent = title;
        } else {
            const viewTitles = {
                'dashboard': '儀表板大廳',
                'catalog': '資料總庫目錄',
                'admin': '後台管理中心'
            };
            pageTitle.textContent = viewTitles[viewName] || '資料庫系統';
        }
    }
}

export async function loadSidebarVtubers() {
    try {
        const response = await fetch(`${API_BASE}/vtubers/`);
        const vtubers = await response.json();
        state.cacheVtubers = vtubers; 
        
        const listContainer = document.getElementById('sidebar-vtuber-list');
        listContainer.innerHTML = '';
        
        if (vtubers.length === 0) {
            listContainer.innerHTML = '<p class="sub-text" style="padding-left:10px;">尚無主播資料</p>';
            return;
        }
        
        vtubers.forEach(vt => {
            const item = document.createElement('div');
            item.className = 'vtuber-item';
            item.setAttribute('data-id', vt.id);
            
            if (vt.theme_color) {
                item.style.borderLeft = `3px solid ${vt.theme_color}`;
            }
            
            const avatarHtml = vt.avatar_url 
                ? `<img src="${vt.avatar_url}" style="width:20px; height:20px; border-radius:50%; object-fit:cover; margin-right:8px; flex-shrink:0;">`
                : `<div class="vtuber-avatar-mini" style="margin-right:8px; flex-shrink:0;">${vt.name_main.charAt(0)}</div>`;
                
            item.innerHTML = `
                ${avatarHtml}
                <div class="vtuber-name-mini" style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${vt.name_main}</div>
            `;
            
            item.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.vtuber-item').forEach(el => el.classList.remove('active'));
                
                item.classList.add('active');
                loadVtuberProfile(vt.id);
            });
            
            listContainer.appendChild(item);
        });
    } catch (error) {
        console.error('載入 VTuber 列表失敗:', error);
    }
}

export async function loadDashboardData() {
    try {
        const vtubers = state.cacheVtubers;
        const songs = state.cacheSongs;
        const records = state.cacheRecords;
        const videos = state.cacheVideos;
        
        document.getElementById('stat-vtubers').textContent = vtubers.length;
        document.getElementById('stat-songs').textContent = songs.length;
        document.getElementById('stat-records').textContent = records.length;
        document.getElementById('stat-videos').textContent = videos.length;
        
        const sortedVideos = [...videos].sort((a, b) => {
            const dateA = a.published_at || '';
            const dateB = b.published_at || '';
            return dateB.localeCompare(dateA);
        });
        renderRecentVideos(sortedVideos.slice(0, 10));
        loadActivitiesTimeline();
        
    } catch (error) {
        console.error('載入儀表板統計失敗:', error);
    }
}

function renderRecentVideos(videos) {
    const container = document.getElementById('dashboard-recent-records');
    container.innerHTML = '';
    
    if (videos.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color:#64748b;">
                <i class="fa-solid fa-video-slash" style="font-size: 30px; margin-bottom:10px;"></i>
                <p>目前尚無 YouTube 直播或影音存檔，請前往後台或主播頁同步！</p>
            </div>
        `;
        return;
    }
    
    videos.forEach(v => {
        const card = document.createElement('div');
        card.className = 'record-card';
        card.style.cssText = 'display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 12px; margin-bottom: 12px; border-radius: 12px;';
        
        const thumbnail = v.thumbnail_url || `https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg`;
        const pubDate = v.published_at || '無發布日期';
        
        const ownerVt = state.cacheVtubers.find(vt => vt.id == v.vtuber_id);
        const ownerName = ownerVt ? ownerVt.name_main : '未知主播';
        
        const timelineBadge = v.has_timeline 
            ? '<span class="badge" style="background:rgba(57, 255, 20, 0.08); border:1px solid rgba(57,255,20,0.2); color:var(--neon-green); font-size:10px;">已建立時間軸</span>' 
            : '<span class="badge" style="background:rgba(255, 0, 127, 0.08); border:1px solid rgba(255,0,127,0.2); color:var(--neon-pink); font-size:10px;">尚未建立時間軸</span>';
            
        card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0;">
                <div class="record-thumb-container" style="width: 100px; height: 56px; margin: 0; flex-shrink: 0;" onclick="window.playRecord('${v.video_id}', 0, '${v.title.replace(/'/g, "\\'")}', '${ownerName}', '${v.title.replace(/'/g, "\\'")}')">
                    <img src="${thumbnail}" alt="Video thumbnail">
                    <div class="record-play-overlay"><i class="fa-solid fa-play"></i></div>
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 700; color: var(--text-bright); font-size: 13.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px;" title="${v.title}">
                        ${v.title}
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 11px; color: #94a3b8; flex-wrap: wrap;">
                        <span><i class="fa-solid fa-user" style="color: var(--neon-purple);"></i> ${ownerName}</span>
                        <span>•</span>
                        <span><i class="fa-regular fa-calendar"></i> ${pubDate}</span>
                        <span>•</span>
                        ${timelineBadge}
                    </div>
                </div>
            </div>
            <div class="admin-only" style="display: flex; gap: 8px; flex-shrink: 0;">
                <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 11px; font-weight: 700; display: flex; align-items: center; gap: 4px;" onclick="window.curateSetlist('${v.video_id}', '${v.title.replace(/'/g, "\\'")}')">
                    <i class="fa-solid fa-microphone"></i> 彙整歌單
                </button>
            </div>
        `;
        
        container.appendChild(card);
    });
}

export async function loadActivitiesTimeline(typeFilter = '') {
    const container = document.getElementById('dashboard-timeline');
    if (!container) return;
    container.innerHTML = '';
    
    try {
        let url = `${API_BASE}/activities/`;
        if (typeFilter) {
            url += `?activity_type=${typeFilter}`;
        }
        
        const response = await fetch(url);
        const activities = await response.json();
        
        if (activities.length === 0) {
            container.innerHTML = '<p class="sub-text" style="text-align:center; padding: 20px;">目前無符合類型的活動公告</p>';
            return;
        }
        
        activities.forEach(act => {
            const item = document.createElement('div');
            item.className = `timeline-item ${act.activity_type}`;
            
            const ownerVt = state.cacheVtubers.find(vt => vt.id === act.vtuber_id);
            const vtuberTag = ownerVt ? `<span style="color:var(--neon-purple); font-weight:600;">@${ownerVt.name_main}</span>` : '<span style="color:#64748b;">[官方公告]</span>';
            const linkTag = act.link_url ? `
                <a href="${act.link_url}" target="_blank" class="timeline-link">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> 連結參考
                </a>
            ` : '';
            
            item.innerHTML = `
                <div class="timeline-dot"></div>
                <div class="timeline-content">
                    <div class="timeline-date-row">
                        <span>${act.event_date}</span>
                        <span>${vtuberTag}</span>
                    </div>
                    <div class="timeline-title">${act.title}</div>
                    ${act.description ? `<div class="timeline-desc">${act.description}</div>` : ''}
                    ${linkTag}
                </div>
            `;
            
            container.appendChild(item);
        });
    } catch (error) {
        console.error(error);
    }
}

export async function loadVtuberProfile(vtuberId) {
    switchView('vtuber-profile', '載入中...');
    state.selectedVtuberId = vtuberId;
    
    const container = document.getElementById('vtuber-profile-detail');
    if (!container) return;
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const [vtResponse, recResponse, videoResponse] = await Promise.all([
            fetch(`${API_BASE}/vtubers/${vtuberId}`),
            fetch(`${API_BASE}/records/?vtuber_id=${vtuberId}&limit=100000`),
            fetch(`${API_BASE}/videos/?vtuber_id=${vtuberId}&limit=100000`)
        ]);
        
        if (!vtResponse.ok) {
            container.innerHTML = '<p class="sub-text">找不到此 VTuber 資訊</p>';
            return;
        }
        
        const vt = await vtResponse.json();
        const records = await recResponse.json();
        const vtVideos = await videoResponse.json();
        
        switchView('vtuber-profile', `${vt.name_main} 的個人歌唱專頁`);
        
        // --- 注入個性化主題配色與 Banner ---
        if (vt.theme_color) {
            document.documentElement.style.setProperty('--vtuber-active-theme', vt.theme_color);
            document.body.classList.add('custom-vtuber-theme');
        } else {
            document.documentElement.style.removeProperty('--vtuber-active-theme');
            document.body.classList.remove('custom-vtuber-theme');
        }
        
        const bannerStyle = vt.banner_url
            ? `style="background-image: linear-gradient(to bottom, rgba(15, 12, 30, 0.4), rgba(10, 10, 15, 0.95)), url('${vt.banner_url}'); background-size: cover; background-position: center; border-bottom: 1px solid rgba(255,255,255,0.08);"`
            : '';
        
        const songCounts = {};
        records.forEach(rec => {
            if (rec.song) {
                const title = rec.song.title_main;
                songCounts[title] = (songCounts[title] || 0) + 1;
            }
        });
        const topSongs = Object.entries(songCounts)
            .map(([title, count]) => ({ title, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);

        const artistCounts = {};
        records.forEach(rec => {
            if (rec.song && rec.song.artists) {
                rec.song.artists.forEach(art => {
                    const name = art.name_main;
                    artistCounts[name] = (artistCounts[name] || 0) + 1;
                });
            }
        });
        const topArtists = Object.entries(artistCounts)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);

        let linksHtml = '';
        if (vt.links) {
            vt.links.forEach(l => {
                let iconClass = 'fa-solid fa-link';
                let btnClass = '';
                if (l.platform.toLowerCase().includes('twitter') || l.platform.toLowerCase() === 'x') {
                    iconClass = 'fa-brands fa-x-twitter';
                    btnClass = 'twitter';
                } else if (l.platform.toLowerCase().includes('youtube')) {
                    iconClass = 'fa-brands fa-youtube';
                    btnClass = 'youtube';
                }
                linksHtml += `
                    <a href="${l.url}" target="_blank" class="social-icon-btn ${btnClass}">
                        <i class="${iconClass}"></i> ${l.platform}
                    </a>
                `;
            });
        }
        if (linksHtml === '') linksHtml = '<span class="sub-text">暫無社群連結</span>';
        
        let reqSongsRows = '';
        if (vt.requestable_songs) {
            vt.requestable_songs.forEach(song => {
                const artists = song.artists.map(a => a.name_main).join(', ');
                const isOriginal = song.artists && song.artists.some(art => art.name_main === vt.name_main);
                reqSongsRows += `
                    <tr>
                        <td style="font-weight:700; color:var(--text-bright);">${song.title_main}</td>
                        <td>${artists || '未知'}</td>
                        <td><span class="badge ${isOriginal ? 'badge-original' : 'badge-cover'}">${isOriginal ? '原創' : '翻唱'}</span></td>
                        <td style="text-align:center;">
                            <button class="table-play-btn" onclick="window.searchSongHistory(${song.id}, '${song.title_main.replace(/'/g, "\\'")}')" title="查詢歷史紀錄">
                                <i class="fa-solid fa-magnifying-glass"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
        }
        
        let singingRows = '';
        let liveRows = '';
        
        const singingVideos = vtVideos.filter(v => v.video_type === 'stream_singing');
        const liveVideos = vtVideos.filter(v => v.video_type === 'stream_other' || v.video_type === 'other');
        
        const buildVideoRow = (v) => {
            const thumbnail = v.thumbnail_url || `https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg`;
            const pubDate = v.published_at || '無發布日期';
            
            const timelineBadge = v.has_timeline 
                ? '<span class="badge" style="background:rgba(57, 255, 20, 0.08); border:1px solid rgba(57,255,20,0.2); color:var(--neon-green);">已建立時間軸</span>' 
                : '<span class="badge" style="background:rgba(255, 0, 127, 0.08); border:1px solid rgba(255,0,127,0.2); color:var(--neon-pink);">尚未建立時間軸</span>';
            
            const vTypeMap = {
                'stream_singing': '歌回直播',
                'stream_other': '日常直播',
                'cover_mv': '翻唱 MV',
                'original_mv': '原創 MV',
                'other': '其他影片'
            };
            const typeStr = vTypeMap[v.video_type] || v.video_type;
            
            const typeElement = state.isAdminMode
                ? `<select class="form-select-sm" style="padding: 4px 8px; font-size:11px;" onchange="window.updateVideoType('${v.video_id}', this.value)">
                     <option value="stream_singing" ${v.video_type === 'stream_singing' ? 'selected' : ''}>歌回直播</option>
                     <option value="stream_other" ${v.video_type === 'stream_other' ? 'selected' : ''}>日常直播</option>
                     <option value="cover_mv" ${v.video_type === 'cover_mv' ? 'selected' : ''}>翻唱 MV</option>
                     <option value="original_mv" ${v.video_type === 'original_mv' ? 'selected' : ''}>原創 MV</option>
                     <option value="other" ${v.video_type === 'other' ? 'selected' : ''}>其他影片</option>
                   </select>`
                : `<span class="badge" style="background:rgba(59,130,246,0.1); color:var(--neon-blue); border: 1px solid rgba(59,130,246,0.2);">${typeStr}</span>`;
            
            return `
                <tr>
                    <td>
                        <div class="record-thumb-container" style="width: 80px; height: 45px; margin: 0;" onclick="window.playRecord('${v.video_id}', 0, '${v.title.replace(/'/g, "\\'")}', '${vt.name_main.replace(/'/g, "\\'")}', '${v.title.replace(/'/g, "\\'")}')">
                            <img src="${thumbnail}" alt="thumbnail">
                            <div class="record-play-overlay"><i class="fa-solid fa-play"></i></div>
                        </div>
                    </td>
                    <td style="font-weight:700; color:var(--text-bright); max-width: 230px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <a href="https://www.youtube.com/watch?v=${v.video_id}" target="_blank" style="color:inherit; text-decoration:none;" title="前往 YouTube 播放">
                            ${v.title} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; opacity:0.6;"></i>
                        </a>
                    </td>
                    <td>${typeElement}</td>
                    <td>${pubDate}</td>
                    <td>${timelineBadge}</td>
                    <td class="admin-only" style="text-align:center;">
                        <button class="btn btn-secondary" style="padding: 4px 10px; font-size:11px; font-weight:700;" onclick="window.curateSetlist('${v.video_id}', '${v.title.replace(/'/g, "\\'")}')">
                            <i class="fa-solid fa-microphone"></i> 彙整歌單
                        </button>
                    </td>
                </tr>
            `;
        };

        singingVideos.forEach(v => {
            singingRows += buildVideoRow(v);
        });

        liveVideos.forEach(v => {
            liveRows += buildVideoRow(v);
        });
        
        let historyRows = '';
        records.forEach(rec => {
            if (!rec.song) return;
            const artists = rec.song.artists ? rec.song.artists.map(a => a.name_main).join(', ') : '未知';
            const singers = rec.singers ? rec.singers.map(s => s.name_main).join(' feat. ') : '未知';
            const timeStr = formatSeconds(rec.timestamp_seconds);
            const isOriginal = rec.song.artists && rec.song.artists.some(art => art.name_main === vt.name_main);
            
            historyRows += `
                <tr class="clickable" data-original="${isOriginal}" data-feat="${rec.singers && rec.singers.length > 1}" onclick="window.playRecord('${rec.video.video_id}', ${rec.timestamp_seconds}, '${rec.song.title_main.replace(/'/g, "\\'")}', '${singers.replace(/'/g, "\\'")}', '${rec.video.title.replace(/'/g, "\\'")}')">
                    <td style="font-weight:700; color:var(--text-bright);">${rec.song.title_main}</td>
                    <td>${artists || '未知'}</td>
                    <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${rec.video.title}</td>
                    <td><span class="record-timestamp-tag"><i class="fa-regular fa-clock"></i> ${timeStr}</span></td>
                    <td>${rec.note || '-'}</td>
                    <td style="text-align:center;">
                        <button class="table-play-btn"><i class="fa-solid fa-circle-play" style="font-size:16px;"></i></button>
                    </td>
                </tr>
            `;
        });
        
        const mvRecords = records.filter(rec => 
            rec.video && (rec.video.video_type === 'cover_mv' || rec.video.video_type === 'original_mv')
        );
        let mvRows = '';
        mvRecords.forEach(rec => {
            if (!rec.song) return;
            const artists = rec.song.artists ? rec.song.artists.map(a => a.name_main).join(', ') : '未知';
            const singers = rec.singers ? rec.singers.map(s => s.name_main).join(' feat. ') : '未知';
            const isOriginal = rec.song.artists && rec.song.artists.some(art => art.name_main === vt.name_main);
            mvRows += `
                <tr class="clickable" onclick="window.playRecord('${rec.video.video_id}', ${rec.timestamp_seconds}, '${rec.song.title_main.replace(/'/g, "\\'")}', '${singers.replace(/'/g, "\\'")}', '${rec.video.title.replace(/'/g, "\\'")}')">
                    <td style="font-weight:700; color:var(--text-bright);">${rec.song.title_main}</td>
                    <td>${artists || '未知'}</td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${rec.video.title}</td>
                    <td>
                        <span class="badge ${isOriginal ? 'badge-original' : 'badge-cover'}">
                            ${isOriginal ? '原創 MV' : '翻唱 MV'}
                        </span>
                    </td>
                    <td style="text-align:center;">
                        <button class="table-play-btn"><i class="fa-solid fa-circle-play" style="font-size:16px;"></i></button>
                    </td>
                </tr>
            `;
        });
        
        const allSongsMap = new Map();
        if (vt.signature_songs) {
            vt.signature_songs.forEach(song => {
                allSongsMap.set(song.id, { song, status: 'signature' });
            });
        }
        if (vt.requestable_songs) {
            vt.requestable_songs.forEach(song => {
                if (!allSongsMap.has(song.id)) {
                    allSongsMap.set(song.id, { song, status: 'requestable' });
                } else if (allSongsMap.get(song.id).status !== 'signature') {
                    allSongsMap.set(song.id, { song, status: 'requestable' });
                }
            });
        }
        records.forEach(rec => {
            if (rec.song && !allSongsMap.has(rec.song.id)) {
                allSongsMap.set(rec.song.id, { song: rec.song, status: 'sung' });
            }
        });
        
        const sortedRepertoire = Array.from(allSongsMap.values()).sort((a, b) => b.song.id - a.song.id);
        let repertoireRows = '';
        sortedRepertoire.forEach(item => {
            const song = item.song;
            const artists = song.artists ? song.artists.map(a => a.name_main).join(', ') : '未知';
            const isOriginal = song.artists && song.artists.some(art => art.name_main === vt.name_main);
            
            let statusBadgeHtml = '';
            if (item.status === 'signature') {
                statusBadgeHtml = '<span class="badge badge-purple">常駐拿手歌</span>';
            } else if (item.status === 'requestable') {
                statusBadgeHtml = '<span class="badge badge-original">點歌歌單</span>';
            } else {
                statusBadgeHtml = '<span class="badge badge-cover">已演唱過</span>';
            }
            
            repertoireRows += `
                <tr data-status="${item.status}">
                    <td style="font-weight:700; color:var(--text-bright);">${song.title_main}</td>
                    <td>${artists || '未知'}</td>
                    <td><span class="badge ${isOriginal ? 'badge-original' : 'badge-cover'}">${isOriginal ? '原創' : '翻唱'}</span></td>
                    <td>${statusBadgeHtml}</td>
                    <td style="text-align:center;">
                        <button class="table-play-btn" onclick="window.searchSongHistory(${song.id}, '${song.title_main.replace(/'/g, "\\'")}')" title="查詢歷史紀錄">
                            <i class="fa-solid fa-magnifying-glass"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        let personalActivitiesHtml = '';
        if (vt.activities) {
            [...vt.activities].sort((a,b) => b.event_date.localeCompare(a.event_date)).forEach(act => {
                personalActivitiesHtml += `
                    <div class="timeline-item ${act.activity_type}" style="padding-bottom:18px;">
                        <div class="timeline-dot"></div>
                        <div class="timeline-content" style="padding:10px 14px;">
                            <div class="timeline-date-row" style="margin-bottom:2px;">
                                <span>${act.event_date}</span>
                                <span class="badge ${act.activity_type === 'milestone' ? 'badge-purple' : 'badge-original'}">${act.activity_type}</span>
                            </div>
                            <div class="timeline-title" style="font-size:13px;">${act.title}</div>
                            ${act.description ? `<div class="timeline-desc" style="font-size:11px; margin-top:4px;">${act.description}</div>` : ''}
                        </div>
                    </div>
                `;
            });
        }
        if (personalActivitiesHtml === '') personalActivitiesHtml = '<p class="sub-text" style="text-align:center; padding:20px;">尚無成就里程碑</p>';
        
        const avatarHtml = vt.avatar_url 
            ? `<img src="${vt.avatar_url}" alt="${vt.name_main}" class="vtuber-avatar-large" style="object-fit:cover;">`
            : `<div class="vtuber-avatar-large">${vt.name_main.charAt(0)}</div>`;
            
        container.innerHTML = `
            <div class="vtuber-hero" ${bannerStyle}>
                ${avatarHtml}
                <div class="vtuber-info-hero">
                    <div class="vtuber-names">
                        <h2>${vt.name_main}</h2>
                        <div class="sub-names">
                            ${vt.name_ja ? `<span>${vt.name_ja}</span>` : ''} 
                            ${vt.name_zh ? `<span>| ${vt.name_zh}</span>` : ''}
                        </div>
                    </div>
                    <p class="vtuber-description">${vt.description || '暫無簡介。'}</p>
                    <div class="vtuber-links-row">${linksHtml}</div>
                </div>
            </div>
            
            <div class="profile-grid" style="grid-template-columns: 1fr;">
                <div class="content-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; gap: 20px; flex-wrap: wrap; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 15px;">
                        <div class="playlist-tabs" style="margin-bottom: 0; border-bottom: 0; padding-bottom: 0; display: flex; flex-wrap: wrap; gap: 4px;">
                            <button class="playlist-tab-btn active" id="tab-btn-bio">主播簡介與活動</button>
                            <button class="playlist-tab-btn" id="tab-btn-requestable">歌唱總歌單 (${sortedRepertoire.length})</button>
                            <button class="playlist-tab-btn" id="tab-btn-singing">歌回直播 (${singingVideos.length})</button>
                            <button class="playlist-tab-btn" id="tab-btn-live">日常與其他直播 (${liveVideos.length})</button>
                            <button class="playlist-tab-btn" id="tab-btn-history">歷史歌回單曲 (${records.length})</button>
                            <button class="playlist-tab-btn" id="tab-btn-mv">MV 影片清單 (${mvRecords.length})</button>
                        </div>
                        <div>
                            <input type="text" id="profile-search-input" placeholder="🔍 搜尋歌名、原唱、直播名稱..." style="padding: 8px 16px; font-size:12.5px; width: 260px; border-radius: 20px; border:1px solid var(--border-color); background: var(--input-bg); color: var(--text-bright);">
                        </div>
                    </div>
                    
                    <div class="tab-pane active" id="pane-bio">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 10px; margin-bottom: 24px;">
                            <div style="background: rgba(139, 92, 246, 0.02); border: 1px solid rgba(139, 92, 246, 0.1); padding: 18px; border-radius: 12px;">
                                <h4 style="color: var(--neon-purple); font-size:14px; font-weight:800; margin-top:0; margin-bottom:12px; display:flex; align-items:center; gap:6px;">
                                    <i class="fa-solid fa-trophy"></i> 最常唱歌曲排行 (TOP 5)
                                </h4>
                                <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:8px;">
                                    ${topSongs.map((s, idx) => `
                                        <li style="display:flex; justify-content:space-between; align-items:center; font-size:13px; border-bottom: 1px dashed rgba(255,255,255,0.03); padding-bottom: 6px;">
                                            <span><span style="color:#64748b; font-weight:700; margin-right:8px;">#${idx+1}</span> <strong style="color:var(--text-bright);">${s.title}</strong></span>
                                            <span class="badge badge-purple" style="font-size:10.5px; padding: 2px 8px; border-radius: 10px; background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.2); color: var(--neon-purple); font-weight: 700;">${s.count} 次</span>
                                        </li>
                                    `).join('') || '<li class="sub-text" style="font-size:12.5px;">暫無歌唱數據</li>'}
                                </ul>
                            </div>
                            
                            <div style="background: rgba(59, 130, 246, 0.02); border: 1px solid rgba(59, 130, 246, 0.1); padding: 18px; border-radius: 12px;">
                                <h4 style="color: var(--neon-blue); font-size:14px; font-weight:800; margin-top:0; margin-bottom:12px; display:flex; align-items:center; gap:6px;">
                                    <i class="fa-solid fa-microphone"></i> 最常唱原唱歌手 (TOP 5)
                                </h4>
                                <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:8px;">
                                    ${topArtists.map((a, idx) => `
                                        <li style="display:flex; justify-content:space-between; align-items:center; font-size:13px; border-bottom: 1px dashed rgba(255,255,255,0.03); padding-bottom: 6px;">
                                            <span><span style="color:#64748b; font-weight:700; margin-right:8px;">#${idx+1}</span> <strong style="color:var(--text-bright);">${a.name}</strong></span>
                                            <span class="badge badge-original" style="font-size:10.5px; padding: 2px 8px; border-radius: 10px; background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); color: var(--neon-blue); font-weight: 700;">${a.count} 次</span>
                                        </li>
                                    `).join('') || '<li class="sub-text" style="font-size:12.5px;">暫無原創歌手數據</li>'}
                                </ul>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1.2fr; gap: 40px; margin-top: 15px;">
                            <div>
                                <h3 style="margin-bottom:12px; font-weight:800; font-size:16px;">關於主播</h3>
                                <p style="line-height:1.7; color:#cbd5e1; font-size:14px; background:rgba(255,255,255,0.01); border:1px solid var(--border-color); padding: 18px; border-radius:12px;">
                                    ${vt.description || '暫無詳細描述介紹。'}
                                </p>
                            </div>
                            <div>
                                <h3 style="margin-bottom:12px; font-weight:800; font-size:16px;">成就公告時間軸</h3>
                                <div class="vertical-timeline" style="max-height: 400px; padding-top: 10px;">
                                    ${personalActivitiesHtml}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="pane-requestable" style="max-height: 480px; overflow-y:auto;">
                        <table class="premium-table" style="font-size:12.5px;">
                            <thead>
                                <tr>
                                    <th>主要歌名</th>
                                    <th>原著歌手</th>
                                    <th>屬性</th>
                                    <th>所屬歌單</th>
                                    <th style="text-align:center; width:80px;">歷史</th>
                                </tr>
                            </thead>
                            <tbody id="profile-repertoire-tbody">${repertoireRows}</tbody>
                        </table>
                    </div>
                    
                    <div class="tab-pane" id="pane-singing" style="max-height: 480px; overflow-y:auto;">
                        <table class="premium-table" style="font-size:12.5px;">
                            <thead>
                                <tr>
                                    <th>縮圖</th>
                                    <th>影片標題</th>
                                    <th>類型</th>
                                    <th>日期</th>
                                    <th>時間軸狀態</th>
                                    <th class="admin-only" style="text-align:center; width:100px;">彙整</th>
                                </tr>
                            </thead>
                            <tbody id="profile-singing-tbody">${singingRows}</tbody>
                        </table>
                    </div>
                    
                    <div class="tab-pane" id="pane-live" style="max-height: 480px; overflow-y:auto;">
                        <table class="premium-table" style="font-size:12.5px;">
                            <thead>
                                <tr>
                                    <th>縮圖</th>
                                    <th>影片標題</th>
                                    <th>類型</th>
                                    <th>日期</th>
                                    <th>時間軸狀態</th>
                                    <th class="admin-only" style="text-align:center; width:100px;">彙整</th>
                                </tr>
                            </thead>
                            <tbody id="profile-live-tbody">${liveRows}</tbody>
                        </table>
                    </div>
                    
                    <div class="tab-pane" id="pane-history" style="max-height: 480px; overflow-y:auto;">
                        <table class="premium-table" style="font-size:12.5px;">
                            <thead>
                                <tr>
                                    <th>歌名</th>
                                    <th>原唱</th>
                                    <th>出自直播影片</th>
                                    <th>時間點</th>
                                    <th>備註</th>
                                    <th style="text-align:center; width:80px;">播放</th>
                                </tr>
                            </thead>
                            <tbody id="profile-history-tbody">${historyRows}</tbody>
                        </table>
                    </div>
                    
                    <div class="tab-pane" id="pane-mv" style="max-height: 480px; overflow-y:auto;">
                        <table class="premium-table" style="font-size:12.5px;">
                            <thead>
                                <tr>
                                    <th>歌名</th>
                                    <th>原唱</th>
                                    <th>MV 影片標題</th>
                                    <th>屬性</th>
                                    <th style="text-align:center; width:80px;">播放</th>
                                </tr>
                            </thead>
                            <tbody id="profile-mv-tbody">${mvRows}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        setupProfileTabs();
        
        const searchInput = document.getElementById('profile-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                const query = searchInput.value.toLowerCase().trim();
                filterProfileRows(query);
            });
        }
        
    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="sub-text">加載主播個人資料時出錯</p>';
    }
}

function setupProfileTabs() {
    const tabs = document.querySelectorAll('#vtuber-profile-detail .playlist-tab-btn');
    tabs.forEach(btn => {
        btn.addEventListener('click', () => {
            tabs.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const paneId = btn.id.replace('tab-btn-', 'pane-');
            const targetPane = document.getElementById(paneId);
            
            document.querySelectorAll('#vtuber-profile-detail .tab-pane').forEach(p => p.classList.remove('active'));
            if (targetPane) targetPane.classList.add('active');
        });
    });
}

function filterProfileRows(query) {
    document.querySelectorAll('#profile-repertoire-tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
    document.querySelectorAll('#profile-singing-tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
    document.querySelectorAll('#profile-live-tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
    document.querySelectorAll('#profile-history-tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
    document.querySelectorAll('#profile-mv-tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
}

export async function searchSongHistory(songId, songTitle) {
    try {
        const response = await fetch(`${API_BASE}/records/?song_id=${songId}`);
        const records = await response.json();
        
        if (records.length === 0) {
            showToast(`《${songTitle}》目前尚無演唱歷史紀錄`, 'error');
            return;
        }
        
        if (records.length === 1) {
            const rec = records[0];
            const singersStr = rec.singers ? rec.singers.map(s => s.name_main).join(' feat. ') : '未知';
            const videoTitle = rec.video ? rec.video.title : '未知影片';
            playRecord(
                rec.video_id, 
                rec.timestamp_seconds, 
                rec.song.title_main, 
                singersStr,
                videoTitle
            );
        } else {
            // 切換至儀表板並將多筆演唱紀錄渲染至「最新 Live」位置進行展示！
            switchView('dashboard', `《${songTitle}》的演唱歷史紀錄`);
            renderRecentRecords(records);
            showToast(`已為您篩選出《${songTitle}》的 ${records.length} 筆演唱紀錄！`);
        }
    } catch (error) {
        showToast('查詢演唱紀錄出錯', 'error');
    }
}

export function renderRecentRecords(records) {
    const container = document.getElementById('dashboard-recent-records');
    if (!container) return;
    container.innerHTML = '';
    
    if (records.length === 0) {
        container.innerHTML = '<p class="sub-text" style="text-align:center; padding: 20px;">無演唱紀錄</p>';
        return;
    }
    
    records.forEach(rec => {
        const card = document.createElement('div');
        card.className = 'record-card';
        card.style.cssText = 'display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 12px; margin-bottom: 12px; border-radius: 12px;';
        
        const thumbnail = rec.video && rec.video.thumbnail_url 
            ? rec.video.thumbnail_url 
            : `https://img.youtube.com/vi/${rec.video_id}/mqdefault.jpg`;
            
        const singersStr = rec.singers ? rec.singers.map(s => s.name_main).join(' feat. ') : '未知主播';
        const timeStr = formatSeconds(rec.timestamp_seconds);
        const videoTitle = rec.video ? rec.video.title : '未知直播';
        
        card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0;">
                <div class="record-thumb-container" style="width: 100px; height: 56px; margin: 0; flex-shrink: 0;" onclick="window.playRecord('${rec.video_id}', ${rec.timestamp_seconds}, '${rec.song.title_main.replace(/'/g, "\\'")}', '${singersStr.replace(/'/g, "\\'")}', '${videoTitle.replace(/'/g, "\\'")}')">
                    <img src="${thumbnail}" alt="Video thumbnail">
                    <div class="record-play-overlay"><i class="fa-solid fa-play"></i></div>
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 700; color: var(--text-bright); font-size: 13.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px;" title="${rec.song.title_main}">
                        ${rec.song.title_main}
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 11px; color: #94a3b8; flex-wrap: wrap;">
                        <span><i class="fa-solid fa-user" style="color: var(--neon-purple);"></i> ${singersStr}</span>
                        <span>•</span>
                        <span><i class="fa-regular fa-clock"></i> ${timeStr}</span>
                        <span>•</span>
                        <span style="max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${videoTitle}</span>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

export function renderCatalog() {
    const searchVal = document.getElementById('catalog-search-input').value.trim().toLowerCase();
    console.log('[Search Debug] Input query:', searchVal);
    console.log('[Search Debug] Cache sizes - Songs:', state.cacheSongs ? state.cacheSongs.length : 0, 
                'Artists:', state.cacheArtists ? state.cacheArtists.length : 0,
                'Records:', state.cacheRecords ? state.cacheRecords.length : 0);
    
    // 1. 歌曲大表
    const songBody = document.getElementById('catalog-songs-tbody');
    if (songBody) {
        songBody.innerHTML = '';
        const filteredSongs = state.cacheSongs.filter(s => {
            const matchesTitle = s.title_main.toLowerCase().includes(searchVal) ||
                (s.title_ja && s.title_ja.toLowerCase().includes(searchVal)) ||
                (s.title_zh && s.title_zh.toLowerCase().includes(searchVal)) ||
                (s.title_romaji && s.title_romaji.toLowerCase().includes(searchVal));
            const matchesArtist = s.artists && s.artists.some(a => 
                a.name_main.toLowerCase().includes(searchVal) ||
                (a.name_ja && a.name_ja.toLowerCase().includes(searchVal)) ||
                (a.name_zh && a.name_zh.toLowerCase().includes(searchVal)) ||
                (a.name_romaji && a.name_romaji.toLowerCase().includes(searchVal))
            );
            return matchesTitle || matchesArtist;
        });
        
        const songsToShow = filteredSongs.slice(0, 100);
        songsToShow.forEach(song => {
            const artists = song.artists ? song.artists.map(a => a.name_main).join(', ') : '';
            const artistHtml = artists || '<span class="badge" style="background:rgba(255,0,127,0.06); color:var(--neon-pink);">未知 (請指定原著)</span>';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-weight:700; color:var(--text-bright);">${song.title_main}</td>
                <td>${artistHtml}</td>
                <td class="admin-only" style="text-align:center;">
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; margin-right:4px;" onclick="window.editSong(${song.id})"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15);" onclick="window.deleteSongRecord(${song.id}, '${song.title_main.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i> 刪除</button>
                </td>
            `;
            songBody.appendChild(tr);
        });
        
        if (filteredSongs.length > 100) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="3" style="text-align:center; color:#64748b; font-size:11.5px; padding:12px 0;"><i class="fa-solid fa-circle-info"></i> 💡 僅顯示前 100 筆歌曲，請輸入關鍵字精確搜尋...</td>`;
            songBody.appendChild(tr);
        }
    }

    // 2. 歌手大表
    const artistBody = document.getElementById('catalog-artists-tbody');
    if (artistBody) {
        artistBody.innerHTML = '';
        const filteredArtists = state.cacheArtists.filter(a => 
            a.name_main.toLowerCase().includes(searchVal) ||
            (a.name_ja && a.name_ja.toLowerCase().includes(searchVal)) ||
            (a.name_zh && a.name_zh.toLowerCase().includes(searchVal)) ||
            (a.name_romaji && a.name_romaji.toLowerCase().includes(searchVal))
        );
        
        const artistsToShow = filteredArtists.slice(0, 100);
        artistsToShow.forEach(art => {
            const extra = [art.name_ja, art.name_zh, art.name_romaji].filter(x => x).join(' / ');
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-weight:700; color:var(--text-bright);">${art.name_main}</td>
                <td>${extra || '-'}</td>
                <td class="admin-only" style="text-align:center;">
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; margin-right:4px;" onclick="window.editArtist(${art.id})"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15);" onclick="window.deleteArtistRecord(${art.id}, '${art.name_main.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i> 刪除</button>
                </td>
            `;
            artistBody.appendChild(tr);
        });
        
        if (filteredArtists.length > 100) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="3" style="text-align:center; color:#64748b; font-size:11.5px; padding:12px 0;"><i class="fa-solid fa-circle-info"></i> 💡 僅顯示前 100 筆歌手，請輸入關鍵字精確搜尋...</td>`;
            artistBody.appendChild(tr);
        }
    }

    // 3. 影音大表
    const videoBody = document.getElementById('catalog-videos-tbody');
    if (videoBody) {
        videoBody.innerHTML = '';
        
        const filterType = document.getElementById('catalog-video-filter-type')?.value || '';
        const filterVtuber = document.getElementById('catalog-video-filter-vtuber')?.value || '';
        const filterTimeline = document.getElementById('catalog-video-filter-timeline')?.value || '';
        
        const filteredVideos = state.cacheVideos.filter(v => {
            const ownerVt = state.cacheVtubers.find(vt => vt.id == v.vtuber_id);
            const vtName = ownerVt ? ownerVt.name_main.toLowerCase() : '';
            
            // 文字過濾
            const matchesText = v.title.toLowerCase().includes(searchVal) ||
                                v.video_id.toLowerCase().includes(searchVal) ||
                                vtName.includes(searchVal);
            if (!matchesText) return false;
            
            // 類型過濾
            if (filterType && v.video_type !== filterType) return false;
            
            // 主播過濾
            if (filterVtuber && String(v.vtuber_id) !== String(filterVtuber)) return false;
            
            // 時間軸有無過濾
            if (filterTimeline) {
                const hasTimeline = state.cacheRecords.some(r => r.video_id === v.video_id);
                if (filterTimeline === 'yes' && !hasTimeline) return false;
                if (filterTimeline === 'no' && hasTimeline) return false;
            }
            
            return true;
        });
        
        const videosToShow = filteredVideos.slice(0, 100);
        videosToShow.forEach(video => {
            const ownerVt = state.cacheVtubers.find(vt => vt.id == video.vtuber_id);
            const vtName = ownerVt ? ownerVt.name_main : '未指派';
            const vTypeMap = {
                'stream_singing': '歌回直播',
                'stream_other': '日常直播',
                'cover_mv': '翻唱 MV',
                'original_mv': '原創 MV',
                'other': '其他影片'
            };
            const typeStr = vTypeMap[video.video_type] || video.video_type;
            const publishedStr = video.published_at || '-';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank" style="font-weight:700; color:var(--neon-blue); text-decoration:none;">
                        ${video.title} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:10px;"></i>
                    </a>
                </td>
                <td><span class="badge">${typeStr}</span></td>
                <td>${publishedStr}</td>
                <td><span class="badge" style="background:rgba(139,92,246,0.06); color:var(--neon-purple);">${vtName}</span></td>
                <td class="admin-only" style="text-align:center;">
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; margin-right:4px;" onclick="window.editVideo('${video.video_id}')"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15);" onclick="window.deleteVideoRecord('${video.video_id}', '${video.title.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i> 刪除</button>
                </td>
            `;
            videoBody.appendChild(tr);
        });
        
        if (filteredVideos.length > 100) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="5" style="text-align:center; color:#64748b; font-size:11.5px; padding:12px 0;"><i class="fa-solid fa-circle-info"></i> 💡 僅顯示前 100 筆影片，請輸入關鍵字精確搜尋...</td>`;
            videoBody.appendChild(tr);
        }
    }

    // 4. 歷史演唱紀錄大表
    const recordBody = document.getElementById('catalog-records-tbody');
    if (recordBody) {
        recordBody.innerHTML = '';
        const filteredRecords = state.cacheRecords.filter(r => {
            const songTitle = r.song ? r.song.title_main.toLowerCase() : '';
            const songArtist = (r.song && r.song.artists) ? r.song.artists.map(a => a.name_main).join(' ').toLowerCase() : '';
            const singersStr = r.singers ? r.singers.map(s => s.name_main).join(' ').toLowerCase() : '';
            const noteStr = r.note ? r.note.toLowerCase() : '';
            const videoId = r.video_id.toLowerCase();
            return songTitle.includes(searchVal) ||
                   songArtist.includes(searchVal) ||
                   singersStr.includes(searchVal) ||
                   noteStr.includes(searchVal) ||
                   videoId.includes(searchVal);
        });
        
        const recordsToShow = filteredRecords.slice(0, 100);
        recordsToShow.forEach(rec => {
            const songTitle = rec.song ? rec.song.title_main : '未知歌曲';
            const originalArtist = (rec.song && rec.song.artists && rec.song.artists.length > 0) ? rec.song.artists.map(a => a.name_main).join(', ') : '未知';
            const singersStr = rec.singers ? rec.singers.map(s => s.name_main).join(', ') : '未指派';
            const noteStr = rec.note || '-';
            const timeStr = formatSeconds(rec.timestamp_seconds);
            const videoTitle = rec.video ? rec.video.title : '未知影片';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <span style="font-weight:700; color:var(--text-bright);">${songTitle}</span>
                    <span style="font-size:11px; color:#64748b; display:block;">原唱：${originalArtist}</span>
                </td>
                <td><span class="badge" style="background:rgba(139,92,246,0.06); color:var(--neon-purple);">${singersStr}</span></td>
                <td>
                    <a href="#" style="font-weight:600; color:inherit; text-decoration:none; display:block; max-width:260px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" onclick="window.playRecord('${rec.video_id}', ${rec.timestamp_seconds}, '${songTitle.replace(/'/g, "\\'")}', '${singersStr.replace(/'/g, "\\'")}', '${videoTitle.replace(/'/g, "\\'")}')">
                        <i class="fa-solid fa-circle-play text-blue"></i> ${videoTitle}
                    </a>
                    <span class="record-timestamp-tag"><i class="fa-regular fa-clock"></i> ${timeStr}</span>
                </td>
                <td>${noteStr}</td>
                <td class="admin-only" style="text-align:center;">
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; margin-right:4px;" onclick="window.editHistoryRecord(${rec.id})"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15);" onclick="window.deleteHistoryRecord(${rec.id}, '${songTitle.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i> 刪除</button>
                </td>
            `;
            recordBody.appendChild(tr);
        });
        
        if (filteredRecords.length > 100) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="5" style="text-align:center; color:#64748b; font-size:11.5px; padding:12px 0;"><i class="fa-solid fa-circle-info"></i> 💡 僅顯示前 100 筆紀錄，請輸入關鍵字精確搜尋...</td>`;
            recordBody.appendChild(tr);
        }
    }

    // 5. 公告里程碑大表
    const activityBody = document.getElementById('catalog-activities-tbody');
    if (activityBody) {
        activityBody.innerHTML = '';
        const filteredActivities = state.cacheActivities.filter(act => {
            const ownerVt = state.cacheVtubers.find(vt => vt.id == act.vtuber_id);
            const vtName = ownerVt ? ownerVt.name_main.toLowerCase() : '';
            return act.title.toLowerCase().includes(searchVal) ||
                   act.activity_type.toLowerCase().includes(searchVal) ||
                   vtName.includes(searchVal) ||
                   (act.description && act.description.toLowerCase().includes(searchVal));
        });
        
        const activitiesToShow = filteredActivities.slice(0, 100);
        activitiesToShow.forEach(act => {
            const ownerVt = state.cacheVtubers.find(vt => vt.id == act.vtuber_id);
            const vtName = ownerVt ? ownerVt.name_main : '全站公告';
            const aTypeMap = {
                'milestone': '成就里程碑',
                'schedule': '直播排程',
                'news': '官方消息',
                'other': '其他消息'
            };
            const typeStr = aTypeMap[act.activity_type] || act.activity_type;
            const linkHtml = act.link_url 
                ? `<a href="${act.link_url}" target="_blank" style="color:var(--neon-blue); text-decoration:none;"><i class="fa-solid fa-arrow-up-right-from-square"></i> 參考網址</a>`
                : '-';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <span style="font-weight:700; color:var(--text-bright);">${act.title}</span>
                    ${act.description ? `<span style="font-size:11px; color:#64748b; display:block; max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${act.description}">${act.description}</span>` : ''}
                </td>
                <td><span class="badge">${typeStr}</span></td>
                <td>${act.event_date}</td>
                <td><span class="badge" style="background:rgba(139,92,246,0.06); color:var(--neon-purple);">${vtName}</span></td>
                <td>${linkHtml}</td>
                <td class="admin-only" style="text-align:center;">
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; margin-right:4px;" onclick="window.editActivity(${act.id})"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15);" onclick="window.deleteActivityRecord(${act.id}, '${act.title.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i> 刪除</button>
                </td>
            `;
            activityBody.appendChild(tr);
        });
        
        if (filteredActivities.length > 100) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="6" style="text-align:center; color:#64748b; font-size:11.5px; padding:12px 0;"><i class="fa-solid fa-circle-info"></i> 💡 僅顯示前 100 筆公告，請輸入關鍵字精確搜尋...</td>`;
            activityBody.appendChild(tr);
        }
    }
}

export function renderVtuberCatalog() {
    const tbody = document.getElementById('catalog-vtubers-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    state.cacheVtubers.forEach(vt => {
        const avatarHtml = vt.avatar_url 
            ? `<img src="${vt.avatar_url}" alt="avatar" style="width:30px; height:30px; border-radius:50%; object-fit:cover; display:block; margin:0 auto;">`
            : `<div class="vtuber-avatar-mini" style="margin:0 auto;">${vt.name_main.charAt(0)}</div>`;
            
        const nameJaZh = [vt.name_ja, vt.name_zh].filter(x => x).join(' / ') || '-';
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; vertical-align:middle;">${avatarHtml}</td>
            <td style="font-weight:700; color:var(--text-bright); vertical-align:middle;">${vt.name_main}</td>
            <td style="vertical-align:middle;">${nameJaZh}</td>
            <td style="font-family:monospace; vertical-align:middle;">${vt.youtube_channel_id || '-'}</td>
            <td style="max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:middle;" title="${vt.description || ''}">${vt.description || '-'}</td>
            <td class="admin-only" style="text-align:center; vertical-align:middle;">
                <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; margin-right:4px;" onclick="window.editVtuber(${vt.id})"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15);" onclick="window.deleteVtuberRecord(${vt.id}, '${vt.name_main.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i> 刪除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

export function populateCatalogDropdowns() {
    const vtSelect = document.getElementById('catalog-video-filter-vtuber');
    if (vtSelect) {
        const vtubers = state.cacheVtubers;
        vtSelect.innerHTML = '<option value="">-- 依所屬主播篩選 --</option>';
        vtubers.forEach(vt => {
            vtSelect.innerHTML += `<option value="${vt.id}">${vt.name_main}</option>`;
        });
    }
}
