/**
 * Utilitários diversos para o frontend.
 */

/**
 * Formata um valor numérico ou string como moeda (BRL).
 */
export function formatCurrency(value: string | number): string {
  const amount = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(amount);
}

/**
 * Filtra classes CSS condicionais.
 */
export function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}
