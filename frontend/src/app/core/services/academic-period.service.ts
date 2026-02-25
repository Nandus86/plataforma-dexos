import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
    AcademicPeriod,
    AcademicPeriodCreate,
    PeriodBreak,
    NonSchoolDay,
    ExtraSchoolDay,
    PeriodStatistics
} from '../models/academic-period.model';

@Injectable({
    providedIn: 'root'
})
export class AcademicPeriodService {
    private apiUrl = `${environment.apiUrl}/academic-periods`;

    constructor(private http: HttpClient) { }

    // ========== Academic Periods ==========

    getAcademicPeriods(activeOnly: boolean = false): Observable<AcademicPeriod[]> {
        let params = new HttpParams();
        if (activeOnly) {
            params = params.set('active_only', 'true');
        }
        return this.http.get<AcademicPeriod[]>(this.apiUrl, { params });
    }

    getAcademicPeriod(id: string): Observable<AcademicPeriod> {
        return this.http.get<AcademicPeriod>(`${this.apiUrl}/${id}`);
    }

    createAcademicPeriod(data: AcademicPeriodCreate): Observable<AcademicPeriod> {
        return this.http.post<AcademicPeriod>(this.apiUrl, data);
    }

    updateAcademicPeriod(id: string, data: Partial<AcademicPeriodCreate>): Observable<AcademicPeriod> {
        return this.http.put<AcademicPeriod>(`${this.apiUrl}/${id}`, data);
    }

    deleteAcademicPeriod(id: string): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/${id}`);
    }

    getPeriodStatistics(id: string): Observable<PeriodStatistics> {
        return this.http.get<PeriodStatistics>(`${this.apiUrl}/${id}/statistics`);
    }

    // ========== Period Breaks ==========

    addPeriodBreak(periodId: string, data: Omit<PeriodBreak, 'id' | 'academic_period_id'>): Observable<PeriodBreak> {
        return this.http.post<PeriodBreak>(`${this.apiUrl}/${periodId}/breaks`, data);
    }

    deletePeriodBreak(breakId: string): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/breaks/${breakId}`);
    }

    // ========== Non-School Days ==========

    addNonSchoolDay(periodId: string, data: Omit<NonSchoolDay, 'id' | 'academic_period_id'>): Observable<NonSchoolDay> {
        return this.http.post<NonSchoolDay>(`${this.apiUrl}/${periodId}/non-school-days`, data);
    }

    deleteNonSchoolDay(dayId: string): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/non-school-days/${dayId}`);
    }

    importHolidays(periodId: string, countryCode: string = 'BR', subdiv?: string): Observable<any> {
        let params = new HttpParams().set('country_code', countryCode);
        if (subdiv) {
            params = params.set('subdiv', subdiv);
        }
        return this.http.post(`${this.apiUrl}/${periodId}/import-holidays`, {}, { params });
    }

    // ========== Extra School Days ==========

    addExtraSchoolDay(periodId: string, data: Omit<ExtraSchoolDay, 'id' | 'academic_period_id'>): Observable<ExtraSchoolDay> {
        return this.http.post<ExtraSchoolDay>(`${this.apiUrl}/${periodId}/extra-school-days`, data);
    }

    deleteExtraSchoolDay(dayId: string): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/extra-school-days/${dayId}`);
    }

    // ========== Helper Methods ==========

    getBreakTypeLabel(type: string): string {
        const labels: { [key: string]: string } = {
            'mensal': 'Mensal',
            'bimestral': 'Bimestral',
            'trimestral': 'Trimestral',
            'quadrimestral': 'Quadrimestral',
            'semestral': 'Semestral',
            'anual': 'Anual'
        };
        return labels[type] || type;
    }

    getNonSchoolDayReasonLabel(reason: string): string {
        const labels: { [key: string]: string } = {
            'sabado': 'Sábado',
            'domingo': 'Domingo',
            'feriado': 'Feriado',
            'evento': 'Evento',
            'recesso': 'Recesso',
            'outro': 'Outro'
        };
        return labels[reason] || reason;
    }
}
