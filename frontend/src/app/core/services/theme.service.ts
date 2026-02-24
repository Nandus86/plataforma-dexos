import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type ThemeMode = 'dark' | 'light';

@Injectable({
    providedIn: 'root'
})
export class ThemeService {
    private readonly STORAGE_KEY = 'exousia_theme';
    private themeSubject: BehaviorSubject<ThemeMode>;
    public theme$;

    constructor() {
        const stored = localStorage.getItem(this.STORAGE_KEY) as ThemeMode;
        const initial: ThemeMode = stored === 'light' ? 'light' : 'dark';
        this.themeSubject = new BehaviorSubject<ThemeMode>(initial);
        this.theme$ = this.themeSubject.asObservable();
        this.applyTheme(initial);
    }

    get currentTheme(): ThemeMode {
        return this.themeSubject.value;
    }

    get isDark(): boolean {
        return this.currentTheme === 'dark';
    }

    toggleTheme(): void {
        const next: ThemeMode = this.isDark ? 'light' : 'dark';
        this.setTheme(next);
    }

    setTheme(theme: ThemeMode): void {
        localStorage.setItem(this.STORAGE_KEY, theme);
        this.themeSubject.next(theme);
        this.applyTheme(theme);
    }

    private applyTheme(theme: ThemeMode): void {
        const html = document.documentElement;
        html.classList.remove('theme-dark', 'theme-light');
        html.classList.add(`theme-${theme}`);
    }
}
