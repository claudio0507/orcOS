// src/pages/OrcamentoDetailPage.tsx
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../components/ui/Button';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useDeleteOrcamento, useOrcamento } from '../hooks/useApi';
import { formatCurrency, formatDateLong } from '../utils/format';

export function OrcamentoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useOrcamento(id);
  const deleteMutation = useDeleteOrcamento();
  const [showDelete, setShowDelete] = useState(false);

  async function handleDelete() {
    try {
      await deleteMutation.mutateAsync(id!);
      toast.success('Orçamento excluído.');
      navigate('/orcamentos');
    } catch {
      // error toast already shown by useDeleteOrcamento onError
    }
  }

  if (isLoading) {
    return (
      <div className="loading-center">
        <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="empty-state">
        <p>Orçamento não encontrado.</p>
        <Link to="/orcamentos" style={{ marginTop: '1rem', display: 'block' }}>
          ← Voltar para lista
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/orcamentos" className="muted" style={{ fontSize: '0.875rem' }}>
            ← Orçamentos
          </Link>
          <h1 className="page-title" style={{ marginTop: '0.25rem' }}>
            {data.titulo}
          </h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Button variant="outline" onClick={() => navigate(`/orcamentos/${id}/editar`)}>
            Editar
          </Button>
          <Button variant="outline" onClick={() => setShowDelete(true)}>
            Excluir
          </Button>
        </div>
      </div>

      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1.5rem', marginBottom: '1.5rem' }}>
        <div className="detail-grid">
          <div className="detail-field">
            <label>Status</label>
            <StatusBadge status={data.status} />
          </div>
          <div className="detail-field">
            <label>Custo Fixo Total</label>
            <p>{formatCurrency(data.custo_fixo_total)}</p>
          </div>
          <div className="detail-field">
            <label>Criado em</label>
            <p className="muted">{formatDateLong(data.created_at)}</p>
          </div>
          <div className="detail-field">
            <label>Atualizado em</label>
            <p className="muted">{formatDateLong(data.updated_at)}</p>
          </div>
          {data.descricao && (
            <div className="detail-field" style={{ gridColumn: '1 / -1' }}>
              <label>Descrição</label>
              <p>{data.descricao}</p>
            </div>
          )}
        </div>
      </div>

      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1.5rem' }}>
        <p className="detail-section-title">Fichas</p>
        <p className="muted" style={{ fontSize: '0.875rem' }}>
          Gerenciamento de fichas disponível na Fase 6.
        </p>
      </div>

      <ConfirmDialog
        open={showDelete}
        title="Excluir orçamento?"
        message={`"${data.titulo}" será removido permanentemente.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
