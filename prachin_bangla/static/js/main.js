// Product quantity control
function updateQuantity(change) {
    const quantityInput = document.getElementById('quantity');
    let quantity = parseInt(quantityInput.value) + change;
    if (quantity < 1) quantity = 1;
    quantityInput.value = quantity;
    updateTotal();
}

// Update total price based on quantity
function updateTotal() {
    const quantity = parseInt(document.getElementById('quantity').value);
    const price = parseFloat(document.getElementById('price').dataset.price);
    const discount = parseFloat(document.getElementById('price').dataset.discount || 0);
    
    const discountedPrice = price * (1 - discount/100);
    const total = discountedPrice * quantity;
    
    document.getElementById('total-price').textContent = total.toFixed(2);
}

// Delete product confirmation
function deleteProduct(productId) {
    if (confirm('Are you sure you want to delete this product?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/product/delete/${productId}`;
        document.body.appendChild(form);
        form.submit();
    }
}

// Preview image before upload
function previewImage(event) {
    const reader = new FileReader();
    reader.onload = function() {
        const preview = document.getElementById('image-preview');
        preview.src = reader.result;
        preview.style.display = 'block';
    }
    reader.readAsDataURL(event.target.files[0]);
}

// Initialize any components when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize quantity handlers
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        updateTotal();
    }
    
    // Initialize image preview
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', previewImage);
    }
});
