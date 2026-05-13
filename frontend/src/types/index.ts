export interface Orcamento {
  id: string;
  numero: string;
  titulo: string;
  descricao: string;
  tenant_id: string;
  custo_fixo_total: string;
  created_at: string;
  updated_at: string;
}

export interface Ficha {
  id: string;
  orcamento_id: string;
  descricao: string;
  unidade: string;
  quantidade: number;
  custo_unitario: string;
  tipo_precificacao: string;
  preco_unitario_calculado: string | null;
  ordem: number;
}

export interface LoginRequest {
  email: string;
  senha: string;
  tenant_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string | null;
  mfa_required: boolean;
  token_type: string;
}

export interface MfaLoginRequest {
  partial_token: string;
  totp_code: string;
}
