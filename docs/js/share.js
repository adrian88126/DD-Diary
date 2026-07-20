// 數據存儲與全域變數
let vt = window.vtuberData || {};
let videos = window.videosData || [];
let activities = window.activitiesData || [];
let records = window.recordsData || [];

let ytPlayer = null;
let activeVideoId = null;
let currentSelectedYear = null;
let currentSelectedMonth = null;

// 時間格式化輔助函數 (獨立內建，避開 file:// 協議 CORS import 限制)
function formatSeconds(seconds) {
    if (!seconds || seconds === 0) return '00:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    
    const mm = m < 10 ? '0' + m : m;
    const ss = s < 10 ? '0' + s : s;
    
    if (h > 0) {
        const hh = h < 10 ? '0' + h : h;
        return `${hh}:${mm}:${ss}`;
    }
    return `${mm}:${ss}`;
}

// YouTube IFrame API Ready Handler
window.onYouTubeIframeAPIReady = function() {
    // 預留，當點擊播放時建立 Player 實例
};

// 播放歷史紀錄中的影片
function playRecord(videoId, seconds, songTitle, singerName, shouldAutoplay = true) {
    const songTitleEl = document.getElementById('current-song-title');
    const singerNameEl = document.getElementById('current-singer-name');
    if (songTitleEl) songTitleEl.textContent = songTitle;
    if (singerNameEl) singerNameEl.innerHTML = `<i class="fa-solid fa-user"></i> ${singerName}`;
    
    // 平滑滾動到播放器卡片 (僅在行動裝置下適用，且啟動播放時)
    if (window.innerWidth <= 1024 && shouldAutoplay) {
        const playerCard = document.querySelector('.player-card');
        if (playerCard) playerCard.scrollIntoView({ behavior: 'smooth' });
    }

    if (ytPlayer && activeVideoId === videoId) {
        // 如果是同一支影片，直接跳轉秒數並播放
        ytPlayer.seekTo(seconds, true);
        if (shouldAutoplay) {
            ytPlayer.playVideo();
        }
    } else {
        // 如果是新影片或播放器未初始化
        activeVideoId = videoId;
        const playerContainer = document.getElementById('youtube-player');
        if (playerContainer) {
            playerContainer.innerHTML = '<div id="yt-player-iframe"></div>';
            
                const pVars = {
                    'autoplay': shouldAutoplay ? 1 : 0,
                    'playsinline': 1,
                    'start': seconds,
                    'enablejsapi': 1,
                    'widget_referrer': window.location.href
                };
                if (window.location.protocol.startsWith('http')) {
                    pVars['origin'] = window.location.origin;
                }
                ytPlayer = new YT.Player('yt-player-iframe', {
                    height: '100%',
                    width: '100%',
                    videoId: videoId,
                    playerVars: pVars,
                    events: {
                        'onReady': function(event) {
                            if (shouldAutoplay) {
                                event.target.playVideo();
                            }
                        }
                    }
                });
        }
    }
}

// 切換分頁 Tab
function switchTab(tabId) {
    document.querySelectorAll('.playlist-tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    
    const targetBtn = document.getElementById(`tab-btn-${tabId}`);
    if (targetBtn) targetBtn.classList.add('active');
    
    const targetPane = document.getElementById(`pane-${tabId}`);
    if (targetPane) targetPane.classList.add('active');
}

// 顯示 Toast 訊息
function showToast(message) {
    let toast = document.getElementById('share-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'share-toast';
        toast.style.cssText = `
            position: fixed;
            top: 24px;
            right: 24px;
            background: rgba(10, 14, 12, 0.95);
            border: 1px solid var(--vtuber-active-theme);
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 8px 32px rgba(0,0,0,0.8);
            z-index: 10000;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 8px;
            transform: translateY(-20px);
            opacity: 0;
        `;
        document.body.appendChild(toast);
    }
    toast.innerHTML = `<i class="fa-solid fa-circle-check" style="color:var(--vtuber-active-theme);"></i> ${message}`;
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
    }, 2500);
}

// 一鍵複製點歌指令
function copySongRequest(title, artist) {
    const text = `點歌：${title}${artist && artist !== '未知' ? ' / ' + artist : ''}`;
    const successMsg = `已複製點歌指令：${text}`;
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(successMsg);
        }).catch(() => {
            fallbackCopy(text, successMsg);
        });
    } else {
        fallbackCopy(text, successMsg);
    }
}

