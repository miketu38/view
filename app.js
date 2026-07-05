let currentPage = 'home';
const pages = ['home', 'booking', 'profile', 'orders'];
const pageTitles = {
    home: '餐厅预订',
    booking: '餐饮预订',
    profile: '我的信息',
    orders: '我的订单'
};
const API_URL = '/api';

let currentUser = null;

function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function showLogin() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
}

async function handleLogin() {
    const phone = document.getElementById('loginPhone').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!phone || !password) {
        showToast('请输入手机号和密码');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = result.user;
            localStorage.setItem('food_app_user', JSON.stringify(currentUser));
            document.getElementById('authPage').style.display = 'none';
            document.getElementById('app').style.display = 'block';
            loadProfile();
            showToast('登录成功');
        } else {
            showToast(result.message || '登录失败');
        }
    } catch (error) {
        showToast('网络错误，请重试');
    }
}

async function handleRegister() {
    const phone = document.getElementById('regPhone').value;
    const password = document.getElementById('regPassword').value;
    const name = document.getElementById('regName').value;
    
    if (!phone || !password) {
        showToast('请输入手机号和密码');
        return;
    }
    
    if (password.length < 4) {
        showToast('密码至少4位');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, password, name })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('注册成功，请登录');
            showLogin();
        } else {
            showToast(result.message || '注册失败');
        }
    } catch (error) {
        showToast('网络错误，请重试');
    }
}

function handleLogout() {
    currentUser = null;
    localStorage.removeItem('food_app_user');
    document.getElementById('app').style.display = 'none';
    document.getElementById('authPage').style.display = 'flex';
    document.getElementById('loginPhone').value = '';
    document.getElementById('loginPassword').value = '';
    showToast('已退出登录');
}

function navigateTo(pageId) {
    if (pageId === currentPage) return;
    
    document.getElementById(`page${currentPage.charAt(0).toUpperCase() + currentPage.slice(1)}`).classList.remove('active');
    document.getElementById(`page${pageId.charAt(0).toUpperCase() + pageId.slice(1)}`).classList.add('active');
    
    currentPage = pageId;
    
    document.getElementById('pageTitle').textContent = pageTitles[pageId];
    document.getElementById('backBtn').style.display = pageId === 'home' ? 'none' : 'flex';
    
    if (pageId === 'orders') {
        loadOrders();
    } else if (pageId === 'booking') {
        loadMenu('recommend');
    }
}

function goBack() {
    if (currentPage !== 'home') {
        navigateTo('home');
    }
}

function switchCategory(category) {
    const tabs = document.querySelectorAll('.category-tabs .tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    loadMenu(category);
}

async function loadMenu(category) {
    const foodList = document.getElementById('foodList');
    foodList.innerHTML = '';
    
    try {
        const response = await fetch(`${API_URL}/menu?category=${category}`);
        if (response.ok) {
            const items = await response.json();
            
            if (items.length === 0) {
                foodList.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">暂无菜品</div>';
                return;
            }
            
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'food-item';
                div.innerHTML = `
                    <img src="${item.image_url || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Chinese%20food&image_size=square'}" alt="${item.name}">
                    <div class="food-info">
                        <h3>${item.name}</h3>
                        <p class="food-desc">${item.description || ''}</p>
                        <div class="food-price">¥${item.price}</div>
                    </div>
                    <div class="food-controls">
                        <button class="control-btn minus" onclick="updateQuantity(this, -1)">-</button>
                        <span class="quantity">0</span>
                        <button class="control-btn plus" onclick="updateQuantity(this, 1)">+</button>
                    </div>
                `;
                foodList.appendChild(div);
            });
        }
    } catch (error) {
        foodList.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">加载失败</div>';
    }
}

function updateQuantity(btn, delta) {
    const controls = btn.parentElement;
    const quantitySpan = controls.querySelector('.quantity');
    let quantity = parseInt(quantitySpan.textContent);
    quantity = Math.max(0, quantity + delta);
    quantitySpan.textContent = quantity;
    
    updateTotal();
}

function updateTotal() {
    let totalCount = 0;
    let totalPrice = 0;
    
    document.querySelectorAll('.food-item').forEach(item => {
        const quantity = parseInt(item.querySelector('.quantity').textContent);
        const price = parseFloat(item.querySelector('.food-price').textContent.replace('¥', ''));
        
        totalCount += quantity;
        totalPrice += quantity * price;
    });
    
    document.getElementById('selectedCount').textContent = totalCount;
    document.getElementById('totalPrice').textContent = totalPrice;
}

