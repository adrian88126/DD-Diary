// app/static/js/artists.js (Non-module script for file:/// compatibility)

(function () {
  var PAGE_SIZE = 60;
  var catalog = window.ARTIST_CATALOG_DATA || { vtubers: [], artists: [] };
  var allArtists = Array.isArray(catalog.artists) ? catalog.artists : [];
  var allVtubers = Array.isArray(catalog.vtubers) ? catalog.vtubers : [];

  var vtuberMap = {};
  allVtubers.forEach(function (vt) {
    vtuberMap[vt.id] = vt;
  });

  var artistMap = {};
  var songMap = {};
  var recordMap = {};
  allArtists.forEach(function (artist) {
    artistMap[artist.id] = artist;
    (artist.songs || []).forEach(function (song) {
      songMap[song.id] = song;
      (song.records || []).forEach(function (rec) {
        recordMap[rec.id] = { artist: artist, song: song, record: rec };
      });
    });
  });

  var filteredArtists = [];
  var visibleLimit = PAGE_SIZE;
  var searchQuery = '';
  var currentSort = 'records';
  var currentVtuberFilter = 'all';
  var wikidataOnly = false;
  var selectedArtistId = null;

  // Player state
  var ytPlayer = null;
  var pendingPlayItem = null;
  var playlist = [];
  var currentPlayIndex = -1;
  var currentPlayingRecId = null;
  var isAutoplay = true;
  var isShuffle = false;
  var shuffleHistory = [];

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () {
        fallbackCopy(text);
      });
    }
    fallbackCopy(text);
    return Promise.resolve();
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  function buildShareUrl(vtuberId, videoId, timestamp) {
    var vt = vtuberMap[vtuberId];
    var slug = vt ? vt.share_slug : String(vtuberId || '');
    var base = window.SHARE_BASE_URL || '/share/';
    if (window.IS_STATIC_MODE) {
      return base + slug + '/index.html?play=' + encodeURIComponent(videoId) + '&t=' + encodeURIComponent(String(timestamp || 0));
    }
    return base + slug + '?play=' + encodeURIComponent(videoId) + '&t=' + encodeURIComponent(String(timestamp || 0));
  }

  function artistMatchesSearch(artist, q) {
    if (!q) return true;
    var fields = [
      artist.name_main,
      artist.name_en,
      artist.name_ja,
      artist.name_zh,
      artist.name_romaji,
      artist.wikidata_id
    ];
    for (var i = 0; i < fields.length; i++) {
      if (fields[i] && String(fields[i]).toLowerCase().indexOf(q) !== -1) {
        return true;
      }
    }
    var songs = artist.songs || [];
    for (var j = 0; j < songs.length; j++) {
      if (songs[j].title_main && songs[j].title_main.toLowerCase().indexOf(q) !== -1) {
        return true;
      }
    }
    return false;
  }

  function getArtistStatsForFilter(artist) {
    if (currentVtuberFilter === 'all') {
      return {
        songCount: artist.song_count || 0,
        recordCount: artist.record_count || 0,
        vtuberCount: (artist.vtuber_ids || []).length
      };
    }
    var vtId = Number(currentVtuberFilter);
    var sCount = 0;
    var rCount = 0;
    (artist.songs || []).forEach(function (song) {
      var matching = (song.records || []).filter(function (rec) {
        return rec.vtuber_id === vtId;
      });
      if (matching.length > 0) {
        sCount += 1;
        rCount += matching.length;
      }
    });
    return {
      songCount: sCount,
      recordCount: rCount,
      vtuberCount: sCount > 0 ? 1 : 0
    };
  }

  function applyFiltersAndSort() {
    var q = searchQuery.trim().toLowerCase();
    filteredArtists = allArtists.filter(function (artist) {
      if (wikidataOnly && !artist.wikidata_id) return false;
      if (currentVtuberFilter !== 'all') {
        var vtId = Number(currentVtuberFilter);
        if (!artist.vtuber_ids || artist.vtuber_ids.indexOf(vtId) === -1) return false;
      }
      return artistMatchesSearch(artist, q);
    });

    filteredArtists.sort(function (a, b) {
      var sa = getArtistStatsForFilter(a);
      var sb = getArtistStatsForFilter(b);
      if (currentSort === 'records') {
        return (sb.recordCount - sa.recordCount) || (sb.songCount - sa.songCount) || a.name_main.localeCompare(b.name_main, 'zh-Hant');
      }
      if (currentSort === 'songs') {
        return (sb.songCount - sa.songCount) || (sb.recordCount - sa.recordCount) || a.name_main.localeCompare(b.name_main, 'zh-Hant');
      }
      if (currentSort === 'vtubers') {
        return (sb.vtuberCount - sa.vtuberCount) || (sb.recordCount - sa.recordCount) || a.name_main.localeCompare(b.name_main, 'zh-Hant');
      }
      return a.name_main.localeCompare(b.name_main, 'zh-Hant');
    });

    updateStatsBar();
    renderArtistList();

    if (filteredArtists.length > 0) {
      var stillVisible = filteredArtists.some(function (a) { return a.id === selectedArtistId; });
      if (!stillVisible) {
        selectedArtistId = filteredArtists[0].id;
      }
      renderSelectedArtist(false);
    } else {
      selectedArtistId = null;
      renderEmptyDetail();
    }
  }

  function updateStatsBar() {
    var totalEl = document.getElementById('stat-total-artists');
    var wdEl = document.getElementById('stat-wikidata-artists');
    var filtEl = document.getElementById('stat-filtered-artists');
    var wdCount = allArtists.filter(function (a) { return !!a.wikidata_id; }).length;
    if (totalEl) totalEl.textContent = String(allArtists.length);
    if (wdEl) wdEl.textContent = String(wdCount);
    if (filtEl) filtEl.textContent = String(filteredArtists.length);
  }

  function renderVtuberFilterTabs() {
    var container = document.getElementById('vtuber-filter-tabs');
    if (!container) return;
    var html = '<button type="button" class="filter-pill-btn ' + (currentVtuberFilter === 'all' ? 'active' : '') + '" data-vtuber="all" onclick="filterArtistVtuber(\'all\')">全部主播</button>';
    allVtubers.forEach(function (vt) {
      var shortName = (vt.name_main || '').split(' ')[0];
      var isAct = String(currentVtuberFilter) === String(vt.id);
      html += '<button type="button" class="filter-pill-btn ' + (isAct ? 'active' : '') + '" data-vtuber="' + vt.id + '" onclick="filterArtistVtuber(' + vt.id + ')">'
        + '<span style="width:8px;height:8px;border-radius:50%;display:inline-block;background:' + escapeHtml(vt.theme_color || '#a78bfa') + ';"></span>'
        + escapeHtml(shortName) + '</button>';
    });
    container.innerHTML = html;
  }

  function renderArtistList() {
    var listEl = document.getElementById('artist-catalog-list');
    var loadBtn = document.getElementById('load-more-artists-btn');
    if (!listEl) return;

    if (filteredArtists.length === 0) {
      listEl.innerHTML = '<div style="text-align:center; padding:28px; color:var(--text-muted); font-size:13px;">找不到符合條件的原唱歌手</div>';
      if (loadBtn) loadBtn.style.display = 'none';
      return;
    }

    var slice = filteredArtists.slice(0, visibleLimit);
    listEl.innerHTML = slice.map(function (artist) {
      var st = getArtistStatsForFilter(artist);
      var aliases = [artist.name_en, artist.name_ja, artist.name_zh, artist.name_romaji]
        .filter(function (x) { return x && x.trim() && x.trim() !== artist.name_main; })
        .join(' · ');
      var isActive = artist.id === selectedArtistId;
      var qidHtml = artist.wikidata_id ? '<span class="qid-mini-badge">' + escapeHtml(artist.wikidata_id) + '</span>' : '';

      return '<div class="artist-list-item ' + (isActive ? 'active' : '') + '" onclick="selectArtist(' + artist.id + ')">'
        + '<div class="artist-item-top">'
        + '<div class="artist-item-name">' + escapeHtml(artist.name_main) + '</div>'
        + qidHtml
        + '</div>'
        + (aliases ? '<div class="artist-item-aliases">' + escapeHtml(aliases) + '</div>' : '')
        + '<div class="artist-item-meta">'
        + '<span><i class="fa-solid fa-music"></i> ' + st.songCount + ' 首</span>'
        + '<span><i class="fa-solid fa-microphone-lines"></i> ' + st.recordCount + ' 次</span>'
        + '<span><i class="fa-solid fa-user-group"></i> ' + st.vtuberCount + ' 位主播</span>'
        + '</div>'
        + '</div>';
    }).join('');

    if (loadBtn) {
      if (filteredArtists.length > visibleLimit) {
        loadBtn.style.display = 'block';
        loadBtn.textContent = '載入更多歌手 (尚餘 ' + (filteredArtists.length - visibleLimit) + ' 位)';
      } else {
        loadBtn.style.display = 'none';
      }
    }
  }

  function renderEmptyDetail() {
    var headerEl = document.getElementById('artist-detail-header');
    var songsEl = document.getElementById('artist-songs-list');
    if (headerEl) {
      headerEl.innerHTML = '<div style="text-align:center; padding:24px; color:var(--text-muted);">目前篩選條件下沒有歌手資料，請試著清空搜尋條件</div>';
    }
    if (songsEl) {
      songsEl.innerHTML = '';
    }
  }

  function buildArtistPlaylist(artist) {
    if (!artist) return [];
    var list = [];
    var vtFilter = currentVtuberFilter === 'all' ? null : Number(currentVtuberFilter);
    (artist.songs || []).forEach(function (song) {
      (song.records || []).forEach(function (rec) {
        if (vtFilter !== null && rec.vtuber_id !== vtFilter) return;
        list.push({
          recId: rec.id,
          artistId: artist.id,
          songId: song.id,
          videoId: rec.video_id,
          timestamp: rec.t || 0,
          title: song.title_main,
          vtuberId: rec.vtuber_id,
          date: rec.date || '',
          videoTitle: rec.video_title || ''
        });
      });
    });
    return list;
  }

  function renderSelectedArtist(shouldScroll) {
    var artist = artistMap[selectedArtistId];
    if (!artist) {
      renderEmptyDetail();
      return;
    }

    var headerEl = document.getElementById('artist-detail-header');
    var songsEl = document.getElementById('artist-songs-list');
    var st = getArtistStatsForFilter(artist);

    var langChips = [];
    if (artist.name_en) langChips.push({ label: 'EN', val: artist.name_en });
    if (artist.name_ja) langChips.push({ label: 'JA', val: artist.name_ja });
    if (artist.name_zh) langChips.push({ label: 'ZH', val: artist.name_zh });
    if (artist.name_romaji) langChips.push({ label: 'Romaji', val: artist.name_romaji });

    var langHtml = langChips.length > 0
      ? '<div class="artist-names-grid">' + langChips.map(function (c) {
          return '<span class="lang-chip"><span class="lang-chip-label">' + escapeHtml(c.label) + '</span>' + escapeHtml(c.val) + '</span>';
        }).join('') + '</div>'
      : '<div style="font-size:12.5px; color:var(--text-muted); margin-top:6px;">尚未填寫其他語言別名</div>';

    var wikidataHtml = artist.wikidata_id
      ? '<div class="wikidata-chip-group">'
          + '<a class="wikidata-link-badge" href="https://www.wikidata.org/wiki/' + encodeURIComponent(artist.wikidata_id) + '" target="_blank" rel="noopener noreferrer">'
          + '<i class="fa-solid fa-database"></i> Wikidata: ' + escapeHtml(artist.wikidata_id) + ' <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:10.5px;"></i></a>'
          + '<button type="button" class="artist-action-btn" style="padding:4px 10px; font-size:12px;" onclick="copyArtistQid()"><i class="fa-regular fa-copy"></i> 複製 QID</button>'
        + '</div>'
      : '<div class="wikidata-chip-group"><span style="font-size:12px; color:var(--text-muted);">尚未連結 Wikidata QID</span></div>';

    if (headerEl) {
      headerEl.innerHTML =
        '<div class="artist-header-top">'
        + '<div>'
        + '<h2 class="artist-detail-title">' + escapeHtml(artist.name_main) + '</h2>'
        + '<div style="font-size:13px; color:var(--text-muted); display:flex; gap:12px; flex-wrap:wrap;">'
        + '<span><i class="fa-solid fa-music"></i> 收錄 <strong>' + st.songCount + '</strong> 首歌曲</span>'
        + '<span><i class="fa-solid fa-microphone-lines"></i> 全站演唱 <strong>' + st.recordCount + '</strong> 次</span>'
        + '<span><i class="fa-solid fa-user-group"></i> 跨 <strong>' + st.vtuberCount + '</strong> 位主播</span>'
        + '</div>'
        + langHtml
        + wikidataHtml
        + '</div>'
        + '</div>'
        + '<div class="action-btn-row">'
        + '<button type="button" class="artist-action-btn primary" onclick="playArtistAll(false)"><i class="fa-solid fa-play"></i> 播放此歌手全部</button>'
        + '<button type="button" class="artist-action-btn" onclick="playArtistAll(true)"><i class="fa-solid fa-shuffle"></i> 隨機連播</button>'
        + '<button type="button" class="artist-action-btn" onclick="shareSelectedArtist()"><i class="fa-solid fa-share-nodes"></i> 分享此歌手歌單</button>'
        + '</div>';
    }

    if (songsEl) {
      var vtFilter = currentVtuberFilter === 'all' ? null : Number(currentVtuberFilter);
      var q = searchQuery.trim().toLowerCase();
      var songs = (artist.songs || []).filter(function (song) {
        if (vtFilter === null) return true;
        return (song.records || []).some(function (rec) { return rec.vtuber_id === vtFilter; });
      });

      if (songs.length === 0) {
        songsEl.innerHTML = '<div style="text-align:center; padding:24px; color:var(--text-muted);">此篩選條件下尚無演唱紀錄</div>';
      } else {
        songsEl.innerHTML = songs.map(function (song) {
          var recs = (song.records || []).filter(function (rec) {
            return vtFilter === null || rec.vtuber_id === vtFilter;
          });
          var titleHighlight = q && song.title_main && song.title_main.toLowerCase().indexOf(q) !== -1
            ? ' style="box-shadow:0 0 0 1px var(--neon-purple);"'
            : '';

          var recPills = recs.map(function (rec) {
            var vt = vtuberMap[rec.vtuber_id] || {};
            var vtName = (vt.name_main || 'VTuber').split(' ')[0];
            var vtColor = vt.theme_color || '#a78bfa';
            var timeStr = typeof formatSeconds === 'function' ? formatSeconds(rec.t) : String(rec.t || 0);
            var jumpUrl = buildShareUrl(rec.vtuber_id, rec.video_id, rec.t || 0);
            var playingCls = currentPlayingRecId === rec.id ? ' is-playing' : '';
            var noteText = rec.note ? ' · ' + rec.note : '';

            return '<div class="record-pill-group' + playingCls + '" data-rec-id="' + rec.id + '" style="--vt-color:' + escapeHtml(vtColor) + ';">'
              + '<button type="button" class="record-play-btn" onclick="playArtistRecord(' + artist.id + ', ' + song.id + ', ' + rec.id + ')" title="' + escapeHtml((rec.video_title || '') + (rec.date ? ' (' + rec.date + ')' : '')) + '">'
              + '<span class="record-vt-dot"></span>'
              + '<span><strong>' + escapeHtml(vtName) + '</strong>' + (rec.date ? ' · ' + escapeHtml(rec.date) : '') + ' · ' + escapeHtml(timeStr) + escapeHtml(noteText) + '</span>'
              + '</button>'
              + '<a href="' + escapeHtml(jumpUrl) + '" class="record-jump-link" title="前往主播專頁並跳轉至此時間軸"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>'
              + '</div>';
          }).join('');

          return '<div class="song-group-card"' + titleHighlight + '>'
            + '<div class="song-group-header">'
            + '<div class="song-group-title">'
            + '<span>' + escapeHtml(song.title_main) + '</span>'
            + '<span class="qid-mini-badge" style="color:var(--neon-purple); border-color:rgba(167,139,250,0.35); background:rgba(167,139,250,0.12);">' + recs.length + ' 次演唱</span>'
            + '<span class="qid-mini-badge" style="color:var(--text-muted); border-color:var(--card-border); background:var(--card-bg);">' + escapeHtml(song.song_type || 'cover') + '</span>'
            + '</div>'
            + '<button type="button" class="artist-action-btn" style="padding:4px 10px; font-size:12px;" onclick="copyArtistSongTitle(event, ' + song.id + ')"><i class="fa-regular fa-copy"></i> 複製歌名</button>'
            + '</div>'
            + '<div class="song-records-wrap">' + recPills + '</div>'
            + '</div>';
        }).join('');
      }
    }

    if (shouldScroll && window.innerWidth <= 992) {
      var detailPanel = document.getElementById('artist-detail-panel');
      if (detailPanel && detailPanel.scrollIntoView) {
        detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  function updateUrlParam(artistId) {
    try {
      var url = new URL(window.location.href);
      if (artistId) {
        url.searchParams.set('artist', String(artistId));
      } else {
        url.searchParams.delete('artist');
      }
      window.history.replaceState(null, '', url.toString());
    } catch (e) {}
  }

  function highlightPlayingPill(recId) {
    document.querySelectorAll('.record-pill-group').forEach(function (el) {
      if (Number(el.getAttribute('data-rec-id')) === recId) {
        el.classList.add('is-playing');
      } else {
        el.classList.remove('is-playing');
      }
    });
  }

  function syncPlayerControlsUI() {
    var autoBtn = document.getElementById('artist-autoplay-btn');
    var shufBtn = document.getElementById('artist-shuffle-btn');
    if (autoBtn) {
      if (isAutoplay) autoBtn.classList.add('active');
      else autoBtn.classList.remove('active');
    }
    if (shufBtn) {
      if (isShuffle) shufBtn.classList.add('active');
      else shufBtn.classList.remove('active');
    }
  }

  function updatePlayPauseButton(isPlaying) {
    var btn = document.getElementById('artist-play-pause-btn');
    if (!btn) return;
    if (isPlaying) {
      btn.innerHTML = '<i class="fa-solid fa-pause"></i> 暫停';
    } else {
      btn.innerHTML = '<i class="fa-solid fa-play"></i> 播放';
    }
  }

  function onPlayerStateChange(event) {
    if (typeof YT === 'undefined') return;
    if (event.data === YT.PlayerState.PLAYING) {
      updatePlayPauseButton(true);
    } else if (event.data === YT.PlayerState.PAUSED) {
      updatePlayPauseButton(false);
    } else if (event.data === YT.PlayerState.ENDED) {
      updatePlayPauseButton(false);
      if (isAutoplay) {
        window.artistNextSong();
      }
    }
  }

  function playItem(item, rebuildList) {
    if (!item || !item.videoId) return;
    if (rebuildList) {
      playlist = buildArtistPlaylist(artistMap[item.artistId]);
      currentPlayIndex = -1;
      for (var i = 0; i < playlist.length; i++) {
        if (playlist[i].recId === item.recId) {
          currentPlayIndex = i;
          break;
        }
      }
    }

    currentPlayingRecId = item.recId;
    highlightPlayingPill(item.recId);

    var vt = vtuberMap[item.vtuberId] || {};
    var vtName = vt.name_main || 'VTuber';
    var artist = artistMap[item.artistId];
    var artistLabel = artist ? artist.name_main : '';
    var timeStr = typeof formatSeconds === 'function' ? formatSeconds(item.timestamp || 0) : String(item.timestamp || 0);

    var titleEl = document.getElementById('artist-player-song-title');
    var infoEl = document.getElementById('artist-player-vtuber-info');
    var shareLink = document.getElementById('artist-player-share-link');
    var ytLink = document.getElementById('artist-player-yt-link');

    if (titleEl) {
      titleEl.textContent = item.title + (artistLabel ? ' — ' + artistLabel : '');
    }
    if (infoEl) {
      infoEl.innerHTML = '<span style="color:' + escapeHtml(vt.theme_color || '#a78bfa') + '; font-weight:700;"><i class="fa-solid fa-microphone"></i> ' + escapeHtml(vtName) + '</span>'
        + (item.date ? '<span>· ' + escapeHtml(item.date) + '</span>' : '')
        + '<span>· ' + escapeHtml(timeStr) + '</span>';
    }
    if (shareLink) {
      shareLink.href = buildShareUrl(item.vtuberId, item.videoId, item.timestamp || 0);
      shareLink.style.display = 'inline-flex';
    }
    if (ytLink) {
      ytLink.href = 'https://www.youtube.com/watch?v=' + encodeURIComponent(item.videoId) + '&t=' + encodeURIComponent(String(item.timestamp || 0)) + 's';
      ytLink.style.display = 'inline-flex';
    }

    if ('mediaSession' in navigator && typeof MediaMetadata !== 'undefined') {
      try {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: item.title || 'Unknown Song',
          artist: (artistLabel ? artistLabel + ' · ' : '') + vtName,
          album: 'DDDiary VTuber Song Database',
          artwork: [
            { src: 'https://img.youtube.com/vi/' + item.videoId + '/mqdefault.jpg', sizes: '320x180', type: 'image/jpeg' },
            { src: 'https://img.youtube.com/vi/' + item.videoId + '/hqdefault.jpg', sizes: '480x360', type: 'image/jpeg' }
          ]
        });
        navigator.mediaSession.setActionHandler('play', function () { window.artistTogglePlay(); });
        navigator.mediaSession.setActionHandler('pause', function () { window.artistTogglePlay(); });
        navigator.mediaSession.setActionHandler('previoustrack', function () { window.artistPrevSong(); });
        navigator.mediaSession.setActionHandler('nexttrack', function () { window.artistNextSong(); });
      } catch (e) {}
    }

    if (typeof YT === 'undefined' || !YT.Player) {
      pendingPlayItem = item;
      return;
    }

    var container = document.getElementById('artist-yt-player');
    if (!container) return;

    var onPlayerError = function (event) {
      if (ytPlayer) {
        try { ytPlayer.destroy(); } catch (e) {}
        ytPlayer = null;
      }
      container.innerHTML =
        '<div class="player-placeholder-box" style="color:#fff;">'
        + '<i class="fa-solid fa-triangle-exclamation" style="font-size:24px; color:#f87171; margin-bottom:8px; display:block;"></i>'
        + '<div style="margin-bottom:10px;">此影片無法嵌入播放 (代碼: ' + escapeHtml(event.data) + ')</div>'
        + '<a href="https://www.youtube.com/watch?v=' + encodeURIComponent(item.videoId) + '&t=' + encodeURIComponent(String(item.timestamp || 0)) + 's" target="_blank" rel="noopener noreferrer" class="artist-action-btn primary">在 YouTube 開啟</a>'
        + '</div>';
    };

    if (!ytPlayer) {
      container.innerHTML = '<div id="artist-yt-iframe"></div>';
      ytPlayer = new YT.Player('artist-yt-iframe', {
        height: '100%',
        width: '100%',
        videoId: item.videoId,
        playerVars: {
          autoplay: 1,
          start: item.timestamp || 0
        },
        events: {
          onReady: function (e) { e.target.playVideo(); },
          onError: onPlayerError,
          onStateChange: onPlayerStateChange
        }
      });
    } else {
      try {
        ytPlayer.loadVideoById({ videoId: item.videoId, startSeconds: item.timestamp || 0 });
      } catch (e) {
        container.innerHTML = '<div id="artist-yt-iframe"></div>';
        ytPlayer = new YT.Player('artist-yt-iframe', {
          height: '100%',
          width: '100%',
          videoId: item.videoId,
          playerVars: { autoplay: 1, start: item.timestamp || 0 },
          events: {
            onReady: function (ev) { ev.target.playVideo(); },
            onError: onPlayerError,
            onStateChange: onPlayerStateChange
          }
        });
      }
    }
  }

  window.onYouTubeIframeAPIReady = function () {
    if (pendingPlayItem) {
      var item = pendingPlayItem;
      pendingPlayItem = null;
      playItem(item, true);
    }
  };

  function onArtistSearchInput() {
    var input = document.getElementById('artist-search-input');
    var clearBtn = document.getElementById('clear-artist-search-btn');
    searchQuery = input ? input.value : '';
    if (clearBtn) clearBtn.style.display = searchQuery ? 'block' : 'none';
    visibleLimit = PAGE_SIZE;
    applyFiltersAndSort();
  }

  function clearArtistSearch() {
    var input = document.getElementById('artist-search-input');
    var clearBtn = document.getElementById('clear-artist-search-btn');
    if (input) input.value = '';
    searchQuery = '';
    if (clearBtn) clearBtn.style.display = 'none';
    visibleLimit = PAGE_SIZE;
    applyFiltersAndSort();
  }

  function sortArtists(mode) {
    currentSort = mode || 'records';
    document.querySelectorAll('#artist-sort-group .filter-pill-btn').forEach(function (btn) {
      if (btn.getAttribute('data-sort') === currentSort) btn.classList.add('active');
      else btn.classList.remove('active');
    });
    visibleLimit = PAGE_SIZE;
    applyFiltersAndSort();
  }

  function filterArtistVtuber(vtId) {
    currentVtuberFilter = String(vtId);
    document.querySelectorAll('#vtuber-filter-tabs .filter-pill-btn').forEach(function (btn) {
      if (btn.getAttribute('data-vtuber') === currentVtuberFilter) btn.classList.add('active');
      else btn.classList.remove('active');
    });
    visibleLimit = PAGE_SIZE;
    applyFiltersAndSort();
  }

  function toggleWikidataOnly() {
    wikidataOnly = !wikidataOnly;
    var btn = document.getElementById('wikidata-only-btn');
    if (btn) {
      if (wikidataOnly) btn.classList.add('active');
      else btn.classList.remove('active');
    }
    visibleLimit = PAGE_SIZE;
    applyFiltersAndSort();
  }

  function loadMoreArtists() {
    visibleLimit += PAGE_SIZE;
    renderArtistList();
  }

  function selectArtist(artistId) {
    if (!artistMap[artistId]) return;
    selectedArtistId = artistId;
    updateUrlParam(artistId);
    renderArtistList();
    renderSelectedArtist(true);
  }

  function playArtistRecord(artistId, songId, recId) {
    var entry = recordMap[recId];
    if (!entry) return;
    var item = {
      recId: recId,
      artistId: artistId,
      songId: songId,
      videoId: entry.record.video_id,
      timestamp: entry.record.t || 0,
      title: entry.song.title_main,
      vtuberId: entry.record.vtuber_id,
      date: entry.record.date || '',
      videoTitle: entry.record.video_title || ''
    };
    playItem(item, true);
  }

  function playArtistAll(shuffle) {
    var artist = artistMap[selectedArtistId];
    if (!artist) return;
    isAutoplay = true;
    isShuffle = !!shuffle;
    syncPlayerControlsUI();
    playlist = buildArtistPlaylist(artist);
    if (playlist.length === 0) {
      if (typeof showToast === 'function') showToast('此條件下尚無可播放紀錄', 'warning');
      return;
    }
    shuffleHistory = [];
    currentPlayIndex = isShuffle ? Math.floor(Math.random() * playlist.length) : 0;
    playItem(playlist[currentPlayIndex], false);
  }

  function artistNextSong() {
    if (playlist.length === 0) {
      playlist = buildArtistPlaylist(artistMap[selectedArtistId]);
    }
    if (playlist.length === 0) return;

    if (isShuffle) {
      if (currentPlayIndex >= 0) shuffleHistory.push(currentPlayIndex);
      if (shuffleHistory.length > 50) shuffleHistory.shift();
      var nextIdx = Math.floor(Math.random() * playlist.length);
      if (playlist.length > 1 && nextIdx === currentPlayIndex) {
        nextIdx = (nextIdx + 1) % playlist.length;
      }
      currentPlayIndex = nextIdx;
    } else {
      currentPlayIndex = (currentPlayIndex + 1) % playlist.length;
    }
    playItem(playlist[currentPlayIndex], false);
  }

  function artistPrevSong() {
    if (playlist.length === 0) {
      playlist = buildArtistPlaylist(artistMap[selectedArtistId]);
    }
    if (playlist.length === 0) return;

    if (isShuffle && shuffleHistory.length > 0) {
      currentPlayIndex = shuffleHistory.pop();
    } else {
      currentPlayIndex = (currentPlayIndex - 1 + playlist.length) % playlist.length;
    }
    playItem(playlist[currentPlayIndex], false);
  }

  function artistTogglePlay() {
    if (!ytPlayer || typeof ytPlayer.getPlayerState !== 'function') {
      playArtistAll(false);
      return;
    }
    var state = ytPlayer.getPlayerState();
    if (state === YT.PlayerState.PLAYING) {
      ytPlayer.pauseVideo();
    } else {
      ytPlayer.playVideo();
    }
  }

  function artistToggleAutoplay() {
    isAutoplay = !isAutoplay;
    syncPlayerControlsUI();
  }

  function artistToggleShuffle() {
    isShuffle = !isShuffle;
    syncPlayerControlsUI();
  }

  function copyArtistQid() {
    var artist = artistMap[selectedArtistId];
    if (!artist || !artist.wikidata_id) return;
    copyText(artist.wikidata_id).then(function () {
      if (typeof showToast === 'function') {
        showToast('已複製 Wikidata QID：' + artist.wikidata_id, 'success');
      }
    });
  }

  function shareSelectedArtist() {
    var artist = artistMap[selectedArtistId];
    if (!artist) return;
    try {
      var url = new URL(window.location.href);
      url.searchParams.set('artist', String(artist.id));
      copyText(url.toString()).then(function () {
        if (typeof showToast === 'function') {
          showToast('🔗 已複製「' + artist.name_main + '」歌單專屬連結！', 'success');
        }
      });
    } catch (e) {}
  }

  function copyArtistSongTitle(event, songId) {
    if (event) event.stopPropagation();
    var song = songMap[songId];
    if (!song) return;
    copyText(song.title_main).then(function () {
      if (typeof showToast === 'function') {
        showToast('📋 已複製歌名：「' + song.title_main + '」', 'success');
      }
    });
  }

  function initArtistsPage() {
    renderVtuberFilterTabs();
    syncPlayerControlsUI();

    try {
      var params = new URLSearchParams(window.location.search);
      var qParam = params.get('q');
      var artistParam = params.get('artist');
      if (qParam) {
        var input = document.getElementById('artist-search-input');
        var clearBtn = document.getElementById('clear-artist-search-btn');
        if (input) input.value = qParam;
        if (clearBtn) clearBtn.style.display = 'block';
        searchQuery = qParam;
      }
      if (artistParam && artistMap[Number(artistParam)]) {
        selectedArtistId = Number(artistParam);
      }
    } catch (e) {}

    applyFiltersAndSort();
    if (selectedArtistId && artistMap[selectedArtistId]) {
      var idx = filteredArtists.findIndex(function (a) { return a.id === selectedArtistId; });
      if (idx >= visibleLimit) {
        visibleLimit = idx + PAGE_SIZE;
        renderArtistList();
      }
      renderSelectedArtist(false);
    }
  }

  window.onArtistSearchInput = onArtistSearchInput;
  window.clearArtistSearch = clearArtistSearch;
  window.sortArtists = sortArtists;
  window.filterArtistVtuber = filterArtistVtuber;
  window.toggleWikidataOnly = toggleWikidataOnly;
  window.loadMoreArtists = loadMoreArtists;
  window.selectArtist = selectArtist;
  window.playArtistRecord = playArtistRecord;
  window.playArtistAll = playArtistAll;
  window.artistNextSong = artistNextSong;
  window.artistPrevSong = artistPrevSong;
  window.artistTogglePlay = artistTogglePlay;
  window.artistToggleAutoplay = artistToggleAutoplay;
  window.artistToggleShuffle = artistToggleShuffle;
  window.copyArtistQid = copyArtistQid;
  window.shareSelectedArtist = shareSelectedArtist;
  window.copyArtistSongTitle = copyArtistSongTitle;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initArtistsPage);
  } else {
    initArtistsPage();
  }
})();
