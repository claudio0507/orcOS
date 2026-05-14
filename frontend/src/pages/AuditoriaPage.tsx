import axios from 'axios';
import { useAuditStatus, useAuditVerify } from '../hooks/useApi';
import type { AuditStatusValue } from '../types';

const AUDIT_BADGE: Record<AuditStatusValue, { label: string; className: string }> = {
  OK:        { label: '✓ Cadeia íntegra',      className: 'audit-badge ok' },
  CORRUPTED: { label: '✗ Corrupção detectada', className: 'audit-badge corrupted' },
  PENDING:   { label: 'Verificação pendente',  className: 'audit-badge pending' },
  EMPTY:     { label: 'Sem registros',          className: 'audit-badge empty' },
};

export function AuditoriaPage() {
  const { data, isLoading, error } = useAuditStatus();
  const auditVerify = useAuditVerify();

  const is403 =
    axios.isAxiosError(error) && error.response?.status === 403;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Auditoria de Integridade</h1>
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
        {isLoading && (
          <div className="loading-center" style={{ minHeight: '6rem' }}>
            <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
          </div>
        )}

        {is403 && (
          <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>
            Acesso restrito a administradores.
          </p>
        )}

        {!isLoading && !is403 && data && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <span className={AUDIT_BADGE[data.status].className}>
              {AUDIT_BADGE[data.status].label}
            </span>

            <div style={{ fontSize: '0.875rem', color: 'var(--muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {data.checked_at && (
                <span>Última verificação: {new Date(data.checked_at).toLocaleString('pt-BR')}</span>
              )}
              {data.total_entries !== undefined && (
                <span>Total de entradas: {data.total_entries}</span>
              )}
              {data.corrupted_entry && (
                <span style={{ color: '#dc2626' }}>
                  Entrada corrompida: <code>{data.corrupted_entry}</code>
                </span>
              )}
            </div>

            <button
              onClick={() => auditVerify.mutate()}
              disabled={auditVerify.isPending}
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
              {auditVerify.isPending ? (
                <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />
              ) : (
                'Verificar agora'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
