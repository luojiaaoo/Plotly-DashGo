// 改造console.error()以隐藏无关痛痒的警告信息
const originalConsoleError = console.error;
console.error = function (...args) {
    // 检查args中是否包含需要过滤的内容
    const shouldFilter = args.some(arg => typeof arg === 'string' && arg.includes('Warning:'));

    if (!shouldFilter) {
        originalConsoleError.apply(console, args);
    }
};

// function getCookie(name) {
//     const cookies = document.cookie.split(';');
//     for (const cookie of cookies) {
//       const [cookieName, cookieValue] = cookie.trim().split('=');
//       if (cookieName === name) {
//         return decodeURIComponent(cookieValue); // 解码特殊字符（如空格、中文）
//       }
//     }
//     return null; // 未找到返回 null
//   }
  
//   document.addEventListener('DOMContentLoaded', function() {
//     const originalFetch = window.fetch;
//     window.fetch = function(url, config) {
//         // if (url.includes('/_dash-update-component')) {
//             config = config || {};
//             let authToken = null;
//             // 检查授权 cookie
//             authToken = getCookie("access_token");
//             // 如果存在 Token，添加 Header
//             if (authToken !== null && authToken !== '' && authToken != '""') {
//                 authToken = authToken.replace(/"/g, '')
//                 if (!authToken.startsWith('Bearer ')) {
//                     authToken = 'Bearer ' + authToken;
//                 }
//                 config.headers = {
//                     ...(config.headers || {}),
//                     Authorization: authToken // 添加 Authorization 
//                 };
//             }
//         // }
//         return originalFetch(url, config);
//     };
// });