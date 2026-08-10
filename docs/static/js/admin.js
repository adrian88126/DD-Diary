// app/static/js/admin.js
import { showToast } from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
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
      const rows = document.querySelectorAll('.data-table tbody tr');
      
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
});

  // 1. Table Sorting
  const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
  const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
    v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
  )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

  document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', (() => {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    Array.from(tbody.querySelectorAll('tr'))
      .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
      .forEach(tr => tbody.appendChild(tr));
    
    // Update visual indicators
    table.querySelectorAll('th.sortable').forEach(el => { el.classList.remove('asc', 'desc'); });
    th.classList.add(this.asc ? 'asc' : 'desc');
  })));

  // 2. Inline Editing
  document.querySelectorAll('.editable-cell').forEach(cell => {
    cell.addEventListener('dblclick', function() {
      if (this.classList.contains('editing')) return;
      
      const originalValue = this.innerText.trim();
      this.classList.add('editing');
      this.innerHTML = <input type="text" class="inline-edit-input" value=" + originalValue.replace(/"/g, '&quot;') + ">;
      
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
              import('./ui.js').then(module => module.showToast('Saved successfully', 'success'));
              this.innerText = newValue;
            } else {
              throw new Error(data.error || 'Failed to save');
            }
          } catch (error) {
            import('./ui.js').then(module => module.showToast('Error saving: ' + error.message, 'error'));
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
    // Esc to close drawer
    if (e.key === 'Escape') {
      const drawer = document.getElementById('form-drawer');
      if (drawer && drawer.classList.contains('open')) {
        drawer.classList.remove('open');
      }
    }
    
    // Ctrl+F or / to focus search (if not in an input)
    if ((e.ctrlKey && e.key === 'f') || (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
      const searchInput = document.getElementById('table-search');
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
      }
    }
    
    // Alt+N for New
    if (e.altKey && e.key.toLowerCase() === 'n') {
      const newBtn = document.querySelector('.action-header .btn-primary');
      if (newBtn) {
        e.preventDefault();
        newBtn.click();
      }
    }
  });

