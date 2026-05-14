// src/components/ui/SpreadingResultTable.tsx
import type { SpreadingResponse } from '../../types';
import { formatCurrency } from '../../utils/format';

interface SpreadingResultTableProps {
  result: SpreadingResponse;
  onClear: () => void;
}

export function SpreadingResultTable({ result, onClear }: SpreadingResultTableProps) {
  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.75rem',
          flexWrap: 'wrap',
          gap: '0.5rem',
        }}
      >
        <span className={`badge ${result.ca001_validado ? 'badge-green' : 'badge-yellow'}`}>
          {result.ca001_validado ? '✓ CA-001 validado' : '⚠ CA-001 falhou'}
        </span>
        <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.875rem', color: 'var(--muted)' }}>
          <span>Variável: {formatCurrency(result.total_variavel)}</span>
          <span>Fixo: {formatCurrency(result.custo_fixo_total)}</span>
          <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>
            Total: {formatCurrency(result.total_final)}
          </span>
        </div>
      </div>

      <div className="table-container">
        <table className="spreading-table">
          <thead>
            <tr>
              <th>Descrição</th>
              <th>Qtd</th>
              <th>Preço var. (R$)</th>
              <th>Fixo rat. (R$)</th>
              <th>Preço final (R$)</th>
            </tr>
          </thead>
          <tbody>
            {result.linhas.map((linha) => (
              <tr key={linha.ficha_id}>
                <td>
                  {linha.descricao}
                  {linha.carries_residue && (
                    <span
                      title="Absorveu resíduo de arredondamento (±R$0,01)"
                      style={{ marginLeft: '0.25rem', fontSize: '0.75rem', color: 'var(--muted)' }}
                    >
                      *
                    </span>
                  )}
                </td>
                <td>{linha.quantity}</td>
                <td>{formatCurrency(linha.variable_unit_price)}</td>
                <td>+{formatCurrency(linha.allocated_fixed)}</td>
                <td>{formatCurrency(linha.final_unit_price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div
        style={{
          marginTop: '0.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <p style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
          * Absorveu resíduo de arredondamento monetário (tolerância ±R$0,01)
        </p>
        <button
          type="button"
          onClick={onClear}
          style={{
            fontSize: '0.875rem',
            color: 'var(--muted)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            textDecoration: 'underline',
          }}
        >
          Limpar resultado
        </button>
      </div>
    </div>
  );
}