async function saveProfile() {
    const name = document.getElementById('name').value;
    const phone = document.getElementById('phone').value;
    const address = document.getElementById('address').value;
    const remark = document.getElementById('remark').value;
    
    if (!name || !phone) {
        showToast('请填写姓名和电话');
        return;
    }
    
    const profile = { name, phone, address, remark };
    
    try {
        const response = await fetch(`${API_URL}/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profile)
        });
        
        if (response.ok) {
            localStorage.setItem('food_app_profile', JSON.stringify(profile));
            showToast('信息保存成功！');
        } else {
            showToast('保存失败，请重试');
        }
    } catch (error) {
        localStorage.setItem('food_app_profile', JSON.stringify(profile));
        showToast('已保存到本地');
    }
}

function loadProfile() {
    const saved = localStorage.getItem('food_app_profile');
    if (saved) {
        const profile = JSON.parse(saved);
        document.getElementById('name').value = profile.name || '';
        document.getElementById('phone').value = profile.phone || '';
        document.getElementById('address').value = profile.address || '';
        document.getElementById('remark').value = profile.remark || '';
    }
}

async function submitBooking() {
    const selectedCount = parseInt(document.getElementById('selectedCount').textContent);
    if (selectedCount === 0) {
        showToast('请先选择菜品');
        return;
    }
    
    const profile = JSON.parse(localStorage.getItem('food_app_profile') || '{}');
    if (!profile.name || !profile.phone) {
        showToast('请先完善个人信息');
        navigateTo('profile');
        return;
    }
    
    const orderItems = [];
    document.querySelectorAll('.food-item').forEach(item => {
        const quantity = parseInt(item.querySelector('.quantity').textContent);
        if (quantity > 0) {
            const name = item.querySelector('h3').textContent;
            const price = parseFloat(item.querySelector('.food-price').textContent.replace('¥', ''));
            orderItems.push({ name, price, quantity });
        }
    });
    
    const orderData = {
        profile: profile,
        items: orderItems,
        total: parseFloat(document.getElementById('totalPrice').textContent)
    };
    
    try {
        const response = await fetch(`${API_URL}/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('预订成功！订单号：' + result.order_id);
        } else {
            showToast('预订失败，请重试');
            return;
        }
    } catch (error) {
        const newOrder = {
            id: Date.now(),
            items: orderItems,
            total: parseFloat(document.getElementById('totalPrice').textContent),
            status: 'pending',
            createTime: new Date().toLocaleString()
        };
        const orders = JSON.parse(localStorage.getItem('food_app_orders') || '[]');
        orders.unshift(newOrder);
        localStorage.setItem('food_app_orders', JSON.stringify(orders));
        showToast('已保存到本地');
    }
    
    document.querySelectorAll('.quantity').forEach(q => q.textContent = '0');
    updateTotal();
    navigateTo('orders');
}

async function loadOrders() {
    const orderList = document.getElementById('orderList');
    const emptyState = document.getElementById('emptyState');
    
    const existingCards = orderList.querySelectorAll('.order-card');
    existingCards.forEach(card => card.remove());
    
    const profile = JSON.parse(localStorage.getItem('food_app_profile') || '{}');
    const phone = profile.phone || '';
    
    let url = `${API_URL}/orders`;
    if (phone) {
        url += `?phone=${encodeURIComponent(phone)}`;
    }
    
    try {
        const response = await fetch(url);
        if (response.ok) {
            const orders = await response.json();
            
            if (orders.length === 0) {
                emptyState.style.display = 'block';
            } else {
                emptyState.style.display = 'none';
                orders.forEach(order => {
                    const items = order.order_items || order.items || [];
                    const card = document.createElement('div');
                    card.className = 'order-card';
                    card.innerHTML = `
                        <div class="order-status ${order.status}">${getStatusText(order.status)}</div>
                        <div class="order-content">
                            <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Chinese%20food%20meal&image_size=square" alt="订单">
                            <div class="order-info">
                                <h3>${items.map(i => i.name).join('、')}</h3>
                                <p>合计 ${items.reduce((sum, i) => sum + i.quantity, 0)}件</p>
                                <div class="order-price">¥${order.total}</div>
                            </div>
                        </div>
                        <button class="order-btn ${order.status === 'completed' ? 'disabled' : ''}" onclick="updateOrderStatus(${order.id}, 'completed')">
                            ${order.status === 'completed' ? '已送达' : '送达'}
                        </button>
                    `;
                    orderList.appendChild(card);
                });
            }
        }
    } catch (error) {
        const orders = JSON.parse(localStorage.getItem('food_app_orders') || '[]');
        if (orders.length === 0) {
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
            orders.forEach(order => {
                const card = document.createElement('div');
                card.className = 'order-card';
                card.innerHTML = `
                    <div class="order-status ${order.status}">${getStatusText(order.status)}</div>
                    <div class="order-content">
                        <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Chinese%20food%20meal&image_size=square" alt="订单">
                        <div class="order-info">
                            <h3>${order.items.map(i => i.name).join('、')}</h3>
                            <p>合计 ${order.items.reduce((sum, i) => sum + i.quantity, 0)}件</p>
                            <div class="order-price">¥${order.total}</div>
                        </div>
                    </div>
                    <button class="order-btn ${order.status === 'completed' ? 'disabled' : ''}" onclick="updateOrderStatus(${order.id}, 'completed')">
                        ${order.status === 'completed' ? '已送达' : '送达'}
                    </button>
                `;
                orderList.appendChild(card);
            });
        }
    }
}

function getStatusText(status) {
    const texts = {
        pending: '待确认',
        confirmed: '已确认',
        completed: '已完成'
    };
    return texts[status] || status;
}

async function updateOrderStatus(orderId, newStatus) {
    try {
        const response = await fetch(`${API_URL}/orders/${orderId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (response.ok) {
            showToast('订单状态已更新');
            loadOrders();
        }
    } catch (error) {
        const orders = JSON.parse(localStorage.getItem('food_app_orders') || '[]');
        const order = orders.find(o => o.id === orderId);
        if (order) {
            order.status = newStatus;
            localStorage.setItem('food_app_orders', JSON.stringify(orders));
            showToast('订单状态已更新');
            loadOrders();
        }
    }
}

function contactMerchant() {
    showToast('商家电话：400-123-4567');
}

function showToast(message) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

document.addEventListener('DOMContentLoaded', () => {
    const savedUser = localStorage.getItem('food_app_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        document.getElementById('authPage').style.display = 'none';
        document.getElementById('app').style.display = 'block';
        loadProfile();
    }
});