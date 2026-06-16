import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import type {
  AugmentResponse,
  ExplanationFeedback,
  ExplanationListResponse,
  ExplanationRecord,
} from '../../core/contracts';

const API = '/api/explanations';

@Injectable({ providedIn: 'root' })
export class ExplanationsApiService {
  private readonly http = inject(HttpClient);

  list(
    params: {
      limit?: number;
      offset?: number;
      severity?: string;
      source_key?: string;
    } = {},
  ): Observable<ExplanationListResponse> {
    const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v != null)) as Record<
      string,
      string | number
    >;
    return this.http.get<ExplanationListResponse>(API, { params: clean });
  }

  listSourceKeys(): Observable<string[]> {
    return this.http.get<string[]>(`${API}/source-keys`);
  }

  get(id: string): Observable<ExplanationRecord> {
    return this.http.get<ExplanationRecord>(`${API}/${id}`);
  }

  setFeedback(id: string, feedback: ExplanationFeedback): Observable<ExplanationRecord> {
    return this.http.patch<ExplanationRecord>(`${API}/${id}/feedback`, { feedback });
  }

  augment(id: string): Observable<AugmentResponse> {
    return this.http.post<AugmentResponse>(`${API}/${id}/augment`, {});
  }
}
