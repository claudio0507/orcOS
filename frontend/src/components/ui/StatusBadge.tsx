// src/components/ui/StatusBadge.tsx
interface StatusBadgeProps {
  status: string;
}

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  rascunho: { label: 'Rascunho', className: 'badge-gray' },
  ativo:    { label: 'Ativo',    className: 'badge-green' },
  cancelado:{ label: 'Cancelado',className: 'badge-red' },
  pendente: { label: 'Pendente', className: 'badge-yellow' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const entry = STATUS_MAP[status] ?? { label: status, className: 'badge-blue' };
  return <span className={`badge ${entry.className}`}>{entry.label}</span>;
}
