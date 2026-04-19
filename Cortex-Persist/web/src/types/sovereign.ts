export interface GovernorMetrics {
  vsa_dimension: number;
  semantic_pressure: number;
  thermodynamic_pressure: number;
  governor_error: number;
  kp: number;
  ki: number;
  kd: number;
  pid_output: number;
  status: string;
}

export type Protocol911State = 'NORMAL' | 'PREVENCION' | 'STRIKE' | 'EMERGENCIA' | 'ENFRIAMIENTO';

export interface ArchiProduct {
  id: string;
  directive: string;
  timestamp: string;
  status?: string;
}

export type PersistMode = 'CONSOLIDADO' | 'RESPALDO' | 'DESCONECTADO';

export type Zone = 'CONSOLIDACIÓN' | 'EQUILIBRIO' | 'DIVERGENCIA';
