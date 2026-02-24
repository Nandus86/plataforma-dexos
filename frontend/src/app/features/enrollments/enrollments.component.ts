import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Observable } from 'rxjs';
import { startWith, map } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-enrollments',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatProgressSpinnerModule, MatChipsModule,
    MatSelectModule, MatFormFieldModule, MatInputModule,
    MatDialogModule, MatSnackBarModule,
    MatAutocompleteModule, ReactiveFormsModule,
  ],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><mat-icon>how_to_reg</mat-icon> Matrículas</h1>
          <p class="page-subtitle">Matricule estudantes nos cursos</p>
        </div>
        @if (canManage) {
          <button class="btn-gold" mat-flat-button (click)="showForm = !showForm">
            <mat-icon>{{ showForm ? 'close' : 'add' }}</mat-icon>
            {{ showForm ? 'Cancelar' : 'Nova Matrícula' }}
          </button>
        }
      </div>

      <!-- New Enrollment Form -->
      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3><mat-icon class="text-gold">assignment_ind</mat-icon> Nova Matrícula</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline">
              <mat-label>Estudante</mat-label>
              <input type="text" matInput [matAutocomplete]="autoStudent" [formControl]="studentCtrl" placeholder="Pesquisar estudante" (input)="newEnrollment.student_id = ''">
              <mat-autocomplete #autoStudent="matAutocomplete" [displayWith]="displayStudentFn" (optionSelected)="onStudentSelected($event)">
                @for (s of filteredStudents$ | async; track s.id) {
                  <mat-option [value]="s">{{ s.name }} ({{ s.registration_number || s.email }})</mat-option>
                }
              </mat-autocomplete>
            </mat-form-field>
            <mat-form-field appearance="outline">
              <mat-label>Curso</mat-label>
              <mat-select [(ngModel)]="newEnrollment.course_id">
                @for (c of courses; track c.id) {
                  <mat-option [value]="c.id">{{ c.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline">
              <mat-label>Ano Letivo</mat-label>
              <mat-select [(ngModel)]="newEnrollment.academic_period_id" (selectionChange)="onAcademicPeriodChange()">
                @for (ap of academicPeriods; track ap.id) {
                  <mat-option [value]="ap.id">{{ ap.name }} ({{ ap.year }})</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline">
              <mat-label>Período (Bimestre/Semestre)</mat-label>
              <mat-select [(ngModel)]="newEnrollment.period_break_ids" [disabled]="!newEnrollment.academic_period_id" multiple>
                @for (pb of periodBreaks; track pb.id) {
                  <mat-option [value]="pb.id">{{ pb.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
          </div>
          <div class="form-actions">
            <button mat-button (click)="showForm = false">Cancelar</button>
            <button class="btn-gold" mat-flat-button (click)="createEnrollment()" [disabled]="saving">
              <mat-icon>save</mat-icon> Salvar
            </button>
          </div>
        </div>
      }

      <!-- Filters -->
      <div class="filters glass-card">
        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>Filtrar por status</mat-label>
          <mat-select [(ngModel)]="filterStatus" (selectionChange)="loadEnrollments()">
            <mat-option value="">Todos</mat-option>
            <mat-option value="active">Ativo</mat-option>
            <mat-option value="completed">Concluído</mat-option>
            <mat-option value="failed">Reprovado</mat-option>
            <mat-option value="locked">Trancado</mat-option>
            <mat-option value="inactive">Inativo</mat-option>
            <mat-option value="transferred">Transferido</mat-option>
          </mat-select>
        </mat-form-field>
      </div>

      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <div class="table-card glass-card">
          <table mat-table [dataSource]="enrollments" class="dark-table">
            <ng-container matColumnDef="student">
              <th mat-header-cell *matHeaderCellDef>Estudante</th>
              <td mat-cell *matCellDef="let e">{{ e.student_name || e.student_id }}</td>
            </ng-container>
            <ng-container matColumnDef="course">
              <th mat-header-cell *matHeaderCellDef>Curso</th>
              <td mat-cell *matCellDef="let e">{{ e.course_name || e.course_id }}</td>
            </ng-container>
            <ng-container matColumnDef="period">
              <th mat-header-cell *matHeaderCellDef>Ano / Período</th>
              <td mat-cell *matCellDef="let e">{{ e.academic_period_name || 'N/A' }} - {{ formatPeriodBreaks(e.period_breaks) }}</td>
            </ng-container>
            <ng-container matColumnDef="status">
              <th mat-header-cell *matHeaderCellDef>Status</th>
              <td mat-cell *matCellDef="let e">
                <mat-chip [class]="'status-chip status-' + e.status">{{ statusLabel(e.status) }}</mat-chip>
              </td>
            </ng-container>
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef>Ações</th>
              <td mat-cell *matCellDef="let e">
                @if (canManage) {
                  <mat-form-field appearance="outline" style="width:140px;margin:0">
                    <mat-select [value]="e.status" (selectionChange)="updateStatus(e.id, $event.value)">
                      <mat-option value="active">Ativo</mat-option>
                      <mat-option value="completed">Concluído</mat-option>
                      <mat-option value="failed">Reprovado</mat-option>
                      <mat-option value="locked">Trancado</mat-option>
                      <mat-option value="inactive">Inativo</mat-option>
                      <mat-option value="transferred">Transferido</mat-option>
                    </mat-select>
                  </mat-form-field>
                }
              </td>
            </ng-container>
            <tr mat-header-row *matHeaderRowDef="cols"></tr>
            <tr mat-row *matRowDef="let row; columns: cols;"></tr>
          </table>
          @if (enrollments.length === 0) {
            <div class="empty-state"><mat-icon>how_to_reg</mat-icon><p>Nenhuma matrícula encontrada</p></div>
          }
        </div>
      }
    </div>
  `,
  styleUrls: [],
})
export class EnrollmentsComponent implements OnInit {
  enrollments: any[] = [];
  students: any[] = [];
  courses: any[] = [];
  academicPeriods: any[] = [];
  periodBreaks: any[] = [];

  loading = false;
  saving = false;
  showForm = false;
  filterStatus = '';
  cols = ['student', 'course', 'period', 'status', 'actions'];

  newEnrollment: { student_id: string; course_id: string; year: number; academic_period_id: string; period_break_ids: string[] } = {
    student_id: '', course_id: '', year: new Date().getFullYear(), academic_period_id: '', period_break_ids: []
  };

  studentCtrl = new FormControl('');
  filteredStudents$!: Observable<any[]>;

  canManage = false;

  constructor(private api: ApiService, private auth: AuthService, private snack: MatSnackBar) { }

  ngOnInit() {
    const role = this.auth.userRole;
    this.canManage = ['superadmin', 'admin', 'coordenacao'].includes(role);
    this.loadEnrollments();
    if (this.canManage) {
      this.loadStudents();
      this.loadCourses();
      this.loadAcademicPeriods();
    }
  }

  loadEnrollments() {
    this.loading = true;
    this.api.get<any[]>('/academic/enrollments/').subscribe({
      next: (data) => {
        this.enrollments = data;
        if (this.filterStatus) {
          this.enrollments = this.enrollments.filter(e => e.status === this.filterStatus);
        }
        this.loading = false;
      },
      error: () => this.loading = false,
    });
  }

  loadStudents() {
    this.api.get<any>('/users/', { role: 'estudante' }).subscribe({
      next: (data) => {
        this.students = data.users || data;
        this.setupStudentAutocomplete();
      }
    });
  }

  setupStudentAutocomplete() {
    this.filteredStudents$ = this.studentCtrl.valueChanges.pipe(
      startWith(''),
      map(value => {
        const name = typeof value === 'string' ? value : (value as any)?.name;
        return name ? this._filterStudents(name) : this.students.slice();
      })
    );
  }

  private _filterStudents(name: string): any[] {
    const filterValue = name.toLowerCase();
    return this.students.filter(s => s.name?.toLowerCase().includes(filterValue) || s.email?.toLowerCase().includes(filterValue) || s.registration_number?.toLowerCase().includes(filterValue));
  }

  displayStudentFn(student: any): string {
    return student ? `${student.name} (${student.registration_number || student.email})` : '';
  }

  onStudentSelected(event: any) {
    this.newEnrollment.student_id = event.option.value?.id;
  }

  loadCourses() {
    this.api.get<any[]>('/courses/').subscribe({
      next: (data) => this.courses = data,
    });
  }

  loadAcademicPeriods() {
    this.api.get<any[]>('/academic-periods?active_only=true').subscribe({
      next: (periods) => this.academicPeriods = periods
    });
  }

  onAcademicPeriodChange() {
    const selectedAP = this.academicPeriods.find(ap => ap.id === this.newEnrollment.academic_period_id);
    this.periodBreaks = selectedAP ? selectedAP.period_breaks : [];
    this.newEnrollment.period_break_ids = [];
  }

  createEnrollment() {
    this.saving = true;
    this.api.post('/academic/enrollments/', this.newEnrollment).subscribe({
      next: () => {
        this.snack.open('Matrícula criada com sucesso!', 'OK', { duration: 3000 });
        this.showForm = false;
        this.saving = false;
        this.loadEnrollments();
        this.newEnrollment = { student_id: '', course_id: '', year: new Date().getFullYear(), academic_period_id: '', period_break_ids: [] };
        this.studentCtrl.setValue('');
        this.periodBreaks = [];
      },
      error: (err) => {
        this.snack.open(err?.error?.detail || 'Erro ao criar matrícula', 'OK', { duration: 4000 });
        this.saving = false;
      },
    });
  }

  updateStatus(id: string, newStatus: string) {
    this.api.put(`/academic/enrollments/${id}`, { status: newStatus }).subscribe({
      next: () => {
        this.snack.open('Status atualizado!', 'OK', { duration: 2000 });
        this.loadEnrollments();
      },
      error: (err) => this.snack.open(err?.error?.detail || 'Erro ao atualizar', 'OK', { duration: 4000 }),
    });
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Ativo', completed: 'Concluído', failed: 'Reprovado', locked: 'Trancado',
      inactive: 'Inativo', transferred: 'Transferido'
    };
    return labels[status] || status;
  }

  formatPeriodBreaks(breaks: any[]): string {
    if (!breaks || breaks.length === 0) return 'Todo o Período';
    return breaks.map(b => b.name).join(', ');
  }
}
