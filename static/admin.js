const adminPanel = document.createElement('section');
adminPanel.className = 'hidden card admin-panel';
adminPanel.innerHTML = `<div class="section-title"><h2>Administration des utilisateurs</h2><button id="adminRefresh" class="light">Actualiser</button></div>
<p id="adminMessage" role="status" aria-live="polite"></p><div id="adminStats" class="stats"></div>
<details><summary>Créer un utilisateur</summary><form id="adminCreate" class="admin-form">
<label>Nom complet<input name="name" required minlength="2"></label>
<label>Identifiant<input name="username" required minlength="3" autocomplete="off"></label>
<label>Mot de passe initial<input name="password" type="password" required minlength="6" autocomplete="new-password"></label>
<button class="primary">Créer le compte</button></form></details>
<label>Rechercher<input id="adminSearch" type="search" placeholder="Nom ou identifiant"></label>
<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Utilisateur</th><th>Rôle / statut</th><th>Progression</th><th>Actions</th></tr></thead><tbody id="adminUsers"></tbody></table></div>`;
document.querySelector('#app .container').prepend(adminPanel);
let managedUsers = [];
function adminMessage(message, error = false) {
  $('#adminMessage').textContent = message; $('#adminMessage').classList.toggle('error', error);
}
async function adminApi(username, method, data) {
  return api('/api/admin/users' + (username === null ? '' : '/' + encodeURIComponent(username)), {
    method, headers: {'Content-Type': 'application/json', 'X-CSRF-Token': dash.csrf},
    ...(data ? {body: JSON.stringify(data)} : {})});
}
async function loadAdmin() {
  try {
    const data = await api('/api/admin/users'); managedUsers = data.users;
    $('#adminStats').replaceChildren(...[['Comptes', data.stats.total], ['Actifs', data.stats.active],
      ['Quiz réalisés', data.stats.attempts], ['Examens réalisés', data.stats.exams]].map(([label, value]) => {
      const box = document.createElement('div'); box.className = 'stat';
      const span = document.createElement('span'); span.textContent = label;
      const b = document.createElement('b'); b.textContent = value; box.append(span, b); return box;
    })); renderAdminUsers();
  } catch (error) { adminMessage(error.message, true); }
}
function renderAdminUsers() {
  const search = $('#adminSearch').value.toLocaleLowerCase('fr');
  const tbody = $('#adminUsers'); tbody.replaceChildren();
  managedUsers.filter(u => `${u.name} ${u.username}`.toLocaleLowerCase('fr').includes(search)).forEach(user => {
    const row = document.createElement('tr');
    function cell(text) { const td = document.createElement('td'); td.textContent = text; row.append(td); return td; }
    cell(`${user.name} (${user.username}) · Inscription : ${user.created_at ? new Date(user.created_at).toLocaleDateString('fr-CA') : '—'}`);
    cell(`${user.role === 'superadmin' ? 'Superadmin' : 'Utilisateur'} · ${user.active ? 'Actif' : 'Désactivé'}`);
    cell(`${user.completed}/${dash.total} modules · ${user.attempts} quiz · ${user.exams} examens · Moyenne : ${user.average === null ? '—' : user.average + '%'}`);
    const actions = cell('');
    function button(label, handler, disabled = false) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'light'; b.textContent = label; b.disabled = disabled;
      b.onclick = async () => { try { await handler(); } catch (error) { adminMessage(error.message, true); } }; actions.append(b);
    }
    async function update(data) { await adminApi(user.username, 'PATCH', data); adminMessage('Compte mis à jour.'); await loadAdmin(); }
    const self = user.username === dash.user.username;
    button('Modifier le nom', async () => { const name = prompt('Nom complet', user.name); if (name !== null) await update({name}); });
    button('Réinitialiser le mot de passe', () => openPasswordReset(user));
    button(user.active ? 'Désactiver' : 'Réactiver', async () => {
      if (confirm(`Changer le statut de ${user.username} ?`)) await update({active: !user.active});
    }, self);
    button(user.role === 'superadmin' ? 'Retirer le rôle superadmin' : 'Nommer superadmin', async () => {
      if (confirm(`Changer le rôle de ${user.username} ?`)) await update({role: user.role === 'superadmin' ? 'user' : 'superadmin'});
    }, self);
    button('Supprimer', async () => {
      if (confirm(`Supprimer définitivement ${user.username} et tous ses résultats ?`)) {
        await adminApi(user.username, 'DELETE'); adminMessage('Compte supprimé.'); await loadAdmin();
      }
    }, self); tbody.append(row);
  });
  if (!tbody.children.length) { const cell = tbody.insertRow().insertCell(); cell.colSpan = 4; cell.textContent = 'Aucun utilisateur trouvé.'; }
}
const passwordDialog = document.createElement('dialog');
passwordDialog.innerHTML = `<form class="admin-panel" id="adminPasswordForm"><h2>Réinitialiser le mot de passe</h2><p id="adminPasswordUser"></p>
<label>Nouveau mot de passe<input id="adminNewPassword" type="password" minlength="6" required autocomplete="new-password"></label>
<label>Confirmer le mot de passe<input id="adminConfirmPassword" type="password" minlength="6" required autocomplete="new-password"></label>
<p id="adminPasswordError" class="error" role="alert"></p><button class="primary">Enregistrer</button>
<button type="button" id="adminPasswordCancel" class="light">Annuler</button><p>Les sessions existantes du compte seront déconnectées.</p></form>`;
document.body.append(passwordDialog);
let passwordUser;
function openPasswordReset(user) {
  passwordUser = user; $('#adminPasswordForm').reset(); $('#adminPasswordError').textContent = '';
  $('#adminPasswordUser').textContent = user.username; passwordDialog.showModal();
}
$('#adminPasswordCancel').onclick = () => passwordDialog.close();
passwordDialog.addEventListener('close', () => $('#adminPasswordForm').reset());
$('#adminPasswordForm').onsubmit = async event => {
  event.preventDefault();
  if ($('#adminNewPassword').value !== $('#adminConfirmPassword').value) { $('#adminPasswordError').textContent = 'Les mots de passe ne correspondent pas.'; return; }
  try {
    await adminApi(passwordUser.username, 'PATCH', {password: $('#adminNewPassword').value}); passwordDialog.close();
    if (passwordUser.username === dash.user.username) { location.reload(); return; }
    adminMessage('Mot de passe réinitialisé. Transmettez-le à l’utilisateur par un canal privé.');
  } catch (error) { $('#adminPasswordError').textContent = error.message; }
};
$('#adminSearch').oninput = renderAdminUsers; $('#adminRefresh').onclick = loadAdmin;
$('#adminCreate').onsubmit = async event => {
  event.preventDefault();
  try { await adminApi(null, 'POST', Object.fromEntries(new FormData(event.target))); event.target.reset(); adminMessage('Compte créé.'); await loadAdmin(); }
  catch (error) { adminMessage(error.message, true); }
};
const renderDashboard = render;
render = function () { renderDashboard(); const isAdmin = dash.user.role === 'superadmin'; adminPanel.classList.toggle('hidden', !isAdmin); if (isAdmin) loadAdmin(); };
if (dash) render();
