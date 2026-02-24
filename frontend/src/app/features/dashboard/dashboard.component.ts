import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService, UserInfo } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';

interface StatCard {
    label: string;
    value: string | number;
    icon: string;
    color: string;
    route: string;
}

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, RouterModule, MatCardModule, MatIconModule, MatButtonModule, MatChipsModule, MatProgressSpinnerModule],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
    user: UserInfo | null = null;
    greeting = '';
    stats: StatCard[] = [];
    loadingStats = true;

    constructor(private auth: AuthService, private api: ApiService) { }

    ngOnInit(): void {
        this.user = this.auth.currentUser;
        this.setGreeting();
        this.loadStats();
    }

    private setGreeting(): void {
        const hour = new Date().getHours();
        if (hour < 12) this.greeting = 'Bom dia';
        else if (hour < 18) this.greeting = 'Boa tarde';
        else this.greeting = 'Boa noite';
    }

    private loadStats(): void {
        this.loadingStats = true;
        this.api.get<any>('/dashboard/stats').subscribe({
            next: (data) => {
                this.setStats(data);
                this.loadingStats = false;
            },
            error: () => {
                this.setStats({});
                this.loadingStats = false;
            },
        });
    }

    private setStats(data: any): void {
        const role = this.user?.role || '';

        if (role === 'superadmin' || role === 'admin') {
            this.stats = [
                { label: 'Estudantes', value: data.total_students ?? '—', icon: 'people', color: '#D4AF37', route: '/students' },
                { label: 'Professores', value: data.total_professors ?? '—', icon: 'school', color: '#F0D97A', route: '/staff' },
                { label: 'Cursos', value: data.total_courses ?? '—', icon: 'menu_book', color: '#997500', route: '/courses' },
                { label: 'Matrículas Ativas', value: data.total_enrollments ?? '—', icon: 'how_to_reg', color: '#E5C54F', route: '/enrollments' },
            ];
        } else if (role === 'coordenacao') {
            this.stats = [
                { label: 'Estudantes', value: data.total_students ?? '—', icon: 'people', color: '#D4AF37', route: '/coordination' },
                { label: 'Professores', value: data.total_professors ?? '—', icon: 'school', color: '#F0D97A', route: '/coordination' },
                { label: 'Cursos', value: data.total_courses ?? '—', icon: 'menu_book', color: '#997500', route: '/courses' },
                { label: 'Matrículas Ativas', value: data.total_enrollments ?? '—', icon: 'how_to_reg', color: '#E5C54F', route: '/enrollments' },
                { label: 'Planos de Aula', value: data.total_lesson_plans ?? '—', icon: 'description', color: '#BF9200', route: '/lesson-plans' },
                { label: 'Materiais', value: data.total_materials ?? '—', icon: 'folder_open', color: '#D4AF37', route: '/materials' },
            ];
        } else if (role === 'professor') {
            this.stats = [
                { label: 'Minhas Disciplinas', value: data.total_subjects ?? '—', icon: 'class', color: '#D4AF37', route: '/subjects' },
                { label: 'Meus Estudantes', value: data.total_students ?? '—', icon: 'people', color: '#F0D97A', route: '/grades' },
                { label: 'Planos de Aula', value: data.total_lesson_plans ?? '—', icon: 'description', color: '#997500', route: '/lesson-plans' },
                { label: 'Materiais', value: data.total_materials ?? '—', icon: 'folder_open', color: '#E5C54F', route: '/materials' },
            ];
        } else {
            // Estudante
            this.stats = [
                { label: 'Matrículas Ativas', value: data.total_enrollments ?? '—', icon: 'how_to_reg', color: '#D4AF37', route: '/grades' },
                { label: 'Avaliações', value: data.total_grades ?? '—', icon: 'grade', color: '#F0D97A', route: '/grades' },
                { label: 'Média Geral', value: data.average_grade ?? '—', icon: 'trending_up', color: '#997500', route: '/grades' },
                { label: 'Frequência', value: data.attendance_percentage ? data.attendance_percentage + '%' : '—', icon: 'event_available', color: '#E5C54F', route: '/attendance' },
            ];
        }
    }

    get firstName(): string {
        return this.user?.name?.split(' ')[0] || '';
    }

    get roleLabel(): string {
        const labels: Record<string, string> = {
            superadmin: 'Super Administrador',
            admin: 'Gestor',
            coordenacao: 'Coordenação Pedagógica',
            professor: 'Professor',
            estudante: 'Estudante',
        };
        return labels[this.user?.role || ''] || '';
    }
}
