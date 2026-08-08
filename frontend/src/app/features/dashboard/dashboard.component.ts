import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
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
    imports: [CommonModule, RouterModule, FormsModule, MatCardModule, MatIconModule, MatButtonModule, MatChipsModule, MatProgressSpinnerModule, MatFormFieldModule, MatSelectModule, MatTooltipModule],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
    user: UserInfo | null = null;
    greeting = '';
    stats: StatCard[] = [];
    loadingStats = true;

    // Student specific
    isStudent = false;
    enrollments: any[] = [];
    selectedEnrollmentId: string = '';
    boletim: any = null;
    loadingBoletim = false;
    assignments: any[] = [];
    loadingAssignments = false;

    constructor(private auth: AuthService, private api: ApiService) { }

    ngOnInit(): void {
        this.user = this.auth.currentUser;
        this.isStudent = this.user?.role === 'estudante';
        this.setGreeting();
        this.loadStats();
        
        if (this.isStudent && this.user) {
            this.loadStudentEnrollments(this.user.id);
        }
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

    // --- Student Real Data Flow ---

    private loadStudentEnrollments(studentId: string): void {
        this.api.get<any>(`/academic/enrollments/?student_id=${studentId}`).subscribe({
            next: data => {
                this.enrollments = data.items || [];
                if (this.enrollments.length > 0) {
                    const active = this.enrollments.find(e => e.status === 'active') || this.enrollments[0];
                    this.selectedEnrollmentId = active.id;
                    this.loadBoletim();
                    this.loadStudentAssignments(active.matrix_id);
                }
            }
        });
    }

    onEnrollmentChange(): void {
        if (this.selectedEnrollmentId) {
            this.loadBoletim();
            const enrollment = this.enrollments.find(e => e.id === this.selectedEnrollmentId);
            if (enrollment) {
                this.loadStudentAssignments(enrollment.matrix_id);
            }
        }
    }

    private loadStudentAssignments(matrixId: string): void {
        if (!matrixId) return;
        this.loadingAssignments = true;
        this.api.get<any>(`/academic/assignments/`, { matrix_id: matrixId, limit: 5 }).subscribe({
            next: (res) => {
                // Filter to get only the nearest pending/upcoming assignments
                const now = new Date();
                this.assignments = (res.items || res || [])
                    .filter((a: any) => new Date(a.due_date) >= now)
                    .sort((a: any, b: any) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())
                    .slice(0, 5);
                this.loadingAssignments = false;
            },
            error: () => {
                this.assignments = [];
                this.loadingAssignments = false;
            }
        });
    }

    private loadBoletim(): void {
        if (!this.selectedEnrollmentId) return;
        this.loadingBoletim = true;
        this.api.get<any>(`/academic/boletim/${this.selectedEnrollmentId}`).subscribe({
            next: d => {
                this.boletim = d;
                this.loadingBoletim = false;
            },
            error: () => {
                this.boletim = null;
                this.loadingBoletim = false;
            }
        });
    }
}

