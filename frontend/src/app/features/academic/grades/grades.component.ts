import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-grades',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatCardModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatSelectModule,
    MatProgressBarModule
  ],
  template: `
    <div class="page animate-fade-in">
      <div class="page-header" style="margin-bottom: 1rem;">
        <div>
          <h1 class="page-title"><mat-icon>school</mat-icon> Boletim e Notas</h1>
          <p class="page-subtitle">Acompanhe o rendimento acadêmico detalhado</p>
        </div>
        <button *ngIf="boletim && auth.userRole !== 'estudante'" mat-stroked-button color="primary" (click)="closeBoletim()">
            <mat-icon>arrow_back</mat-icon> Voltar
        </button>
      </div>

      <!-- VISÃO: PROFESSOR / ADMIN / COORDENAÇÃO -->
      <ng-container *ngIf="auth.userRole !== 'estudante'">
        
        <!-- Filtros (Turma ou Estudante Direto) -->
        <div class="filter-card glass-card" *ngIf="!boletim">
          <div class="filter-row" style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem; flex-wrap: wrap;">
            
            <mat-form-field appearance="outline" class="filter-field" style="flex: 1; min-width: 200px; margin: 0;">
              <mat-label>Filtrar por Turma</mat-label>
              <mat-select [(ngModel)]="selectedGroupId" (selectionChange)="onGroupChange()">
                <mat-option [value]="''">-- Selecionar Turma --</mat-option>
                @for (g of classGroups; track g.id) {
                  <mat-option [value]="g.id">{{ g.name }} ({{ g.course_name }} - {{ g.shift | titlecase }})</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <span style="color: gray; font-size: 0.9em; font-weight: 500;">OU</span>

            <mat-form-field appearance="outline" class="filter-field" style="flex: 1; min-width: 200px; margin: 0;">
              <mat-label>Pesquisar Estudante</mat-label>
              <mat-select [(ngModel)]="selectedDirectStudentId" (selectionChange)="onDirectStudentChange()">
                <mat-option [value]="''">-- Selecionar Estudante --</mat-option>
                @for (s of allStudents; track s.id) {
                  <mat-option [value]="s.id">{{ s.name }} - RA: {{ s.registration_number || 'Sem RA' }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-spinner diameter="30" *ngIf="loadingFilter"></mat-spinner>
          </div>
        </div>

        <!-- Opções de Matrícula (quando pesquisa direto o estudante) -->
        <div class="filter-card glass-card" *ngIf="selectedDirectStudentId && enrollments.length > 0 && !boletim && !loadingFilter" style="margin-top: 1rem;">
          <div class="filter-row" style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
            <mat-form-field appearance="outline" class="filter-field" style="flex: 1; margin: 0;">
              <mat-label>Selecione a Matrícula do Aluno</mat-label>
              <mat-select [(ngModel)]="selectedEnrollmentId" (selectionChange)="onEnrollmentChange()">
                @for (e of enrollments; track e.id) {
                  <mat-option [value]="e.id">{{ e.course_name }} ({{ e.academic_period_name }}) - {{ e.enrollment_code || 'S/ Código' }} - {{ e.status }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
          </div>
        </div>

        <!-- Lista de Alunos da Turma Selecionada (Grid) -->
        <div class="table-card glass-card" *ngIf="selectedGroupId && !boletim && !loadingFilter" style="margin-top: 1rem;">
          <table mat-table [dataSource]="groupStudents" class="dark-table clickable-rows">
            <ng-container matColumnDef="student_name">
              <th mat-header-cell *matHeaderCellDef> Estudante </th>
              <td mat-cell *matCellDef="let s">
                  <div><strong>{{ s.student_name }}</strong></div>
                  <div style="font-size: 0.8em; color: gray;">{{ s.student_email }}</div>
              </td>
            </ng-container>

            <ng-container matColumnDef="registration_number">
              <th mat-header-cell *matHeaderCellDef> Matrícula </th>
              <td mat-cell *matCellDef="let s"> {{ s.registration_number || '-' }} </td>
            </ng-container>
            
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef style="text-align: right;">Ações</th>
              <td mat-cell *matCellDef="let s" style="text-align: right;">
                 <button mat-icon-button color="primary" matTooltip="Ver Boletim do Aluno">
                    <mat-icon>visibility</mat-icon>
                 </button>
              </td>
            </ng-container>

            <tr mat-header-row *matHeaderRowDef="studentCols"></tr>
            <tr mat-row *matRowDef="let row; columns: studentCols;" (click)="openBoletimFromGrid(row)" class="clickable-row"></tr>
          </table>
          <div *ngIf="groupStudents.length === 0" class="empty-state">
              <mat-icon>info</mat-icon>
              <p>Nenhum aluno matriculado nesta turma.</p>
          </div>
        </div>
      </ng-container>

      <!-- VISÃO: ESTUDANTE (Seleciona Matrícula) -->
      <ng-container *ngIf="auth.userRole === 'estudante'">
        <div class="filter-card glass-card">
          <div class="filter-row" style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
            <mat-form-field appearance="outline" class="filter-field" *ngIf="enrollments.length > 0" style="flex: 1; margin: 0;">
              <mat-label>Minhas Matrículas</mat-label>
              <mat-select [(ngModel)]="selectedEnrollmentId" (selectionChange)="onEnrollmentChange()">
                @for (e of enrollments; track e.id) {
                  <mat-option [value]="e.id">{{ e.course_name }} ({{ e.academic_period_name }}) - {{ e.enrollment_code || 'S/ Código' }} - {{ e.status }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <mat-spinner diameter="30" *ngIf="loadingFilter"></mat-spinner>
          </div>
        </div>
      </ng-container>

      <!-- EXIBIÇÃO DO BOLETIM (Para ambos) -->
      @if (loading) {
        <div class="loading-center" style="margin-top: 2rem;"><mat-spinner diameter="40"></mat-spinner></div>
      } @else if (boletim) {
        <div class="boletim-header glass-card animate-fade-in" style="margin-bottom: 1rem; padding: 1.5rem; text-align: center;">
          <h2 style="margin: 0; color: var(--gold-primary); font-size: 1.5rem;">{{ boletim.course_name }}</h2>
          <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            <strong>Aluno:</strong> {{ boletim.student_name }} &nbsp;|&nbsp; <strong>Período:</strong> {{ boletim.academic_period_name }}
          </p>
        </div>
        
        <div class="content-row animate-fade-in-delay">
          <mat-accordion multi>
            @for (sub of boletim.subjects; track sub.subject_id) {
              <mat-expansion-panel class="subject-panel glass-card" expanded="true" style="margin-bottom: 1rem; background: rgba(30, 30, 30, 0.6) !important;">
                <mat-expansion-panel-header>
                  <mat-panel-title>
                    <span style="font-size: 1.1rem; font-weight: 500;">{{ sub.subject_name }}</span>
                  </mat-panel-title>
                  <mat-panel-description style="display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: 4px;">
                    <span style="font-size: 0.9rem;">Freq: {{ sub.frequency_percentage }}% ({{sub.total_presences}}/{{sub.total_planned_classes}})</span>
                    <mat-progress-bar mode="determinate" [value]="sub.frequency_percentage" 
                        [color]="sub.frequency_percentage >= 75 ? 'primary' : 'warn'" style="width: 150px;">
                    </mat-progress-bar>
                  </mat-panel-description>
                </mat-expansion-panel-header>

                @if (sub.grades.length > 0) {
                  <table class="simple-table" style="width: 100%; margin-top: 1rem; border-collapse: collapse;">
                    <thead>
                      <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left;">
                        <th style="padding: 12px 8px;">Avaliação</th>
                        <th style="padding: 12px 8px;">Data</th>
                        <th style="padding: 12px 8px;">Nota Tirada</th>
                        <th style="padding: 12px 8px;">Obs</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (g of sub.grades; track g.id) {
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                          <td style="padding: 12px 8px;">{{ g.evaluation_name }}</td>
                          <td style="padding: 12px 8px;">{{ g.date ? (g.date | date:'dd/MM/yyyy') : '-' }}</td>
                          <td style="padding: 12px 8px;">
                            <strong style="color: var(--gold-primary); font-size: 1.1em;">{{ g.value }}</strong> 
                            <span style="opacity: 0.7;">/ {{ g.max_value }}</span>
                          </td>
                          <td style="padding: 12px 8px; font-style: italic; opacity: 0.8;">{{ g.observations || '-' }}</td>
                        </tr>
                      }
                    </tbody>
                  </table>
                } @else {
                  <div class="empty-state" style="padding: 1rem; opacity: 0.7;">
                    <p style="margin:0;"><mat-icon style="vertical-align: middle; margin-right: 8px;">info</mat-icon>Nenhuma atividade avaliativa registrada nesta disciplina.</p>
                  </div>
                }
              </mat-expansion-panel>
            }
            @if (boletim.subjects.length === 0) {
              <div class="empty-state">
                <mat-icon>info</mat-icon>
                <p>Nenhuma disciplina encontrada no boletim do aluno.</p>
              </div>
            }
          </mat-accordion>
        </div>
      }
    </div>
  `,
  styles: [`
    .clickable-rows .mat-mdc-row {
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    .clickable-rows .mat-mdc-row:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    .simple-table th { color: #B3B3B3; font-weight: 500; }
  `]
})
export class GradesComponent implements OnInit {
  boletim: any = null;
  loading = false;
  loadingFilter = false;

