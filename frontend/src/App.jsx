import React, { useState } from 'react';
import LoginForm from './components/ui/LoginForm';
import RegisterForm from './components/ui/RegisterForm';

function App() {
  const [view, setView] = useState('login'); // 'login' | 'register' | 'welcome'
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');

  // Connexion
  const handleLogin = async (username, password) => {
    setError('');
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok) {
        setUser(data.user);
        setView('welcome');
      } else {
        setError(data.error || 'Erreur de connexion');
      }
    } catch (e) {
      setError('Erreur réseau');
    }
  };

  // Inscription
  const handleRegister = async (infos) => {
    setError('');
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(infos)
      });
      const data = await res.json();
      if (res.ok) {
        setView('login');
        setError('Inscription réussie, connectez-vous.');
      } else {
        setError(data.error || "Erreur d'inscription");
      }
    } catch (e) {
      setError('Erreur réseau');
    }
  };

  // Déconnexion
  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    setUser(null);
    setView('login');
    setError('');
  };

  return (
    <div className="container" style={{ maxWidth: 400, margin: '2rem auto' }}>
      <div className="logo" style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1>🛡 SLOMAH ACT 1</h1>
        <p>Créé par KEMCHE</p>
      </div>
      {view === 'login' && (
        <LoginForm onLogin={handleLogin} onGoToRegister={() => { setView('register'); setError(''); }} error={error} />
      )}
      {view === 'register' && (
        <RegisterForm onRegister={handleRegister} onGoToLogin={() => { setView('login'); setError(''); }} error={error} />
      )}
      {view === 'welcome' && user && (
        <div style={{ textAlign: 'center' }}>
          <h2>Bienvenue, {user.username} !</h2>
          <button onClick={handleLogout} style={{ marginTop: '1.5rem', width: '100%', padding: '0.7rem', background: '#d32f2f', color: 'white', border: 'none', borderRadius: 4, fontSize: '1rem', cursor: 'pointer' }}>
            Se déconnecter
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
