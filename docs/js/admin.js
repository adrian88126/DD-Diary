
function formatScheduleImageUrl(rawInput) {
    if (!rawInput || !rawInput.trim()) return null;
    let val = rawInput.trim();
    // If user inputs pure 11-char Video ID (e.g. y3Vyg3nOsFA)
    if (/^[a-zA-Z0-9_-]{11}$/.test(val)) {
        return `https://img.youtube.com/vi/${val}/maxresdefault.jpg`;
    }
    // If user inputs youtube URL (e.g. https://www.youtube.com/watch?v=y3Vyg3nOsFA)
    if (val.includes('youtube.com/watch?v=')) {
        const vid = val.split('v=')[1].split('&')[0];
        return `https://img.youtube.com/vi/${vid}/maxresdefault.jpg`;
    }
    if (val.includes('youtu.be/')) {
        const vid = val.split('youtu.be/')[1].split('?')[0];
        return `https://img.youtube.com/vi/${vid}/maxresdefault.jpg`;
    }
    return val;
}

// 後台管理控制模組
import { API_BASE } from './config.js';
import { state } from './state.js';
import { showToast, scrollToElementInsideContent, formatApiError, formatSeconds } from './ui.js';
import { deleteRecordOnServer, fetchAllData } from './api.js';
import { switchView, renderCatalog, renderVtuberCatalog, loadSidebarVtubers, loadDashboardData, loadVtuberProfile } from './portal.js';