  // Filtros Globais (Professor/Admin)
  classGroups: any[] = [];
  selectedGroupId: string = '';
  allStudents: any[] = [];
  selectedDirectStudentId: string = '';

  groupStudents: any[] = [];
  studentCols = ['student_name', 'registration_number', 'actions'];

  // Matrículas selecionáveis (para pesquisa direta ou fluxo estudante)
  enrollments: any[] = [];
  selectedEnrollmentId: string = '';

  constructor(private api: ApiService, public auth: AuthService) { }

  ngOnInit() {
    if (this.auth.userRole !== 'estudante') {
      this.loadClassGroups();
      this.loadAllStudents();
    } else {
      if (this.auth.currentUser) {
        this.loadStudentEnrollments(this.auth.currentUser.id);
      }
    }
  }

  // --- Fluxo Professor/Admin ---

  loadClassGroups() {
    this.loadingFilter = true;
    this.api.get<any[]>('/class-groups/').subscribe({
      next: res => { this.classGroups = res; this.loadingFilter = false; },
      error: () => this.loadingFilter = false
    });
  }

  loadAllStudents() {
    this.api.get<any>('/users/?role=estudante&limit=1000').subscribe({
      next: res => { this.allStudents = res.users; },
      error: () => { }
    });
  }

  onGroupChange() {
    this.selectedDirectStudentId = ''; // Reseta o outro filtro
    this.boletim = null;
    this.groupStudents = [];
    this.enrollments = [];
    this.selectedEnrollmentId = '';

    if (this.selectedGroupId) {
      this.loadGroupStudents();
    }
  }

