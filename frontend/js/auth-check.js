function checkAuth(requiredRole) {
    const token = localStorage.getItem('ecolyy_access_token');
    const user = localStorage.getItem('ecolyy_user');
    const role = localStorage.getItem('ecolyy_role');
    
    console.log('Auth Check:', { 
        token: token ? ' Present' : 'Missing', 
        user: user ? ' Present' : 'Missing', 
        role: role,
        requiredRole: requiredRole 
    });
    
    // Check if logged in
    if (!token || !user) {
        console.log('No token or user!');
        localStorage.clear();
        window.location.replace('../../pages/login.html');
        return false;
    }
    
    // Check if role matches
    if (requiredRole && role !== requiredRole) {
        console.log('Role mismatch!');
        const redirectMap = {
            'admin': '../../admin/dashboard.html',
            'partner': '../../partner/dashboard.html',
            'institution': '../../institute/dashboard.html',
            'user': '../../user/dashboard.html'
        };
        window.location.href = redirectMap[role] || '../../pages/login.html';
        return false;
    }
    
    console.log('Auth check passed!');
    return true;
}

function logoutUser() {
    if (!confirm('Are you sure you want to logout?')) {
        return;
    }
    
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
    
    window.location.replace('../../pages/login.html');
}

window.checkAuth = checkAuth;
window.logoutUser = logoutUser;

// Prevent back button after logout
window.addEventListener('popstate', function(event) {
    const token = localStorage.getItem('ecolyy_access_token');
    if (!token) {
        window.location.replace('../../pages/login.html');
    }
});