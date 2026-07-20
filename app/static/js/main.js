// 應用主程式入口模組 (main.js)
import { state, initAdminModeFromStorage, setIsAdminMode } from './state.js';
import { fetchAllData } from './api.js';
import { 
    switchView, 
    loadSidebarVtubers, 
    loadDashboardData, 
    renderCatalog, 
    renderVtuberCatalog,
    loadVtuberProfile,
    searchSongHistory,
    populateCatalogDropdowns
} from './portal.js';
import { 
    setupAutocompleteSelects, 
    setupAdminFormListeners, 
    runSongNameDiagnostics, 
    navigateToAdminPane,
    addSetlistRow,
    populateAdminDropdowns,
    setupCurateModalListeners
} from './admin.js';
import { playRecord, closePlayerOverlay, showToast } from './ui.js';

// 將需要全域呼叫的函數掛載到 window 物件上以支援 HTML inline 事件
window.playRecord = playRecord;
window.closePlayerOverlay = closePlayerOverlay;
window.searchSongHistory = searchSongHistory;
window.loadVtuberProfile = loadVtuberProfile;

// 初始化應用
document.addEventListener('DOMContentLoaded', async () => {
    // 1. 初始化管理狀態
    initAdminModeFromStorage();
    updateVisitorModeClass();
    
    // 2. 加載初始快取數據
    const ok = await fetchAllData();
    if (!ok) {
        showToast('與伺服器連線失敗，請檢查後端是否正常運作！', 'error');
    } else {
        // 成功加載快取後，填入後台所有需要主播清單的下拉選單
        populateAdminDropdowns();
        populateCatalogDropdowns();
    }
    
    // 3. 初始化 UI 互動與事件監聽
    setupTheme();
    setupNavigation();
    setupCatalogTabs();
    setupAdminToggle();
    
    // 4. 初始化自動完成與表單監聽 (後台)
    setupAutocompleteSelects();
    setupAdminFormListeners();
    setupCurateModalListeners();
    addSetlistRow(); // 初始化第一個空曲目列
    
    // 5. 渲染頁面
    await loadSidebarVtubers();
    await loadDashboardData();
    renderCatalog();
    renderVtuberCatalog();
    
    // 後台統計診斷
    if (state.isAdminMode) {
        runSongNameDiagnostics();
    }
});

// 管理登入狀態更新樣式與視圖限制
function updateVisitorModeClass() {
    const toggleBtn = document.getElementById('admin-mode-toggle');
    if (state.isAdminMode) {
        document.body.classList.remove('visitor-mode');
        if (toggleBtn) {
            toggleBtn.className = 'btn btn-purple';
            toggleBtn.style.margin = '0';
            toggleBtn.innerHTML = '<i class="fa-solid fa-unlock-keyhole"></i> <span>管理登出</span>';
        }
    } else {
        document.body.classList.add('visitor-mode');
        if (toggleBtn) {
            toggleBtn.className = 'btn btn-secondary';
            toggleBtn.style.margin = '0';
            toggleBtn.innerHTML = '<i class="fa-solid fa-key"></i> <span>管理登入</span>';
        }
        // 如果目前正在後台管理頁面，強行退回到前台大廳
        const activeNav = document.querySelector('.nav-item.active');
        if (activeNav && activeNav.getAttribute('data-view') === 'admin') {
            switchView('dashboard');
        }
    }
}

// 密碼驗證登入燈箱控制
function setupAdminToggle() {
    const toggleBtn = document.getElementById('admin-mode-toggle');
    const loginModal = document.getElementById('admin-login-modal');
    const loginForm = document.getElementById('form-admin-login');
    const btnCancel = document.getElementById('btn-cancel-admin-login');
    const btnClose = document.getElementById('btn-close-admin-login-modal');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            if (state.isAdminMode) {
                // 登出
                setIsAdminMode(false);
                updateVisitorModeClass();
                renderCatalog();
                renderVtuberCatalog();
                showToast('已安全登出管理者身分，切換為唯讀訪客模式。');
            } else {
                // 開啟驗證燈箱
                if (loginModal) loginModal.classList.add('active');
            }
        });
    }
    
    const closeLoginModal = () => {
        if (loginModal) loginModal.classList.remove('active');
        if (loginForm) loginForm.reset();
    };
    
    if (btnClose) btnClose.addEventListener('click', closeLoginModal);
    if (btnCancel) btnCancel.addEventListener('click', closeLoginModal);
    
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const password = document.getElementById('admin-password').value;
            if (password === 'admin123') {
                setIsAdminMode(true);
                updateVisitorModeClass();
                renderCatalog();
                renderVtuberCatalog();
                runSongNameDiagnostics();
                closeLoginModal();
                showToast('🎉 密碼驗證成功！已啟用管理員身分與完整修改權利。');
            } else {
                showToast('密碼錯誤，請再試一次！', 'error');
            }
        });
    }
}

