import { API_BASE, IS_STATIC } from './config.js';
import { state } from './state.js';

export async function fetchAllData() {
    try {
        let songsRes, artistsRes, vtubersRes, videosRes, recordsRes, activitiesRes;
        
        const t = Date.now();
        if (IS_STATIC) {
            let relativePrefix = './';
            if (window.location.pathname.includes('/share/')) {
                relativePrefix = '../../';
            }
            
            [songsRes, artistsRes, vtubersRes, videosRes, recordsRes, activitiesRes] = await Promise.all([
                fetch(`${relativePrefix}data/songs.json?t=${t}`),
                fetch(`${relativePrefix}data/artists.json?t=${t}`),
                fetch(`${relativePrefix}data/vtubers.json?t=${t}`),
                fetch(`${relativePrefix}data/videos.json?t=${t}`),
                fetch(`${relativePrefix}data/records.json?t=${t}`),
                fetch(`${relativePrefix}data/activities.json?t=${t}`)
            ]);
        } else {
            [songsRes, artistsRes, vtubersRes, videosRes, recordsRes, activitiesRes] = await Promise.all([
                fetch(`${API_BASE}/songs/?limit=100000&t=${t}`),
                fetch(`${API_BASE}/artists/?limit=100000&t=${t}`),
                fetch(`${API_BASE}/vtubers/?limit=100000&t=${t}`),
                fetch(`${API_BASE}/videos/?limit=100000&t=${t}`),
                fetch(`${API_BASE}/records/?limit=200000&t=${t}`),
                fetch(`${API_BASE}/activities/?limit=100000&t=${t}`)
            ]);
        }
        
        state.cacheSongs = await songsRes.json();
        state.cacheArtists = await artistsRes.json();
        state.cacheVtubers = await vtubersRes.json();
        state.cacheVideos = await videosRes.json();
        state.cacheRecords = await recordsRes.json();
        state.cacheActivities = await activitiesRes.json();
        
        return true;
    } catch (error) {
        console.error('無法加載數據快取:', error);
        return false;
    }
}

export async function deleteRecordOnServer(endpoint, id) {
    const response = await fetch(`${API_BASE}/${endpoint}/${id}`, {
        method: 'DELETE'
    });
    return response.ok;
}
