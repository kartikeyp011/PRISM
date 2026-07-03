/** Risk colors aligned with backend/api_contract.yaml */
export const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export const SENSOR_COLORS: Record<string, string> = {
  normal: "#3b82f6",
  critical: "#ef4444",
  unknown: "#64748b",
};

export type PageId = "dashboard" | "map" | "incidents";
