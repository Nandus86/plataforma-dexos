import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';

export interface UserInfo {
    id: string;
    name: string;
    email: string;
    role: string;
    tenant_id: string | null;
    avatar_url: string | null;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: UserInfo;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private currentUserSubject = new BehaviorSubject<UserInfo | null>(null);
    public currentUser$ = this.currentUserSubject.asObservable();

    constructor(
        private api: ApiService,
        private router: Router,
    ) {
        this.loadStoredUser();
    }

    private loadStoredUser(): void {
        const stored = localStorage.getItem('current_user');
        if (stored) {
            try {
                this.currentUserSubject.next(JSON.parse(stored));
            } catch {
                this.logout();
            }
        }
    }

    get currentUser(): UserInfo | null {
        return this.currentUserSubject.value;
    }

    get isLoggedIn(): boolean {
        return !!localStorage.getItem('access_token');
    }

    get userRole(): string {
        return this.currentUser?.role || '';
    }

    login(email: string, password: string): Observable<LoginResponse> {
        return this.api.post<LoginResponse>('/auth/login', { email, password }).pipe(
            tap((response) => {
                localStorage.setItem('access_token', response.access_token);
                localStorage.setItem('current_user', JSON.stringify(response.user));
                this.currentUserSubject.next(response.user);
            })
        );
    }

    logout(): void {
        localStorage.removeItem('access_token');
        localStorage.removeItem('current_user');
        this.currentUserSubject.next(null);
        this.router.navigate(['/login']);
    }

    refreshUser(): Observable<UserInfo> {
        return this.api.get<UserInfo>('/auth/me').pipe(
            tap((user) => {
                localStorage.setItem('current_user', JSON.stringify(user));
                this.currentUserSubject.next(user);
            })
        );
    }

    hasRole(...roles: string[]): boolean {
        return roles.includes(this.userRole);
    }
}
