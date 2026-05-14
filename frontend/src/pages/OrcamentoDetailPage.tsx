// src/pages/OrcamentoDetailPage.tsx
import { Fragment, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../components/ui/Button';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { FichaForm } from '../components/ui/FichaForm';
import { SpreadingResultTable } from '../components/ui/SpreadingResultTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import {
  useCalcularFicha,
  useDeleteFicha,
  useDeleteOrcamento,
  useFichas,
  useOrcamento,
  useSpreading,
} from '../hooks/useApi';
import type { Ficha, SpreadingResponse } from '../types';
import { formatCurrency, formatDateLong } from '../utils/format';

export function OrcamentoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // orcamento
  const { data, isLoading, error } = useOrcamento(id);
  const deleteMutation = useDeleteOrcamento();
  const [showDeleteOrcamento, setShowDeleteOrcamento] = useState(false);

  // fichas
  const { data: fichas = [], isLoading: fichasLoading } = useFichas(id);
  const calcularFicha = useCalcularFicha();
  const deleteFicha = useDeleteFicha();
  const spreading = useSpreading();

  // ui state
  const [openFormId, setOpenFormId] = useState<string | null>(null);
  const [deleteFichaId, setDeleteFichaId] = useState<string | null>(null);
  const [pendingCalcId, setPendingCalcId] = useState<string | null>(null);
  const [spreadingResult, setSpreadingResult] = useState<SpreadingResponse | null>(null);

  // ── Handlers orcamento ──────────────────────────────────────────
  async function handleDeleteOrcamento() {
    try {
      await deleteMutation.mutateAsync(id!);
      toast.success('Orçamento excluído.');
      navigate('/orcamentos');
    } catch {
      // error toast shown by mutation
    }
  }

  // ── Handlers fichas ─────────────────────────────────────────────
  function openEditForm(fichaId: string) {
    setOpenFormId(openFormId === fichaId ? null : fichaId);
  }

  function openNewForm() {
    setOpenFormId(openFormId === 'new' ? null : 'new');
  }

  async function handleCalcular(fichaId: string) {
    setPendingCalcId(fichaId);
    try {
      const result = await calcularFicha.mutateAsync({ orcamentoId: id!, fichaId });
      toast.success(`Preço calculado: ${formatCurrency(result.preco_unitario)}`);
    } catch {
      // error toast shown by mutation
    } finally {
      setPendingCalcId(null);
    }
  }

  async function handleDeleteFicha() {
    if (!deleteFichaId) return;
    try {
      await deleteFicha.mutateAsync({ orcamentoId: id!, fichaId: deleteFichaId });
      toast.success('Ficha excluída.');
    } catch {
      // error toast shown by mutation
    } finally {
      setDeleteFichaId(null);
    }
  }

  async function handleSpreading() {
    try {
      const result = await spreading.mutateAsync(id!);
      setSpreadingResult(result);
      toast.success(`Spreading aplicado! Total: ${formatCurrency(result.total_final)}`);
    } catch {
      // error toast shown by mutation
    }
  }

  function fichaToDefaultValues(ficha: Ficha) {
    return {
      descricao:         ficha.descricao,
      unidade:           ficha.unidade,
      quantidade:        ficha.quantidade,
      custo_unitario:    ficha.custo_unitario,
      tipo_precificacao: ficha.tipo_precificacao as 'markup' | 'bdi_manual' | 'bdi_classico',
      ordem:             ficha.ordem,
    };
  }

  // ── Loading / Error states ──────────────────────────────────────
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

  // ── Render ──────────────────────────────────────────────────────
  return (
    <div>
      {/* ── Cabeçalho ── */}
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
          <Button variant="outline" onClick={() => setShowDeleteOrcamento(true)}>
            Excluir
          </Button>
        </div>
      </div>

      {/* ── Detalhes do orçamento ── */}
      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1.5rem',
          marginBottom: '1.5rem',
        }}
      >
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

      {/* ── Seção Fichas ── */}
      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1.5rem',
        }}
      >
        <div className="fichas-header">
          <h2>Fichas</h2>
          <Button size="sm" onClick={openNewForm}>
            {openFormId === 'new' ? '✕ Fechar' : '+ Nova ficha'}
          </Button>
        </div>

        {/* Form de criação */}
        {openFormId === 'new' && (
          <FichaForm
            orcamentoId={id!}
            onSuccess={() => {
              setOpenFormId(null);
              toast.success('Ficha criada!');
            }}
            onCancel={() => setOpenFormId(null)}
          />
        )}

        {/* Loading fichas */}
        {fichasLoading && (
          <div className="loading-center" style={{ minHeight: '6rem' }}>
            <span className="spinner" />
          </div>
        )}

        {/* Estado vazio */}
        {!fichasLoading && fichas.length === 0 && (
          <div className="empty-state" style={{ minHeight: '6rem' }}>
            <p>Nenhuma ficha cadastrada.</p>
            {openFormId !== 'new' && (
              <button
                type="button"
                onClick={openNewForm}
                style={{
                  marginTop: '0.5rem',
                  color: 'var(--primary)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                + Adicionar primeira ficha
              </button>
            )}
          </div>
        )}

        {/* Tabela normal ou resultado de spreading */}
        {!fichasLoading && fichas.length > 0 && (
          <>
            {spreadingResult ? (
              <SpreadingResultTable
                result={spreadingResult}
                onClear={() => setSpreadingResult(null)}
              />
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Descrição</th>
                      <th>Unidade</th>
                      <th>Qtd</th>
                      <th>Custo unit. (R$)</th>
                      <th>Preço calc. (R$)</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fichas.map((ficha) => (
                      <Fragment key={ficha.id}>
                        <tr>
                          <td>{ficha.descricao}</td>
                          <td>{ficha.unidade}</td>
                          <td>{ficha.quantidade}</td>
                          <td>{formatCurrency(ficha.custo_unitario)}</td>
                          <td>
                            {ficha.preco_unitario_calculado
                              ? formatCurrency(ficha.preco_unitario_calculado)
                              : <span className="muted">—</span>}
                          </td>
                          <td>
                            <div className="table-actions">
                              <button
                                className="action-btn"
                                onClick={() => handleCalcular(ficha.id)}
                                disabled={pendingCalcId === ficha.id}
                                title="Calcular preço unitário"
                              >
                                Calcular
                              </button>
                              <button
                                className="action-btn"
                                onClick={() => openEditForm(ficha.id)}
                                title="Editar ficha"
                              >
                                {openFormId === ficha.id ? 'Fechar' : 'Editar'}
                              </button>
                              <button
                                className="action-btn"
                                onClick={() => setDeleteFichaId(ficha.id)}
                                title="Excluir ficha"
                              >
                                Excluir
                              </button>
                            </div>
                          </td>
                        </tr>
                        {openFormId === ficha.id && (
                          <tr className="ficha-inline-form-row">
                            <td colSpan={6}>
                              <FichaForm
                                orcamentoId={id!}
                                fichaId={ficha.id}
                                defaultValues={fichaToDefaultValues(ficha)}
                                onSuccess={() => {
                                  setOpenFormId(null);
                                  toast.success('Ficha atualizada!');
                                }}
                                onCancel={() => setOpenFormId(null)}
                              />
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {!spreadingResult && (
              <div
                style={{
                  marginTop: '1.25rem',
                  paddingTop: '1rem',
                  borderTop: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '1rem',
                  flexWrap: 'wrap',
                }}
              >
                <p style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>
                  Custo fixo total do orçamento:{' '}
                  <strong style={{ color: 'var(--foreground)' }}>
                    {formatCurrency(data.custo_fixo_total)}
                  </strong>
                </p>
                <Button
                  onClick={handleSpreading}
                  disabled={spreading.isPending || fichas.length === 0}
                >
                  {spreading.isPending ? <span className="spinner" /> : 'Executar Spreading'}
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Dialogs ── */}
      <ConfirmDialog
        open={showDeleteOrcamento}
        title="Excluir orçamento?"
        message={`"${data.titulo}" será removido permanentemente.`}
        confirmLabel="Excluir"
        onConfirm={handleDeleteOrcamento}
        onCancel={() => setShowDeleteOrcamento(false)}
        isLoading={deleteMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteFichaId}
        title="Excluir ficha?"
        message="Esta ficha será removida permanentemente do orçamento."
        confirmLabel="Excluir"
        onConfirm={handleDeleteFicha}
        onCancel={() => setDeleteFichaId(null)}
        isLoading={deleteFicha.isPending}
      />
    </div>
  );
}