function fallbackCopy(text, successMsg) {
    const input = document.createElement('input');
    input.value = text;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
    showToast(successMsg);
}

// 外跳 YouTube 精確秒數播放
function openExternalYoutube(videoId, seconds) {
    const url = `https://www.youtube.com/watch?v=${videoId}&t=${seconds}s`;
    window.open(url, '_blank');
}

// 在大表中搜尋單曲歷史
function searchSongInHistory(songTitle) {
    switchTab('history');
    const searchInput = document.getElementById('share-search-input');
    if (searchInput) {
        searchInput.value = songTitle;
        const event = new Event('input');
        searchInput.dispatchEvent(event);
    }
}

// 🖼️ 高清圖片燈箱 (Lightbox) 控制
function openLightbox(url, caption) {
    const modal = document.getElementById('image-lightbox-modal');
    const img = document.getElementById('lightbox-img');
    const cap = document.getElementById('lightbox-caption');
    if (modal && img) {
        img.src = url;
        img.classList.remove('zoomed');
        if (cap) cap.textContent = caption || '高清圖檔展示';
        modal.classList.add('active');
    }
}

function closeLightbox() {
    const modal = document.getElementById('image-lightbox-modal');
    if (modal) modal.classList.remove('active');
}

function toggleLightboxZoom(e) {
    if (e) e.stopPropagation();
    const img = document.getElementById('lightbox-img');
    if (img) img.classList.toggle('zoomed');
}