  onDirectStudentChange() {
    this.selectedGroupId = ''; // Reseta a turma
    this.boletim = null;
    this.groupStudents = [];
    this.enrollments = [];
    this.selectedEnrollmentId = '';

    if (this.selectedDirectStudentId) {
      this.loadStudentEnrollments(this.selectedDirectStudentId);
    }
  }

  loadGroupStudents() {
    this.loadingFilter = true;
    this.api.get<any[]>(`/class-groups/${this.selectedGroupId}/students/`).subscribe({
      next: res => {
        this.groupStudents = res;
        this.loadingFilter = false;
      },
      error: () => this.loadingFilter = false
    });
  }

  openBoletimFromGrid(studentRecord: any) {
    this.selectedEnrollmentId = studentRecord.enrollment_id;
    this.loadBoletim();
  }

  closeBoletim() {
    this.boletim = null;
    this.selectedEnrollmentId = '';
    if (this.selectedDirectStudentId) {
      // Mantém a pesquisa de estudante aberta, recarrega dropdown se necessário
      this.loadStudentEnrollments(this.selectedDirectStudentId);
    }
  }


  // --- Fluxo Estudante e Comum ---

  loadStudentEnrollments(studentId: string) {
    this.loadingFilter = true;
    this.api.get<any[]>(`/academic/enrollments/?student_id=${studentId}`).subscribe({
      next: data => {
        this.enrollments = data;
        this.loadingFilter = false;

        if (this.enrollments.length > 0) {
          const active = this.enrollments.find(e => e.status === 'active') || this.enrollments[0];
          this.selectedEnrollmentId = active.id;

          // Se for estudante vendo si mesmo, abre de imediato. 
          // Se for prof pesquisando direto, também abre de imediato se achar 1 ativa:
          this.loadBoletim();
        }
      },
      error: () => this.loadingFilter = false
    });
  }

  onEnrollmentChange() {
    if (this.selectedEnrollmentId) this.loadBoletim();
  }

  loadBoletim() {
    if (!this.selectedEnrollmentId) return;
    this.loading = true;
    this.api.get<any>(`/academic/boletim/${this.selectedEnrollmentId}`).subscribe({
      next: d => {
        this.boletim = d;
        this.loading = false;
      },
      error: () => {
        this.boletim = null;
        this.loading = false;
      }
    });
  }
}
