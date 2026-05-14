// src/pages/LoginPage.tsx
import { useState } from 'react';
import { Card } from '../components/ui/Card';
import { LoginForm } from '../components/auth/LoginForm';
import { MFAForm } from '../components/auth/MFAForm';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const [mfaRequired, setMfaRequired] = useState(false);
  const [partialToken, setPartialToken] = useState('');
  const { verifyMfa } = useAuth();

  function handleMfaRequired(token: string) {
    setPartialToken(token);
    setMfaRequired(true);
  }

  async function handleMfaVerify(code: string) {
    await verifyMfa({ partial_token: partialToken, totp_code: code });
  }

  return (
    <div className="login-page">
      <div className="auth-card">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--foreground)' }}>orcOS</h1>
          <p className="muted" style={{ marginTop: '0.5rem' }}>
            {mfaRequired ? 'Verificação em duas etapas' : 'Sistema de Orçamentos'}
          </p>
        </div>
        <Card>
          {mfaRequired ? (
            <MFAForm onVerify={handleMfaVerify} />
          ) : (
            <LoginForm onMfaRequired={handleMfaRequired} />
          )}
        </Card>
      </div>
    </div>
  );
}
