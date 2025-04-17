

const cartItemsContainer = document.getElementById('cart-items');
const totalPriceElement = document.getElementById('total-price');

// Fetch the cart data and update dynamically
function fetchCart() {
    fetch('/cart-data')
        .then(response => response.json())
        .then(data => updateCart(data.cart, data.total_price))
        .catch(error => console.error('Error fetching cart:', error));
}

// Delete a product from the cart
function deleteProduct(productId) {
    fetch(`/delete/${productId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => updateCart(data.cart, data.total_price))
        .catch(error => console.error('Error deleting product:', error));
}

// Update the cart display dynamically
function updateCart(cart, totalPrice) {
    cartItemsContainer.innerHTML = '';
    cart.forEach(product => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${product.name}</td>
            <td>${product.price} AMD</td>
            <td><button class="delete-button" onclick="deleteProduct(${product.id})">Delete</button></td>
        `;
        cartItemsContainer.appendChild(row);
    });
    totalPriceElement.textContent = `${totalPrice} AMD`;
}

// Handle the Pay Now button click
function payNow() {
    const cartItems = document.querySelectorAll('#cart-items tr');
    if (cartItems.length === 0) {
        alert('Your cart is empty!');
        return;
    }
    alert('Proceeding to payment...');
    // Redirect to receipt page
    window.location.href = '/receipt';
}

// Initial fetch on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchCart();
});
