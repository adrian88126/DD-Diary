// 前端基本設定檔
export const API_BASE = '/api/v1';

export const IS_STATIC = window.location.hostname.includes('github.io') || 
                         window.location.hostname.includes('pages.dev') ||
                         window.location.hostname.includes('vercel.app') ||
                         window.location.protocol === 'file:' ||
                         (window.location.hostname === 'localhost' && window.location.port !== '8000') ||
                         (window.location.hostname === '127.0.0.1' && window.location.port !== '8000');
