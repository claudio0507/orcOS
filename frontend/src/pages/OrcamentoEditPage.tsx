// src/pages/OrcamentoEditPage.tsx
import { useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { OrcamentoForm, OrcamentoFormData } from '../components/ui/OrcamentoForm';
import { useOrcamento, useUpdateOrcamento } from '../hooks/useApi';

export function OrcamentoEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading } = useOrcamento(id);
  const updateMutation = useUpdateOrcamento();

  async function handleSubmit(formData: OrcamentoFormData) {
    await updateMutation.mutateAsync({ id: id!, payload: formData });
    toast.success('Alterações salvas!');
    navigate(`/orcamentos/${id}`);
  }

  if (isLoading) {
    return (
      <div className="loading-center">
        <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
      </div>
    );
  }

  if (!data) {
    return <p className="muted">Orçamento não encontrado.</p>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Editar Orçamento</h1>
      </div>
      <div style={{ maxWidth: 640 }}>
        <OrcamentoForm
          defaultValues={{
            titulo: data.titulo,
            descricao: data.descricao ?? undefined,
            custo_fixo_total: data.custo_fixo_total,
          }}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/orcamentos/${id}`)}
          isLoading={updateMutation.isPending}
          submitLabel="Salvar Alterações"
        />
      </div>
    </div>
  );
}