// 📅 精緻月曆渲染 (時區安全型字串解析)
function renderSingingCalendar() {
    const container = document.getElementById('singing-calendar-container');
    if (!container) return;

    // 重新從 window.recordsData 或 records 獲取最新紀錄
    if (window.recordsData && window.recordsData.length > 0) {
        records = window.recordsData;
    }

    const dateMap = {};
    const availableYears = new Set();
    
    records.forEach(rec => {
        let dateStr = '';
        if (rec.video && rec.video.published_at) {
            dateStr = rec.video.published_at.substring(0, 10);
            const y = parseInt(dateStr.substring(0, 4));
            if (y) availableYears.add(y);
        }
        if (dateStr) {
            dateMap[dateStr] = (dateMap[dateStr] || 0) + 1;
        }
    });

    const dates = Object.keys(dateMap).sort();
    const yearList = Array.from(availableYears).sort((a, b) => b - a);
    if (yearList.length === 0) yearList.push(new Date().getFullYear());

    if (!currentSelectedYear) {
        if (dates.length > 0) {
            const lastDateParts = dates[dates.length - 1].split('-');
            currentSelectedYear = parseInt(lastDateParts[0]);
            currentSelectedMonth = parseInt(lastDateParts[1]);
        } else {
            currentSelectedYear = new Date().getFullYear();
            currentSelectedMonth = new Date().getMonth() + 1;
        }
    }

    const year = currentSelectedYear;
    const month = currentSelectedMonth;

    let yearOptionsHtml = yearList.map(y => `<option value="${y}" ${y === year ? 'selected' : ''}>${y} 年</option>`).join('');
    let monthOptionsHtml = '';
    for (let m = 1; m <= 12; m++) {
        monthOptionsHtml += `<option value="${m}" ${m === month ? 'selected' : ''}>${m < 10 ? '0'+m : m} 月</option>`;
    }

    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();

    let html = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
            <span style="font-size:13px; font-weight:800; color:var(--text-bright); display:flex; align-items:center; gap:6px;">
                <i class="fa-solid fa-calendar-check" style="color:var(--vtuber-active-theme);"></i> 歌回月曆
            </span>
            <div style="display:flex; gap:6px; align-items:center;">
                <select id="calendar-year-select" class="calendar-select-dropdown" onchange="onCalendarYearMonthChange()">
                    ${yearOptionsHtml}
                </select>
                <select id="calendar-month-select" class="calendar-select-dropdown" onchange="onCalendarYearMonthChange()">
                    ${monthOptionsHtml}
                </select>
            </div>
        </div>
        <div class="calendar-grid-compact">
            <div class="calendar-day-header">日</div>
            <div class="calendar-day-header">一</div>
            <div class="calendar-day-header">二</div>
            <div class="calendar-day-header">三</div>
            <div class="calendar-day-header">四</div>
            <div class="calendar-day-header">五</div>
            <div class="calendar-day-header">六</div>
    `;

    for (let i = 0; i < firstDay; i++) {
        html += `<div class="calendar-day-cell empty"></div>`;
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const mStr = month < 10 ? '0' + month : month;
        const dStr = day < 10 ? '0' + day : day;
        const fullDateStr = `${year}-${mStr}-${dStr}`;
        const count = dateMap[fullDateStr] || 0;

        if (count > 0) {
            html += `
                <div class="calendar-day-cell has-singing" onclick="filterByCalendarDate('${fullDateStr}')" title="${fullDateStr} 開唱 ${count} 首歌曲 (點擊過濾)">
                    <span>${day}</span>
                    <div class="calendar-singing-dot"></div>
                </div>
            `;
        } else {
            html += `
                <div class="calendar-day-cell">
                    <span>${day}</span>
                </div>
            `;
        }
    }

    html += `</div>
        <div style="margin-top:10px; font-size:11px; color:#64748b; text-align:center;">
            💡 點擊日期可過濾
        </div>
    `;
    container.innerHTML = html;
}

function onCalendarYearMonthChange() {
    const ySelect = document.getElementById('calendar-year-select');
    const mSelect = document.getElementById('calendar-month-select');
    if (ySelect && mSelect) {
        currentSelectedYear = parseInt(ySelect.value);
        currentSelectedMonth = parseInt(mSelect.value);
        renderSingingCalendar();
    }
}

function filterByCalendarDate(dateStr) {
    switchTab('history');
    const searchInput = document.getElementById('share-search-input');
    if (searchInput) {
        searchInput.value = dateStr;
        const event = new Event('input');
        searchInput.dispatchEvent(event);
        showToast(`已過濾 ${dateStr} 開唱歌曲 (${document.querySelectorAll('#history-tbody tr:not([style*="display: none"])').length} 首)`);
    }
}

// 清空搜尋輸入框
function clearSearchInput() {
    const searchInput = document.getElementById('share-search-input');
    const clearBtn = document.getElementById('clear-search-btn');
    if (searchInput) {
        searchInput.value = '';
        const event = new Event('input');
        searchInput.dispatchEvent(event);
        searchInput.focus();
    }
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
}

// 匯出 Excel 功能
function exportToExcel() {
    if (typeof XLSX === 'undefined') {
        showToast('正在非同步載入 Excel 匯出元件...');
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js';
        script.onload = () => {
            doExportToExcel();
        };
        script.onerror = () => {
            alert('Excel 匯出元件載入失敗，請檢查網路連線！');
        };
        document.head.appendChild(script);
        return;
    }
    doExportToExcel();
}

function doExportToExcel() {
    const wb = XLSX.utils.book_new();
    
    // 1. 基本資料 Sheet
    const vtInfo = [
        ["項目", "內容"],
        ["主播姓名", vt.name_main],
        ["英文/日文名稱", vt.name_romaji || "-"],
        ["簡介", vt.description || "-"],
        ["YouTube 頻道 ID", vt.youtube_channel_id || "-"],
        ["主色調", vt.theme_color || "-"],
        ["頭像連結", vt.avatar_url || "-"],
        ["橫幅連結", vt.banner_url || "-"]
    ];
    const wsInfo = XLSX.utils.aoa_to_sheet(vtInfo);
    XLSX.utils.book_append_sheet(wb, wsInfo, "基本資料");
    
    // 2. 總歌單 Sheet
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
            }
        });
    }
    records.forEach(rec => {
        if (rec.song && !allSongsMap.has(rec.song.id)) {
            allSongsMap.set(rec.song.id, { song: rec.song, status: 'sung' });
        }
    });
    const localSortedRepertoire = Array.from(allSongsMap.values()).sort((a, b) => b.song.id - a.song.id);
    
    const repHeader = ["歌曲名稱", "原唱歌手", "屬性", "狀態標籤"];
    const repRows = localSortedRepertoire.map(item => {
        const song = item.song;
        const artists = song.artists ? song.artists.map(a => a.name_main).join(', ') : '未知';
        const isOriginal = song.artists && song.artists.some(art => art.name_main === vt.name_main) ? "原創" : "翻唱";
        let statusBadge = "已演唱過";
        if (item.status === 'signature') statusBadge = '拿手常駐歌';
        else if (item.status === 'requestable') statusBadge = '點歌歌單';
        return [song.title_main, artists, isOriginal, statusBadge];
    });
    const wsRep = XLSX.utils.aoa_to_sheet([repHeader, ...repRows]);
    XLSX.utils.book_append_sheet(wb, wsRep, "總歌單");
    
    // 3. 直播影片 Sheet
    const vidHeader = ["影片ID", "直播影片標題", "類型", "發表日期", "時間軸狀態"];
    const vidRows = videos.map(v => {
        const typeMap = {
            'stream_singing': '歌回直播',
            'stream_other': '日常直播',
            'other': '其他直播'
        };
        const typeStr = typeMap[v.video_type] || '日常直播';
        const timeline = v.has_timeline ? "已建時間軸" : "未建時間軸";
        return [v.video_id, v.title, typeStr, v.published_at || '', timeline];
    });
    const wsVid = XLSX.utils.aoa_to_sheet([vidHeader, ...vidRows]);
    XLSX.utils.book_append_sheet(wb, wsVid, "直播影片紀錄");
    
    // 4. 歷史歌回單曲 Sheet
    const histHeader = ["歌曲名稱", "原唱", "演唱組合", "出自直播影片", "演唱時間點", "備註"];
    const histRows = records.map(rec => {
        if (!rec.song) return null;
        const artists = rec.song.artists ? rec.song.artists.map(a => a.name_main).join(', ') : '未知';
        const singers = rec.singers ? rec.singers.map(s => s.name_main).join(' feat. ') : '未知';
        const timeStr = formatSeconds(rec.timestamp_seconds);
        const videoTitle = rec.video ? rec.video.title : '未知直播';
        return [rec.song.title_main, artists, singers, videoTitle, timeStr, rec.note || '-'];
    }).filter(r => r !== null);
    const wsHist = XLSX.utils.aoa_to_sheet([histHeader, ...histRows]);
    XLSX.utils.book_append_sheet(wb, wsHist, "歷史單曲演唱");
    
    // 5. 大事記 Sheet
    const actHeader = ["事件日期", "類型", "事件標題", "描述說明"];
    const actRows = (activities || []).map(act => [act.event_date, act.activity_type, act.title, act.description || '']);
    const wsAct = XLSX.utils.aoa_to_sheet([actHeader, ...actRows]);
    XLSX.utils.book_append_sheet(wb, wsAct, "大事記大事");
    
    XLSX.writeFile(wb, `${vt.name_main}_歌唱存檔資料庫.xlsx`);
}

// 主渲染流程
async function initSharePage() {
    vt = window.vtuberData || {};
    videos = window.videosData || [];
    activities = window.activitiesData || [];
    records = window.recordsData || [];

    // 若非同步載入專屬 JSON
    if ((!records || records.length === 0) && vt.id) {
        try {
            let relativePrefix = './';
            if (window.location.pathname.includes('/share/')) {
                relativePrefix = '../../';
            }
            const res = await fetch(`${relativePrefix}data/records_vtuber_${vt.id}.json`);
            if (res.ok) {
                records = await res.json();
                window.recordsData = records;
            }
        } catch(e) {
            console.log('Async fetch vtuber records fallback:', e);
        }
    }

    // 1. 綁定按鈕與面板切換
    const bioBtn = document.getElementById('tab-btn-bio');
    if (bioBtn) bioBtn.addEventListener('click', () => switchTab('bio'));

    // 2. 社群連結
    const socialContainer = document.getElementById('social-links-container');
    if (socialContainer) {
        if (vt.links && vt.links.length > 0) {
            socialContainer.innerHTML = '';
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
                socialContainer.innerHTML += `
                    <a href="${l.url}" target="_blank" class="social-icon-btn ${btnClass}" style="padding:6px 12px; font-size:11px; margin: 0;">
                        <i class="${iconClass}"></i> ${l.platform}
                    </a>
                `;
            });
        } else {
            socialContainer.innerHTML = '<span style="font-size:11.5px; color:#64748b;">暫無社群連結</span>';
        }
    }

    // 3. 最常唱歌曲與原唱 Top 5
    const songCounts = {};
    const artistCounts = {};
    records.forEach(rec => {
        if (rec.song) {
            const title = rec.song.title_main;
            songCounts[title] = (songCounts[title] || 0) + 1;
            if (rec.song.artists) {
                rec.song.artists.forEach(art => {
                    const artName = art.name_main;
                    artistCounts[artName] = (artistCounts[artName] || 0) + 1;
                });
            }
        }
    });

    const topSongsList = document.getElementById('top-songs-list');
    if (topSongsList) {
        topSongsList.innerHTML = '';
        const sortedSongs = Object.entries(songCounts)
            .map(([title, count]) => ({ title, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
            
        if (sortedSongs.length > 0) {
            sortedSongs.forEach((s, idx) => {
                topSongsList.innerHTML += `
                    <li style="display:flex; justify-content:space-between; align-items:center; font-size:12.5px; border-bottom: 1px dashed rgba(255,255,255,0.03); padding-bottom: 6px;">
                        <span><span style="color:#64748b; font-weight:700; margin-right:8px;">#${idx+1}</span> <strong style="color:var(--text-bright);">${s.title}</strong></span>
                        <span class="badge" style="font-size:10px; padding: 2px 8px; border-radius: 10px; background: rgba(var(--vtuber-active-theme), 0.08); border: 1px solid rgba(var(--vtuber-active-theme), 0.2); color: var(--vtuber-active-theme); font-weight: 700;">${s.count} 次</span>
                    </li>
                `;
            });
        } else {
            topSongsList.innerHTML = '<li style="font-size:12.5px; color:#64748b;">暫無演唱數據</li>';
        }
    }

    const topArtistsList = document.getElementById('top-artists-list');
    if (topArtistsList) {
        topArtistsList.innerHTML = '';
        const sortedArtists = Object.entries(artistCounts)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
            
        if (sortedArtists.length > 0) {
            sortedArtists.forEach((a, idx) => {
                topArtistsList.innerHTML += `
                    <li style="display:flex; justify-content:space-between; align-items:center; font-size:12.5px; border-bottom: 1px dashed rgba(255,255,255,0.03); padding-bottom: 6px;">
                        <span><span style="color:#64748b; font-weight:700; margin-right:8px;">#${idx+1}</span> <strong style="color:var(--text-bright);">${a.name}</strong></span>
                        <span class="badge" style="font-size:10px; padding: 2px 8px; border-radius: 10px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); color: #cbd5e1; font-weight: 700;">${a.count} 次</span>
                    </li>
                `;
            });
        } else {
            topArtistsList.innerHTML = '<li style="font-size:12.5px; color:#64748b;">暫無原唱歌手數據</li>';
        }
    }

    // 4. 大事記時間軸
    const timelineContainer = document.getElementById('timeline-activities-container');
    if (timelineContainer) {
        timelineContainer.innerHTML = '';
        if (activities && activities.length > 0) {
            activities.forEach(act => {
                timelineContainer.innerHTML += `
                    <div class="timeline-item ${act.activity_type}" style="padding-bottom:18px;">
                        <div class="timeline-dot"></div>
                        <div class="timeline-content" style="padding:10px 14px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                            <div class="timeline-date-row" style="margin-bottom:2px;">
                                <span>${act.event_date}</span>
                                <span class="badge ${act.activity_type === 'milestone' ? 'badge-purple' : 'badge-original'}">${act.activity_type}</span>
                            </div>
                            <div class="timeline-title" style="font-size:13px; font-weight:700; color:var(--text-bright);">${act.title}</div>
                            ${act.description ? `<div class="timeline-desc" style="font-size:11.5px; margin-top:4px; color:#94a3b8;">${act.description}</div>` : ''}
                        </div>
                    </div>
                `;
            });
        } else {
            timelineContainer.innerHTML = '<p style="text-align:center; color:#64748b; padding:20px; font-size:12.5px;">尚無大事記公告</p>';
        }
    }

    // 5. 總歌單
    const repertoireTbody = document.getElementById('repertoire-tbody');
    if (repertoireTbody) {
        repertoireTbody.innerHTML = '';
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
                }
            });
        }
        records.forEach(rec => {
            if (rec.song && !allSongsMap.has(rec.song.id)) {
                allSongsMap.set(rec.song.id, { song: rec.song, status: 'sung' });
            }
        });

        const sortedRepertoire = Array.from(allSongsMap.values()).sort((a, b) => b.song.id - a.song.id);
        const reqTabBtn = document.getElementById('tab-btn-requestable');
        if (reqTabBtn) reqTabBtn.textContent = `總歌單 (${sortedRepertoire.length})`;
        
        sortedRepertoire.forEach(item => {
            const song = item.song;
            const artists = song.artists ? song.artists.map(a => a.name_main).join(', ') : '未知';
            const isOriginal = song.artists && song.artists.some(art => art.name_main === vt.name_main);
            
            let statusBadgeHtml = '';
            if (item.status === 'signature') {
                statusBadgeHtml = '<span class="badge badge-purple">拿手常駐歌</span>';
            } else if (item.status === 'requestable') {
                statusBadgeHtml = '<span class="badge badge-original">點歌歌單</span>';
            } else {
                statusBadgeHtml = '<span class="badge badge-cover">已演唱過</span>';
            }
            
            repertoireTbody.innerHTML += `
                <tr>
                    <td style="font-weight:700; color:var(--text-bright);">${song.title_main}</td>
                    <td>${artists || '未知'}</td>
                    <td class="hide-on-mobile"><span class="badge ${isOriginal ? 'badge-original' : 'badge-cover'}">${isOriginal ? '原創' : '翻唱'}</span></td>
                    <td class="hide-on-mobile">${statusBadgeHtml}</td>
                    <td style="text-align:center;">
                        <button class="table-play-btn" onclick="searchSongInHistory('${song.title_main.replace(/'/g, "\\'")}')" title="查詢歷史紀錄">
                            <i class="fa-solid fa-magnifying-glass"></i>
                        </button>
                        <button class="table-play-btn" onclick="copySongRequest('${song.title_main.replace(/'/g, "\\'")}', '${artists.replace(/'/g, "\\'")}')" title="一鍵複製點歌指令" style="margin-left:4px; color: var(--vtuber-active-theme);">
                            <i class="fa-regular fa-copy"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    // 6. 直播影片
    const singingTbody = document.getElementById('singing-tbody');
    const liveTbody = document.getElementById('live-tbody');
    if (singingTbody && liveTbody) {
        singingTbody.innerHTML = '';
        liveTbody.innerHTML = '';
        const singingVideos = videos.filter(v => v.video_type === 'stream_singing');
        const liveVideos = videos.filter(v => v.video_type === 'stream_other' || v.video_type === 'other');
        
        const singTabBtn = document.getElementById('tab-btn-singing');
        const liveTabBtn = document.getElementById('tab-btn-live');
        if (singTabBtn) singTabBtn.textContent = `歌回直播 (${singingVideos.length})`;
        if (liveTabBtn) liveTabBtn.textContent = `日常與其他直播 (${liveVideos.length})`;

        const renderVideoRowToElement = (v, targetTbody) => {
            const thumbnail = v.thumbnail_url || `https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg`;
            const pubDate = v.published_at || '無日期';
            const timelineBadge = v.has_timeline 
                ? '<span class="badge" style="background:rgba(57, 255, 20, 0.08); border:1px solid rgba(57,255,20,0.2); color:#39ff14;">已建時間軸</span>' 
                : '<span class="badge" style="background:rgba(255, 0, 127, 0.08); border:1px solid rgba(255,0,127,0.2); color:#ff007f;">未建時間軸</span>';
            
            const typeMap = {
                'stream_singing': '歌回直播',
                'stream_other': '日常直播',
                'other': '其他直播'
            };
            const typeStr = typeMap[v.video_type] || '日常直播';

            targetTbody.innerHTML += `
                <tr>
                    <td>
                        <div class="record-thumb-container" style="width: 80px; height: 45px; margin: 0;" onclick="playRecord('${v.video_id}', 0, '${v.title.replace(/'/g, "\\'")}', '${vt.name_main.replace(/'/g, "\\'")}')">
                            <img src="${thumbnail}" alt="thumbnail" loading="lazy" decoding="async">
                            <div class="record-play-overlay"><i class="fa-solid fa-play"></i></div>
                        </div>
                    </td>
                    <td style="font-weight:700; color:var(--text-bright); max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <a href="https://www.youtube.com/watch?v=${v.video_id}" target="_blank" style="color:inherit; text-decoration:none;" title="前往 YouTube 播放">
                            ${v.title} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; opacity:0.6;"></i>
                        </a>
                    </td>
                    <td class="hide-on-mobile"><span class="badge" style="background:rgba(59,130,246,0.1); color:var(--neon-blue); border:1px solid rgba(59,130,246,0.2);">${typeStr}</span></td>
                    <td>${pubDate}</td>
                    <td class="hide-on-mobile">${timelineBadge}</td>
                </tr>
            `;
        };

        singingVideos.forEach(v => renderVideoRowToElement(v, singingTbody));
        liveVideos.forEach(v => renderVideoRowToElement(v, liveTbody));
    }

    // 7. 歷史歌回單曲
    const historyTbody = document.getElementById('history-tbody');
    if (historyTbody) {
        historyTbody.innerHTML = '';
        const histTabBtn = document.getElementById('tab-btn-history');
        if (histTabBtn) histTabBtn.textContent = `歷史歌回單曲 (${records.length})`;
        
        records.forEach(rec => {
            if (!rec.song) return;
            const artists = rec.song.artists ? rec.song.artists.map(a => a.name_main).join(', ') : '未知';
            const singers = rec.singers ? rec.singers.map(s => s.name_main).join(' feat. ') : '未知';
            const timeStr = formatSeconds(rec.timestamp_seconds);
            const videoTitle = rec.video ? rec.video.title : '未知直播';
            const recDate = (rec.video && rec.video.published_at) ? rec.video.published_at.substring(0, 10) : '';

            historyTbody.innerHTML += `
                <tr class="clickable" data-date="${recDate}" onclick="playRecord('${rec.video_id}', ${rec.timestamp_seconds}, '${rec.song.title_main.replace(/'/g, "\\'")}', '${singers.replace(/'/g, "\\'")}')">
                    <td style="font-weight:700; color:var(--text-bright);">${rec.song.title_main}</td>
                    <td>${artists}</td>
                    <td class="hide-on-mobile" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${videoTitle}</td>
                    <td><span class="badge" style="font-size:11px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#94a3b8;"><i class="fa-regular fa-calendar" style="margin-right:3px;"></i>${recDate || '-'}</span></td>
                    <td><span class="record-timestamp-tag"><i class="fa-regular fa-clock"></i> ${timeStr}</span></td>
                    <td class="hide-on-mobile">${rec.note || '-'}</td>
                    <td style="text-align:center;">
                        <button class="table-play-btn" title="在網頁內播放"><i class="fa-solid fa-circle-play" style="font-size:16px;"></i></button>
                        <button class="table-play-btn" onclick="event.stopPropagation(); openExternalYoutube('${rec.video_id}', ${rec.timestamp_seconds})" title="於 YouTube App / 新分頁開啟精確秒數" style="margin-left: 6px; opacity: 0.75;">
                            <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:12px;"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    // 8. MV 影片
    const mvTbody = document.getElementById('mv-tbody');
    const mvRecords = records.filter(rec => 
        rec.video && (rec.video.video_type === 'cover_mv' || rec.video.video_type === 'original_mv')
    );
    if (mvTbody) {
        mvTbody.innerHTML = '';
        const mvTabBtn = document.getElementById('tab-btn-mv');
        if (mvTabBtn) mvTabBtn.textContent = `MV 影片清單 (${mvRecords.length})`;
        
        mvRecords.forEach(rec => {
            if (!rec.song) return;
            const artists = rec.song.artists ? rec.song.artists.map(a => a.name_main).join(', ') : '未知';
            const singers = rec.singers ? rec.singers.map(s => s.name_main).join(' feat. ') : '未知';
            const isOriginal = rec.video.video_type === 'original_mv';

            mvTbody.innerHTML += `
                <tr class="clickable" onclick="playRecord('${rec.video_id}', ${rec.timestamp_seconds}, '${rec.song.title_main.replace(/'/g, "\\'")}', '${singers.replace(/'/g, "\\'")}')">
                    <td style="font-weight:700; color:var(--text-bright);">${rec.song.title_main}</td>
                    <td>${artists}</td>
                    <td class="hide-on-mobile" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${rec.video.title}</td>
                    <td>
                        <span class="badge ${isOriginal ? 'badge-original' : 'badge-cover'}">
                            ${isOriginal ? '原創 MV' : '翻唱 MV'}
                        </span>
                    </td>
                    <td style="text-align:center;">
                        <button class="table-play-btn" title="在網頁內播放"><i class="fa-solid fa-circle-play" style="font-size:16px;"></i></button>
                        <button class="table-play-btn" onclick="event.stopPropagation(); openExternalYoutube('${rec.video_id}', ${rec.timestamp_seconds})" title="於 YouTube App / 新分頁開啟精確秒數" style="margin-left: 6px; opacity: 0.75;">
                            <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:12px;"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    // 9. 搜尋監聽
    const searchInput = document.getElementById('share-search-input');
    const clearBtn = document.getElementById('clear-search-btn');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.toLowerCase().trim();
            if (clearBtn) {
                clearBtn.style.display = searchInput.value.trim() ? 'inline-flex' : 'none';
            }
            document.querySelectorAll('#repertoire-tbody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
            });
            document.querySelectorAll('#singing-tbody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
            });
            document.querySelectorAll('#live-tbody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
            });
            document.querySelectorAll('#history-tbody tr').forEach(row => {
                const rowText = row.textContent.toLowerCase();
                const dateAttr = row.getAttribute('data-date') || '';
                row.style.display = (rowText.includes(query) || dateAttr.includes(query)) ? '' : 'none';
            });
            document.querySelectorAll('#mv-tbody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
            });
        });
    }

    // 10. 預設載入預覽影片
    if (mvRecords && mvRecords.length > 0) {
        let defaultMv = mvRecords.find(rec => rec.video && rec.video.video_type === 'original_mv');
        if (!defaultMv) defaultMv = mvRecords[0];
        const singers = defaultMv.singers ? defaultMv.singers.map(s => s.name_main).join(' feat. ') : '未知';
        setTimeout(() => {
            playRecord(defaultMv.video_id, defaultMv.timestamp_seconds, defaultMv.song.title_main, singers, false);
        }, 500);
    }

    // 11. 歌回月曆
    renderSingingCalendar();
}

