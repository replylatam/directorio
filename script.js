// Base de datos en el navegador
const DB = {
  users: JSON.parse(localStorage.getItem('users')) || [
    { username: 'admin', password: '1234', role: 'admin' }
  ],
  clientes: [
    { nombre: 'Ana López', email: 'ana@empresa.com', telefono: '3001234567', empresa: 'TechCorp' },
    { nombre: 'Carlos Ruiz', email: 'carlos@ventas.com', telefono: '3109876543', empresa: 'VentasPro' },
    { nombre: 'María Gómez', email: 'maria@startup.io', telefono: '3205554433', empresa: 'StartUpX' },
    { nombre: 'Luis Pérez', email: 'luis@negocios.co', telefono: '3154443322', empresa: 'Negocios Global' },
    { nombre: 'Sofía Martínez', email: 'sofia@tech.io', telefono: '3015556677', empresa: 'TechSolutions' }
  ]
};

// Guardar usuarios
function saveUsers() {
  localStorage.setItem('users', JSON.stringify(DB.users));
}

// Login
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const error = document.getElementById('error');

    const user = DB.users.find(u => u.username === username && u.password === password);

    if (user) {
      sessionStorage.setItem('currentUser', JSON.stringify(user));
      error.textContent = '';
      if (user.role === 'admin') {
        window.location.href = './admin.html';
      } else {
        window.location.href = './usuarios.html';
      }
    } else {
      error.textContent = 'Usuario o contraseña incorrectos';
    }
  });
}

// Verificar sesión
function checkAuth(requiredRole = null) {
  const user = JSON.parse(sessionStorage.getItem('currentUser'));
  if (!user || (requiredRole && user.role !== requiredRole)) {
    window.location.href = './index.html';
  }
  return user;
}

// Cerrar sesión
function logout() {
  if (confirm('¿Seguro que quieres cerrar sesión?')) {
    sessionStorage.removeItem('currentUser');
    window.location.href = './index.html';
  }
}

// === PANEL ADMIN ===
if (window.location.pathname.includes('admin')) {
  checkAuth('admin');

  // Crear lista y formulario si no existen
  let container = document.querySelector('.container');
  let userList = document.getElementById('userList');
  if (!userList) {
    userList = document.createElement('ul');
    userList.id = 'userList';
    container.insertBefore(userList, document.querySelector('table'));
  }

  let createForm = document.getElementById('createUserForm');
  if (!createForm) {
    createForm = document.createElement('form');
    createForm.id = 'createUserForm';
    createForm.innerHTML = `
      <h2>Crear Nuevo Usuario</h2>
      <input type="text" id="newUsername" placeholder="Usuario" required />
      <input type="password" id="newPassword" placeholder="Contraseña" required />
      <button type="submit">Crear Usuario</button>
    `;
    container.insertBefore(createForm, userList);
  }

  function loadUsers() {
    userList.innerHTML = '';
    DB.users.forEach(u => {
      if (u.role !== 'admin') {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${u.username}</strong> → Contraseña: <code>${u.password}</code>`;
        userList.appendChild(li);
      }
    });
  }

  createForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('newUsername').value.trim();
    const password = document.getElementById('newPassword').value;

    if (!username || !password) return alert('Completa todos los campos');
    if (DB.users.some(u => u.username === username)) return alert('Este usuario ya existe');

    DB.users.push({ username, password, role: 'user' });
    saveUsers();
    loadUsers();
    alert(`Usuario "${username}" creado con éxito`);
    this.reset();
  });

  loadUsers();
}

// === DIRECTORIO CLIENTES (usuarios normales) ===
if (window.location.pathname.includes('usuarios')) {
  checkAuth();

  const tbody = document.querySelector('#clientesTable tbody');
  DB.clientes.forEach(cliente => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${cliente.nombre}</strong></td>
      <td>${cliente.email}</td>
      <td>${cliente.telefono}</td>
      <td>${cliente.empresa}</td>
    `;
    tbody.appendChild(tr);
  });
}
