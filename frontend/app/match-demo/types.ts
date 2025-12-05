// Types matching backend/app/models/matching.py

export interface ScoreBreakdown {
  industry: number;
  region: number;
  certifications: number;
  total: number;
}

export interface MatchVendor {
  vendor_id: string;
  name: string;
  score: number;
  score_breakdown: ScoreBreakdown | null;
  matched_reasons: string[];
}

export interface MatchResponse {
  vendors: MatchVendor[];
}

export interface NLMatchRequest {
  query: string;
}
