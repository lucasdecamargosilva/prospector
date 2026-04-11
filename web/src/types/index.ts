export interface Lead {
  id: string;
  instagram: string;
  nome_loja: string | null;
  site: string | null;
  seguidores: number;
  tem_provador: boolean;
  status: LeadStatus;
  notas: string;
  created_at: string;
  updated_at: string;
}

export type LeadStatus =
  | "novo"
  | "dm_enviada"
  | "respondeu"
  | "interessado"
  | "fechou"
  | "descartado";

export const LEAD_STATUSES: LeadStatus[] = [
  "novo",
  "dm_enviada",
  "respondeu",
  "interessado",
  "fechou",
  "descartado",
];

export interface Interacao {
  id: string;
  lead_id: string;
  tipo: InteracaoTipo;
  conteudo: string;
  created_at: string;
}

export type InteracaoTipo = "dm_enviada" | "resposta" | "follow_up" | "nota";

export const INTERACAO_TIPOS: InteracaoTipo[] = [
  "dm_enviada",
  "resposta",
  "follow_up",
  "nota",
];

export const STATUS_LABELS: Record<LeadStatus, string> = {
  novo: "Novo",
  dm_enviada: "DM Enviada",
  respondeu: "Respondeu",
  interessado: "Interessado",
  fechou: "Fechou",
  descartado: "Descartado",
};

export const STATUS_COLORS: Record<LeadStatus, string> = {
  novo: "bg-blue-500",
  dm_enviada: "bg-yellow-500",
  respondeu: "bg-purple-500",
  interessado: "bg-orange-500",
  fechou: "bg-green-500",
  descartado: "bg-gray-500",
};
