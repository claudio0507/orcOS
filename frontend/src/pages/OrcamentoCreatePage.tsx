// src/pages/OrcamentoCreatePage.tsx
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { OrcamentoForm } from '../components/ui/OrcamentoForm';
import type { OrcamentoFormData } from '../components/ui/OrcamentoForm';
import { useCreateOrcamento } from '../hooks/useApi';

export function OrcamentoCreatePage() {
  const navigate = useNavigate();
  const createMutation = useCreateOrcamento();

  async function handleSubmit(data: OrcamentoFormData) {
    const created = await createMutation.mutateAsync(data);
    toast.success('Orçamento criado!');
    navigate(`/orcamentos/${created.id}`);
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Novo Orçamento</h1>
      </div>
      <div style={{ maxWidth: 640 }}>
        <OrcamentoForm
          onSubmit={handleSubmit}
          onCancel={() => navigate('/orcamentos')}
          isLoading={createMutation.isPending}
          submitLabel="Criar Orçamento"
        />
      </div>
    </div>
  );
}
