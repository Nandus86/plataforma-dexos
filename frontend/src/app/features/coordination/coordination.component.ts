import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '../../core/services/api.service';

interface StatCard {
  label: string;
  value: string | number;
  icon: string;
  color: string;
}

@Component({
  selector: 'app-coordination',
  standalone: true,
  imports: [
    CommonModule, RouterModule,
    MatCardModule, MatIconModule, MatButtonModule,
    MatTabsModule, MatTableModule, MatProgressSpinnerModule,
    MatChipsModule, MatExpansionModule, MatTooltipModule,
  ],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><mat-icon>supervisor_account</mat-icon> Coordenação Pedagógica</h1>
          <p class="page-subtitle">Painel de acompanhamento acadêmico e pedagógico</p>
        </div>
      </div>

      <!-- Overview Cards -->
      @if (loadingStats) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <div class="stats-grid animate-fade-in">
          @for (stat of overviewStats; track stat.label; let i = $index) {
            <div class="stat-card glass-card" [style.animation-delay]="(i * 0.08) + 's'">
              <div class="stat-icon" [style.background]="stat.color + '18'" [style.color]="stat.color">
                <mat-icon>{{ stat.icon }}</mat-icon>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stat.value }}</span>
                <span class="stat-label">{{ stat.label }}</span>
              </div>
            </div>
          }
        </div>
      }

      <!-- Tabbed Reports -->
      <mat-tab-group class="reports-tabs animate-fade-in-delay" animationDuration="300ms">
        <!-- Low Performance -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon class="tab-icon">trending_down</mat-icon>
            Baixo Desempenho
          </ng-template>
          <div class="tab-content">
            @if (loadingReports) { <div class="loading-center"><mat-spinner diameter="36"></mat-spinner></div> }
            @else {
              <div class="table-card glass-card">
                <table mat-table [dataSource]="lowPerformance" class="dark-table">
                  <ng-container matColumnDef="student_name"><th mat-header-cell *matHeaderCellDef>Estudante</th><td mat-cell *matCellDef="let r">{{ r.student_name }}</td></ng-container>
                  <ng-container matColumnDef="registration_number"><th mat-header-cell *matHeaderCellDef>Matrícula</th><td mat-cell *matCellDef="let r">{{ r.registration_number || '—' }}</td></ng-container>
                  <ng-container matColumnDef="average_grade"><th mat-header-cell *matHeaderCellDef>Média</th><td mat-cell *matCellDef="let r"><span class="text-danger">{{ r.average_grade }}</span></td></ng-container>
                  <ng-container matColumnDef="total_evaluations"><th mat-header-cell *matHeaderCellDef>Avaliações</th><td mat-cell *matCellDef="let r">{{ r.total_evaluations }}</td></ng-container>
                  <tr mat-header-row *matHeaderRowDef="lpCols"></tr><tr mat-row *matRowDef="let row; columns: lpCols;"></tr>
                </table>
                @if (lowPerformance.length === 0) { <div class="empty-state"><mat-icon>check_circle</mat-icon><p>Nenhum estudante com baixo desempenho</p></div> }
              </div>
            }
          </div>
        </mat-tab>

        <!-- Low Attendance -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon class="tab-icon">event_busy</mat-icon>
            Baixa Frequência
          </ng-template>
          <div class="tab-content">
            @if (loadingReports) { <div class="loading-center"><mat-spinner diameter="36"></mat-spinner></div> }
            @else {
              <div class="table-card glass-card">
                <table mat-table [dataSource]="lowAttendance" class="dark-table">
                  <ng-container matColumnDef="student_name"><th mat-header-cell *matHeaderCellDef>Estudante</th><td mat-cell *matCellDef="let r">{{ r.student_name }}</td></ng-container>
                  <ng-container matColumnDef="registration_number"><th mat-header-cell *matHeaderCellDef>Matrícula</th><td mat-cell *matCellDef="let r">{{ r.registration_number || '—' }}</td></ng-container>
                  <ng-container matColumnDef="attendance_percentage"><th mat-header-cell *matHeaderCellDef>Frequência</th><td mat-cell *matCellDef="let r"><span class="text-warning">{{ r.attendance_percentage }}%</span></td></ng-container>
                  <ng-container matColumnDef="total_classes"><th mat-header-cell *matHeaderCellDef>Aulas</th><td mat-cell *matCellDef="let r">{{ r.present_classes }}/{{ r.total_classes }}</td></ng-container>
                  <tr mat-header-row *matHeaderRowDef="laCols"></tr><tr mat-row *matRowDef="let row; columns: laCols;"></tr>
                </table>
                @if (lowAttendance.length === 0) { <div class="empty-state"><mat-icon>check_circle</mat-icon><p>Todos os estudantes com frequência adequada</p></div> }
              </div>
            }
          </div>
        </mat-tab>

        <!-- Critical Subjects -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon class="tab-icon">warning</mat-icon>
            Disciplinas Críticas
          </ng-template>
          <div class="tab-content">
            @if (loadingReports) { <div class="loading-center"><mat-spinner diameter="36"></mat-spinner></div> }
            @else {
              <div class="table-card glass-card">
                <table mat-table [dataSource]="criticalSubjects" class="dark-table">
                  <ng-container matColumnDef="subject_name"><th mat-header-cell *matHeaderCellDef>Disciplina</th><td mat-cell *matCellDef="let r">{{ r.subject_name }}</td></ng-container>
                  <ng-container matColumnDef="subject_code"><th mat-header-cell *matHeaderCellDef>Código</th><td mat-cell *matCellDef="let r">{{ r.subject_code }}</td></ng-container>
                  <ng-container matColumnDef="total_enrollments"><th mat-header-cell *matHeaderCellDef>Matrículas</th><td mat-cell *matCellDef="let r">{{ r.total_enrollments }}</td></ng-container>
                  <ng-container matColumnDef="failure_rate"><th mat-header-cell *matHeaderCellDef>% Reprovação</th><td mat-cell *matCellDef="let r"><span [class]="r.failure_rate > 30 ? 'text-danger' : ''">{{ r.failure_rate }}%</span></td></ng-container>
                  <ng-container matColumnDef="average_grade"><th mat-header-cell *matHeaderCellDef>Média Geral</th><td mat-cell *matCellDef="let r">{{ r.average_grade ?? '—' }}</td></ng-container>
                  <tr mat-header-row *matHeaderRowDef="csCols"></tr><tr mat-row *matRowDef="let row; columns: csCols;"></tr>
                </table>
                @if (criticalSubjects.length === 0) { <div class="empty-state"><mat-icon>check_circle</mat-icon><p>Nenhuma disciplina crítica identificada</p></div> }
              </div>
            }
          </div>
        </mat-tab>

        <!-- Professor Activity -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon class="tab-icon">person_search</mat-icon>
            Atividade dos Professores
          </ng-template>
          <div class="tab-content">
            @if (loadingReports) { <div class="loading-center"><mat-spinner diameter="36"></mat-spinner></div> }
            @else {
              <div class="table-card glass-card">
                <table mat-table [dataSource]="professorActivity" class="dark-table">
                  <ng-container matColumnDef="professor_name"><th mat-header-cell *matHeaderCellDef>Professor</th><td mat-cell *matCellDef="let r">{{ r.professor_name }}</td></ng-container>
                  <ng-container matColumnDef="subjects_count"><th mat-header-cell *matHeaderCellDef>Disciplinas</th><td mat-cell *matCellDef="let r">{{ r.subjects_count }}</td></ng-container>
                  <ng-container matColumnDef="lesson_plans_count"><th mat-header-cell *matHeaderCellDef>Planos de Aula</th><td mat-cell *matCellDef="let r">
                    <span [class]="r.lesson_plans_count === 0 ? 'text-warning' : 'text-gold'">{{ r.lesson_plans_count }}</span>
                  </td></ng-container>
                  <ng-container matColumnDef="materials_count"><th mat-header-cell *matHeaderCellDef>Materiais</th><td mat-cell *matCellDef="let r">
                    <span [class]="r.materials_count === 0 ? 'text-warning' : 'text-gold'">{{ r.materials_count }}</span>
                  </td></ng-container>
                  <tr mat-header-row *matHeaderRowDef="paCols"></tr><tr mat-row *matRowDef="let row; columns: paCols;"></tr>
                </table>
                @if (professorActivity.length === 0) { <div class="empty-state"><mat-icon>school</mat-icon><p>Nenhum professor registrado</p></div> }
              </div>
            }
          </div>
        </mat-tab>

        <!-- Recent Occurrences -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon class="tab-icon">report</mat-icon>
            Ocorrências Recentes
          </ng-template>
          <div class="tab-content">
            @if (loadingReports) { <div class="loading-center"><mat-spinner diameter="36"></mat-spinner></div> }
            @else {
              <div class="table-card glass-card">
                <table mat-table [dataSource]="recentOccurrences" class="dark-table">
                  <ng-container matColumnDef="date"><th mat-header-cell *matHeaderCellDef>Data</th><td mat-cell *matCellDef="let r">{{ r.date }}</td></ng-container>
                  <ng-container matColumnDef="type_label"><th mat-header-cell *matHeaderCellDef>Tipo</th><td mat-cell *matCellDef="let r">
                    <span [class]="getOccurrenceClass(r.type)">{{ r.type_label }}</span>
                  </td></ng-container>
                  <ng-container matColumnDef="title"><th mat-header-cell *matHeaderCellDef>Título</th><td mat-cell *matCellDef="let r">{{ r.title }}</td></ng-container>
                  <ng-container matColumnDef="student_name"><th mat-header-cell *matHeaderCellDef>Estudante</th><td mat-cell *matCellDef="let r">{{ r.student_name }}</td></ng-container>
                  <ng-container matColumnDef="author_name"><th mat-header-cell *matHeaderCellDef>Autor</th><td mat-cell *matCellDef="let r">{{ r.author_name }}</td></ng-container>
                  <tr mat-header-row *matHeaderRowDef="ocCols"></tr><tr mat-row *matRowDef="let row; columns: ocCols;"></tr>
                </table>
                @if (recentOccurrences.length === 0) { <div class="empty-state"><mat-icon>check_circle</mat-icon><p>Nenhuma ocorrência recente registrada</p></div> }
              </div>
            }
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 32px;

        .stat-card {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          animation: fadeInUp 0.5s ease-out both;

          .stat-icon {
            width: 48px; height: 48px;
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            mat-icon { font-size: 24px; }
          }
          .stat-info {
            display: flex; flex-direction: column;
            .stat-value { font-size: 24px; font-weight: 800; color: #F5F5F5; }
            .stat-label { font-size: 13px; color: #999; font-weight: 500; }
          }
        }
      }

      .reports-tabs {
        ::ng-deep .mdc-tab { color: #B3B3B3 !important; }
        ::ng-deep .mdc-tab--active { color: #D4AF37 !important; }
        ::ng-deep .mdc-tab-indicator__content--underline { border-color: #D4AF37 !important; }
      }

      .tab-icon { margin-right: 8px; font-size: 20px; }

      .tab-content { padding-top: 16px; }

      .text-danger { color: #F44336; font-weight: 700; }
      .text-warning { color: #FF9800; font-weight: 700; }
      .text-praise { color: #4CAF50; font-weight: 600; }

      @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to { opacity: 1; transform: translateY(0); }
      }
    `],
})
export class CoordinationComponent implements OnInit {
  loadingStats = false;
  loadingReports = false;
  overviewStats: StatCard[] = [];

  lowPerformance: any[] = [];
  lowAttendance: any[] = [];
  criticalSubjects: any[] = [];
  professorActivity: any[] = [];
  recentOccurrences: any[] = [];

  lpCols = ['student_name', 'registration_number', 'average_grade', 'total_evaluations'];
  laCols = ['student_name', 'registration_number', 'attendance_percentage', 'total_classes'];
  csCols = ['subject_name', 'subject_code', 'total_enrollments', 'failure_rate', 'average_grade'];
  paCols = ['professor_name', 'subjects_count', 'lesson_plans_count', 'materials_count'];
  ocCols = ['date', 'type_label', 'title', 'student_name', 'author_name'];

  constructor(private api: ApiService) { }

  ngOnInit() {
    this.loadStats();
    this.loadReports();
  }

  loadStats() {
    this.loadingStats = true;
    this.api.get<any>('/dashboard/stats').subscribe({
      next: (data) => {
        this.overviewStats = [
          { label: 'Estudantes', value: data.total_students ?? 0, icon: 'people', color: '#D4AF37' },
          { label: 'Professores', value: data.total_professors ?? 0, icon: 'school', color: '#F0D97A' },
          { label: 'Cursos', value: data.total_courses ?? 0, icon: 'menu_book', color: '#997500' },
          { label: 'Matrículas Ativas', value: data.total_enrollments ?? 0, icon: 'how_to_reg', color: '#E5C54F' },
          { label: 'Disciplinas', value: data.total_subjects ?? 0, icon: 'class', color: '#BF9200' },
          { label: 'Planos de Aula', value: data.total_lesson_plans ?? 0, icon: 'description', color: '#D4AF37' },
          { label: 'Materiais', value: data.total_materials ?? 0, icon: 'folder_open', color: '#F0D97A' },
        ];
        this.loadingStats = false;
      },
      error: () => this.loadingStats = false,
    });
  }

  loadReports() {
    this.loadingReports = true;
    let loaded = 0;
    const checkDone = () => { loaded++; if (loaded >= 5) this.loadingReports = false; };

    this.api.get<any[]>('/dashboard/reports/low-performance').subscribe({
      next: (d) => { this.lowPerformance = d; checkDone(); },
      error: () => checkDone(),
    });
    this.api.get<any[]>('/dashboard/reports/low-attendance').subscribe({
      next: (d) => { this.lowAttendance = d; checkDone(); },
      error: () => checkDone(),
    });
    this.api.get<any[]>('/dashboard/reports/critical-subjects').subscribe({
      next: (d) => { this.criticalSubjects = d; checkDone(); },
      error: () => checkDone(),
    });
    this.api.get<any[]>('/dashboard/reports/professor-activity').subscribe({
      next: (d) => { this.professorActivity = d; checkDone(); },
      error: () => checkDone(),
    });
    this.api.get<any[]>('/dashboard/reports/recent-occurrences').subscribe({
      next: (d) => { this.recentOccurrences = d; checkDone(); },
      error: () => checkDone(),
    });
  }

  getOccurrenceClass(type: string): string {
    switch (type) {
      case 'warning': return 'text-warning';
      case 'complaint': return 'text-danger';
      case 'praise': return 'text-praise';
      default: return '';
    }
  }
}
