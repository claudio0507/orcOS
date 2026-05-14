// src/utils/format.ts
export function formatCurrency(value: string): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(
    Number(value),
  );
}

export function formatDateShort(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR');
}

export function formatDateLong(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR');
}
