document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar submenu functionality
    const submenuToggles = document.querySelectorAll('.submenu-toggle');
    
    submenuToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const menuItem = this.parentElement;
            
            // Toggle active class
            if (menuItem.classList.contains('active')) {
                menuItem.classList.remove('active');
            } else {
                // First close all other open menus
                document.querySelectorAll('.menu > li.active').forEach(item => {
                    if (item !== menuItem) {
                        item.classList.remove('active');
                    }
                });
                
                menuItem.classList.add('active');
            }
        });
    });
    
    // Automatically open menu based on current URL
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.menu > li');
    
    menuItems.forEach(item => {
        const submenuLinks = item.querySelectorAll('.submenu a');
        let shouldActivate = false;
        
        submenuLinks.forEach(link => {
            if (currentPath === link.getAttribute('href')) {
                shouldActivate = true;
            }
        });
        
        if (shouldActivate) {
            item.classList.add('active');
        }
    });
    
    // Flash messages with SweetAlert2
    const flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
        const messages = flashMessages.getElementsByClassName('message');
        if (messages.length > 0) {
            Swal.fire({
                title: 'Notification',
                text: messages[0].textContent,
                icon: 'info',
                confirmButtonText: 'OK'
            });
        }
    }
});

// Format currency utility function
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', { 
        style: 'currency', 
        currency: 'NGN',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}