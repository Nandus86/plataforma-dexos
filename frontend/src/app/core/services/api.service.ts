import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private baseUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    private getHeaders(): HttpHeaders {
        const token = localStorage.getItem('access_token');
        return new HttpHeaders({
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        });
    }

    get<T>(path: string, params?: any): Observable<T> {
        return this.http.get<T>(`${this.baseUrl}${path}`, {
            headers: this.getHeaders(),
            params,
        });
    }

    post<T>(path: string, body: any): Observable<T> {
        return this.http.post<T>(`${this.baseUrl}${path}`, body, {
            headers: this.getHeaders(),
        });
    }

    put<T>(path: string, body: any): Observable<T> {
        return this.http.put<T>(`${this.baseUrl}${path}`, body, {
            headers: this.getHeaders(),
        });
    }

    delete<T>(path: string): Observable<T> {
        return this.http.delete<T>(`${this.baseUrl}${path}`, {
            headers: this.getHeaders(),
        });
    }
}
