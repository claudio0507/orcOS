export enum TipoPrecificacao {
  MARKUP = 'markup',
  BDI_MANUAL = 'bdi_manual',
  BDI_CLASSICO = 'bdi_classico',
}

export interface Orcamento {
  id: string;
  titulo: string;
  descricao: string | null;
  tenant_id: string;
  status: string;
  custo_fixo_total: string;
  created_at: string;
  updated_at: string;
}

export interface Ficha {
  id: string;
  orcamento_id: string;
  tenant_id: string;
  descricao: string;
  unidade: string;
  quantidade: string;
  custo_unitario: string;
  tipo_precificacao: TipoPrecificacao | string;
  preco_unitario_calculado: string | null;
  ordem: number;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  tenant_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string | null;
  mfa_required: boolean;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  nome: string;
  tenant_id: string;
}

export interface MfaLoginRequest {
  partial_token: string;
  totp_code: string;
}
