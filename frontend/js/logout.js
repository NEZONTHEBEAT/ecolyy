// frontend/js/logout.js

function logoutUser() {
    if (!confirm('Are you sure you want to logout?')) {
        return;
    }
    
    // Clear all auth data
    const keys = [
        'ecolyy_access_token',
        'ecolyy_refresh_token',
        'ecolyy_token_type',
        'ecolyy_role',
        'ecolyy_user',
        'ecolyy_user_name',
        'ecolyy_user_email',
        'ecolyy_partner_name',
        'ecolyy_partner_email',
        'ecolyy_institute_name',
        'ecolyy_institute_email'
    ];
    keys.forEach(key => localStorage.removeItem(key));
    
    // =============================================
    // DETECT CORRECT PATH
    // =============================================
    
    // Get current path
    const currentPath = window.location.pathname;
    console.log('Current path:', currentPath);
    
    // Determine how many levels to go up
    let loginPath = '';
    
    if (currentPath.includes('/partner/')) {
        loginPath = '../../pages/login.html';
    } else if (currentPath.includes('/institute/')) {
        loginPath = '../../pages/login.html';
    } else if (currentPath.includes('/admin/')) {
        loginPath = '../../pages/login.html';
    } else if (currentPath.includes('/user/')) {
        loginPath = '../../pages/login.html';
    } else {
        loginPath = '/pages/login.html';
    }
    
    console.log('Redirecting to:', loginPath);
    
    // Redirect
    window.location.replace(loginPath);
}

// Make globally available
window.logoutUser = logoutUser;