export function loadAdminVtubers() {
    const tbody = document.getElementById('admin-vtubers-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const vtubers = state.cacheVtubers;
    if (vtubers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="sub-text" style="text-align:center; padding:20px;">暫無已收錄的 VTuber</td></tr>';
        return;
    }
    
    vtubers.forEach(vt => {
        const avatarHtml = vt.avatar_url 
            ? `<img src="${vt.avatar_url}" alt="avatar" style="width:30px; height:30px; border-radius:50%; object-fit:cover; display:block; margin:0 auto;">`
            : `<div class="vtuber-avatar-mini" style="margin:0 auto;">${vt.name_main.charAt(0)}</div>`;
            
        const namesHtml = `
            <div style="font-weight:700; color:var(--text-bright);">${vt.name_main}</div>
            <div class="sub-names" style="font-size:10.5px; opacity:0.6;">
                ${vt.name_ja ? `<span>${vt.name_ja}</span>` : ''} 
                ${vt.name_zh ? `<span>| ${vt.name_zh}</span>` : ''}
            </div>
        `;
        
        const channelLink = vt.youtube_channel_id 
            ? `<a href="https://www.youtube.com/channel/${vt.youtube_channel_id}" target="_blank" style="color:var(--neon-blue); text-decoration:none;">
                 ${vt.youtube_channel_id} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px;"></i>
               </a>`
            : '<span class="sub-text">-</span>';
            
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${avatarHtml}</td>
            <td>${namesHtml}</td>
            <td>${channelLink}</td>
            <td style="text-align:center;">
                <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; margin-right:4px;" onclick="window.editVtuber(${vt.id})"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15);" onclick="window.deleteVtuberRecord(${vt.id}, '${vt.name_main.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i> 刪除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

export function navigateToAdminPane(paneId) {
    // 隱藏所有後台 Pane
    document.querySelectorAll('.admin-tab-pane').forEach(el => el.classList.remove('active'));
    // 顯示目標後台 Pane
    const target = document.getElementById(paneId);
    if (target) target.classList.add('active');
    
    // 更新後台選單 Active 狀態
    document.querySelectorAll('.admin-nav-menu .admin-nav-item').forEach(item => {
        if (item.getAttribute('data-pane') === paneId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    if (paneId === 'admin-pane-vtuber') {
        loadAdminVtubers();
    }
}

// 7. 模糊搜尋自動完成篩選器 (Dropdown Filters)
function setupDropdownFilterVideo(inputEl, idEl, dropdownEl) {
    inputEl.addEventListener('focus', () => filterVideos());
    inputEl.addEventListener('input', () => filterVideos());
    
    function filterVideos() {
        const val = inputEl.value.trim().toLowerCase();
        const filtered = state.cacheVideos.filter(item => 
            item.title.toLowerCase().includes(val) || 
            item.video_id.toLowerCase().includes(val)
        );
        dropdownEl.innerHTML = '';
        if (filtered.length === 0) {
            dropdownEl.innerHTML = '<div class="autocomplete-item sub-text">無匹配影片</div>';
        } else {
            filtered.slice(0, 10).forEach(item => {
                const div = document.createElement('div');
                div.className = 'autocomplete-item';
                div.textContent = `${item.title} (${item.video_id})`;
                div.addEventListener('click', () => {
                    inputEl.value = item.title;
                    idEl.value = item.video_id;
                    dropdownEl.classList.remove('active');
                });
                dropdownEl.appendChild(div);
            });
        }
        dropdownEl.classList.add('active');
    }
}

function setupDropdownFilterNormal(inputElement, dropdownElement, getCacheListFn, displayFieldFn, onSelectFn) {
    if (!inputElement) return;
    
    inputElement.addEventListener('focus', () => {
        filterAndShowDropdown();
    });
    
    inputElement.addEventListener('input', () => {
        filterAndShowDropdown();
    });
    
    function filterAndShowDropdown() {
        const val = inputElement.value.trim().toLowerCase();
        const items = getCacheListFn();
        
        const filtered = items.filter(item => {
            const displayStr = displayFieldFn(item).toLowerCase();
            const ja = item.name_ja || item.title_ja || '';
            const zh = item.name_zh || item.title_zh || '';
            const romaji = item.name_romaji || item.title_romaji || '';
            return displayStr.includes(val) || 
                   ja.toLowerCase().includes(val) || 
                   zh.toLowerCase().includes(val) || 
                   romaji.toLowerCase().includes(val);
        });
        
        dropdownElement.innerHTML = '';
        
        if (filtered.length === 0) {
            dropdownElement.innerHTML = '<div class="autocomplete-item sub-text">無匹配項目</div>';
        } else {
            filtered.slice(0, 10).forEach(item => {
                const div = document.createElement('div');
                div.className = 'autocomplete-item';
                div.textContent = displayFieldFn(item);
                div.addEventListener('click', () => {
                    onSelectFn(item);
                    dropdownElement.classList.remove('active');
                });
                dropdownElement.appendChild(div);
            });
        }
        dropdownElement.classList.add('active');
    }
}

function setupDropdownFilterArtist(inputElement, dropdownElement, getCacheListFn, onSelectFn) {
    inputElement.addEventListener('focus', () => filterAndShowDropdown());
    inputElement.addEventListener('input', () => filterAndShowDropdown());
    
    async function filterAndShowDropdown() {
        const val = inputElement.value.trim();
        const valLower = val.toLowerCase();
        const items = getCacheListFn();
        
        const filtered = items.filter(item => {
            const name = item.name_main.toLowerCase();
            const ja = (item.name_ja || '').toLowerCase();
            const zh = (item.name_zh || '').toLowerCase();
            const romaji = (item.name_romaji || '').toLowerCase();
            return name.includes(valLower) || ja.includes(valLower) || zh.includes(valLower) || romaji.includes(valLower);
        });
        
        dropdownElement.innerHTML = '';
        
        filtered.slice(0, 8).forEach(item => {
            const div = document.createElement('div');
            div.className = 'autocomplete-item';
            div.textContent = item.name_main;
            div.addEventListener('click', () => {
                onSelectFn(item);
                dropdownElement.classList.remove('active');
            });
            dropdownElement.appendChild(div);
        });
        
        if (val) {
            const existsExact = items.some(item => item.name_main.toLowerCase() === valLower);
            if (!existsExact) {
                const div = document.createElement('div');
                div.className = 'autocomplete-item';
                div.style.cssText = 'color: var(--neon-blue); font-weight: 700; border-top: 1px solid rgba(255,255,255,0.05);';
                div.innerHTML = `<i class="fa-solid fa-plus-circle"></i> 新增 "${val}" 為新原唱歌手`;
                
                div.addEventListener('click', async () => {
                    dropdownElement.classList.remove('active');
                    try {
                        const response = await fetch(`${API_BASE}/artists/`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name_main: val })
                        });
                        
                        if (response.ok) {
                            const newArtist = await response.json();
                            showToast(`已在背景成功為您建立歌手「${newArtist.name_main}」！`);
                            state.cacheArtists.push(newArtist);
                            onSelectFn(newArtist);
                        } else {
                            showToast('快速建立歌手失敗', 'error');
                        }
                    } catch (error) {
                        showToast('連線失敗', 'error');
                    }
                });
                dropdownElement.appendChild(div);
            }
        }
        dropdownElement.classList.add('active');
    }
}

export function setupAutocompleteSelects() {
    const artSearch = document.getElementById('song-artists-search');
    const artDropdown = document.getElementById('song-artists-dropdown');
    
    if (artSearch && artDropdown) {
        setupDropdownFilterArtist(artSearch, artDropdown, () => state.cacheArtists, (selectedItem) => {
            if (!state.selectedArtists.some(a => a.id === selectedItem.id)) {
                state.selectedArtists.push(selectedItem);
                renderSelectedArtistsTags();
            }
            artSearch.value = '';
        });
    }

    const recordVideoSearch = document.getElementById('record-video-search');
    const recordVideoId = document.getElementById('record-video-id');
    const recordVideoDropdown = document.getElementById('record-video-dropdown');
    if (recordVideoSearch && recordVideoDropdown) {
        setupDropdownFilterVideo(recordVideoSearch, recordVideoId, recordVideoDropdown);
    }

    const assocSongSearch = document.getElementById('assoc-song-search');
    const assocSongId = document.getElementById('assoc-song-id');
    const assocSongDropdown = document.getElementById('assoc-song-dropdown');
    if (assocSongSearch && assocSongDropdown) {
        setupDropdownFilterNormal(assocSongSearch, assocSongDropdown, () => state.cacheSongs, (item) => item.title_main, (selectedItem) => {
            assocSongSearch.value = selectedItem.title_main;
            assocSongId.value = selectedItem.id;
        });
    }

    const videoSongSearch = document.getElementById('video-song-search');
    const videoSongId = document.getElementById('video-song-id');
    const videoSongDropdown = document.getElementById('video-song-dropdown');
    if (videoSongSearch && videoSongDropdown) {
        setupDropdownFilterNormal(videoSongSearch, videoSongDropdown, () => state.cacheSongs, (item) => item.title_main, (selectedItem) => {
            videoSongSearch.value = selectedItem.title_main;
            videoSongId.value = selectedItem.id;
        });
    }

    // 編輯歌唱紀錄 Modal
    const editRecSongSearch = document.getElementById('edit-rec-song-search');
    const editRecSongId = document.getElementById('edit-rec-song-id');
    const editRecSongDropdown = document.getElementById('edit-rec-song-dropdown');
    if (editRecSongSearch && editRecSongDropdown) {
        setupDropdownFilterNormal(editRecSongSearch, editRecSongDropdown, () => state.cacheSongs, (item) => item.title_main, (selectedItem) => {
            editRecSongSearch.value = selectedItem.title_main;
            editRecSongId.value = selectedItem.id;
            
            const editSongBtn = document.getElementById('btn-edit-rec-song');
            if (editSongBtn) editSongBtn.disabled = false;
        });
        
        editRecSongSearch.addEventListener('input', (e) => {
            if (!e.target.value.trim()) {
                editRecSongId.value = '';
                const editSongBtn = document.getElementById('btn-edit-rec-song');
                if (editSongBtn) editSongBtn.disabled = true;
            }
        });
    }

    const editRecVideoSearch = document.getElementById('edit-rec-video-search');
    const editRecVideoId = document.getElementById('edit-rec-video-id');
    const editRecVideoDropdown = document.getElementById('edit-rec-video-dropdown');
    if (editRecVideoSearch && editRecVideoDropdown) {
        setupDropdownFilterVideo(editRecVideoSearch, editRecVideoId, editRecVideoDropdown);
    }

    // 編輯影音 Modal 的歌曲自動完成
    const editVideoSongSearch = document.getElementById('edit-video-song-search');
    const editVideoSongId = document.getElementById('edit-video-song-id');
    const editVideoSongDropdown = document.getElementById('edit-video-song-dropdown');
    if (editVideoSongSearch && editVideoSongDropdown) {
        setupDropdownFilterNormal(editVideoSongSearch, editVideoSongDropdown, () => state.cacheSongs, (item) => item.title_main, (selectedItem) => {
            editVideoSongSearch.value = selectedItem.title_main;
            editVideoSongId.value = selectedItem.id;
        });
    }

    // 歷史演唱紀錄編輯 Modal 的歌手 Tag 自動完成
    const editRecSingersSearch = document.getElementById('edit-rec-singers-search');
    const editRecSingersDropdown = document.getElementById('edit-rec-singers-dropdown');
    if (editRecSingersSearch && editRecSingersDropdown) {
        setupDropdownFilterNormal(editRecSingersSearch, editRecSingersDropdown, () => state.cacheVtubers, (item) => item.name_main, (selectedItem) => {
            if (!state.editRecSelectedSingers.some(s => s.id === selectedItem.id)) {
                state.editRecSelectedSingers.push(selectedItem);
                renderEditRecSingersTags();
            }
            editRecSingersSearch.value = '';
        });
    }

    // 歌曲編輯燈箱
    const editSongArtistsSearch = document.getElementById('edit-song-artists-search');
    const editSongArtistsDropdown = document.getElementById('edit-song-artists-dropdown');
    if (editSongArtistsSearch && editSongArtistsDropdown) {
        setupDropdownFilterArtist(editSongArtistsSearch, editSongArtistsDropdown, () => state.cacheArtists, (selectedItem) => {
            if (!state.editSongSelectedArtists.some(a => a.id === selectedItem.id)) {
                state.editSongSelectedArtists.push(selectedItem);
                renderEditSongArtistsTags();
            }
            editSongArtistsSearch.value = '';
        });
    }

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.searchable-select-container')) {
            document.querySelectorAll('.autocomplete-dropdown').forEach(el => el.classList.remove('active'));
        }
    });
}

// 歌手 Tag 渲染與控制
export function renderSelectedArtistsTags() {
    const container = document.getElementById('song-selected-artists-tags');
    if (!container) return;
    container.innerHTML = '';
    state.selectedArtists.forEach(art => {
        const tag = document.createElement('span');
        tag.className = 'artist-tag';
        tag.innerHTML = `
            <span>${art.name_main}</span>
            <i class="fa-solid fa-xmark remove-btn" onclick="window.removeArtist(${art.id})"></i>
        `;
        container.appendChild(tag);
    });
}

window.removeArtist = function(artistId) {
    state.selectedArtists = state.selectedArtists.filter(a => a.id !== artistId);
    renderSelectedArtistsTags();
};

export function renderEditSongArtistsTags() {
    const container = document.getElementById('edit-song-selected-artists-tags');
    if (!container) return;
    container.innerHTML = '';
    state.editSongSelectedArtists.forEach(art => {
        const tag = document.createElement('span');
        tag.className = 'artist-tag';
        tag.innerHTML = `
            <span>${art.name_main}</span>
            <i class="fa-solid fa-xmark remove-btn" onclick="window.removeEditSongArtist(${art.id})"></i>
        `;
        container.appendChild(tag);
    });
}

window.removeEditSongArtist = function(artistId) {
    state.editSongSelectedArtists = state.editSongSelectedArtists.filter(a => a.id !== artistId);
    renderEditSongArtistsTags();
};

export function renderEditRecSingersTags() {
    const container = document.getElementById('edit-rec-selected-singers-tags');
    if (!container) return;
    container.innerHTML = '';
    state.editRecSelectedSingers.forEach(vt => {
        const tag = document.createElement('span');
        tag.className = 'artist-tag';
        tag.innerHTML = `
            <span>${vt.name_main}</span>
            <i class="fa-solid fa-xmark remove-btn" onclick="window.removeEditRecSinger(${vt.id})"></i>
        `;
        container.appendChild(tag);
    });
}

window.removeEditRecSinger = function(vtId) {
    state.editRecSelectedSingers = state.editRecSelectedSingers.filter(s => s.id !== vtId);
    renderEditRecSingersTags();
};

// 6 大編輯燈箱開啟/回填與關閉邏輯
window.editSong = function(songId) {
    const song = state.cacheSongs.find(s => s.id === songId);
    if (!song) return;
    
    document.getElementById('edit-song-id-modal').value = song.id;
    document.getElementById('edit-song-display-id').textContent = song.id;
    document.getElementById('edit-song-title-main').value = song.title_main;
    document.getElementById('edit-song-title-ja').value = song.title_ja || '';
    document.getElementById('edit-song-title-zh').value = song.title_zh || '';
    document.getElementById('edit-song-title-romaji').value = song.title_romaji || '';
    document.getElementById('edit-song-type').value = song.song_type || 'cover';
    
    state.editSongSelectedArtists = song.artists ? [...song.artists] : [];
    renderEditSongArtistsTags();
    
    const modal = document.getElementById('edit-song-modal');
    if (modal) modal.classList.add('active');
};

window.closeEditSongModal = function() {
    const modal = document.getElementById('edit-song-modal');
    if (modal) modal.classList.remove('active');
    const form = document.getElementById('form-edit-song-modal');
    if (form) form.reset();
    state.editSongSelectedArtists = [];
    renderEditSongArtistsTags();
};

window.editArtist = function(artistId) {
    const artist = state.cacheArtists.find(a => a.id === artistId);
    if (!artist) return;
    
    document.getElementById('edit-artist-id-modal').value = artist.id;
    document.getElementById('edit-artist-display-id').textContent = artist.id;
    document.getElementById('edit-artist-name-main').value = artist.name_main;
    document.getElementById('edit-artist-name-ja').value = artist.name_ja || '';
    document.getElementById('edit-artist-name-zh').value = artist.name_zh || '';
    document.getElementById('edit-artist-name-romaji').value = artist.name_romaji || '';
    
    const modal = document.getElementById('edit-artist-modal');
    if (modal) modal.classList.add('active');
};

window.closeEditArtistModal = function() {
    const modal = document.getElementById('edit-artist-modal');
    if (modal) modal.classList.remove('active');
    const form = document.getElementById('form-edit-artist-modal');
    if (form) form.reset();
};

window.editVtuber = function(vtuberId) {
    const vt = state.cacheVtubers.find(v => v.id === vtuberId);
    if (!vt) return;
    
    document.getElementById('edit-vtuber-id').value = vt.id;
    document.getElementById('vtuber-name-main').value = vt.name_main;
    document.getElementById('vtuber-name-ja').value = vt.name_ja || '';
    document.getElementById('vtuber-name-zh').value = vt.name_zh || '';
    document.getElementById('vtuber-name-romaji').value = vt.name_romaji || '';
    document.getElementById('vtuber-youtube').value = vt.youtube_channel_id || '';
    document.getElementById('vtuber-avatar-url').value = vt.avatar_url || '';
    document.getElementById('vtuber-theme-color').value = vt.theme_color || '';
    document.getElementById('vtuber-banner-url').value = vt.banner_url || '';
    if (document.getElementById('vtuber-schedule-image-url')) {
        document.getElementById('vtuber-schedule-image-url').value = vt.schedule_image_url || '';
    }
    if (document.getElementById('edit-vtuber-schedule-image-url')) {
        document.getElementById('edit-vtuber-schedule-image-url').value = vt.schedule_image_url || '';
    }
    document.getElementById('vtuber-desc').value = vt.description || '';
    
    document.getElementById('form-vtuber-title-header').innerHTML = '<i class="fa-solid fa-user-pen neon-text-purple"></i> 編輯 VTuber 主播';
    const submitBtn = document.getElementById('btn-vtuber-submit');
    submitBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> 儲存修改';
    document.getElementById('btn-vtuber-cancel-edit').style.display = 'block';
    
    navigateToAdminPane('admin-pane-vtuber');
    
    const vtuberForm = document.getElementById('form-create-vtuber');
    if (vtuberForm) {
        vtuberForm.scrollIntoView({ behavior: 'smooth' });
    }
};

window.closeEditVtuberModal = function() {
    const modal = document.getElementById('edit-vtuber-modal');
    if (modal) modal.classList.remove('active');
    const form = document.getElementById('form-edit-vtuber-modal');
    if (form) form.reset();
};

window.editVideo = function(videoId) {
    const video = state.cacheVideos.find(v => v.video_id === videoId);
    if (!video) return;
    
    const vtSelect = document.getElementById('edit-video-vtuber-id');
    if (vtSelect) {
        vtSelect.innerHTML = '<option value="">-- 請選擇主播 --</option>';
        state.cacheVtubers.forEach(vt => {
            const opt = document.createElement('option');
            opt.value = vt.id;
            opt.textContent = vt.name_main;
            vtSelect.appendChild(opt);
        });
    }
    
    document.getElementById('edit-video-id-modal').value = video.video_id;
    document.getElementById('edit-video-display-id').textContent = video.video_id;
    document.getElementById('edit-video-vtuber-id').value = video.vtuber_id || '';
    document.getElementById('edit-video-title').value = video.title;
    document.getElementById('edit-video-type').value = video.video_type || 'stream_singing';
    document.getElementById('edit-video-published').value = video.published_at || '';
    document.getElementById('edit-video-thumb').value = video.thumbnail_url || '';
    
    // 檢查是否有已綁定的歌曲紀錄 (如 MV)
    const existingRec = state.cacheRecords.find(r => r.video_id === video.video_id);
    const songSearchInput = document.getElementById('edit-video-song-search');
    const songIdInput = document.getElementById('edit-video-song-id');
    if (songSearchInput && songIdInput) {
        if (existingRec && existingRec.song) {
            songSearchInput.value = existingRec.song.title_main;
            songIdInput.value = existingRec.song.id;
        } else {
            songSearchInput.value = '';
            songIdInput.value = '';
        }
    }

    const modal = document.getElementById('edit-video-modal');
    if (modal) modal.classList.add('active');
};

window.closeEditVideoModal = function() {
    const modal = document.getElementById('edit-video-modal');
    if (modal) modal.classList.remove('active');
    const form = document.getElementById('form-edit-video-modal');
    if (form) form.reset();
};

window.editHistoryRecord = async function(recordId) {
    const record = state.cacheRecords.find(r => r.id === recordId);
    if (!record) {
        showToast('找不到該筆演唱紀錄！', 'error');
        return;
    }
    
    document.getElementById('edit-rec-id').value = record.id;
    document.getElementById('edit-rec-display-id').textContent = record.id;
    document.getElementById('edit-rec-song-id').value = record.song ? record.song.id : '';
    document.getElementById('edit-rec-song-search').value = record.song ? record.song.title_main : '';
    document.getElementById('edit-rec-video-id').value = record.video_id;
    document.getElementById('edit-rec-video-search').value = record.video ? record.video.title : record.video_id;
    document.getElementById('edit-rec-timestamp').value = record.timestamp_seconds;
    document.getElementById('edit-rec-note').value = record.note || '';
    
    const editSongBtn = document.getElementById('btn-edit-rec-song');
    if (editSongBtn) {
        editSongBtn.disabled = !record.song;
    }
    
    state.editRecSelectedSingers = record.singers ? [...record.singers] : [];
    renderEditRecSingersTags();
    
    const modal = document.getElementById('edit-record-modal');
    if (modal) modal.classList.add('active');
};

window.closeEditRecordModal = function() {
    const modal = document.getElementById('edit-record-modal');
    if (modal) modal.classList.remove('active');
    const editRecordForm = document.getElementById('form-edit-record');
    if (editRecordForm) editRecordForm.reset();
    state.editRecSelectedSingers = [];
    renderEditRecSingersTags();
    
    const editSongBtn = document.getElementById('btn-edit-rec-song');
    if (editSongBtn) editSongBtn.disabled = true;
};

window.editActivity = function(actId) {
    const act = state.cacheActivities.find(a => a.id === actId);
    if (!act) return;
    
    const vtSelect = document.getElementById('edit-activity-vtuber-id');
    if (vtSelect) {
        vtSelect.innerHTML = '<option value="">-- 全域公告 --</option>';
        state.cacheVtubers.forEach(vt => {
            const opt = document.createElement('option');
            opt.value = vt.id;
            opt.textContent = vt.name_main;
            vtSelect.appendChild(opt);
        });
    }
    
    document.getElementById('edit-activity-id-modal').value = act.id;
    document.getElementById('edit-activity-display-id').textContent = act.id;
    document.getElementById('edit-activity-title').value = act.title;
    document.getElementById('edit-activity-vtuber-id').value = act.vtuber_id || '';
    document.getElementById('edit-activity-type').value = act.activity_type || 'milestone';
    document.getElementById('edit-activity-date').value = act.event_date || '';
    document.getElementById('edit-activity-link').value = act.link_url || '';
    document.getElementById('edit-activity-desc').value = act.description || '';
    
    const modal = document.getElementById('edit-activity-modal');
    if (modal) modal.classList.add('active');
};

window.closeEditActivityModal = function() {
    const modal = document.getElementById('edit-activity-modal');
    if (modal) modal.classList.remove('active');
    const form = document.getElementById('form-edit-activity-modal');
    if (form) form.reset();
};

// 刪除數據流程
window.deleteSongRecord = async function(id, name) {
    if (!confirm(`確定要刪除歌曲「${name}」嗎？這將會同步清除關聯的演唱紀錄！`)) return;
    const ok = await deleteRecordOnServer('songs', id);
    if (ok) {
        showToast('歌曲已成功刪除');
        await fetchAllData();
        renderCatalog();
        loadDashboardData();
    } else {
        showToast('刪除失敗', 'error');
    }
};

window.deleteArtistRecord = async function(id, name) {
    if (!confirm(`確定要刪除原著歌手「${name}」嗎？`)) return;
    const ok = await deleteRecordOnServer('artists', id);
    if (ok) {
        showToast('歌手已成功刪除');
        await fetchAllData();
        renderCatalog();
        loadDashboardData();
    } else {
        showToast('刪除失敗，該歌手可能已有歌曲關聯。', 'error');
    }
};

window.deleteVtuberRecord = async function(id, name) {
    if (!confirm(`確定要刪除 VTuber 「${name}」嗎？這將會同步刪除該主播的所有影音存檔與演唱歷史！`)) return;
    const ok = await deleteRecordOnServer('vtubers', id);
    if (ok) {
        showToast('主播資料已刪除');
        
        const editId = document.getElementById('edit-vtuber-id').value;
        if (editId && parseInt(editId) === id) {
            document.getElementById('edit-vtuber-id').value = '';
            document.getElementById('form-create-vtuber').reset();
            document.getElementById('form-vtuber-title-header').innerHTML = '<i class="fa-solid fa-user-plus neon-text-purple"></i> 登錄/編輯 VTuber 主播';
            document.getElementById('btn-vtuber-submit').innerHTML = '<i class="fa-solid fa-plus"></i> 登錄 VTuber';
            document.getElementById('btn-vtuber-cancel-edit').style.display = 'none';
        }
        
        await fetchAllData();
        loadSidebarVtubers();
        populateAdminDropdowns();
        renderVtuberCatalog();
        loadDashboardData();
        loadAdminVtubers();
    } else {
        showToast('刪除失敗', 'error');
    }
};

window.deleteVideoRecord = async function(id, name) {
    if (!confirm(`確定要刪除已登記影音「${name}」嗎？其下的時間軸歷史也將會一併清除！`)) return;
    const ok = await deleteRecordOnServer('videos', id);
    if (ok) {
        showToast('影片已成功刪除');
        await fetchAllData();
        renderCatalog();
        loadDashboardData();
    } else {
        showToast('刪除失敗', 'error');
    }
};

window.deleteHistoryRecord = async function(id, name) {
    if (!confirm(`確定要刪除這筆歌曲「${name}」的歷史演唱時間軸紀錄嗎？`)) return;
    const ok = await deleteRecordOnServer('records', id);
    if (ok) {
        showToast('演唱紀錄已成功刪除');
        await fetchAllData();
        renderCatalog();
        loadDashboardData();
    } else {
        showToast('刪除失敗', 'error');
    }
};

window.deleteActivityRecord = async function(id, name) {
    if (!confirm(`確定要刪除公告「${name}」嗎？`)) return;
    const ok = await deleteRecordOnServer('activities', id);
    if (ok) {
        showToast('公告與里程碑已刪除');
        await fetchAllData();
        renderCatalog();
        loadDashboardData();
    } else {
        showToast('刪除失敗', 'error');
    }
};

// 影片類型動態更新
window.updateVideoType = async function(videoId, newType) {
    try {
        const response = await fetch(`${API_BASE}/videos/${videoId}/type?video_type=${newType}`, {
            method: 'PATCH'
        });
        
        if (response.ok) {
            showToast('影片類型更新成功');
            await fetchAllData();
        } else {
            showToast('影片類型更新失敗', 'error');
        }
    } catch (error) {
        showToast('連線失敗', 'error');
    }
};

// 🎙 動態多曲目時間軸登錄 (Setlist Rows Manager & Autocomplete)
export function addSetlistRow(defaultSongId = null, defaultSongTitle = '') {
    const container = document.getElementById('setlist-rows-container');
    if (!container) return null;
    
    const row = document.createElement('div');
    row.className = 'setlist-row';
    row.style.cssText = 'display: grid; grid-template-columns: 1.3fr 0.8fr 1.3fr 1fr auto; gap: 14px; align-items: start; margin-bottom: 14px; background: rgba(255,255,255,0.015); border: 1px solid var(--border-color); padding: 18px; border-radius: 14px;';
    
    row.innerHTML = `
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11.5px; color:#64748b;">選擇歌曲 <span class="required">*</span></label>
            <div class="searchable-select-container">
                <input type="text" class="row-song-search" placeholder="搜尋並點選歌曲..." autocomplete="off" value="${defaultSongTitle}">
                <input type="hidden" class="row-song-id" value="${defaultSongId || ''}">
                <div class="autocomplete-dropdown"></div>
            </div>
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11.5px; color:#64748b;">時間軸 (HH:MM:SS 或 MM:SS) <span class="required">*</span></label>
            <input type="text" class="row-timestamp" placeholder="例如 01:23:45" value="00:00:00" style="font-family:monospace; font-weight:600;" required>
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11.5px; color:#64748b;">演唱主播 (打字搜尋選取) <span class="required">*</span></label>
            <div class="searchable-select-container">
                <input type="text" class="row-singers-search" placeholder="搜尋主播..." autocomplete="off">
                <div class="autocomplete-dropdown"></div>
            </div>
            <div class="selected-tags-container" style="display:flex; flex-wrap:wrap; gap:5px; margin-top:6px;"></div>
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11.5px; color:#64748b;">演唱備註 (選填)</label>
            <input type="text" class="row-note" placeholder="例如 Acapella, 聯動合唱">
        </div>
        <button type="button" class="btn btn-secondary btn-remove-row" style="margin-top: 21px; padding: 10px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15); height: 42px;" title="刪除此列"><i class="fa-solid fa-trash-can"></i></button>
    `;
    
    container.appendChild(row);
    
    let rowSelectedSingers = [];
    
    const songInput = row.querySelector('.row-song-search');
    const songIdHidden = row.querySelector('.row-song-id');
    const songDropdown = row.querySelector('.row-song-search + input + .autocomplete-dropdown');
    
    setupDropdownFilterNormal(songInput, songDropdown, () => state.cacheSongs, (item) => item.title_main, (selectedItem) => {
        songInput.value = selectedItem.title_main;
        songIdHidden.value = selectedItem.id;
    });
    
    const singerInput = row.querySelector('.row-singers-search');
    const singerDropdown = row.querySelector('.row-singers-search + .autocomplete-dropdown');
    const tagsContainer = row.querySelector('.selected-tags-container');
    
    function renderRowTags() {
        tagsContainer.innerHTML = '';
        rowSelectedSingers.forEach(vt => {
            const tag = document.createElement('span');
            tag.className = 'selected-tag-pill singer-tag';
            tag.style.cssText = 'padding: 2px 8px; font-size:11px; margin-top:2px;';
            tag.innerHTML = `
                ${vt.name_main}
                <button type="button" class="tag-remove-btn" style="font-size:10px;">&times;</button>
            `;
            tag.querySelector('.tag-remove-btn').addEventListener('click', () => {
                rowSelectedSingers = rowSelectedSingers.filter(v => v.id !== vt.id);
                renderRowTags();
            });
            tagsContainer.appendChild(tag);
        });
    }
    
    setupDropdownFilterNormal(singerInput, singerDropdown, () => state.cacheVtubers, (item) => item.name_main, (selectedItem) => {
        if (!rowSelectedSingers.some(v => v.id === selectedItem.id)) {
            rowSelectedSingers.push(selectedItem);
            renderRowTags();
        }
        singerInput.value = '';
    });
    
    row.querySelector('.btn-remove-row').addEventListener('click', () => {
        if (container.querySelectorAll('.setlist-row').length > 1) {
            row.remove();
        } else {
            showToast('請至少保留一首曲目列！', 'error');
        }
    });
    
    row.getSingers = () => rowSelectedSingers;
    row.setSingers = (list) => {
        rowSelectedSingers = list;
        renderRowTags();
    };
    
    return row;
}

export function parseTimeToSeconds(timeStr) {
    if (!timeStr) return 0;
    const parts = timeStr.trim().split(':').map(Number);
    if (parts.some(isNaN)) return 0;
    if (parts.length === 3) {
        return (parts[0] * 3600) + (parts[1] * 60) + parts[2];
    } else if (parts.length === 2) {
        return (parts[0] * 60) + parts[1];
    } else if (parts.length === 1) {
        return parts[0];
    }
    return 0;
}

export function formatTimeToHHMMSS(timeStr) {
    const parts = timeStr.split(':');
    if (parts.length === 2) {
        return `00:${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`;
    } else if (parts.length === 3) {
        return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}:${parts[2].padStart(2, '0')}`;
    }
    return '00:00:00';
}

// 彙整歌單彈出視窗工作流
window.curateSetlist = function(videoId, videoTitle) {
    const modal = document.getElementById('curate-setlist-modal');
    if (!modal) return;
    
    document.getElementById('curate-video-title-display').value = videoTitle;
    document.getElementById('curate-video-id').value = videoId;
    
    const container = document.getElementById('curate-rows-container');
    if (container) {
        container.innerHTML = '';
    }
    
    const row = addCurateSetlistRow();
    
    if (state.selectedVtuberId) {
        const currentVt = state.cacheVtubers.find(v => v.id == state.selectedVtuberId);
        if (currentVt && row) {
            row.setSingers([currentVt]);
        }
    }
    
    modal.classList.add('active');
    showToast(`已為您自動帶入直播影音《${videoTitle}》與預設歌手！`);
};

// 一鍵導出原唱未指派 (未知) 的歌曲為 Excel
export async function exportUnassignedSongs() {
    let unknownSongs = [];
    
    // 優先從 API 或 Cache 獲取未指派原唱的歌曲
    try {
        const res = await fetch(`${API_BASE}/diagnostics/unknown_songs`);
        if (res.ok) {
            unknownSongs = await res.json();
        } else {
            unknownSongs = (state.cacheSongs || []).filter(s => 
                !s.artists || s.artists.length === 0 || s.artists.some(a => a.name_main === '未知')
            );
        }
    } catch (e) {
        unknownSongs = (state.cacheSongs || []).filter(s => 
            !s.artists || s.artists.length === 0 || s.artists.some(a => a.name_main === '未知')
        );
    }

    if (!unknownSongs || unknownSongs.length === 0) {
        showToast('目前所有歌曲均已指派原唱，沒有未指派的歌曲！', 'success');
        return;
    }

    // 若 SheetJS (XLSX) 尚未載入則非同步載入
    if (typeof XLSX === 'undefined') {
        showToast('正在非同步載入 Excel 導出模組...', 'warning');
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js';
        script.onload = () => {
            doExportUnassignedSongs(unknownSongs);
        };
        script.onerror = () => {
            showToast('Excel 導出模組載入失敗，請檢查網路連線！', 'error');
        };
        document.head.appendChild(script);
    } else {
        doExportUnassignedSongs(unknownSongs);
    }
}

function doExportUnassignedSongs(unknownSongs) {
    const wb = XLSX.utils.book_new();
    const header = ["歌曲 ID", "主要歌名", "羅馬字 / 別名", "目前歌手紀錄", "建立時間"];
    const rows = unknownSongs.map(song => {
        const artistsStr = song.artists ? song.artists.map(a => a.name_main).join(', ') : '未知';
        return [
            song.id,
            song.title_main,
            song.title_romaji || '-',
            artistsStr,
            song.created_at || '-'
        ];
    });

    const ws = XLSX.utils.aoa_to_sheet([header, ...rows]);
    XLSX.utils.book_append_sheet(wb, ws, "未指派原唱歌曲");
    const dateStr = new Date().toISOString().substring(0, 10);
    XLSX.writeFile(wb, `原唱未指派歌曲清單_${dateStr}.xlsx`);
    showToast(`🎉 成功導出 ${unknownSongs.length} 筆原唱未指派的歌曲資料！`, 'success');
}

// 缺漏數據診斷大廳與重複比對
export async function runSongNameDiagnostics() {
    const unknownList = document.getElementById('unknown-artists-list');
    const duplicateList = document.getElementById('duplicate-songs-list');
    
    if (!unknownList && !duplicateList) return;
    
    if (unknownList) unknownList.innerHTML = '<div class="loading-spinner-small"></div> 診斷中...';
    if (duplicateList) duplicateList.innerHTML = '<div class="loading-spinner-small"></div> 診斷中...';
    
    try {
        const [diagnoseRes, duplicatesRes, duplicateArtistsRes] = await Promise.all([
            fetch(`${API_BASE}/diagnostics/unknown_songs`),
            fetch(`${API_BASE}/diagnostics/duplicate_songs`),
            fetch(`${API_BASE}/diagnostics/duplicate_artists`)
        ]);
        
        const unknownSongs = await diagnoseRes.json();
        const duplicates = await duplicatesRes.json();
        const duplicateArtists = await duplicateArtistsRes.json();
        
        if (unknownList) {
            unknownList.innerHTML = '';
            if (unknownSongs.length === 0) {
                unknownList.innerHTML = '<div style="color:var(--neon-green); font-weight:700; padding:10px;"><i class="fa-solid fa-circle-check"></i> 完美診斷！所有歌曲均已指派原唱。</div>';
            } else {
                unknownSongs.forEach(song => {
                    const row = document.createElement('div');
                    row.className = 'diagnose-row';
                    row.style.cssText = 'display:flex; justify-content:space-between; align-items:center; gap:10px; background:rgba(255,255,255,0.02); padding:8px 12px; border-radius:8px; border:1px solid rgba(255,255,255,0.04); margin-bottom:6px;';
                    row.innerHTML = `
                        <div style="font-weight:700; color:var(--text-bright); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1;">
                            ${song.title_main} <span class="badge" style="font-size:10px; opacity:0.6;">ID: ${song.id}</span>
                        </div>
                        <div class="searchable-select-container" style="width: 200px; position:relative; flex-shrink:0;">
                            <input type="text" class="form-input-sm" id="diag-art-search-${song.id}" placeholder="🔍 搜尋歌手一鍵綁定..." style="font-size:11px; padding:4px 8px; width:100%; border-radius:6px;">
                            <div class="autocomplete-dropdown" id="diag-art-drop-${song.id}"></div>
                        </div>
                    `;
                    unknownList.appendChild(row);
                    
                    setTimeout(() => {
                        const input = document.getElementById(`diag-art-search-${song.id}`);
                        const dropdown = document.getElementById(`diag-art-drop-${song.id}`);
                        if (input && dropdown) {
                            setupDropdownFilterArtist(input, dropdown, () => state.cacheArtists, async (selectedArtist) => {
                                try {
                                    const response = await fetch(`${API_BASE}/songs/${song.id}`, {
                                        method: 'PUT',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                            title_main: song.title_main,
                                            title_ja: song.title_ja,
                                            title_zh: song.title_zh,
                                            title_romaji: song.title_romaji,
                                            song_type: song.song_type,
                                            artist_ids: [selectedArtist.id]
                                        })
                                    });
                                    if (response.ok) {
                                        showToast(`歌曲《${song.title_main}》已成功關聯原唱「${selectedArtist.name_main}」！`);
                                        await fetchAllData();
                                        runSongNameDiagnostics();
                                        renderCatalog();
                                    } else {
                                        showToast('綁定失敗', 'error');
                                    }
                                } catch (e) {
                                    showToast('連線失敗', 'error');
                                }
                            });
                        }
                    }, 10);
                });
            }
        }
        
        if (duplicateList) {
            duplicateList.innerHTML = '';
            if (duplicates.length === 0) {
                duplicateList.innerHTML = '<div style="color:var(--neon-green); font-weight:700; padding:10px;"><i class="fa-solid fa-circle-check"></i> 無重複歌曲，資料健康！</div>';
            } else {
                const div = document.createElement('div');
                div.innerHTML = `
                    <div style="color:#94a3b8; font-size:11.5px; margin-bottom:10px; line-height:1.5; padding: 0 4px;">
                        💡 發現 <b>${duplicates.length}</b> 首名稱相同但 ID 不同的重複歌曲，可能導致演唱統計數據被分散。
                    </div>
                    <button class="btn btn-secondary" style="padding:6px 12px; font-size:11px; font-weight:700; width:100%; margin-bottom:12px;" onclick="window.autoLinkDuplicateSongs()">
                        <i class="fa-solid fa-link"></i> 執行一鍵同名歌曲整併關聯
                    </button>
                    <div style="margin-top:12px; max-height:180px; overflow-y:auto; display:flex; flex-direction:column; gap:4px; padding-right:4px;">
                        ${duplicates.map(s => `
                            <div style="display:flex; justify-content:space-between; font-size:11px; color:#cbd5e1; background:rgba(255,255,255,0.01); padding:4px 8px; border-radius:4px;">
                                <span>${s.title_main}</span>
                                <span style="color:#64748b;">ID: ${s.id}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
                duplicateList.appendChild(div);
            }
        }

        const duplicateArtistsList = document.getElementById('duplicate-artists-list');
        if (duplicateArtistsList) {
            duplicateArtistsList.innerHTML = '';
            if (duplicateArtists.length === 0) {
                duplicateArtistsList.innerHTML = '<div style="color:var(--neon-green); font-weight:700; padding:10px;"><i class="fa-solid fa-circle-check"></i> 無重複歌手，資料健康！</div>';
            } else {
                const div = document.createElement('div');
                div.innerHTML = `
                    <div style="color:#94a3b8; font-size:11.5px; margin-bottom:10px; line-height:1.5; padding: 0 4px;">
                        💡 發現 <b>${duplicateArtists.length}</b> 位名稱相同但 ID 不同的重複歌手，可能導致歌曲演唱歸屬不一致。
                    </div>
                    <button class="btn btn-secondary" style="padding:6px 12px; font-size:11px; font-weight:700; width:100%; margin-bottom:12px;" onclick="window.autoLinkDuplicateArtists()">
                        <i class="fa-solid fa-users-viewfinder"></i> 執行一鍵同名歌手整併關聯
                    </button>
                    <div style="margin-top:12px; max-height:180px; overflow-y:auto; display:flex; flex-direction:column; gap:4px; padding-right:4px;">
                        ${duplicateArtists.map(a => `
                            <div style="display:flex; justify-content:space-between; font-size:11px; color:#cbd5e1; background:rgba(255,255,255,0.01); padding:4px 8px; border-radius:4px;">
                                <span>${a.name_main}</span>
                                <span style="color:#64748b;">ID: ${a.id}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
                duplicateArtistsList.appendChild(div);
            }
        }
        
    } catch (e) {
        console.error('載入診斷失敗:', e);
        if (unknownList) unknownList.innerHTML = '<p class="sub-text">載入診斷失敗</p>';
        if (duplicateList) duplicateList.innerHTML = '<p class="sub-text">載入診斷失敗</p>';
    }
}

window.autoLinkDuplicateSongs = async function() {
    if (!confirm('確定要執行重複同名歌曲一鍵整併嗎？系統將比對名稱相同的歌曲，將歷史演唱紀錄統整，並清除多餘的重複歌曲。')) return;
    try {
        const response = await fetch(`${API_BASE}/diagnostics/auto_link_duplicates`, { method: 'POST' });
        if (response.ok) {
            const res = await response.json();
            showToast(`🎉 同名整併完成！成功處理 ${res.cleaned_count} 筆重複歌曲！`);
            await fetchAllData();
            runSongNameDiagnostics();
            renderCatalog();
            loadDashboardData();
        } else {
            showToast('自動整併失敗', 'error');
        }
    } catch (e) {
        showToast('連線失敗', 'error');
    }
};

window.autoLinkDuplicateArtists = async function() {
    if (!confirm('確定要執行重複同名歌手一鍵整併嗎？系統將比對名稱相同的歌手，將所有歌曲關聯統整，並清除多餘的重複歌手。')) return;
    try {
        const response = await fetch(`${API_BASE}/diagnostics/auto_link_duplicate_artists`, { method: 'POST' });
        if (response.ok) {
            const res = await response.json();
            showToast(`🎉 同名整併完成！成功處理 ${res.cleaned_count} 位重複歌手！`);
            await fetchAllData();
            runSongNameDiagnostics();
            renderCatalog();
            loadDashboardData();
        } else {
            const err = await response.json();
            showToast(`整併失敗: ${formatApiError(err)}`, 'error');
        }
    } catch (e) {
        showToast('連線失敗', 'error');
    }
};

// 綁定後台大廳表單與燈箱按鈕事件監聽器




let linksAdminActiveLinks = [];

function setupLinksAdminPane() {
    const vtSelect = document.getElementById('admin-links-vtuber-select');
    const editorArea = document.getElementById('admin-links-editor-area');
    const currentListDiv = document.getElementById('admin-links-current-list');
    
    const platformSelect = document.getElementById('admin-links-platform-select');
    const platformCustomGroup = document.getElementById('admin-links-platform-custom-group');
    const platformCustomInput = document.getElementById('admin-links-platform-custom');
    const urlInput = document.getElementById('admin-links-url');
    
    const btnAddSingle = document.getElementById('btn-admin-links-add-single');
    const bulkTextarea = document.getElementById('admin-links-bulk-textarea');
    const btnParseBulk = document.getElementById('btn-admin-links-parse-bulk');
    const btnSave = document.getElementById('btn-admin-links-save');
    
    if (!vtSelect) return;
    
    // 監聽下拉選單顯示隱藏自訂平台
    platformSelect.addEventListener('change', (e) => {
        platformCustomGroup.style.display = e.target.value === 'other' ? 'block' : 'none';
    });
    
    // 渲染連結列表
    function renderLinks() {
        currentListDiv.innerHTML = '';
        if (linksAdminActiveLinks.length === 0) {
            currentListDiv.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; font-style: italic; padding: 10px 0;">目前此主播無登錄任何連結。</div>';
            return;
        }
        
        linksAdminActiveLinks.forEach((link, idx) => {
            const item = document.createElement('div');
            item.className = 'link-item';
            item.style.cssText = 'display:flex; gap:12px; align-items:center; background: rgba(255,255,255,0.02); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--card-border);';
            item.innerHTML = `
                <span style="font-weight: 700; color: var(--neon-purple); min-width: 100px;">${link.platform}</span>
                <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:12px; color: var(--text-bright);">${link.url}</span>
                <button type="button" class="btn-delete-link" style="background:transparent; border:none; color:#ef4444; cursor:pointer;" data-index="${idx}"><i class="fa-solid fa-trash"></i></button>
            `;
            currentListDiv.appendChild(item);
        });
        
        // 刪除按鈕事件綁定
        currentListDiv.querySelectorAll('.btn-delete-link').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.getAttribute('data-index'));
                linksAdminActiveLinks.splice(idx, 1);
                renderLinks();
            });
        });
    }
    
    // 主播變更事件
    vtSelect.addEventListener('change', () => {
        const vtId = vtSelect.value;
        if (!vtId) {
            editorArea.style.display = 'none';
            linksAdminActiveLinks = [];
            return;
        }
        
        const vt = state.cacheVtubers.find(v => v.id === parseInt(vtId));
        if (!vt) return;
        
        // 讀取該主播的所有連結
        linksAdminActiveLinks = vt.links ? [...vt.links] : [];
        if (vt.social_links && vt.social_links.startsWith('[')) {
            try {
                linksAdminActiveLinks = JSON.parse(vt.social_links);
            } catch(e){}
        }
        
        renderLinks();
        editorArea.style.display = 'block';
    });
    
    // 新增單筆
    btnAddSingle.addEventListener('click', () => {
        let platform = platformSelect.value === 'other' ? platformCustomInput.value.trim() : platformSelect.value;
        const url = urlInput.value.trim();
        
        if (!platform) {
            showToast('請選擇或輸入平台名稱！', 'error');
            return;
        }
        if (!url || (!url.startsWith('http://') && !url.startsWith('https://'))) {
            showToast('請輸入有效的 URL (需以 http:// 或 https:// 開頭)！', 'error');
            return;
        }
        
        linksAdminActiveLinks.push({ platform, url });
        renderLinks();
        
        urlInput.value = '';
        platformCustomInput.value = '';
        platformCustomGroup.style.display = 'none';
        platformSelect.value = 'YouTube';
        showToast('已加入暫存列表');
    });
    
    // 多排貼上自動解析
    btnParseBulk.addEventListener('click', () => {
        const linesText = bulkTextarea.value.trim();
        if (!linesText) {
            showToast('請貼上多行內容！', 'error');
            return;
        }
        
        const lines = linesText.split('\n');
        let parseCount = 0;
        
        lines.forEach(line => {
            line = line.trim();
            if (!line) return;
            
            let platform = 'link';
            let url = line;
            
            // 1. 支援 "平台,網址" 格式
            if (line.includes(',')) {
                const parts = line.split(',', 2);
                const pCandidate = parts[0].trim();
                const uCandidate = parts[1].trim();
                if (uCandidate.startsWith('http://') || uCandidate.startsWith('https://')) {
                    platform = pCandidate;
                    url = uCandidate;
                }
            }
            
            // 2. 自動識別平台
            if (url.startsWith('http://') || url.startsWith('https://')) {
                const urlLower = url.toLowerCase();
                if (urlLower.includes('twitter.com') || urlLower.includes('x.com')) {
                    if (platform === 'link') platform = 'Twitter';
                } else if (urlLower.includes('youtube.com') || urlLower.includes('youtu.be')) {
                    if (platform === 'link') platform = 'YouTube';
                } else if (urlLower.includes('twitch.tv')) {
                    if (platform === 'link') platform = 'Twitch';
                } else if (urlLower.includes('facebook.com')) {
                    if (platform === 'link') platform = 'Facebook';
                } else if (urlLower.includes('instagram.com')) {
                    if (platform === 'link') platform = 'Instagram';
                } else if (urlLower.includes('bilibili.com')) {
                    if (platform === 'link') platform = 'Bilibili';
                }
                
                linksAdminActiveLinks.push({ platform, url });
                parseCount++;
            }
        });
        
        if (parseCount > 0) {
            renderLinks();
            bulkTextarea.value = '';
            showToast(`成功解析並加入 ${parseCount} 筆連結到暫存列表！`);
        } else {
            showToast('未能識別任何有效 URL，請確認格式！', 'error');
        }
    });
    
    // 儲存修改
    btnSave.addEventListener('click', async () => {
        const vtId = vtSelect.value;
        if (!vtId) return;
        
        const vt = state.cacheVtubers.find(v => v.id === parseInt(vtId));
        if (!vt) return;
        
        const payload = {
            name_main: vt.name_main,
            name_ja: vt.name_ja || null,
            name_zh: vt.name_zh || null,
            name_romaji: vt.name_romaji || null,
            youtube_channel_id: vt.youtube_channel_id || null,
            avatar_url: vt.avatar_url || null,
            theme_color: vt.theme_color || null,
            banner_url: vt.banner_url || null,
            description: vt.description || null,
            social_links: JSON.stringify(linksAdminActiveLinks)
        };
        
        try {
            const response = await fetch(`${API_BASE}/vtubers/${vtId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                showToast('🎉 主播社群連結已成功儲存！');
                await fetchAllData(); // 刷新快取
                
                // 同步更新選擇主播後的連結
                const updatedVt = state.cacheVtubers.find(v => v.id === parseInt(vtId));
                linksAdminActiveLinks = updatedVt.links ? [...updatedVt.links] : [];
                if (updatedVt.social_links && updatedVt.social_links.startsWith('[')) {
                    try { linksAdminActiveLinks = JSON.parse(updatedVt.social_links); } catch(e){}
                }
                renderLinks();
            } else {
                const err = await response.json();
                showToast(`儲存失敗: ${formatApiError(err)}`, 'error');
            }
        } catch (error) {
            showToast('連線失敗，請檢查網路！', 'error');
        }
    });
}

export function setupAdminFormListeners() {
    setupLinksAdminPane();
    // 編輯歷史演唱紀錄中直接點選編輯該歌曲
    const btnEditRecSong = document.getElementById('btn-edit-rec-song');
    if (btnEditRecSong) {
        btnEditRecSong.addEventListener('click', () => {
            const songId = document.getElementById('edit-rec-song-id').value;
            if (songId) {
                closeEditRecordModal();
                window.editSong(parseInt(songId));
            }
        });
    }

    // 增加歌曲列按鈕監聽
    const btnAddRow = document.getElementById('btn-add-setlist-row');
    if (btnAddRow) {
        btnAddRow.addEventListener('click', () => {
            addSetlistRow();
        });
    }

    // 解析時間軸按鈕監聽
    const btnParse = document.getElementById('btn-parse-setlist');
    if (btnParse) {
        btnParse.addEventListener('click', () => {
            const textarea = document.getElementById('setlist-parse-textarea');
            const container = document.getElementById('setlist-rows-container');
            
            if (!textarea || !container) return;
            const text = textarea.value.trim();
            if (!text) {
                showToast('請先貼上包含時間軸的文字！', 'error');
                return;
            }
            
            const lines = text.split('\n');
            let parsedCount = 0;
            const parsedItems = [];
            const regex = /^(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})\s+(.+)$/;
            
            lines.forEach(line => {
                const rowStr = line.trim();
                if (!rowStr) return;
                
                const match = rowStr.match(regex);
                if (match) {
                    const timeStr = match[1];
                    const songTitle = match[2].replace(/^[-\s\.\/]+/, '').trim();
                    parsedItems.push({ time: timeStr, title: songTitle });
                    parsedCount++;
                }
            });
            
            if (parsedItems.length === 0) {
                showToast('找不到符合「時間點 歌名」格式的內容！', 'error');
                return;
            }
            
            container.innerHTML = '';
            
            // 預設主播是目前所選的主播
            const currentVt = state.selectedVtuberId ? state.cacheVtubers.find(v => v.id == state.selectedVtuberId) : null;
            
            parsedItems.forEach(item => {
                const matchedSong = state.cacheSongs.find(s => 
                    s.title_main.toLowerCase() === item.title.toLowerCase() || 
                    (s.title_ja && s.title_ja.toLowerCase() === item.title.toLowerCase()) ||
                    (s.title_zh && s.title_zh.toLowerCase() === item.title.toLowerCase())
                );
                
                const songId = matchedSong ? matchedSong.id : null;
                const displayTitle = matchedSong ? matchedSong.title_main : item.title;
                
                const row = addSetlistRow(songId, displayTitle);
                if (row) {
                    row.querySelector('.row-timestamp').value = formatTimeToHHMMSS(item.time);
                    if (currentVt) {
                        row.setSingers([currentVt]);
                    }
                }
            });
            
            showToast(`🎉 成功解析並填入 ${parsedCount} 首曲目！`);
            textarea.value = '';
        });
    }

    // 批次時間軸表單提交監聽
    const recordForm = document.getElementById('form-create-record');
    if (recordForm) {
        recordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const videoId = document.getElementById('record-video-id').value;
            if (!videoId) {
                showToast('請選擇收錄的直播/影片！', 'error');
                return;
            }
            
            const rowElements = document.querySelectorAll('.setlist-row');
            if (rowElements.length === 0) {
                showToast('曲目列表不可為空！', 'error');
                return;
            }
            
            const recordsPayload = [];
            let validationFailed = false;
            
            rowElements.forEach((row, idx) => {
                const songTitle = row.querySelector('.row-song-search').value.trim();
                const timeStr = row.querySelector('.row-timestamp').value;
                const note = row.querySelector('.row-note').value || null;
                const singers = row.getSingers().map(s => s.name_main);
                
                if (!songTitle) {
                    showToast(`第 ${idx + 1} 列歌曲名稱不能為空！`, 'error');
                    validationFailed = true;
                    return;
                }
                if (singers.length === 0) {
                    showToast(`第 ${idx + 1} 列未指定演唱主播！`, 'error');
                    validationFailed = true;
                    return;
                }
                
                recordsPayload.push({
                    song_title: songTitle,
                    video_id: videoId,
                    timestamp_seconds: parseTimeToSeconds(timeStr),
                    note: note,
                    singers: singers,
                    song_type: "cover"
                });
            });
            
            if (validationFailed) return;
            
            try {
                const response = await fetch(`${API_BASE}/records/batch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(recordsPayload)
                });
                
                if (response.ok) {
                    const results = await response.json();
                    showToast(`🎉 已成功登錄 ${results.length} 筆歌單時間軸！`);
                    recordForm.reset();
                    document.getElementById('record-video-id').value = '';
                    const container = document.getElementById('setlist-rows-container');
                    if (container) container.innerHTML = '';
                    addSetlistRow();
                    
                    await fetchAllData();
                    loadDashboardData();
                    if (state.selectedVtuberId) {
                        const { loadVtuberProfile } = await import('./portal.js');
                        loadVtuberProfile(state.selectedVtuberId);
                    }
                } else {
                    const err = await response.json();
                    showToast(`登錄歌單失敗: ${formatApiError(err, '格式錯誤')}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 登錄 VTuber 表單提交監聽
    const vtuberForm = document.getElementById('form-create-vtuber');
    if (vtuberForm) {
        vtuberForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const editId = document.getElementById('edit-vtuber-id').value;
            const name = document.getElementById('vtuber-name-main').value;
            const ja = document.getElementById('vtuber-name-ja').value;
            const zh = document.getElementById('vtuber-name-zh').value;
            const romaji = document.getElementById('vtuber-name-romaji').value;
            const youtube = document.getElementById('vtuber-youtube').value;
            const avatar = document.getElementById('vtuber-avatar-url').value;
            const theme = document.getElementById('vtuber-theme-color').value;
            const banner = document.getElementById('vtuber-banner-url').value;
            const scheduleImg = document.getElementById('vtuber-schedule-image-url') ? document.getElementById('vtuber-schedule-image-url').value : '';
            const desc = document.getElementById('vtuber-desc').value;
            
            const payload = {
                name_main: name,
                name_ja: ja || null,
                name_zh: zh || null,
                name_romaji: romaji || null,
                youtube_channel_id: youtube || null,
                avatar_url: avatar || null,
                theme_color: theme || null,
                banner_url: banner || null,
                schedule_image_url: formatScheduleImageUrl(scheduleImg),
                description: desc || null
            };
            
            const url = editId ? `${API_BASE}/vtubers/${editId}` : `${API_BASE}/vtubers/`;
            const method = editId ? 'PUT' : 'POST';
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    showToast(editId ? '🎉 主播資料更新成功！' : '🎉 VTuber 主播登錄成功！');
                    vtuberForm.reset();
                    document.getElementById('edit-vtuber-id').value = '';
                    
                    document.getElementById('form-vtuber-title-header').innerHTML = '<i class="fa-solid fa-user-plus neon-text-purple"></i> 登錄/編輯 VTuber 主播';
                    const submitBtn = document.getElementById('btn-vtuber-submit');
                    submitBtn.innerHTML = '<i class="fa-solid fa-plus"></i> 登錄 VTuber';
                    document.getElementById('btn-vtuber-cancel-edit').style.display = 'none';
                    
                    await fetchAllData();
                    loadSidebarVtubers();
                    populateAdminDropdowns();
                    renderVtuberCatalog();
                    loadDashboardData();
                    loadAdminVtubers();
                } else {
                    const err = await response.json();
                    showToast(`操作失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    const cancelVtuberEditBtn = document.getElementById('btn-vtuber-cancel-edit');
    if (cancelVtuberEditBtn) {
        cancelVtuberEditBtn.addEventListener('click', () => {
            document.getElementById('edit-vtuber-id').value = '';
            vtuberForm.reset();
            document.getElementById('form-vtuber-title-header').innerHTML = '<i class="fa-solid fa-user-plus neon-text-purple"></i> 登錄/編輯 VTuber 主播';
            const submitBtn = document.getElementById('btn-vtuber-submit');
            submitBtn.innerHTML = '<i class="fa-solid fa-plus"></i> 登錄 VTuber';
            cancelVtuberEditBtn.style.display = 'none';
        });
    }

    // 自動抓取 YouTube 頻道資訊按鈕監聽
    const btnVtuberFetchInfo = document.getElementById('btn-vtuber-fetch-info');
    if (btnVtuberFetchInfo) {
        btnVtuberFetchInfo.addEventListener('click', async () => {
            const urlInput = document.getElementById('vtuber-fetch-url');
            if (!urlInput) return;
            const channelUrl = urlInput.value.trim();
            if (!channelUrl) {
                showToast('請先輸入頻道網址、@Handle 或 頻道 ID！', 'error');
                return;
            }

            btnVtuberFetchInfo.disabled = true;
            const originalHtml = btnVtuberFetchInfo.innerHTML;
            btnVtuberFetchInfo.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 正在抓取資訊...';

            try {
                const response = await fetch(`${API_BASE}/vtubers/fetch_youtube_info?channel_url=${encodeURIComponent(channelUrl)}`);
                if (response.ok) {
                    const data = await response.json();
                    
                    document.getElementById('vtuber-name-main').value = data.title || '';
                    document.getElementById('vtuber-youtube').value = data.channel_id || '';
                    document.getElementById('vtuber-avatar-url').value = data.avatar_url || '';
                    document.getElementById('vtuber-banner-url').value = data.banner_url || '';
                    document.getElementById('vtuber-desc').value = data.description || '';
                    
                    // 根據 title 自動嘗試生成羅馬字
                    if (data.title) {
                        const englishOnly = data.title.replace(/[^a-zA-Z0-9\s]/g, '').trim().toLowerCase().replace(/\s+/g, ' ');
                        if (englishOnly) {
                            document.getElementById('vtuber-name-romaji').value = englishOnly;
                        }
                    }
                    
                    showToast('🎉 YouTube 頻道資訊抓取成功並已自動填入！');
                    urlInput.value = ''; // 清空抓取輸入框
                } else {
                    const err = await response.json();
                    showToast(`抓取失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                console.error(error);
                showToast('抓取連線失敗', 'error');
            } finally {
                btnVtuberFetchInfo.disabled = false;
                btnVtuberFetchInfo.innerHTML = originalHtml;
            }
        });
    }

    // 登錄原創歌曲表單提交監聽
    const songForm = document.getElementById('form-create-song');
    if (songForm) {
        songForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const editId = document.getElementById('edit-song-id').value;
            const title = document.getElementById('song-title-main').value;
            const ja = document.getElementById('song-title-ja').value;
            const zh = document.getElementById('song-title-zh').value;
            const romaji = document.getElementById('song-title-romaji').value;
            
            const payload = {
                title_main: title,
                title_ja: ja || null,
                title_zh: zh || null,
                title_romaji: romaji || null,
                song_type: 'cover',
                artist_ids: state.selectedArtists.map(a => a.id)
            };
            
            const url = editId ? `${API_BASE}/songs/${editId}` : `${API_BASE}/songs/`;
            const method = editId ? 'PUT' : 'POST';
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    showToast(editId ? '🎉 歌曲資料已更新！' : '🎉 原創歌曲登錄成功！');
                    cancelSongEdit();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`操作失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 登錄原唱歌手表單提交監聽
    const artistForm = document.getElementById('form-create-artist');
    if (artistForm) {
        artistForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const editId = document.getElementById('edit-artist-id').value;
            const name = document.getElementById('artist-name-main').value;
            const ja = document.getElementById('artist-name-ja').value;
            const zh = document.getElementById('artist-name-zh').value;
            const romaji = document.getElementById('artist-name-romaji').value;
            
            const payload = {
                name_main: name,
                name_ja: ja || null,
                name_zh: zh || null,
                name_romaji: romaji || null
            };
            
            const url = editId ? `${API_BASE}/artists/${editId}` : `${API_BASE}/artists/`;
            const method = editId ? 'PUT' : 'POST';
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    showToast(editId ? '🎉 歌手資料已更新！' : '🎉 原唱歌手登錄成功！');
                    cancelArtistEdit();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`操作失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // YouTube 影片 ID 提取助手
    function jsExtractYoutubeId(val) {
        val = val.trim();
        if (val.length === 11 && /^[a-zA-Z0-9_-]{11}$/.test(val)) {
            return val;
        }
        const patterns = [
            /v=([a-zA-Z0-9_-]{11})/,
            /youtu\.be\/([a-zA-Z0-9_-]{11})/,
            /embed\/([a-zA-Z0-9_-]{11})/,
            /live\/([a-zA-Z0-9_-]{11})/,
            /shorts\/([a-zA-Z0-9_-]{11})/
        ];
        for (let pat of patterns) {
            const m = val.match(pat);
            if (m) return m[1];
        }
        if (val.includes('v=')) {
            const parts = val.split('v=');
            if (parts.length > 1) {
                const potential = parts[1].substring(0, 11);
                if (potential.length === 11 && /^[a-zA-Z0-9_-]{11}$/.test(potential)) {
                    return potential;
                }
            }
        }
        return "";
    }

    // YouTube 影片 ID 貼上/輸入自動解析網址與抓取標題
    const videoIdInput = document.getElementById('video-id');
    const ytIndicator = document.getElementById('yt-fetch-indicator');
    if (videoIdInput) {
        videoIdInput.addEventListener('input', async (e) => {
            const rawVal = e.target.value;
            const cleanId = jsExtractYoutubeId(rawVal);
            
            if (cleanId && cleanId !== rawVal) {
                videoIdInput.value = cleanId;
            }
            
            const currentId = videoIdInput.value.trim();
            if (currentId.length === 11 && /^[a-zA-Z0-9_-]{11}$/.test(currentId)) {
                if (ytIndicator) {
                    ytIndicator.textContent = "🔄 正在獲取 YouTube 資訊...";
                    ytIndicator.style.color = "var(--neon-blue)";
                }
                
                try {
                    const res = await fetch(`${API_BASE}/videos/fetch_youtube_info?video_id=${currentId}`);
                    if (res.ok) {
                        const info = await res.json();
                        if (info.title) {
                            document.getElementById('video-title').value = info.title;
                        }
                        if (info.published_date) {
                            document.getElementById('video-published').value = info.published_date;
                        }
                        
                        const titleLower = (info.title || "").toLowerCase();
                        const videoTypeSel = document.getElementById('video-type');
                        if (videoTypeSel) {
                            if (titleLower.includes('mv') || titleLower.includes('original') || titleLower.includes('cover')) {
                                if (titleLower.includes('original') || titleLower.includes('原創')) {
                                    videoTypeSel.value = 'original_mv';
                                } else {
                                    videoTypeSel.value = 'cover_mv';
                                }
                            } else if (titleLower.includes('歌回') || titleLower.includes('歌枠') || titleLower.includes('sing') || titleLower.includes('3d live') || titleLower.includes('3dlive') || titleLower.includes('演唱會')) {
                                videoTypeSel.value = 'stream_singing';
                            } else {
                                videoTypeSel.value = 'stream_other';
                            }
                        }
                        
                        if (ytIndicator) {
                            ytIndicator.textContent = "✅ 已成功抓取資訊";
                            ytIndicator.style.color = "var(--neon-green)";
                        }
                    } else {
                        if (ytIndicator) {
                            ytIndicator.textContent = "⚠️ 無法取得標題 (私有/無此影片)";
                            ytIndicator.style.color = "var(--neon-pink)";
                        }
                    }
                } catch (err) {
                    if (ytIndicator) {
                        ytIndicator.textContent = "❌ 獲取失敗 (連線錯誤)";
                        ytIndicator.style.color = "var(--neon-pink)";
                    }
                }
            } else {
                if (ytIndicator) {
                    ytIndicator.textContent = "";
                }
            }
        });
    }

    // 登錄已登記影音表單提交監聽
    const videoForm = document.getElementById('form-create-video');
    if (videoForm) {
        videoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const vtuberIdVal = document.getElementById('video-vtuber-id').value;
            const videoId = document.getElementById('video-id').value.trim();
            const title = document.getElementById('video-title').value.trim();
            const published = document.getElementById('video-published').value;
            const type = document.getElementById('video-type').value;
            const thumb = document.getElementById('video-thumb').value.trim() || `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
            
            const payload = {
                video_id: videoId,
                title: title,
                video_type: type,
                published_at: published || null,
                thumbnail_url: thumb || null,
                vtuber_id: vtuberIdVal ? parseInt(vtuberIdVal) : null
            };
            
            const isEdit = document.getElementById('video-id').readOnly;
            const url = isEdit ? `${API_BASE}/videos/${videoId}` : `${API_BASE}/videos/`;
            const method = isEdit ? 'PUT' : 'POST';
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    const savedVideo = await response.json();
                    showToast(isEdit ? '🎉 影片/直播資料已更新！' : '🎉 YouTube 直播/影音檔已成功登記！');
                    
                    // 快速關聯單首歌曲
                    const songIdVal = document.getElementById('video-song-id').value;
                    if (songIdVal && vtuberIdVal && !isEdit) {
                        const timeVal = parseInt(document.getElementById('video-song-time').value) || 0;
                        const noteVal = document.getElementById('video-song-note').value.trim() || 'MV 版';
                        
                        const recordPayload = {
                            song_id: parseInt(songIdVal),
                            video_id: savedVideo.video_id,
                            timestamp_seconds: timeVal,
                            note: noteVal,
                            singer_ids: [parseInt(vtuberIdVal)]
                        };
                        
                        try {
                            const recResponse = await fetch(`${API_BASE}/records/`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(recordPayload)
                            });
                            if (recResponse.ok) {
                                showToast('已自動為此影音建立歌曲演唱關聯！');
                            } else {
                                showToast('自動建立歌曲關聯失敗，請稍後手動彙整', 'error');
                            }
                        } catch (err) {
                            console.error('快速關聯歌曲出錯:', err);
                        }
                    }
                    
                    // 重置表單
                    videoForm.reset();
                    document.getElementById('video-id').readOnly = false;
                    document.getElementById('form-video-title-header').innerHTML = `<i class="fa-solid fa-circle-play neon-text-blue"></i> 新增 YouTube 直播 / MV 影音`;
                    const submitBtn = document.getElementById('btn-video-submit');
                    if (submitBtn) submitBtn.innerHTML = '<i class="fa-solid fa-plus"></i> 登記新影音';
                    document.getElementById('btn-video-cancel-edit').style.display = 'none';
                    
                    // 清空快速關聯欄位
                    const vsSearch = document.getElementById('video-song-search');
                    const vsId = document.getElementById('video-song-id');
                    const vsTime = document.getElementById('video-song-time');
                    const vsNote = document.getElementById('video-song-note');
                    if (vsSearch) vsSearch.value = '';
                    if (vsId) vsId.value = '';
                    if (vsTime) vsTime.value = '0';
                    if (vsNote) vsNote.value = '';
                    
                    if (ytIndicator) ytIndicator.textContent = '';
                    
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`操作失敗: ${formatApiError(err, '影片 ID 可能已存在或格式不符')}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 取消影音編輯按鈕監聽
    const cancelVideoEditBtn = document.getElementById('btn-video-cancel-edit');
    if (cancelVideoEditBtn) {
        cancelVideoEditBtn.addEventListener('click', () => {
            document.getElementById('video-id').value = '';
            document.getElementById('video-id').readOnly = false;
            videoForm.reset();
            
            document.getElementById('form-video-title-header').innerHTML = '<i class="fa-solid fa-circle-play neon-text-blue"></i> 新增 YouTube 直播 / MV 影音';
            const submitBtn = document.getElementById('btn-video-submit');
            if (submitBtn) submitBtn.innerHTML = '<i class="fa-solid fa-plus"></i> 登記新影音';
            cancelVideoEditBtn.style.display = 'none';
            
            // 清空快速關聯欄位
            const vsSearch = document.getElementById('video-song-search');
            const vsId = document.getElementById('video-song-id');
            const vsTime = document.getElementById('video-song-time');
            const vsNote = document.getElementById('video-song-note');
            if (vsSearch) vsSearch.value = '';
            if (vsId) vsId.value = '';
            if (vsTime) vsTime.value = '0';
            if (vsNote) vsNote.value = '';
            
            if (ytIndicator) ytIndicator.textContent = '';
        });
    }

    // 登錄里程碑公告表單提交監聽
    const activityForm = document.getElementById('form-create-activity');
    if (activityForm) {
        activityForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('activity-title').value;
            const vtId = document.getElementById('activity-vtuber-id').value;
            const type = document.getElementById('activity-type-field').value;
            const date = document.getElementById('activity-date').value;
            const link = document.getElementById('activity-link').value;
            const desc = document.getElementById('activity-desc').value;
            
            const payload = {
                title: title,
                vtuber_id: vtId ? parseInt(vtId) : null,
                activity_type: type,
                event_date: date,
                link_url: link || null,
                description: desc || null
            };
            
            try {
                const response = await fetch(`${API_BASE}/activities/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    showToast('🎉 主播成就里程碑 / 公告已成功發布！');
                    activityForm.reset();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`操作失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 1. 歌唱歷史紀錄批次匯入
    const btnSubmitBulk = document.getElementById('btn-submit-bulk');
    if (btnSubmitBulk) {
        btnSubmitBulk.addEventListener('click', async () => {
            const format = document.getElementById('bulk-format').value;
            const textarea = document.getElementById('bulk-data-textarea');
            const fileInput = document.getElementById('bulk-records-file');
            
            let rawText = textarea.value.trim();
            
            // 優先從檔案讀取
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                rawText = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.readAsText(file, 'utf-8');
                });
            }
            
            if (!rawText) {
                showToast('請輸入匯入內容或選擇檔案！', 'warning');
                return;
            }
            
            let payloadItems = [];
            
            try {
                if (format === 'json') {
                    payloadItems = JSON.parse(rawText);
                } else {
                    // CSV 格式解析
                    const lines = rawText.split('\n');
                    lines.forEach(line => {
                        line = line.trim();
                        if (!line) return;
                        
                        const parts = line.split(',');
                        if (parts.length >= 4) {
                            payloadItems.push({
                                song_title: parts[0].trim(),
                                video_id: parts[1].trim(),
                                timestamp_seconds: parseInt(parts[2].trim()) || 0,
                                singers: parts[3].split(';').map(s => s.trim()).filter(Boolean),
                                note: parts[4] ? parts[4].trim() : null,
                                song_type: parts[5] ? parts[5].trim() : 'cover'
                            });
                        }
                    });
                }
            } catch (e) {
                showToast('資料格式解析失敗，請檢查欄位！', 'error');
                return;
            }
            
            if (payloadItems.length === 0) {
                showToast('沒有解析到任何有效的資料列！', 'warning');
                return;
            }
            
            try {
                showToast('正在批量匯入歷史紀錄...', 'info');
                const response = await fetch(`${API_BASE}/records/batch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payloadItems)
                });
                
                if (response.ok) {
                    const res = await response.json();
                    showToast(`🎉 成功解析並匯入 ${res.length} 筆歷史演唱紀錄！`);
                    textarea.value = '';
                    fileInput.value = '';
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`批量匯入失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 2. 批量匯入主播個人歌單 (點歌歌單 / 常駐歌單)
    const btnSubmitPlaylist = document.getElementById('btn-submit-bulk-playlist');
    if (btnSubmitPlaylist) {
        btnSubmitPlaylist.addEventListener('click', async () => {
            const vtId = document.getElementById('bulk-playlist-vtuber-id').value;
            const type = document.getElementById('bulk-playlist-type').value;
            const textarea = document.getElementById('bulk-playlist-textarea');
            const fileInput = document.getElementById('bulk-playlist-file');
            
            if (!vtId) {
                showToast('請選擇目標 VTuber 主播！', 'warning');
                return;
            }
            
            let rawText = textarea.value.trim();
            
            // 優先從檔案讀取
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                rawText = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.readAsText(file, 'utf-8');
                });
            }
            
            if (!rawText) {
                showToast('請輸入歌單內容或選擇檔案！', 'warning');
                return;
            }
            
            try {
                showToast('正在批次導入歌單...', 'info');
                const response = await fetch(`${API_BASE}/vtubers/${vtId}/songs/batch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        raw_lines: rawText.split('\n'),
                        association_type: type
                    })
                });
                
                if (response.ok) {
                    const res = await response.json();
                    showToast(`🎉 成功解析並匯入歌曲至個人歌單中！`);
                    textarea.value = '';
                    fileInput.value = '';
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`批次導入失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    const btnCloseEditRecord = document.getElementById('btn-close-edit-record-modal');
    if (btnCloseEditRecord) btnCloseEditRecord.addEventListener('click', closeEditRecordModal);
    const btnCancelEditRecord = document.getElementById('btn-cancel-edit-record');
    if (btnCancelEditRecord) btnCancelEditRecord.addEventListener('click', closeEditRecordModal);
    const editRecordModalOverlay = document.getElementById('edit-record-modal');
    if (editRecordModalOverlay) {
        editRecordModalOverlay.addEventListener('click', (e) => {
            if (e.target === editRecordModalOverlay) closeEditRecordModal();
        });
    }

    const btnCloseEditSong = document.getElementById('btn-close-edit-song-modal');
    if (btnCloseEditSong) btnCloseEditSong.addEventListener('click', closeEditSongModal);
    const btnCancelEditSong = document.getElementById('btn-cancel-edit-song-modal');
    if (btnCancelEditSong) btnCancelEditSong.addEventListener('click', closeEditSongModal);

    const btnCloseEditArtist = document.getElementById('btn-close-edit-artist-modal');
    if (btnCloseEditArtist) btnCloseEditArtist.addEventListener('click', closeEditArtistModal);
    const btnCancelEditArtist = document.getElementById('btn-cancel-edit-artist-modal');
    if (btnCancelEditArtist) btnCancelEditArtist.addEventListener('click', closeEditArtistModal);

    const btnCloseEditVtuber = document.getElementById('btn-close-edit-vtuber-modal');
    if (btnCloseEditVtuber) btnCloseEditVtuber.addEventListener('click', closeEditVtuberModal);
    const btnCancelEditVtuber = document.getElementById('btn-cancel-edit-vtuber-modal');
    if (btnCancelEditVtuber) btnCancelEditVtuber.addEventListener('click', closeEditVtuberModal);

    const btnCloseEditVideo = document.getElementById('btn-close-edit-video-modal');
    if (btnCloseEditVideo) btnCloseEditVideo.addEventListener('click', closeEditVideoModal);
    const btnCancelEditVideo = document.getElementById('btn-cancel-edit-video-modal');
    if (btnCancelEditVideo) btnCancelEditVideo.addEventListener('click', closeEditVideoModal);

    const btnCloseEditActivity = document.getElementById('btn-close-edit-activity-modal');
    if (btnCloseEditActivity) btnCloseEditActivity.addEventListener('click', closeEditActivityModal);
    const btnCancelEditActivity = document.getElementById('btn-cancel-edit-activity-modal');
    if (btnCancelEditActivity) btnCancelEditActivity.addEventListener('click', closeEditActivityModal);

    // 編輯歌曲 Modal 提交
    const editSongFormModal = document.getElementById('form-edit-song-modal');
    if (editSongFormModal) {
        editSongFormModal.addEventListener('submit', async (e) => {
            e.preventDefault();
            const songId = document.getElementById('edit-song-id-modal').value;
            const payload = {
                title_main: document.getElementById('edit-song-title-main').value,
                title_ja: document.getElementById('edit-song-title-ja').value || null,
                title_zh: document.getElementById('edit-song-title-zh').value || null,
                title_romaji: document.getElementById('edit-song-title-romaji').value || null,
                song_type: document.getElementById('edit-song-type').value || 'cover',
                artist_ids: state.editSongSelectedArtists.map(a => a.id)
            };
            try {
                const response = await fetch(`${API_BASE}/songs/${songId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    showToast('🎉 歌曲資訊已成功更新！');
                    closeEditSongModal();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`更新歌曲失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 編輯歌手 Modal 提交
    const editArtistFormModal = document.getElementById('form-edit-artist-modal');
    if (editArtistFormModal) {
        editArtistFormModal.addEventListener('submit', async (e) => {
            e.preventDefault();
            const artistId = document.getElementById('edit-artist-id-modal').value;
            const payload = {
                name_main: document.getElementById('edit-artist-name-main').value,
                name_ja: document.getElementById('edit-artist-name-ja').value || null,
                name_zh: document.getElementById('edit-artist-name-zh').value || null,
                name_romaji: document.getElementById('edit-artist-name-romaji').value || null
            };
            try {
                const response = await fetch(`${API_BASE}/artists/${artistId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    showToast('🎉 歌手資訊已成功更新！');
                    closeEditArtistModal();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`更新歌手失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 編輯主播 Modal 提交
    const editVtuberFormModal = document.getElementById('form-edit-vtuber-modal');
    if (editVtuberFormModal) {
        editVtuberFormModal.addEventListener('submit', async (e) => {
            e.preventDefault();
            const vtuberId = document.getElementById('edit-vtuber-id-modal').value;
            const payload = {
                name_main: document.getElementById('edit-vtuber-name-main').value,
                name_ja: document.getElementById('edit-vtuber-name-ja').value || null,
                name_zh: document.getElementById('edit-vtuber-name-zh').value || null,
                name_romaji: document.getElementById('edit-vtuber-name-romaji').value || null,
                youtube_channel_id: document.getElementById('edit-vtuber-youtube').value || null,
                avatar_url: document.getElementById('edit-vtuber-avatar-url').value || null,
                theme_color: document.getElementById('edit-vtuber-theme-color').value || null,
                banner_url: document.getElementById('edit-vtuber-banner-url').value || null,
                schedule_image_url: formatScheduleImageUrl(document.getElementById('edit-vtuber-schedule-image-url') ? document.getElementById('edit-vtuber-schedule-image-url').value : ''),
                description: document.getElementById('edit-vtuber-desc').value || null
            };
            try {
                const response = await fetch(`${API_BASE}/vtubers/${vtuberId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    showToast('🎉 主播資訊已成功更新！');
                    closeEditVtuberModal();
                    await fetchAllData();
                    loadSidebarVtubers();
                    populateAdminDropdowns();
                    renderVtuberCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`更新主播失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 編輯影音 Modal 提交
    const editVideoFormModal = document.getElementById('form-edit-video-modal');
    if (editVideoFormModal) {
        editVideoFormModal.addEventListener('submit', async (e) => {
            e.preventDefault();
            const videoId = document.getElementById('edit-video-id-modal').value;
            const vtuberIdVal = parseInt(document.getElementById('edit-video-vtuber-id').value) || null;
            const payload = {
                video_id: videoId,
                vtuber_id: vtuberIdVal,
                title: document.getElementById('edit-video-title').value,
                video_type: document.getElementById('edit-video-type').value,
                published_at: document.getElementById('edit-video-published').value || null,
                thumbnail_url: document.getElementById('edit-video-thumb').value || null
            };
            try {
                const response = await fetch(`${API_BASE}/videos/${videoId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    showToast('🎉 影音資訊已成功更新！');

                    // 檢查是否需同步/更新歌曲演唱紀錄 (如 MV 歌曲綁定)
                    const songIdVal = document.getElementById('edit-video-song-id') ? document.getElementById('edit-video-song-id').value : '';
                    if (songIdVal && vtuberIdVal) {
                        const existingRec = state.cacheRecords.find(r => r.video_id === videoId);
                        if (existingRec) {
                            // 更新現有紀錄
                            await fetch(`${API_BASE}/records/${existingRec.id}`, {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    song_id: parseInt(songIdVal),
                                    video_id: videoId,
                                    timestamp_seconds: existingRec.timestamp_seconds || 0,
                                    note: existingRec.note || 'MV 演唱紀錄',
                                    singer_ids: [vtuberIdVal]
                                })
                            });
                        } else {
                            // 建立新紀錄
                            await fetch(`${API_BASE}/records/`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    song_id: parseInt(songIdVal),
                                    video_id: videoId,
                                    timestamp_seconds: 0,
                                    note: 'MV 演唱紀錄',
                                    singer_ids: [vtuberIdVal]
                                })
                            });
                        }
                    }

                    closeEditVideoModal();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`更新影音失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 編輯活動公告 Modal 提交
    const editActivityFormModal = document.getElementById('form-edit-activity-modal');
    if (editActivityFormModal) {
        editActivityFormModal.addEventListener('submit', async (e) => {
            e.preventDefault();
            const actId = document.getElementById('edit-activity-id-modal').value;
            const payload = {
                title: document.getElementById('edit-activity-title').value,
                vtuber_id: parseInt(document.getElementById('edit-activity-vtuber-id').value) || null,
                activity_type: document.getElementById('edit-activity-type').value,
                event_date: document.getElementById('edit-activity-date').value,
                link_url: document.getElementById('edit-activity-link').value || null,
                description: document.getElementById('edit-activity-desc').value || null
            };
            try {
                const response = await fetch(`${API_BASE}/activities/${actId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    showToast('🎉 活動/公告已成功更新！');
                    closeEditActivityModal();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`更新活動失敗: ${formatApiError(err)}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // 編輯時間軸單曲歷史紀錄 Modal 提交
    const editRecordForm = document.getElementById('form-edit-record');
    if (editRecordForm) {
        editRecordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const recordId = document.getElementById('edit-rec-id').value;
            const songId = document.getElementById('edit-rec-song-id').value;
            const videoId = document.getElementById('edit-rec-video-id').value;
            const timestamp = document.getElementById('edit-rec-timestamp').value;
            const note = document.getElementById('edit-rec-note').value;
            
            const checkedSingers = state.editRecSelectedSingers.map(s => s.id);
            if (checkedSingers.length === 0) {
                showToast('請至少選擇一位演唱主播！', 'error');
                return;
            }
            
            const payload = {
                song_id: parseInt(songId),
                video_id: videoId,
                timestamp_seconds: parseInt(timestamp),
                note: note || null,
                singer_ids: checkedSingers
            };
            
            try {
                const response = await fetch(`${API_BASE}/records/${recordId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    showToast('🎉 演唱紀錄已成功更新！');
                    closeEditRecordModal();
                    await fetchAllData();
                    renderCatalog();
                    loadDashboardData();
                } else {
                    const err = await response.json();
                    showToast(`更新失敗: ${formatApiError(err, '請檢查欄位格式')}`, 'error');
                }
            } catch (error) {
                showToast('連線失敗', 'error');
            }
        });
    }

    // YouTube 頻道自動同步爬蟲
    const syncLimitMode = document.getElementById('sync-limit-mode');
    const syncLimitValueGroup = document.getElementById('sync-limit-value-group');
    if (syncLimitMode && syncLimitValueGroup) {
        syncLimitMode.addEventListener('change', (e) => {
            if (e.target.value === 'all') {
                syncLimitValueGroup.style.display = 'none';
            } else {
                syncLimitValueGroup.style.display = 'block';
            }
        });
    }

    const syncCrawlerForm = document.getElementById('form-sync-crawler');
    const syncCrawlerSubmitBtn = document.getElementById('btn-sync-crawler-submit');
    if (syncCrawlerForm && syncCrawlerSubmitBtn) {
        syncCrawlerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const vtuberId = document.getElementById('sync-vtuber-id').value;
            const syncType = document.getElementById('sync-type').value;
            const limitMode = document.getElementById('sync-limit-mode').value;
            const limitVal = parseInt(document.getElementById('sync-limit-value').value) || 30;
            
            const limitParam = limitMode === 'all' ? '' : `limit=${limitVal}`;
            const tabParam = `tab=${syncType}`;
            const queryParams = [limitParam, tabParam].filter(p => p).join('&');
            
            syncCrawlerSubmitBtn.disabled = true;
            const originalBtnHtml = syncCrawlerSubmitBtn.innerHTML;
            syncCrawlerSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 爬蟲同步中，請稍候...';
            
            try {
                if (vtuberId === 'all') {
                    const vtubers = state.cacheVtubers;
                    if (vtubers.length === 0) {
                        showToast('沒有找到已收錄的主播！', 'error');
                        return;
                    }
                    
                    let successCount = 0;
                    let totalSynced = 0;
                    
                    for (let i = 0; i < vtubers.length; i++) {
                        const vt = vtubers[i];
                        if (!vt.youtube_channel_id) continue;
                        
                        syncCrawlerSubmitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> 同步主播 [${vt.name_main}] (${i + 1}/${vtubers.length})...`;
                        
                        try {
                            const res = await fetch(`${API_BASE}/vtubers/${vt.id}/sync_youtube?${queryParams}`, {
                                method: 'POST'
                            });
                            if (res.ok) {
                                const data = await res.json();
                                successCount++;
                                totalSynced += data.length;
                            }
                        } catch (err) {
                            console.error(`同步主播 ${vt.name_main} 失敗:`, err);
                        }
                    }
                    
                    showToast(`🎉 批次同步完成！成功同步 ${successCount} 位主播，共計 ${totalSynced} 部影音。`);
                } else {
                    const vt = state.cacheVtubers.find(v => v.id == vtuberId);
                    const name = vt ? vt.name_main : '主播';
                    
                    const res = await fetch(`${API_BASE}/vtubers/${vtuberId}/sync_youtube?${queryParams}`, {
                        method: 'POST'
                    });
                    
                    if (res.ok) {
                        const data = await res.json();
                        showToast(`🎉 主播 [${name}] 同步成功！共計同步 ${data.length} 部直播與影音。`);
                    } else {
                        const err = await res.json();
                        showToast(`同步失敗: ${formatApiError(err)}`, 'error');
                    }
                }
                
                await fetchAllData();
                renderCatalog();
                loadDashboardData();
            } catch (error) {
                console.error(error);
                showToast('連線失敗或請求超時，請檢查伺服器日誌。', 'error');
            } finally {
                syncCrawlerSubmitBtn.disabled = false;
                syncCrawlerSubmitBtn.innerHTML = originalBtnHtml;
            }
        });
    }
}

// 輔助登錄重置與撤銷方法
export function cancelSongEdit() {
    document.getElementById('edit-song-id').value = '';
    document.getElementById('form-create-song').reset();
    state.selectedArtists = [];
    renderSelectedArtistsTags();
    
    document.getElementById('form-song-title-header').innerHTML = '<i class="fa-solid fa-file-music neon-text-blue"></i> 登錄原創歌曲';
    const submitBtn = document.getElementById('btn-song-submit');
    submitBtn.innerHTML = '<i class="fa-solid fa-plus"></i> 登錄歌曲';
    document.getElementById('btn-song-cancel-edit').style.display = 'none';
}

export function cancelArtistEdit() {
    document.getElementById('edit-artist-id').value = '';
    document.getElementById('form-create-artist').reset();
    
    document.getElementById('form-artist-title-header').innerHTML = '<i class="fa-solid fa-microphone-lines neon-text-purple"></i> 登錄原唱歌手';
    const submitBtn = document.getElementById('btn-artist-submit');
    submitBtn.innerHTML = '<i class="fa-solid fa-plus"></i> 登錄歌手';
    document.getElementById('btn-artist-cancel-edit').style.display = 'none';
}

export function populateAdminDropdowns() {
    const vtubers = state.cacheVtubers;
    
    // 1. YouTube 影音登錄 -> 關聯發布的主播
    const videoVtSelect = document.getElementById('video-vtuber-id');
    if (videoVtSelect) {
        videoVtSelect.innerHTML = '<option value="">-- 請選擇主播 --</option>';
        vtubers.forEach(vt => {
            videoVtSelect.innerHTML += `<option value="${vt.id}">${vt.name_main}</option>`;
        });
    }
    
    // 2. 里程碑與公告 -> 關聯主播
    const actVtSelect = document.getElementById('activity-vtuber-id');
    if (actVtSelect) {
        actVtSelect.innerHTML = '<option value="">-- 全域公告 --</option>';
        vtubers.forEach(vt => {
            actVtSelect.innerHTML += `<option value="${vt.id}">${vt.name_main}</option>`;
        });
    }
    
    // 3. 批次數據匯入 -> 選擇主播
    const batchVtSelect = document.getElementById('batch-vtuber-id');
    if (batchVtSelect) {
        batchVtSelect.innerHTML = '<option value="">-- 請選擇主播 --</option>';
        vtubers.forEach(vt => {
            batchVtSelect.innerHTML += `<option value="${vt.id}">${vt.name_main}</option>`;
        });
    }
    
    // 4. YouTube 頻道自動同步爬蟲 -> 選擇主播
    const syncVtSelect = document.getElementById('sync-vtuber-id');
    if (syncVtSelect) {
        syncVtSelect.innerHTML = '<option value="all">-- 同步所有收錄主播 --</option>';
        vtubers.forEach(vt => {
            syncVtSelect.innerHTML += `<option value="${vt.id}">${vt.name_main}</option>`;
        });
    }
    
    // 5. 相關網站與連結管理 -> 選擇主播
    const linksVtSelect = document.getElementById('admin-links-vtuber-select');
    if (linksVtSelect) {
        linksVtSelect.innerHTML = '<option value="">-- 請選擇主播 --</option>';
        vtubers.forEach(vt => {
            linksVtSelect.innerHTML += `<option value="${vt.id}">${vt.name_main}</option>`;
        });
    }

    // 6. 批量匯入主播個人歌單 -> 選擇主播
    const bulkPlaylistVtSelect = document.getElementById('bulk-playlist-vtuber-id');
    if (bulkPlaylistVtSelect) {
        bulkPlaylistVtSelect.innerHTML = '<option value="">-- 請選擇主播 --</option>';
        vtubers.forEach(vt => {
            bulkPlaylistVtSelect.innerHTML += `<option value="${vt.id}">${vt.name_main}</option>`;
        });
    }
}

export function addCurateSetlistRow(defaultSongId = null, defaultSongTitle = '') {
    const container = document.getElementById('curate-rows-container');
    if (!container) return null;
    
    const row = document.createElement('div');
    row.className = 'curate-setlist-row';
    row.style.cssText = 'display: grid; grid-template-columns: 1.3fr 0.8fr 1.3fr 1fr auto; gap: 10px; align-items: start; margin-bottom: 10px; background: rgba(255,255,255,0.015); border: 1px solid var(--border-color); padding: 12px; border-radius: 8px;';
    
    row.innerHTML = `
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11px; color:#64748b;">選擇歌曲 <span class="required">*</span></label>
            <div class="searchable-select-container">
                <input type="text" class="row-song-search" placeholder="搜尋並點選歌曲..." autocomplete="off" value="${defaultSongTitle}">
                <input type="hidden" class="row-song-id" value="${defaultSongId || ''}">
                <div class="autocomplete-dropdown"></div>
            </div>
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11px; color:#64748b;">時間軸 (HH:MM:SS 或 MM:SS) <span class="required">*</span></label>
            <input type="text" class="row-timestamp" placeholder="例如 01:23:45" value="00:00:00" style="font-family:monospace; font-weight:600;" required>
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11px; color:#64748b;">演唱主播 (打字搜尋選取) <span class="required">*</span></label>
            <div class="searchable-select-container">
                <input type="text" class="row-singers-search" placeholder="搜尋主播..." autocomplete="off">
                <div class="autocomplete-dropdown"></div>
            </div>
            <div class="selected-tags-container" style="display:flex; flex-wrap:wrap; gap:5px; margin-top:6px;"></div>
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label style="font-size:11px; color:#64748b;">演唱備註 (選填)</label>
            <input type="text" class="row-note" placeholder="例如 Acapella, 聯動合唱">
        </div>
        <button type="button" class="btn btn-secondary btn-remove-row" style="margin-top: 19px; padding: 8px; color:var(--neon-pink); border-color:rgba(255,0,127,0.15); height: 38px;" title="刪除此列"><i class="fa-solid fa-trash-can"></i></button>
    `;
    
    container.appendChild(row);
    
    let rowSelectedSingers = [];
    
    const songInput = row.querySelector('.row-song-search');
    const songIdHidden = row.querySelector('.row-song-id');
    const songDropdown = row.querySelector('.row-song-search + input + .autocomplete-dropdown');
    
    setupDropdownFilterNormal(songInput, songDropdown, () => state.cacheSongs, (item) => item.title_main, (selectedItem) => {
        songInput.value = selectedItem.title_main;
        songIdHidden.value = selectedItem.id;
    });
    
    const singerInput = row.querySelector('.row-singers-search');
    const singerDropdown = row.querySelector('.row-singers-search + .autocomplete-dropdown');
    const tagsContainer = row.querySelector('.selected-tags-container');
    
    function renderRowTags() {
        tagsContainer.innerHTML = '';
        rowSelectedSingers.forEach(vt => {
            const tag = document.createElement('span');
            tag.className = 'selected-tag-pill singer-tag';
            tag.style.cssText = 'padding: 2px 8px; font-size:11px; margin-top:2px;';
            tag.innerHTML = `
                ${vt.name_main}
                <button type="button" class="tag-remove-btn" style="font-size:10px;">&times;</button>
            `;
            tag.querySelector('.tag-remove-btn').addEventListener('click', () => {
                rowSelectedSingers = rowSelectedSingers.filter(v => v.id !== vt.id);
                renderRowTags();
            });
            tagsContainer.appendChild(tag);
        });
    }
    
    setupDropdownFilterNormal(singerInput, singerDropdown, () => state.cacheVtubers, (item) => item.name_main, (selectedItem) => {
        if (!rowSelectedSingers.some(v => v.id === selectedItem.id)) {
            rowSelectedSingers.push(selectedItem);
            renderRowTags();
        }
        singerInput.value = '';
    });
    
    row.querySelector('.btn-remove-row').addEventListener('click', () => {
        if (container.querySelectorAll('.curate-setlist-row').length > 1) {
            row.remove();
        } else {
            showToast('請至少保留一首曲目列！', 'error');
        }
    });
    
    row.getSingers = () => rowSelectedSingers;
    row.setSingers = (list) => {
        rowSelectedSingers = list;
        renderRowTags();
    };
    
    return row;
}

export function setupCurateModalListeners() {
    const curateModal = document.getElementById('curate-setlist-modal');
    if (!curateModal) return;
    
    const closeCurateBtn = document.getElementById('btn-close-curate-modal');
    const cancelCurateBtn = document.getElementById('btn-curate-cancel');
    const addCurateRowBtn = document.getElementById('btn-curate-add-row');

    if (closeCurateBtn) {
        closeCurateBtn.addEventListener('click', () => {
            curateModal.classList.remove('active');
        });
    }
    if (cancelCurateBtn) {
        cancelCurateBtn.addEventListener('click', () => {
            curateModal.classList.remove('active');
        });
    }
    if (addCurateRowBtn) {
        addCurateRowBtn.addEventListener('click', () => {
            addCurateSetlistRow();
        });
    }

    // 彈出視窗：智慧解析時間軸
    const curateParseBtn = document.getElementById('btn-curate-parse');
    if (curateParseBtn) {
        curateParseBtn.addEventListener('click', () => {
            const textarea = document.getElementById('curate-parse-textarea');
            const container = document.getElementById('curate-rows-container');
            if (!textarea || !container) return;
            
            const text = textarea.value.trim();
            if (!text) {
                showToast('解析內容不能為空！', 'error');
                return;
            }
            
            const lines = text.split('\n');
            let parsedCount = 0;
            const parsedItems = [];
            const regex = /^(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})\s+(.+)$/;
            
            lines.forEach(line => {
                const rowStr = line.trim();
                if (!rowStr) return;
                
                const match = rowStr.match(regex);
                if (match) {
                    const timeStr = match[1];
                    const songTitle = match[2].replace(/^[-\s\.\/]+/, '').trim();
                    parsedItems.push({ time: timeStr, title: songTitle });
                    parsedCount++;
                }
            });
            
            if (parsedItems.length === 0) {
                showToast('找不到符合「時間點 歌名」格式的內容！', 'error');
                return;
            }
            
            container.innerHTML = '';
            
            // 預設主播是目前所選的主播
            const currentVt = state.selectedVtuberId ? state.cacheVtubers.find(v => v.id == state.selectedVtuberId) : null;
            
            parsedItems.forEach(item => {
                const matchedSong = state.cacheSongs.find(s => 
                    s.title_main.toLowerCase() === item.title.toLowerCase() || 
                    (s.title_ja && s.title_ja.toLowerCase() === item.title.toLowerCase()) ||
                    (s.title_zh && s.title_zh.toLowerCase() === item.title.toLowerCase())
                );
                
                const songId = matchedSong ? matchedSong.id : null;
                const displayTitle = matchedSong ? matchedSong.title_main : item.title;
                
                const row = addCurateSetlistRow(songId, displayTitle);
                if (row) {
                    row.querySelector('.row-timestamp').value = formatTimeToHHMMSS(item.time);
                    if (currentVt) {
                        row.setSingers([currentVt]);
                    }
                }
            });
            
            showToast(`🎉 成功解析並填入 ${parsedCount} 首曲目！`);
            textarea.value = '';
        });
    }

    // 彈出視窗：批次時間軸表單提交監聽
    const curateForm = document.getElementById('form-curate-modal');
    if (curateForm) {
        curateForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const videoId = document.getElementById('curate-video-id').value;
            if (!videoId) {
                showToast('請選擇收錄的直播/影片！', 'error');
                return;
            }
            
            const rowElements = document.querySelectorAll('.curate-setlist-row');
            if (rowElements.length === 0) {
                showToast('曲目列表不可為空！', 'error');
                return;
            }
            
            const recordsPayload = [];
            let validationFailed = false;
            
            rowElements.forEach((row, idx) => {
                const songTitle = row.querySelector('.row-song-search').value.trim();
                const timeStr = row.querySelector('.row-timestamp').value;
                const note = row.querySelector('.row-note').value || null;
                const singers = row.getSingers().map(s => s.name_main);
                
                if (!songTitle) {
                    showToast(`第 ${idx + 1} 列歌曲名稱不能為空！`, 'error');
                    validationFailed = true;
                    return;
                }
                if (singers.length === 0) {
                    showToast(`第 ${idx + 1} 列未指定演唱主播！`, 'error');
                    validationFailed = true;
                    return;
                }
                
                recordsPayload.push({
                    song_title: songTitle,
                    video_id: videoId,
                    timestamp_seconds: parseTimeToSeconds(timeStr),
                    note: note,
                    singers: singers,
                    song_type: "cover"
                });
            });
            
            if (validationFailed) return;
            
            try {
                const response = await fetch(`${API_BASE}/records/batch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(recordsPayload)
                });
                
                if (response.ok) {
                    const results = await response.json();
                    showToast(`🎉 已成功登錄 ${results.length} 筆歌單時間軸！`);
                    curateForm.reset();
                    
                    // 關閉 Modal
                    curateModal.classList.remove('active');
                    
                    const { fetchAllData } = await import('./api.js');
                    await fetchAllData();
                    
                    const { loadVtuberProfile, renderCatalog } = await import('./portal.js');
                    if (state.selectedVtuberId) {
                        loadVtuberProfile(state.selectedVtuberId);
                    } else {
                        renderCatalog();
                    }
                } else {
                    const err = await response.json();
                    showToast(`登錄歌單時出錯：${err.detail || '未知錯誤'}`, 'error');
                }
            } catch (error) {
                console.error(error);
                showToast('送出表單失敗，請確認網路連線！', 'error');
            }
        });
    }
}
