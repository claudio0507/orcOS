import { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import toast from 'react-hot-toast';
import { useMfaSetup, useMfaVerify } from '../hooks/useApi';
import type { MfaSetupResponse } from '../types';

type MfaStep = 'idle' | 'scan' | 'verify' | 'active';

export function ConfiguracoesPage() {
  const [mfaStep, setMfaStep] = useState<MfaStep>('idle');
  const [mfaData, setMfaData] = useState<MfaSetupResponse | null>(null);
  const [verifyCode, setVerifyCode] = useState('');

  const mfaSetup = useMfaSetup();
  const mfaVerify = useMfaVerify();

  async function handleStartSetup() {
    try {
      const data = await mfaSetup.mutateAsync();
      setMfaData(data);
      setMfaStep('scan');
    } catch {
      // error toast shown by mutation
    }
  }

  async function handleVerify() {
    if (!mfaData) return;
    try {
      await mfaVerify.mutateAsync({ secret: mfaData.secret, totp_code: verifyCode });
      toast.success('MFA ativado com sucesso!');
      setMfaStep('active');
      setVerifyCode('');
    } catch {
      setVerifyCode('');
    }
  }

  function handleCopySecret() {
    if (!mfaData) return;
    navigator.clipboard.writeText(mfaData.secret).then(() => {
      toast.success('Chave copiada!');
    });
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Configurações</h1>
      </div>

      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1.5rem',
          maxWidth: '560px',
        }}
      >
        <h2 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: 600 }}>
          Autenticação de Dois Fatores (MFA)
        </h2>

        {/* idle */}
        {mfaStep === 'idle' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span
              style={{
                background: '#f1f5f9',
                color: '#64748b',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                fontSize: '0.8125rem',
                fontWeight: 600,
              }}
            >
              MFA não configurado
            </span>
            <button
              onClick={handleStartSetup}
              disabled={mfaSetup.isPending}
              style={{
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                padding: '0.4rem 0.875rem',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              {mfaSetup.isPending ? (
                <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />
              ) : (
                'Ativar MFA'
              )}
            </button>
          </div>
        )}

        {/* scan */}
        {mfaStep === 'scan' && mfaData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>
              Escaneie o QR Code com Google Authenticator, Authy ou similar:
            </p>
            <QRCodeSVG value={mfaData.provisioning_uri} size={200} />
            <div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--muted)', marginBottom: '0.375rem' }}>
                Ou adicione manualmente a chave secreta:
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <code
                  style={{
                    background: '#f1f5f9',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.8125rem',
                    letterSpacing: '0.05em',
                  }}
                >
                  {mfaData.secret}
                </code>
                <button
                  onClick={handleCopySecret}
                  style={{
                    background: 'none',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                  }}
                >
                  Copiar
                </button>
              </div>
            </div>
            <button
              onClick={() => setMfaStep('verify')}
              style={{
                alignSelf: 'flex-start',
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                padding: '0.4rem 0.875rem',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              Já escaniei, continuar →
            </button>
          </div>
        )}

        {/* verify */}
        {mfaStep === 'verify' && mfaData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>
              Digite o código de 6 dígitos exibido no seu aplicativo autenticador:
            </p>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              autoFocus
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ''))}
              placeholder="000000"
              style={{
                width: '8rem',
                padding: '0.5rem',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                fontSize: '1.25rem',
                textAlign: 'center',
                letterSpacing: '0.2em',
              }}
            />
            <button
              onClick={handleVerify}
              disabled={mfaVerify.isPending || verifyCode.length !== 6}
              style={{
                alignSelf: 'flex-start',
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                padding: '0.4rem 0.875rem',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              {mfaVerify.isPending ? (
                <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />
              ) : (
                'Verificar'
              )}
            </button>
          </div>
        )}

        {/* active */}
        {mfaStep === 'active' && (
          <span
            style={{
              background: '#dcfce7',
              color: '#16a34a',
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.8125rem',
              fontWeight: 600,
            }}
          >
            ✓ MFA ativo
          </span>
        )}
      </div>
    </div>
  );
}
