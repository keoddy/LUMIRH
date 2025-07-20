import React, { useState } from 'react';

export default function RegisterForm({ onRegister, onGoToLogin, error }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [nom, setNom] = useState('');
  const [prenom, setPrenom] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onRegister({ username, password, nom, prenom, email });
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
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="nom">Nom</label><br />
        <input
          type="text"
          id="nom"
          name="nom"
          value={nom}
          onChange={e => setNom(e.target.value)}
          style={{ width: '100%', padding: '0.5rem', marginTop: '0.3rem', borderRadius: 4, border: '1px solid #ccc' }}
        />
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="prenom">Prénom</label><br />
        <input
          type="text"
          id="prenom"
          name="prenom"
          value={prenom}
          onChange={e => setPrenom(e.target.value)}
          style={{ width: '100%', padding: '0.5rem', marginTop: '0.3rem', borderRadius: 4, border: '1px solid #ccc' }}
        />
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="email">Email</label><br />
        <input
          type="email"
          id="email"
          name="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          style={{ width: '100%', padding: '0.5rem', marginTop: '0.3rem', borderRadius: 4, border: '1px solid #ccc' }}
        />
      </div>
      <button type="submit" style={{ width: '100%', padding: '0.7rem', background: '#1976d2', color: 'white', border: 'none', borderRadius: 4, fontSize: '1rem', cursor: 'pointer' }}>
        S'inscrire
      </button>
      <div style={{ marginTop: '1rem', height: '1.2em', color: 'red' }}>{error}</div>
      <button type="button" onClick={onGoToLogin} style={{ width: '100%', padding: '0.5rem', background: '#e3f2fd', color: '#1976d2', border: 'none', borderRadius: 4, fontSize: '0.95rem', cursor: 'pointer', marginTop: 8 }}>
        Déjà un compte ? Se connecter
      </button>
    </form>
  );
}
