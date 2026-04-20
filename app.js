const API_URL = "https://sirsi-sambhrama-backend.onrender.com";
let globalArticles = []; 

function switchAuthScreen(screenId) {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('registerScreen').style.display = 'none';
    document.getElementById('forgotScreen').style.display = 'none';
    
    document.getElementById(screenId).style.display = 'flex';

    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('regOtpForm').style.display = 'none';
    document.getElementById('registerForm').reset();
    document.getElementById('regOtpForm').reset();

    document.getElementById('forgotForm').style.display = 'block';
    document.getElementById('resetForm').style.display = 'none';
    document.getElementById('forgotForm').reset();
    document.getElementById('resetForm').reset();

    document.getElementById('loginForm').reset();
    document.getElementById('loginError').style.display = 'none';
}

function parseJwt(token) {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        return null;
    }
}

window.onload = () => {
    const token = localStorage.getItem("sirsi_token");
    if (token) showDashboard(token);
};

document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    const response = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem("sirsi_token", data.access_token);
        showDashboard(data.access_token);
    } else {
        document.getElementById("loginError").style.display = "block";
    }
});

document.getElementById("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        email: document.getElementById("regEmail").value,
        auth_name: document.getElementById("regName").value,
        password: document.getElementById("regPassword").value,
        invite_code: document.getElementById("regInvite").value
    };

    const res = await fetch(`${API_URL}/register/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        document.getElementById("registerForm").style.display = "none";
        document.getElementById("regOtpForm").style.display = "block";
    } else {
        alert("Registration failed. Check your invite code or email.");
    }
});

document.getElementById("regOtpForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        email: document.getElementById("regEmail").value,
        otp_code: document.getElementById("regOtpCode").value
    };

    const res = await fetch(`${API_URL}/register/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Account Verified! You can now log in.");
        switchAuthScreen('loginScreen');
    } else {
        alert("Invalid OTP");
    }
});

document.getElementById("forgotForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        email: document.getElementById("forgotEmail").value,
        password: "placeholder_not_used" 
    };

    const res = await fetch(`${API_URL}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        document.getElementById("forgotForm").style.display = "none";
        document.getElementById("resetForm").style.display = "block";
    }
});

document.getElementById("resetForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        email: document.getElementById("forgotEmail").value,
        otp_code: document.getElementById("resetOtpCode").value,
        new_password: document.getElementById("resetNewPassword").value
    };

    const res = await fetch(`${API_URL}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Password updated! Please log in.");
        switchAuthScreen('loginScreen');
    } else {
        alert("Failed to reset password. Check OTP.");
    }
});

function logout() {
    localStorage.removeItem("sirsi_token");
    location.reload();
}

function showDashboard(token) {
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("dashboardScreen").style.display = "flex";
    
    const tokenData = parseJwt(token);
    if (tokenData && tokenData.name) {
        document.getElementById("userDisplay").innerText = `Welcome, ${tokenData.name}`;
    }

    loadArticles(token);
}

async function loadArticles(token) {
    const response = await fetch(`${API_URL}/news/me`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!response.ok) return logout();

    globalArticles = await response.json();
    const grid = document.getElementById("newsGrid");
    grid.innerHTML = ""; 

    globalArticles.forEach(article => {
        let statusBadges = '';
        if (article.is_trending) statusBadges += '🔥 Trending ';
        if (article.is_breaking) statusBadges += '🚨 Breaking ';
        if (!article.is_published) statusBadges += '📝 Draft';

        grid.innerHTML += `
            <div class="card">
                <img src="${article.image_url}" alt="News Image">
                <span style="background: #eee; padding: 3px 8px; border-radius: 10px; font-size: 12px;">${article.category}</span>
                <p style="font-size: 12px; margin: 5px 0 0 0; color: #e67e22; font-weight: bold;">${statusBadges}</p>
                <h3 style="margin: 5px 0;">${article.title}</h3>
                <p style="color: gray; font-size: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${article.article}</p>
                <div class="card-actions">
                    <button class="btn btn-edit" onclick="openEditModal(${article.id})">Edit</button>
                    <button class="btn btn-delete" onclick="deleteArticle(${article.id})">Delete</button>
                </div>
            </div>
        `;
    });
}

function openCreateModal() { document.getElementById("createModal").style.display = "block"; }

document.getElementById("createForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("sirsi_token");
    
    let formData = new FormData();
    formData.append("title", document.getElementById("createTitle").value);
    formData.append("article", document.getElementById("createArticle").value);
    formData.append("category", document.getElementById("createCategory").value);
    formData.append("image_cap", document.getElementById("createImageCap").value);
    
    formData.append("is_trending", document.getElementById("createTrending").checked);
    formData.append("is_breaking", document.getElementById("createBreaking").checked);
    formData.append("is_published", document.getElementById("createPublished").checked);
    
    formData.append("image_file", document.getElementById("createImage").files[0]);

    await fetch(`${API_URL}/news/create`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
    });

    closeModals();
    loadArticles(token); 
});

function openEditModal(id) {
    const art = globalArticles.find(a => a.id === id);
    
    document.getElementById("editId").value = art.id;
    document.getElementById("editTitle").value = art.title;
    document.getElementById("editArticle").value = art.article;
    document.getElementById("editCategory").value = art.category;
    document.getElementById("editImageCap").value = art.image_cap;
    
    document.getElementById("editTrending").checked = art.is_trending;
    document.getElementById("editBreaking").checked = art.is_breaking;
    document.getElementById("editPublished").checked = art.is_published;
    
    document.getElementById("editModal").style.display = "block";
}

document.getElementById("editForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("sirsi_token");
    const id = document.getElementById("editId").value;
    
    let formData = new FormData();
    formData.append("title", document.getElementById("editTitle").value);
    formData.append("article", document.getElementById("editArticle").value);
    formData.append("category", document.getElementById("editCategory").value);
    formData.append("image_cap", document.getElementById("editImageCap").value);
    
    formData.append("is_trending", document.getElementById("editTrending").checked);
    formData.append("is_breaking", document.getElementById("editBreaking").checked);
    formData.append("is_published", document.getElementById("editPublished").checked);
    
    const imageFile = document.getElementById("editImage").files[0];
    if (imageFile) {
        formData.append("image_file", imageFile); 
    }

    await fetch(`${API_URL}/news/${id}`, {
        method: "PATCH",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
    });

    closeModals();
    loadArticles(token); 
});

async function deleteArticle(id) {
    if(!confirm("Are you sure you want to delete this article?")) return;
    
    const token = localStorage.getItem("sirsi_token");
    await fetch(`${API_URL}/news/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    
    loadArticles(token); 
}

function closeModals() {
    document.getElementById("createModal").style.display = "none";
    document.getElementById("editModal").style.display = "none";
    document.getElementById("createForm").reset();
    document.getElementById("editForm").reset();
}

async function changeName() {
    const newName = prompt("Enter your new Pen Name:");
    
    if (!newName || newName.trim() === "") return; 
    
    const token = localStorage.getItem("sirsi_token");
    
    const response = await fetch(`${API_URL}/auth/update-name`, {
        method: "PATCH",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ new_name: newName.trim() })
    });

    if (response.ok) {
        alert("Pen Name updated successfully! Please log in again to apply changes.");
        logout();
    } else {
        alert("Failed to update name.");
    }
}