// 手機版懸浮播放器最小化 / 展開切換
function toggleFloatingPlayerMinimize() {
    const playerCard = document.querySelector('.player-card');
    if (playerCard) {
        playerCard.classList.toggle('minimized');
    }
}

// 註冊全域方法供 HTML 內建 onclick / onchange 呼叫
window.playRecord = playRecord;
window.switchTab = switchTab;
window.exportToExcel = exportToExcel;
window.searchSongInHistory = searchSongInHistory;
window.copySongRequest = copySongRequest;
window.openExternalYoutube = openExternalYoutube;
window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;
window.toggleLightboxZoom = toggleLightboxZoom;
window.renderSingingCalendar = renderSingingCalendar;
window.onCalendarYearMonthChange = onCalendarYearMonthChange;
window.filterByCalendarDate = filterByCalendarDate;
window.clearSearchInput = clearSearchInput;
window.toggleFloatingPlayerMinimize = toggleFloatingPlayerMinimize;
window.showToast = showToast;

// DOM 載入時觸發
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSharePage);
} else {
    initSharePage();
}

// 手機版捲動懸浮播放器
window.addEventListener('scroll', function() {
    if (window.innerWidth <= 1100) {
        const sidebar = document.querySelector('.sticky-sidebar');
        const playerCard = document.querySelector('.player-card');
        if (!sidebar || !playerCard) return;
        if (window.scrollY > sidebar.offsetTop + 320 && typeof activeVideoId !== 'undefined' && activeVideoId) {
            playerCard.classList.add('floating-mode');
        } else {
            playerCard.classList.remove('floating-mode');
        }
    } else {
        const playerCard = document.querySelector('.player-card');
        if (playerCard && playerCard.classList.contains('floating-mode')) {
            playerCard.classList.remove('floating-mode');
        }
    }
});
