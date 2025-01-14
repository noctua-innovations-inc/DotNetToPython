// Show the modal
function showModal(modalId) {
    var modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

// Hide the modal
function hideModal(modalId) {
    var modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}