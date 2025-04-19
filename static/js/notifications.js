/**
 * Notifications functionality for the Sports Performance Tracker
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize notification counters
    updateNotificationCount();
    
    // Set up notification filters
    initNotificationFilters();
    
    // Set up mark all as read functionality
    initMarkAllAsRead();
    
    // Set up polling for new notifications
    initNotificationPolling();
});

/**
 * Updates the notification count in the header
 */
function updateNotificationCount() {
    const countElement = document.querySelector('.notification-count');
    if (!countElement) return;
    
    // Determine endpoint based on user role
    let endpoint = '';
    if (document.body.classList.contains('coach-role')) {
        endpoint = '/coach/api/notification_count';
    } else if (document.body.classList.contains('athlete-role')) {
        endpoint = '/athlete/api/notification_count';
    } else {
        return;
    }
    
    // Fetch count from server
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if (data.count > 0) {
                countElement.textContent = data.count;
                countElement.style.display = 'inline';
            } else {
                countElement.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error fetching notification count:', error);
        });
}

/**
 * Initializes notification filtering functionality
 */
function initNotificationFilters() {
    const filterLinks = document.querySelectorAll('.dropdown-item[data-filter]');
    const notificationItems = document.querySelectorAll('.notification-item');
    
    filterLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            filterLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.dataset.filter;
            
            notificationItems.forEach(item => {
                if (filter === 'all') {
                    item.style.display = '';
                } else if (filter === 'unread') {
                    item.style.display = item.classList.contains('unread') ? '' : 'none';
                } else {
                    item.style.display = item.dataset.type.includes(filter) ? '' : 'none';
                }
            });
        });
    });
}

/**
 * Initializes "Mark All as Read" functionality
 */
function initMarkAllAsRead() {
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    if (!markAllReadBtn) return;
    
    markAllReadBtn.addEventListener('click', function() {
        // Determine endpoint based on user role
        let endpoint = '';
        if (document.body.classList.contains('coach-role')) {
            endpoint = '/coach/api/mark_all_read';
        } else if (document.body.classList.contains('athlete-role')) {
            endpoint = '/athlete/api/mark_all_read';
        } else {
            return;
        }
        
        // Send request to mark all as read
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()  // Add CSRF token if needed
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI to show all notifications as read
                const unreadItems = document.querySelectorAll('.notification-item.unread');
                unreadItems.forEach(item => {
                    item.classList.remove('unread');
                    
                    // Remove new badge
                    const badge = item.querySelector('.badge');
                    if (badge) badge.remove();
                    
                    // Remove "Mark as Read" button
                    const markReadBtn = item.querySelector('a[href*="mark_notification_read"]');
                    if (markReadBtn) markReadBtn.remove();
                });
                
                // Update notification count in header
                updateNotificationCount();
                
                // Show success message
                showToast('All notifications marked as read');
            }
        })
        .catch(error => {
            console.error('Error marking all as read:', error);
            showToast('Failed to mark notifications as read', 'danger');
        });
    });
}

/**
 * Gets CSRF token from cookies
 * @returns {string} CSRF token value
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }
    return '';
}

/**
 * Shows a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, danger, etc.)
 */
function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastElement = document.createElement('div');
    toastElement.className = `toast bg-${type} text-white`;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">Notification</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Sets up periodic polling for new notifications
 */
function initNotificationPolling() {
    // Poll every 60 seconds
    setInterval(function() {
        updateNotificationCount();
        checkForNewNotifications();
    }, 60000);
}

/**
 * Checks for new notifications and updates UI if needed
 */
function checkForNewNotifications() {
    // Determine endpoint based on user role
    let endpoint = '';
    if (document.body.classList.contains('coach-role')) {
        endpoint = '/coach/api/new_notifications';
    } else if (document.body.classList.contains('athlete-role')) {
        endpoint = '/athlete/api/new_notifications';
    } else {
        return;
    }
    
    // Get timestamp of most recent notification
    const notificationList = document.getElementById('notificationList');
    if (!notificationList) return;
    
    const firstNotification = notificationList.querySelector('.notification-item');
    if (!firstNotification) return;
    
    const latestTimestamp = firstNotification.dataset.timestamp;
    
    // Fetch new notifications
    fetch(`${endpoint}?since=${latestTimestamp}`)
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                // Add new notifications to the list
                data.notifications.forEach(notification => {
                    const notificationElement = createNotificationElement(notification);
                    notificationList.insertBefore(notificationElement, notificationList.firstChild);
                });
                
                // Show notification alert
                showToast(`${data.notifications.length} new notification(s) received`);
                
                // Update notification count
                updateNotificationCount();
            }
        })
        .catch(error => {
            console.error('Error checking for new notifications:', error);
        });
}

/**
 * Creates a notification list item element
 * @param {Object} notification - The notification data
 * @returns {HTMLElement} The notification element
 */
function createNotificationElement(notification) {
    const element = document.createElement('div');
    element.className = 'list-group-item bg-dark text-white border-light notification-item unread';
    element.dataset.type = notification.type;
    element.dataset.timestamp = notification.created_at;
    
    let iconClass = 'fas fa-bell text-primary';
    switch (notification.type) {
        case 'performance_update':
            iconClass = 'fas fa-chart-line text-info';
            break;
        case 'team_addition':
            iconClass = 'fas fa-user-plus text-success';
            break;
        case 'milestone':
            iconClass = 'fas fa-trophy text-warning';
            break;
    }
    
    element.innerHTML = `
        <div class="d-flex w-100 justify-content-between align-items-center">
            <h6 class="mb-1">
                <i class="${iconClass} me-2"></i>
                ${notification.message}
            </h6>
            <div>
                <small class="text-muted me-3">${formatDate(notification.created_at)}</small>
                <span class="badge bg-primary">New</span>
            </div>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-2">
            <small class="text-muted">
                ${notification.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </small>
            <div>
                ${notification.related_id ? `<a href="#" class="btn btn-sm btn-outline-info me-2">View Details</a>` : ''}
                <a href="/athlete/notifications/mark_read/${notification._id}" class="btn btn-sm btn-outline-light">Mark as Read</a>
            </div>
        </div>
    `;
    
    return element;
}

/**
 * Formats a date for display
 * @param {string} dateString - The date string to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}
