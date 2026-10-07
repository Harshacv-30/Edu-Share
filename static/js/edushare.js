document.addEventListener('DOMContentLoaded', function () {
  // Mobile navigation toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const navLinks = document.getElementById('navLinks');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', function () {
      navLinks.classList.toggle('show');
    });
  }

  // Auto-dismiss alerts after 6 seconds (optional graceful fade)
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(function () {
        if (alert.parentNode) {
          alert.parentNode.removeChild(alert);
        }
      }, 500);
    }, 7000);
  });

  // Rejection modal handler
  window.openRejectModal = function (actionUrl, targetName, targetType) {
    const modal = document.getElementById('rejectModal');
    const form = document.getElementById('rejectForm');
    const label = document.getElementById('rejectModalTarget');
    if (modal && form && label) {
      form.action = actionUrl;
      label.textContent = `${targetType}: ${targetName}`;
      modal.style.display = 'flex';
    }
  };

  window.closeRejectModal = function () {
    const modal = document.getElementById('rejectModal');
    if (modal) {
      modal.style.display = 'none';
    }
  };
});
