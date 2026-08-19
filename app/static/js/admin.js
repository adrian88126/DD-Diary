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
          
          // Handle null / empty values to always put them at the bottom
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
        
        // Re-append sorted rows
        rows.forEach(tr => tbody.appendChild(tr));
      });
    });
  }

  window.initTableSorting = initTableSorting;

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

    // Auto-search / Filter on tables
    const searchInput = document.getElementById('table-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('.data-table tbody tr, .admin-data-table tbody tr');
        
        rows.forEach(row => {
          const text = row.textContent.toLowerCase();
          if (text.includes(term)) {
            row.style.display = '';
          } else {
            row.style.display = 'none';
          }
        });
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

    // Initialize sorting
    initTableSorting();

    // 2. Inline Editing
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

    // 3. Bulk Actions
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

    // 4. Keyboard Shortcuts
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
