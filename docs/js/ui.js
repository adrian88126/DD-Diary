// 前端 UI 與播放器燈箱模組
export function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '<i class="fa-solid fa-circle-check"></i>';
    if (type === 'error') {
        icon = '<i class="fa-solid fa-circle-exclamation"></i>';
    } else if (type === 'warning') {
        icon = '<i class="fa-solid fa-triangle-exclamation"></i>';
    }
    
    toast.innerHTML = `
        ${icon}
        <span class="toast-message">${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('active');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('active');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

export function formatSeconds(seconds) {
    if (seconds === null || seconds === undefined) return '00:00';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    const pad = (val) => String(val).padStart(2, '0');
    
    if (hrs > 0) {
        return `${pad(hrs)}:${pad(mins)}:${pad(secs)}`;
    }
    return `${pad(mins)}:${pad(secs)}`;
}

export function scrollToElementInsideContent(elementId) {
    const el = document.getElementById(elementId);
    const container = document.querySelector('.scroll-content');
    if (el && container) {
        const parentTop = container.getBoundingClientRect().top;
        const elemTop = el.getBoundingClientRect().top;
        const offset = elemTop - parentTop + container.scrollTop - 20;
        container.scrollTo({
            top: offset,
            behavior: 'smooth'
        });
    }
}

export function formatApiError(err, fallback = '發生未知錯誤') {
    if (err && err.detail) {
        if (Array.isArray(err.detail)) {
            return err.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join(', ');
        }
        return err.detail;
    }
    return fallback;
}

export function playRecord(videoId, startSeconds, songTitle, singerNames, videoTitle) {
    const overlay = document.getElementById('yt-player-modal');
    const iframePlaceholder = document.getElementById('player-iframe-placeholder');
    if (!overlay || !iframePlaceholder) return;
    
    document.getElementById('modal-song-title').textContent = `正在觀看演唱：《${songTitle}》`;
    document.getElementById('modal-song-singer').textContent = `演唱者：${singerNames}`;
    document.getElementById('modal-video-title').textContent = `來自直播：${videoTitle}`;
    
    const embedUrl = `https://www.youtube.com/embed/${videoId}?start=${startSeconds}&autoplay=1&enablejsapi=1`;
    iframePlaceholder.innerHTML = `<iframe src="${embedUrl}" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>`;
    
    const directLinkEl = document.getElementById('modal-yt-direct-link');
    if (directLinkEl) {
        directLinkEl.href = `https://www.youtube.com/watch?v=${videoId}&t=${startSeconds}s`;
    }
    
    overlay.classList.add('active');
}

export function closePlayerOverlay() {
    const overlay = document.getElementById('yt-player-modal');
    const iframePlaceholder = document.getElementById('player-iframe-placeholder');
    if (iframePlaceholder) iframePlaceholder.innerHTML = '';
    if (overlay) overlay.classList.remove('active');
}