// 佈景主題切換
function setupTheme() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (!themeToggleBtn) return;
    
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('theme-light');
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }
    
    themeToggleBtn.addEventListener('click', () => {
        const isLight = document.body.classList.toggle('theme-light');
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        themeToggleBtn.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    });
}

// 導覽選單事件
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-menu .nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const viewName = item.getAttribute('data-view');
            
            // 安全防護：如果是訪客模式點選後台管理，彈出登入
            if (viewName === 'admin' && !state.isAdminMode) {
                const loginModal = document.getElementById('admin-login-modal');
                if (loginModal) loginModal.classList.add('active');
                return;
            }
            
            // 清除側邊欄的主播 Active 狀態
            document.querySelectorAll('.vtuber-item').forEach(el => el.classList.remove('active'));
            
            switchView(viewName);
            
            if (viewName === 'admin') {
                navigateToAdminPane('admin-pane-lobby');
                runSongNameDiagnostics();
            }
        });
    });

    // 後台管理左側小選單點選
    const adminNavItems = document.querySelectorAll('.admin-nav-menu .admin-nav-item');
    adminNavItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const paneId = item.getAttribute('data-pane');
            navigateToAdminPane(paneId);
            if (paneId === 'admin-pane-lobby') {
                runSongNameDiagnostics();
            }
        });
    });

    // 播放器燈箱 X 關閉事件與背景關閉事件
    const btnClosePlayer = document.getElementById('btn-close-player-modal');
    if (btnClosePlayer) {
        btnClosePlayer.addEventListener('click', closePlayerOverlay);
    }
    const ytPlayerModal = document.getElementById('yt-player-modal');
    if (ytPlayerModal) {
        ytPlayerModal.addEventListener('click', (e) => {
            if (e.target === ytPlayerModal) {
                closePlayerOverlay();
            }
        });
    }
}

// 總庫目錄 Tab 切換
function setupCatalogTabs() {
    const tabs = document.querySelectorAll('#view-catalog .playlist-tab-btn');
    tabs.forEach(btn => {
        btn.addEventListener('click', () => {
            tabs.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const paneId = btn.id.replace('catalog-tab-btn-', 'catalog-pane-');
            document.querySelectorAll('#view-catalog .tab-pane').forEach(p => p.classList.remove('active'));
            
            const targetPane = document.getElementById(paneId);
            if (targetPane) targetPane.classList.add('active');
        });
    });

    // 總庫大搜尋過濾 (防抖 Debounce 優化與搜尋按鈕支援)
    const catalogSearch = document.getElementById('catalog-search-input');
    const btnCatalogSearchSubmit = document.getElementById('btn-catalog-search-submit');
    
    const triggerSearch = () => {
        renderCatalog();
    };
    
    if (catalogSearch) {
        let debounceTimer;
        catalogSearch.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(triggerSearch, 200);
        });
        catalogSearch.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(debounceTimer);
                triggerSearch();
            }
        });
    }
    
    if (btnCatalogSearchSubmit) {
        btnCatalogSearchSubmit.addEventListener('click', () => {
            triggerSearch();
        });
    }

    // 總庫影音篩選過濾
    const filterType = document.getElementById('catalog-video-filter-type');
    const filterVtuber = document.getElementById('catalog-video-filter-vtuber');
    const filterTimeline = document.getElementById('catalog-video-filter-timeline');
    
    if (filterType) filterType.addEventListener('change', renderCatalog);
    if (filterVtuber) filterVtuber.addEventListener('change', renderCatalog);
    if (filterTimeline) filterTimeline.addEventListener('change', renderCatalog);
}
