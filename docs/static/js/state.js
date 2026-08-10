// 前端全域狀態管理模組
export const state = {
    isAdminMode: false,
    selectedVtuberId: null,
    selectedArtists: [],           // 新增歌曲時已選歌手
    editSongSelectedArtists: [],   // 編輯歌曲燈箱內已選歌手
    editRecSelectedSingers: [],     // 編輯歌唱紀錄燈箱內已選主播
    
    // 全域快取數據
    cacheSongs: [],
    cacheArtists: [],
    cacheVtubers: [],
    cacheVideos: [],
    cacheRecords: [],
    cacheActivities: []
};

// 輔助更新與持久化方法
export function setIsAdminMode(val) {
    state.isAdminMode = !!val;
    localStorage.setItem('vt_db_admin_mode', val ? 'true' : 'false');
}

export function initAdminModeFromStorage() {
    state.isAdminMode = localStorage.getItem('vt_db_admin_mode') === 'true';
    return state.isAdminMode;
}
