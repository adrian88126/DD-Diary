// app/static/js/lobby.js (Non-module script for file:/// compatibility)

(function () {
  var currentGalleryIndex = 0;

  function t(key) {
    return typeof window._ === 'function' ? window._(key) : key;
  }

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function toggleLobbyView() {
    var layout = document.getElementById('lobby-layout');
    var btn = document.getElementById('view-toggle-btn');
    if (!layout || !btn) return;

    var isScheduleMode = layout.classList.toggle('show-schedule');
    if (isScheduleMode) {
      btn.innerHTML = '<i class="fa-solid fa-users"></i> <span>' + escapeHtml(t('View VTubers')) + '</span>';
      btn.style.borderColor = 'rgba(52, 211, 153, 0.4)';
      btn.style.background = 'rgba(52, 211, 153, 0.08)';
      btn.style.color = 'var(--neon-green)';
    } else {
      btn.innerHTML = '<i class="fa-regular fa-calendar-days"></i> <span>' + escapeHtml(t('View Schedule')) + '</span>';
      btn.style.borderColor = 'rgba(167, 139, 250, 0.4)';
      btn.style.background = 'rgba(167, 139, 250, 0.08)';
      btn.style.color = 'var(--neon-purple)';
    }
  }

  function onLobbySearchInput() {
    var input = document.getElementById('lobby-search-input');
    var clearBtn = document.getElementById('clear-lobby-search-btn');
    var query = input ? input.value.toLowerCase().trim() : '';

    if (clearBtn) {
      clearBtn.style.display = query ? 'block' : 'none';
    }

    document.querySelectorAll('#vtuber-grid-container .vtuber-card').forEach(function (card) {
      var searchText = card.getAttribute('data-search-text') || '';
      card.style.display = searchText.toLowerCase().includes(query) ? '' : 'none';
    });

    document.querySelectorAll('#schedule-list .schedule-item-card').forEach(function (card) {
      var searchText = card.getAttribute('data-search-text') || '';
      card.style.display = searchText.toLowerCase().includes(query) ? '' : 'none';
    });
  }

  function clearLobbySearch() {
    var input = document.getElementById('lobby-search-input');
    if (input) {
      input.value = '';
      onLobbySearchInput();
      input.focus();
    }
  }

  function filterScheduleTab(vtuberId, btnEl) {
    document.querySelectorAll('.schedule-tab-btn').forEach(function (btn) {
      btn.classList.remove('active');
    });
    if (btnEl) btnEl.classList.add('active');

    document.querySelectorAll('#schedule-list .schedule-item-card').forEach(function (card) {
      if (vtuberId === 'all') {
        card.style.display = '';
      } else {
        var cardVtId = card.getAttribute('data-vtuber-id');
        card.style.display = (cardVtId === String(vtuberId)) ? '' : 'none';
      }
    });
  }

  function openScheduleGallery(index) {
    var items = window.scheduleGalleryItems || [];
    if (items.length === 0) return;
    currentGalleryIndex = (index + items.length) % items.length;
    var item = items[currentGalleryIndex];

    var img = document.getElementById('schedule-lightbox-img');
    var caption = document.getElementById('schedule-lightbox-caption');
    var modal = document.getElementById('schedule-lightbox-modal');

    if (img && caption && modal) {
      img.src = item.url;
      caption.innerHTML = '<span style="color:var(--neon-purple);">' + escapeHtml(item.name) + '</span> - '
        + escapeHtml(t('Weekly Schedule')) + ' (' + (currentGalleryIndex + 1) + ' / ' + items.length + ')';
      modal.classList.add('active');
    }
  }

  function openScheduleGalleryByVtuberId(vtuberId) {
    var items = window.scheduleGalleryItems || [];
    var index = items.findIndex(function (item) {
      return item.vtuberId === vtuberId;
    });
    if (index !== -1) {
      openScheduleGallery(index);
    }
  }

  function closeScheduleLightbox() {
    var modal = document.getElementById('schedule-lightbox-modal');
    if (modal) modal.classList.remove('active');
  }

  function prevScheduleImage() {
    openScheduleGallery(currentGalleryIndex - 1);
  }

  function nextScheduleImage() {
    openScheduleGallery(currentGalleryIndex + 1);
  }

  document.addEventListener('keydown', function (e) {
    var modal = document.getElementById('schedule-lightbox-modal');
    if (modal && modal.classList.contains('active')) {
      if (e.key === 'ArrowLeft') prevScheduleImage();
      if (e.key === 'ArrowRight') nextScheduleImage();
      if (e.key === 'Escape') closeScheduleLightbox();
    }
  });

  window.toggleLobbyView = toggleLobbyView;
  window.onLobbySearchInput = onLobbySearchInput;
  window.clearLobbySearch = clearLobbySearch;
  window.filterScheduleTab = filterScheduleTab;
  window.openScheduleGalleryByVtuberId = openScheduleGalleryByVtuberId;
  window.openScheduleGallery = openScheduleGallery;
  window.closeScheduleLightbox = closeScheduleLightbox;
  window.prevScheduleImage = prevScheduleImage;
  window.nextScheduleImage = nextScheduleImage;
})();
