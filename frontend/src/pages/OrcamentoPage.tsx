import { useParams } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ArrowLeft, Save, Calculator } from 'lucide-react';

export function OrcamentoPage() {
  const { id } = useParams();

  return (
    <div className="orcamento-container">
      <header className="page-header">
        <Button variant="ghost" onClick={() => window.history.back()} className="gap-2">
          <ArrowLeft size={20} />
          <span>Voltar</span>
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Calculator size={18} />
            Recalcular
          </Button>
          <Button className="gap-2">
            <Save size={18} />
            Salvar
          </Button>
        </div>
      </header>

      <div className="orcamento-layout">
        <Card title={`Orçamento #${id || 'Novo'}`}>
          <p className="muted">Detalhes do orçamento e listagem de fichas.</p>
        </Card>
      </div>
    </div>
  );
}
