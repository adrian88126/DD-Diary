// app/static/js/admin.js
(() => {
  // 1. Table Sorting (Supports text, numbers, dates, timestamps)
  function initTableSorting() {
    const getCellValue = (tr, idx) => {
      const cell = tr.children[idx];
      if (!cell) return '';
      return (cell.innerText || cell.textContent || '').trim();
    };

    const parseVal = (str) => {
      if (!str || str === '-' || str === 'None') return null;
      
      // Check if pure number
      if (/^-?\d+(\.\d+)?$/.test(str)) {
        return parseFloat(str);
      }
      
      // Check if timestamp mm:ss or hh:mm:ss
      if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(str)) {
        const parts = str.split(':').map(Number);
        return parts.length === 3 ? parts[0] * 3600 + parts[1] * 60 + parts[2] : parts[0] * 60 + parts[1];
      }
      
      // Check if date YYYY-MM-DD
      if (/^\d{4}-\d{2}-\d{2}/.test(str)) {
        const d = Date.parse(str);
        if (!isNaN(d)) return d;
      }
      
      return str;
    };

    document.querySelectorAll('th.sortable').forEach(th => {
      if (th._sortBound) return;
      th._sortBound = true;

      th.addEventListener('click', () => {
        const table = th.closest('table');
        if (!table) return;
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        const idx = Array.from(th.parentNode.children).indexOf(th);
        
        // Toggle sorting direction using dataset
        const currentAsc = th.getAttribute('data-asc') === 'true';
        const newAsc = !currentAsc;
        
        // Clear sorting indicators on all headers in this table
        table.querySelectorAll('th.sortable').forEach(el => {
          el.classList.remove('asc', 'desc');
          el.removeAttribute('data-asc');
        });
        
        // Set new direction on clicked header
        th.setAttribute('data-asc', newAsc ? 'true' : 'false');
        th.classList.add(newAsc ? 'asc' : 'desc');

        // Sort rows
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort((a, b) => {
          const raw1 = getCellValue(a, idx);
          const raw2 = getCellValue(b, idx);
          const v1 = parseVal(raw1);
          const v2 = parseVal(raw2);
          
          if (v1 === null && v2 === null) return 0;
          if (v1 === null) return 1;
          if (v2 === null) return -1;
          
          let comparison = 0;
          if (typeof v1 === 'number' && typeof v2 === 'number') {
            comparison = v1 - v2;
          } else {
            comparison = String(v1).localeCompare(String(v2), undefined, { numeric: true, sensitivity: 'base' });
          }
          
          return newAsc ? comparison : -comparison;
        });
        
        rows.forEach(tr => tbody.appendChild(tr));
      });
    });
  }

  window.initTableSorting = initTableSorting;

  // 2. 🌟 全域篩選與 URL 狀態統一化引擎 (AdminFilterEngine)
  function initAdminFilterEngine() {
    const searchInput = document.getElementById('table-search') || document.getElementById('search-input');
    const table = document.querySelector('.data-table, .admin-data-table');
    if (!table && !searchInput) return;

    const rows = Array.from(document.querySelectorAll('.data-table tbody tr, .admin-data-table tbody tr, .search-item'));
    if (rows.length === 0) return;

    const totalCount = rows.length;
    const urlParams = new URLSearchParams(window.location.search);

    // 2.1 增強搜尋框：加入外層封裝、一鍵清空 (✕) 與筆數徽章
    let clearBtn = null;
    let countBadge = null;

    if (searchInput) {
      if (!searchInput.parentElement.classList.contains('search-wrapper')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'search-wrapper';
        searchInput.parentNode.insertBefore(wrapper, searchInput);
        wrapper.appendChild(searchInput);

        clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'search-clear-btn';
        clearBtn.innerHTML = '<i class="fa-solid fa-xmark"></i>';
        clearBtn.title = '清除搜尋';
        wrapper.appendChild(clearBtn);

        countBadge = document.createElement('span');
        countBadge.className = 'filter-count-badge';
        countBadge.innerHTML = `顯示 <strong>${totalCount}</strong> / ${totalCount} 筆`;
        wrapper.parentNode.appendChild(countBadge);
      } else {
        clearBtn = searchInput.parentElement.querySelector('.search-clear-btn');
        countBadge = searchInput.parentElement.parentElement.querySelector('.filter-count-badge');
      }

      // 從 URL 讀取既有搜尋字串還原
      if (urlParams.has('search') && !searchInput.value) {
        searchInput.value = urlParams.get('search');
      }

      if (clearBtn) {
        clearBtn.style.display = searchInput.value ? 'block' : 'none';
        clearBtn.addEventListener('click', () => {
          searchInput.value = '';
          clearBtn.style.display = 'none';
          applyAllFilters();
          searchInput.focus();
        });
      }
    }

    // 2.2 關聯篩選下拉選單 (VTuber / Tag / Author / Type / Records)
    const filterSelectors = {
      vtuber: document.getElementById('vtuber-filter') || document.getElementById('filter-vtuber'),
      author: document.getElementById('author-filter') || document.getElementById('filter-author'),
      tag: document.getElementById('tag-filter') || document.getElementById('filter-tag'),
      records: document.getElementById('records-filter')
    };

    // 從 URL 還原下拉選單
    if (filterSelectors.vtuber && urlParams.has('vtuber_id')) {
      filterSelectors.vtuber.value = urlParams.get('vtuber_id');
    }
    if (filterSelectors.author && urlParams.has('author_id')) {
      filterSelectors.author.value = urlParams.get('author_id');
    }
    if (filterSelectors.tag && urlParams.has('tag')) {
      filterSelectors.tag.value = urlParams.get('tag');
    }
    if (filterSelectors.records && urlParams.has('records')) {
      filterSelectors.records.value = urlParams.get('records');
    }

    // 2.3 統一過濾執行核心
    function applyAllFilters() {
      const searchTerm = (searchInput ? searchInput.value.trim().toLowerCase() : '');
      const vtuberVal = filterSelectors.vtuber ? filterSelectors.vtuber.value : '';
      const authorVal = filterSelectors.author ? filterSelectors.author.value : '';
      const tagVal = filterSelectors.tag ? filterSelectors.tag.value.toLowerCase() : '';
      const recordsVal = filterSelectors.records ? filterSelectors.records.value : '';

      if (clearBtn && searchInput) {
        clearBtn.style.display = searchTerm ? 'block' : 'none';
      }

      let visibleCount = 0;
      rows.forEach(row => {
        const text = (row.querySelector('.search-text') ? row.querySelector('.search-text').textContent : row.textContent).toLowerCase();
        const rowVtuber = row.dataset.vtuber || row.dataset.vtuberId || '';
        const rowAuthor = row.dataset.author || row.dataset.authorId || '';
        const rowTags = (row.dataset.tags || '').toLowerCase();
        const rowRecords = parseInt(row.dataset.records || '0', 10);

        const matchSearch = !searchTerm || text.includes(searchTerm);
        const matchVtuber = !vtuberVal || rowVtuber === vtuberVal || text.includes(vtuberVal.toLowerCase());
        const matchAuthor = !authorVal || rowAuthor === authorVal;
        const matchTag = !tagVal || rowTags.includes(tagVal);
        const matchRecords = !recordsVal || (recordsVal === 'zero' && rowRecords === 0) || (recordsVal === 'has' && rowRecords > 0);

        if (matchSearch && matchVtuber && matchAuthor && matchTag && matchRecords) {
          row.style.display = '';
          visibleCount++;
        } else {
          row.style.display = 'none';
          const cb = row.querySelector('.row-cb');
          if (cb) cb.checked = false;
        }
      });

      if (countBadge) {
        countBadge.innerHTML = `顯示 <strong>${visibleCount}</strong> / ${totalCount} 筆`;
      }

      // 同步寫入網址 Query String (不刷新頁面)
      const currentUrl = new URL(window.location.href);
      if (searchTerm) currentUrl.searchParams.set('search', searchTerm);
      else currentUrl.searchParams.delete('search');

      if (vtuberVal) currentUrl.searchParams.set('vtuber_id', vtuberVal);
      else currentUrl.searchParams.delete('vtuber_id');

      if (authorVal) currentUrl.searchParams.set('author_id', authorVal);
      else currentUrl.searchParams.delete('author_id');

      if (tagVal) currentUrl.searchParams.set('tag', tagVal);
      else currentUrl.searchParams.delete('tag');

      if (recordsVal) currentUrl.searchParams.set('records', recordsVal);
      else currentUrl.searchParams.delete('records');

      window.history.replaceState({}, '', currentUrl.pathname + currentUrl.search + currentUrl.hash);

      // 自動同步抽屜 Form action 帶有目前搜尋條件
      updateDrawerFormActions();
    }

    let debounceTimer = null;
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(applyAllFilters, 120);
      });
    }

    Object.values(filterSelectors).forEach(sel => {
      if (sel) sel.addEventListener('change', applyAllFilters);
    });

    // 初始執行一次過濾還原
    applyAllFilters();
  }

  // 3. 🎯 表單 Action 附帶搜尋狀態與 Anchor 錨點
  function updateDrawerFormActions(targetRowId = '') {
    const forms = document.querySelectorAll('#form-drawer form, .drawer form');
    const search = window.location.search;
    forms.forEach(form => {
      if (!form.dataset.baseAction) {
        form.dataset.baseAction = form.action.split('?')[0];
      }
      let newAction = form.dataset.baseAction;
      const params = new URLSearchParams(search);
      if (targetRowId) {
        params.set('_anchor', targetRowId);
      }
      const qs = params.toString();
      form.action = newAction + (qs ? '?' + qs : '');
    });
  }

  window.updateDrawerFormActions = updateDrawerFormActions;

  // 4. ✨ 儲存後自動捲動至剛編輯的行並柔光高亮
  function initAnchorHighlight() {
    const params = new URLSearchParams(window.location.search);
    let anchorId = params.get('_anchor') || window.location.hash.replace('#', '');
    if (!anchorId) return;

    let targetEl = document.getElementById(anchorId);
    if (!targetEl) {
      targetEl = document.querySelector(`tr[data-id="${anchorId}"], tr[data-vid="${anchorId}"]`);
    }

    if (targetEl) {
      setTimeout(() => {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetEl.classList.add('row-highlight');
        setTimeout(() => targetEl.classList.remove('row-highlight'), 3000);
      }, 200);
    }
  }

  // 5. 🛡️ 表單未儲存防手滑提示與快捷鍵支援
  function initDrawerEnhancements() {
    const drawers = document.querySelectorAll('.drawer');
    drawers.forEach(drawer => {
      let isDirty = false;
      const form = drawer.querySelector('form');
      if (form) {
        form.addEventListener('input', () => { isDirty = true; });
        form.addEventListener('submit', () => { isDirty = false; });

        // 支援 Ctrl + Enter / Cmd + Enter 直接提交
        form.addEventListener('keydown', (e) => {
          if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            form.requestSubmit ? form.requestSubmit() : form.submit();
          }
        });
      }

      // 點擊關閉按鈕或外部遮罩防手滑確認
      const closeBtns = drawer.querySelectorAll('.drawer-close');
      closeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
          if (isDirty && !confirm('您有尚未儲存的修改，確定要關閉嗎？')) {
            e.stopImmediatePropagation();
            return;
          }
          isDirty = false;
        });
      });
    });
  }

  function initAdminCore() {
    // Confirm Delete Modals
    const deleteForms = document.querySelectorAll('form.delete-form');
    const confirmModal = document.getElementById('confirm-modal');
    const confirmBtn = document.getElementById('confirm-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    let currentForm = null;

    if (confirmModal && confirmBtn && cancelBtn) {
      deleteForms.forEach(form => {
        form.addEventListener('submit', (e) => {
          e.preventDefault();
          currentForm = form;
          confirmModal.classList.add('active');
        });
      });

      cancelBtn.addEventListener('click', () => {
        confirmModal.classList.remove('active');
        currentForm = null;
      });

      confirmBtn.addEventListener('click', () => {
        if (currentForm) {
          currentForm.submit();
        }
      });
    }

    // Sidebar toggle
    const sidebarToggleBtn = document.getElementById('admin-sidebar-toggle');
    if (sidebarToggleBtn) {
      sidebarToggleBtn.addEventListener('click', () => {
        const layout = document.querySelector('.admin-layout');
        if (layout) layout.classList.toggle('collapsed');
      });
    }

    // Initialize core features
    initTableSorting();
    initAdminFilterEngine();
    initAnchorHighlight();
    initDrawerEnhancements();

    // Inline Editing
    document.querySelectorAll('.editable-cell').forEach(cell => {
      cell.addEventListener('dblclick', function() {
        if (this.classList.contains('editing')) return;
        
        const originalValue = this.innerText.trim();
        this.classList.add('editing');
        this.innerHTML = `<input type="text" class="inline-edit-input" value="${originalValue.replace(/"/g, '&quot;')}">`;
        
        const input = this.querySelector('input');
        input.focus();
        
        const saveEdit = async () => {
          const newValue = input.value.trim();
          const rowId = this.closest('tr').dataset.id;
          const field = this.dataset.field;
          const endpoint = this.closest('table').dataset.editEndpoint;
          
          if (newValue !== originalValue) {
            try {
              const formData = new FormData();
              formData.append(field, newValue);
              
              const response = await fetch(endpoint.replace('0', rowId), {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
              });
              
              if (!response.ok) throw new Error('Network response was not ok');
              const data = await response.json();
              
              if (data.success) {
                if (window.showToast) window.showToast('Saved successfully', 'success');
                this.innerText = newValue;
              } else {
                throw new Error(data.error || 'Failed to save');
              }
            } catch (error) {
              if (window.showToast) window.showToast('Error saving: ' + error.message, 'error');
              this.innerText = originalValue;
            }
          } else {
            this.innerText = originalValue;
          }
          this.classList.remove('editing');
        };
        
        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
          } else if (e.key === 'Escape') {
            this.innerText = originalValue;
            this.classList.remove('editing');
          }
        });
      });
    });

    // Bulk Actions
    const selectAllCb = document.getElementById('select-all-cb');
    if (selectAllCb) {
      selectAllCb.addEventListener('change', (e) => {
        document.querySelectorAll('.row-cb').forEach(cb => {
          if (cb.closest('tr').style.display !== 'none') {
            cb.checked = e.target.checked;
          }
        });
      });
    }

    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    if (bulkDeleteBtn) {
      bulkDeleteBtn.addEventListener('click', () => {
        const selected = Array.from(document.querySelectorAll('.row-cb:checked')).map(cb => cb.value);
        if (selected.length === 0) return alert('No items selected.');
        
        if (confirm('Are you sure you want to delete ' + selected.length + ' item(s)?')) {
          const form = document.createElement('form');
          form.method = 'POST';
          form.action = document.querySelector('table').dataset.bulkDeleteEndpoint;
          
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = 'ids';
          input.value = JSON.stringify(selected);
          form.appendChild(input);
          
          document.body.appendChild(form);
          form.submit();
        }
      });
    }

    // Global Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const drawer = document.getElementById('form-drawer') || document.getElementById('bulk-edit-drawer');
        if (drawer && drawer.classList.contains('open')) {
          drawer.classList.remove('open');
        }
      }
      
      if ((e.ctrlKey && e.key === 'f') || (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
        const searchInput = document.getElementById('table-search') || document.getElementById('search-input');
        if (searchInput) {
          e.preventDefault();
          searchInput.focus();
        }
      }
      
      if (e.altKey && e.key.toLowerCase() === 'n') {
        const newBtn = document.querySelector('.action-header .btn-primary');
        if (newBtn) {
          e.preventDefault();
          newBtn.click();
        }
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAdminCore);
  } else {
    initAdminCore();
  }
})();
