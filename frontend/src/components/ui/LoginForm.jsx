import React, { useState } from 'react';

export default function LoginForm({ onLogin, onGoToRegister, error }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    onLogin(username, password);
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '1.5rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="username">Nom d'utilisateur</label><br />
        <input
          type="text"
          id="username"
          name="username"
          required
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ width: '100%', padding: '0.5rem', marginTop: '0.3rem', borderRadius: 4, border: '1px solid #ccc' }}
        />
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="password">Mot de passe</label><br />
        <input
          type="password"
          id="password"
          name="password"
          required
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ width: '100%', padding: '0.5rem', marginTop: '0.3rem', borderRadius: 4, border: '1px solid #ccc' }}
        />
      </div>
      <button type="submit" style={{ width: '100%', padding: '0.7rem', background: '#1976d2', color: 'white', border: 'none', borderRadius: 4, fontSize: '1rem', cursor: 'pointer' }}>
        Se connecter
      </button>
      <div style={{ marginTop: '1rem', height: '1.2em', color: 'red' }}>{error}</div>
      <button type="button" onClick={onGoToRegister} style={{ width: '100%', padding: '0.5rem', background: '#e3f2fd', color: '#1976d2', border: 'none', borderRadius: 4, fontSize: '0.95rem', cursor: 'pointer', marginTop: 8 }}>
        Créer un compte
      </button>
    </form>
  );
}
