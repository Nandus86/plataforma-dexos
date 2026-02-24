import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { Observable } from 'rxjs';
import { startWith, map } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { AcademicPeriodService } from '../../core/services/academic-period.service';
import { AcademicPeriod, PeriodBreak } from '../../core/models/academic-period.model';

@Component({
  selector: 'app-class-groups',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule, MatSnackBarModule,
    MatProgressSpinnerModule, MatTooltipModule, MatChipsModule, MatDividerModule,
    MatDialogModule, MatSlideToggleModule, MatAutocompleteModule, ReactiveFormsModule,
  ],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><mat-icon>groups</mat-icon> Turmas</h1>
          <p class="page-subtitle">Gerencie turmas, estudantes e disciplinas</p>
        </div>
        <button mat-raised-button color="primary" (click)="toggleForm()" class="btn-gold">
          <mat-icon>add</mat-icon> Nova Turma
        </button>
      </div>

      <!-- Create/Edit Form -->
      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3>{{ editing ? 'Editar' : 'Nova' }} Turma</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline">
              <mat-label>Curso</mat-label>
              <mat-select [(ngModel)]="form.course_id" required>
                @for (c of courses; track c.id) {
                  <mat-option [value]="c.id">{{ c.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline">
              <mat-label>Nome da Turma</mat-label>
              <input matInput [(ngModel)]="form.name" required placeholder="Ex: Teologia 2026.1 - Noturno">
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>Ano Letivo</mat-label>
              <mat-select [(ngModel)]="form.academic_period_id" (selectionChange)="onPeriodChange()" required>
                @for (p of academicPeriods; track p.id) {
                    <mat-option [value]="p.id">{{ p.name }} ({{ p.year }})</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline" *ngIf="availableBreaks.length > 0">
              <mat-label>Quebra / Semestre</mat-label>
              <mat-select [(ngModel)]="form.period_break_id">
                <mat-option [value]="null">Período Completo</mat-option>
                @for (b of availableBreaks; track b.id) {
                    <mat-option [value]="b.id">{{ b.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>Turno</mat-label>
              <mat-select [(ngModel)]="form.shift">
                <mat-option value="manha">Manhã</mat-option>
                <mat-option value="tarde">Tarde</mat-option>
                <mat-option value="noite">Noite</mat-option>
                <mat-option value="integral">Integral</mat-option>
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline">
              <mat-label>Máx. Estudantes</mat-label>
              <input matInput type="number" [(ngModel)]="form.max_students">
            </mat-form-field>
          </div>
          <div class="form-actions">
            <button mat-button (click)="showForm = false">Cancelar</button>
            <button mat-raised-button color="primary" (click)="save()" class="btn-gold">Salvar</button>
          </div>
        </div>
      }

      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <!-- Groups Table -->
        <div class="table-card glass-card">
          <table mat-table [dataSource]="groups" class="dark-table">
            <ng-container matColumnDef="name">
              <th mat-header-cell *matHeaderCellDef>Turma</th>
              <td mat-cell *matCellDef="let g">{{ g.name }}</td>
            </ng-container>
            <ng-container matColumnDef="course">
              <th mat-header-cell *matHeaderCellDef>Curso</th>
              <td mat-cell *matCellDef="let g">{{ g.course_name }}</td>
            </ng-container>
            <ng-container matColumnDef="period">
              <th mat-header-cell *matHeaderCellDef>Período</th>
              <td mat-cell *matCellDef="let g">
                 {{ g.academic_period_name }} 
                 <span class="text-muted" *ngIf="g.period_break_name">- {{ g.period_break_name }}</span>
                 <span class="text-muted" *ngIf="!g.period_break_name">- Completo</span>
              </td>
            </ng-container>
            <ng-container matColumnDef="shift">
              <th mat-header-cell *matHeaderCellDef>Turno</th>
              <td mat-cell *matCellDef="let g">{{ shiftLabel(g.shift) }}</td>
            </ng-container>
            <ng-container matColumnDef="students">
              <th mat-header-cell *matHeaderCellDef>Estudantes</th>
              <td mat-cell *matCellDef="let g">
                <span class="badge">{{ g.student_count }}</span>
                @if (g.max_students) { <span class="badge-sub">/ {{ g.max_students }}</span> }
              </td>
            </ng-container>
            <ng-container matColumnDef="subjects">
              <th mat-header-cell *matHeaderCellDef>Disciplinas</th>
              <td mat-cell *matCellDef="let g"><span class="badge">{{ g.subject_count }}</span></td>
            </ng-container>
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef></th>
              <td mat-cell *matCellDef="let g">
                <button mat-icon-button (click)="openDetail(g)" matTooltip="Gerenciar"><mat-icon>visibility</mat-icon></button>
                <button mat-icon-button (click)="edit(g)" matTooltip="Editar"><mat-icon>edit</mat-icon></button>
                <button mat-icon-button (click)="confirmDelete(g)" matTooltip="Apagar" color="warn"><mat-icon>delete</mat-icon></button>
              </td>
            </ng-container>
            <tr mat-header-row *matHeaderRowDef="cols"></tr>
            <tr mat-row *matRowDef="let row; columns: cols;"></tr>
          </table>
          @if (groups.length === 0) { <div class="empty-state"><mat-icon>groups</mat-icon><p>Nenhuma turma cadastrada</p></div> }
        </div>

        <!-- Detail Panel -->
        @if (selectedGroup) {
          <div class="detail-panel glass-card animate-fade-in">
            <div class="detail-header">
              <h2><mat-icon>groups</mat-icon> {{ selectedGroup.name }}</h2>
              <button mat-icon-button (click)="selectedGroup = null"><mat-icon>close</mat-icon></button>
            </div>

            <mat-divider></mat-divider>

            <!-- Students Section -->
            <div class="detail-section">
              <div class="section-header">
                <h3><mat-icon>school</mat-icon> Estudantes ({{ groupStudents.length }})</h3>
                <div class="section-actions">
                  <mat-form-field appearance="outline" class="add-field">
                    <mat-label>Adicionar matrícula (estudante)</mat-label>
                    <input type="text" matInput [matAutocomplete]="autoStudent" [formControl]="studentCtrl" placeholder="Pesquisar estudante" (input)="newEnrollmentId = ''">
                    <mat-autocomplete #autoStudent="matAutocomplete" [displayWith]="displayStudentFn" (optionSelected)="onStudentSelected($event)">
                      @for (e of filteredEnrollments$ | async; track e.id) {
                        <mat-option [value]="e">{{ e.student_name }} ({{ e.student_email || '...' }})</mat-option>
                      }
                    </mat-autocomplete>
                  </mat-form-field>
                  <button mat-raised-button color="primary" (click)="addStudent()" [disabled]="!newEnrollmentId" class="btn-gold btn-sm">
                    <mat-icon>person_add</mat-icon> Adicionar
                  </button>
                </div>
              </div>
              <div class="chips-list">
                @for (s of groupStudents; track s.id) {
                  <mat-chip-row (removed)="removeStudent(s)">
                    {{ s.student_name }}
                    <button matChipRemove><mat-icon>cancel</mat-icon></button>
                  </mat-chip-row>
                }
                @if (groupStudents.length === 0) { <p class="text-muted">Nenhum estudante adicionado</p> }
              </div>
            </div>

            <mat-divider></mat-divider>

            <!-- Subjects Section -->
            <div class="detail-section">
              <div class="section-header">
                <h3><mat-icon>menu_book</mat-icon> Disciplinas ({{ groupSubjects.length }})</h3>
                <div class="section-actions">
                  <mat-form-field appearance="outline" class="add-field">
                    <mat-label>Adicionar disciplina</mat-label>
                    <mat-select [(ngModel)]="newSubjectId" (selectionChange)="onSubjectChange()">
                      @for (s of availableSubjects; track s.id) {
                        <mat-option [value]="s.id">{{ s.name }} ({{ s.workload_hours }}h)</mat-option>
                      }
                    </mat-select>
                  </mat-form-field>

                  <mat-form-field appearance="outline" class="add-field" *ngIf="availableBreaks.length > 0">
                    <mat-label>Período / Bimestre</mat-label>
                    <mat-select [(ngModel)]="newPeriodBreakId">
                      <mat-option [value]="''">Todo o período</mat-option>
                      @for (b of availableBreaks; track b.id) {
                        <mat-option [value]="b.id">{{ b.name }}</mat-option>
                      }
                    </mat-select>
                  </mat-form-field>

                  <!-- Professors List for New Subject -->
                  <div class="professors-staging" *ngIf="newSubjectId">
                     <div class="add-prof-row">
                        <mat-form-field appearance="outline" class="prof-select">
                          <mat-label>Professor</mat-label>
                          <input type="text" matInput [matAutocomplete]="autoProf" [formControl]="profCtrl" placeholder="Pesquisar professor" (input)="newProfessorId = ''">
                          <mat-autocomplete #autoProf="matAutocomplete" [displayWith]="displayProfFn" (optionSelected)="onProfSelected($event)">
                            @for (p of filteredProfessors$ | async; track p.id) {
                              <mat-option [value]="p">{{ p.name }}</mat-option>
                            }
                          </mat-autocomplete>
                        </mat-form-field>
                        <mat-form-field appearance="outline" class="hours-input">
                          <mat-label>Horas</mat-label>
                          <input matInput type="number" [(ngModel)]="newProfessorHours">
                        </mat-form-field>
                        <button mat-icon-button color="primary" (click)="addProfessor()" [disabled]="!newProfessorId">
                          <mat-icon>add_circle</mat-icon>
                        </button>
                     </div>
                     
                     <div class="selected-profs">
                        @for (p of selectedProfessors; track p.id; let i = $index) {
                          <mat-chip-row (removed)="removeProfessor(i)">
                            {{ p.name }} ({{ p.assigned_hours }}h)
                            <button matChipRemove><mat-icon>cancel</mat-icon></button>
                          </mat-chip-row>
                        }
                     </div>
                  </div>
                  
                  <button mat-raised-button color="primary" (click)="addSubject()" [disabled]="!newSubjectId || selectedProfessors.length === 0" class="btn-gold btn-sm">
                    <mat-icon>save</mat-icon> Salvar Disciplina
                  </button>
                </div>
              </div>
              <div class="chips-list">
                @for (s of groupSubjects; track s.id) {
                  <div class="subject-card">
                    <div class="subject-header">
                       <div class="subject-title">
                           <strong>{{ s.subject_name }}</strong>
                           <span class="break-tag" *ngIf="s.period_break_id">{{ getBreakName(s.period_break_id) }}</span>
                       </div>
                       <button mat-icon-button color="warn" (click)="removeSubject(s)"><mat-icon>delete</mat-icon></button>
                    </div>
                    <div class="subject-profs">
                       @for (p of s.professors; track p.professor_id) {
                         <small class="prof-tag">{{ p.professor_name }} ({{ p.assigned_hours }}h)</small>
                       }
                    </div>
                  </div>
                }
                @if (groupSubjects.length === 0) { <p class="text-muted">Nenhuma disciplina adicionada</p> }
              </div>
            </div>

            <!-- Student x Subject Grid -->
            @if (groupStudents.length > 0 && groupSubjects.length > 0) {
              <mat-divider></mat-divider>
              <div class="detail-section">
                <h3><mat-icon>grid_on</mat-icon> Grade Estudante × Disciplina</h3>
                @if (gridLoading) { <div class="loading-center"><mat-spinner diameter="30"></mat-spinner></div> }
                @else {
                  <div class="grid-container">
                    <table class="student-subject-grid">
                      <thead>
                        <tr>
                          <th class="grid-header-student">Estudante</th>
                          @for (subj of gridSubjects; track subj.id) {
                            <th class="grid-header-subject">{{ subj.name }}</th>
                          }
                        </tr>
                      </thead>
                      <tbody>
                        @for (student of gridStudents; track student.id) {
                          <tr>
                            <td class="grid-cell-student">{{ student.name }}</td>
                            @for (subj of gridSubjects; track subj.id) {
                              <td class="grid-cell" [class.grid-cell-inactive]="!getGridStatus(student.id, subj.id)">
                                <mat-slide-toggle
                                  [checked]="getGridStatus(student.id, subj.id)"
                                  (change)="toggleGrid(student.id, subj.id, $event.checked)"
                                  color="primary">
                                </mat-slide-toggle>
                                @if (!getGridStatus(student.id, subj.id)) {
                                  <input class="reason-input" placeholder="Motivo..."
                                    [value]="getGridReason(student.id, subj.id)"
                                    (blur)="saveReason(student.id, subj.id, $event)">
                                }
                              </td>
                            }
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
                }
              </div>
            }
          </div>
        }
      }
    </div>
  `,
  styleUrls: ['./class-groups.component.scss'],
})
export class ClassGroupsComponent implements OnInit {
  groups: any[] = [];
  courses: any[] = [];
  academicPeriods: AcademicPeriod[] = [];
  loading = false;
  showForm = false;
  editing: any = null;
  form: any = { course_id: '', name: '', shift: 'noite', max_students: null, academic_period_id: null, period_break_id: null };
  cols = ['name', 'course', 'period', 'shift', 'students', 'subjects', 'actions'];

  // Detail panel
  selectedGroup: any = null;
  groupStudents: any[] = [];
  groupSubjects: any[] = [];
  availableEnrollments: any[] = [];
  availableSubjects: any[] = [];
  availableProfessors: any[] = [];
  availableBreaks: PeriodBreak[] = [];
  selectedProfessors: { id: string, name: string, assigned_hours: number }[] = [];
  newEnrollmentId: string = '';
  newSubjectId: string = '';
  newPeriodBreakId: string = '';
  newProfessorId: string = '';
  newProfessorHours: number = 0;

  // Autocomplete controls
  studentCtrl = new FormControl('');
  filteredEnrollments$!: Observable<any[]>;
  profCtrl = new FormControl('');
  filteredProfessors$!: Observable<any[]>;


  // Grid
  gridData: any[] = [];
  gridStudents: any[] = [];
  gridSubjects: any[] = [];
  gridLoading = false;
  private gridMap: Map<string, any> = new Map();

  constructor(
    private api: ApiService,
    private periodService: AcademicPeriodService,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.loadCourses();
    this.loadAcademicPeriods();
    this.load();
  }

  load() {
    this.loading = true;
    this.api.get<any[]>('/class-groups/').subscribe({
      next: d => { this.groups = d; this.loading = false; },
      error: () => this.loading = false,
    });
  }

  loadCourses() {
    this.api.get<any[]>('/courses/').subscribe({ next: d => this.courses = d });
  }

  loadAcademicPeriods() {
    this.periodService.getAcademicPeriods(true).subscribe({ next: d => this.academicPeriods = d });
  }

  onPeriodChange() {
    if (this.form.academic_period_id) {
      this.loadPeriodBreaks(this.form.academic_period_id);
    } else {
      this.availableBreaks = [];
      this.form.period_break_id = null;
    }
  }

  toggleForm() {
    this.showForm = !this.showForm;
    if (this.showForm && !this.editing) {
      this.form = { course_id: '', name: '', shift: 'noite', max_students: null, academic_period_id: null, period_break_id: null };
      this.availableBreaks = [];
    }
  }

  edit(g: any) {
    this.editing = g;
    this.form = {
      course_id: g.course_id, name: g.name,
      shift: g.shift, max_students: g.max_students,
      academic_period_id: g.academic_period_id,
      period_break_id: g.period_break_id
    };
    if (g.academic_period_id) {
      this.loadPeriodBreaks(g.academic_period_id);
    } else {
      this.availableBreaks = [];
    }
    this.showForm = true;
  }

  save() {
    const obs = this.editing
      ? this.api.put(`/class-groups/${this.editing.id}`, this.form)
      : this.api.post('/class-groups/', this.form);
    obs.subscribe({
      next: () => {
        this.snackBar.open('Salvo!', 'OK', { duration: 3000 });
        this.showForm = false; this.editing = null; this.load();
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
    });
  }

  confirmDelete(g: any) {
    if (confirm(`Deseja realmente apagar a turma "${g.name}"?`)) {
      this.api.delete(`/class-groups/${g.id}`).subscribe({
        next: () => { this.snackBar.open('Turma removida!', 'OK', { duration: 3000 }); this.load(); },
        error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
      });
    }
  }

  shiftLabel(s: string): string {
    const labels: Record<string, string> = { manha: 'Manhã', tarde: 'Tarde', noite: 'Noite', integral: 'Integral' };
    return labels[s] || s;
  }

  // ========== Detail Panel ==========

  openDetail(g: any) {
    this.selectedGroup = g;
    this.loadGroupStudents();
    this.loadGroupSubjects();
    this.loadAvailableEnrollments();
    this.loadAvailableSubjects();
    this.loadAvailableProfessors();
    if (g.academic_period_id) {
      this.loadPeriodBreaks(g.academic_period_id);
    } else {
      this.availableBreaks = [];
    }
  }

  loadPeriodBreaks(periodId: string) {
    this.periodService.getAcademicPeriod(periodId).subscribe({
      next: p => this.availableBreaks = p.period_breaks || []
    });
  }

  loadGroupStudents() {
    this.api.get<any[]>(`/class-groups/${this.selectedGroup.id}/students/`).subscribe({
      next: d => { this.groupStudents = d; this.buildGridMeta(); },
    });
  }

  loadGroupSubjects() {
    this.api.get<any[]>(`/class-groups/${this.selectedGroup.id}/subjects/`).subscribe({
      next: d => { this.groupSubjects = d; this.buildGridMeta(); },
    });
  }

  loadAvailableEnrollments() {
    if (!this.selectedGroup?.course_id) return;
    this.api.get<any[]>('/academic/enrollments/', { course_id: this.selectedGroup.course_id, status: 'active' }).subscribe({
      next: d => {
        this.availableEnrollments = d || [];
        this.setupStudentAutocomplete();
      },
    });
  }

  loadAvailableSubjects() {
    if (!this.selectedGroup?.course_id) return;
    this.api.get<any[]>('/courses/subjects/', { course_id: this.selectedGroup.course_id }).subscribe({
      next: d => this.availableSubjects = d,
    });
  }

  loadAvailableProfessors() {
    this.api.get<any>('/users/', { role: 'professor' }).subscribe({
      next: d => {
        this.availableProfessors = d.users || [];
        this.setupProfAutocomplete();
      },
    });
  }

  // --- Autocomplete Setup Methods ---
  setupStudentAutocomplete() {
    this.filteredEnrollments$ = this.studentCtrl.valueChanges.pipe(
      startWith(''),
      map(value => {
        const name = typeof value === 'string' ? value : (value as any)?.student_name;
        return name ? this._filterStudents(name) : this.availableEnrollments.slice();
      })
    );
  }

  private _filterStudents(name: string): any[] {
    const filterValue = name.toLowerCase();
    return this.availableEnrollments.filter(e => e.student_name?.toLowerCase().includes(filterValue) || e.student_email?.toLowerCase().includes(filterValue));
  }

  displayStudentFn(enrollment: any): string {
    return enrollment ? `${enrollment.student_name} (${enrollment.student_email})` : '';
  }

  onStudentSelected(event: any) {
    this.newEnrollmentId = event.option.value?.id;
  }

  setupProfAutocomplete() {
    this.filteredProfessors$ = this.profCtrl.valueChanges.pipe(
      startWith(''),
      map(value => {
        const name = typeof value === 'string' ? value : (value as any)?.name;
        return name ? this._filterProfs(name) : this.availableProfessors.slice();
      })
    );
  }

  private _filterProfs(name: string): any[] {
    const filterValue = name.toLowerCase();
    return this.availableProfessors.filter(p => p.name?.toLowerCase().includes(filterValue));
  }

  displayProfFn(prof: any): string {
    return prof ? prof.name : '';
  }

  onProfSelected(event: any) {
    this.newProfessorId = event.option.value?.id;
  }
  // ---------------------------------

  addStudent() {
    if (!this.newEnrollmentId) return;
    this.api.post(`/class-groups/${this.selectedGroup.id}/students/`, { enrollment_id: this.newEnrollmentId }).subscribe({
      next: () => {
        this.snackBar.open('Estudante adicionado!', 'OK', { duration: 2000 });
        this.newEnrollmentId = '';
        this.studentCtrl.setValue('');
        this.loadGroupStudents();
        this.loadGrid();
        this.load();
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
    });
  }

  removeStudent(s: any) {
    this.api.delete(`/class-groups/${this.selectedGroup.id}/students/${s.enrollment_id}`).subscribe({
      next: () => {
        this.snackBar.open('Estudante removido', 'OK', { duration: 2000 });
        this.loadGroupStudents();
        this.loadGrid();
        this.load();
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
    });
  }

  onSubjectChange() {
    const s = this.availableSubjects.find(x => x.id === this.newSubjectId);
    if (s) {
      this.selectedProfessors = [];
      this.newProfessorHours = s.workload_hours || 0;
    }
  }

  addProfessor() {
    if (!this.newProfessorId || !this.newProfessorHours) return;
    const p = this.availableProfessors.find(x => x.id === this.newProfessorId);
    if (p) {
      if (this.selectedProfessors.some(x => x.id === p.id)) {
        this.snackBar.open('Professor já adicionado', 'Fechar', { duration: 2000 });
        return;
      }
      this.selectedProfessors.push({ id: p.id, name: p.name, assigned_hours: this.newProfessorHours });
      this.newProfessorId = '';
      this.profCtrl.setValue('');
    }
  }

  removeProfessor(index: number) {
    this.selectedProfessors.splice(index, 1);
  }

  addSubject() {
    if (!this.newSubjectId) return;
    if (this.selectedProfessors.length === 0) {
      this.snackBar.open('Adicione pelo menos um professor', 'Fechar', { duration: 3000 });
      return;
    }

    const payload = {
      subject_id: this.newSubjectId,
      period_break_id: this.newPeriodBreakId || null,
      professors: this.selectedProfessors.map(p => ({ professor_id: p.id, assigned_hours: p.assigned_hours }))
    };

    this.api.post(`/class-groups/${this.selectedGroup.id}/subjects/`, payload).subscribe({
      next: () => {
        this.snackBar.open('Disciplina adicionada!', 'OK', { duration: 2000 });
        this.newSubjectId = '';
        this.newPeriodBreakId = '';
        this.selectedProfessors = [];
        this.newProfessorId = '';
        this.newProfessorHours = 0;
        this.loadGroupSubjects();
        this.loadGrid();
        this.load();
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
    });
  }

  removeSubject(s: any) {
    this.api.delete(`/class-groups/${this.selectedGroup.id}/subjects/${s.id}`).subscribe({
      next: () => {
        this.snackBar.open('Disciplina removida', 'OK', { duration: 2000 });
        this.loadGroupSubjects();
        this.loadGrid();
        this.load();
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
    });
  }

  getBreakName(breakId: string): string {
    if (!breakId) return '';
    const b = this.availableBreaks.find(x => x.id === breakId);
    return b ? b.name : '';
  }

  // ========== Grid ==========

  private buildGridMeta() {
    this.gridStudents = this.groupStudents.map(s => ({ id: s.enrollment_id, name: s.student_name }));
    this.gridSubjects = this.groupSubjects.map(s => ({ id: s.subject_id, name: s.subject_name }));
    if (this.gridStudents.length > 0 && this.gridSubjects.length > 0) {
      this.loadGrid();
    }
  }

  loadGrid() {
    if (!this.selectedGroup) return;
    this.gridLoading = true;
    this.api.get<any[]>(`/class-groups/${this.selectedGroup.id}/grid/`).subscribe({
      next: d => {
        this.gridData = d;
        this.gridMap.clear();
        for (const r of d) {
          this.gridMap.set(`${r.enrollment_id}::${r.subject_id}`, r);
        }
        this.gridLoading = false;
      },
      error: () => this.gridLoading = false,
    });
  }

  getGridStatus(studentId: string, subjectId: string): boolean {
    const r = this.gridMap.get(`${studentId}::${subjectId}`);
    return r ? r.is_active : true;
  }

  getGridReason(studentId: string, subjectId: string): string {
    const r = this.gridMap.get(`${studentId}::${subjectId}`);
    return r?.reason || '';
  }

  toggleGrid(studentId: string, subjectId: string, checked: boolean) {
    const reason = checked ? null : '';
    this.api.put(`/class-groups/${this.selectedGroup.id}/grid/${studentId}/${subjectId}`, {
      is_active: checked, reason
    }).subscribe({
      next: (r: any) => {
        this.gridMap.set(`${studentId}::${subjectId}`, r);
        this.snackBar.open(checked ? 'Ativado' : 'Desativado', 'OK', { duration: 1500 });
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
    });
  }

  saveReason(studentId: string, subjectId: string, event: Event) {
    const reason = (event.target as HTMLInputElement).value;
    this.api.put(`/class-groups/${this.selectedGroup.id}/grid/${studentId}/${subjectId}`, {
      is_active: false, reason
    }).subscribe({
      next: (r: any) => {
        this.gridMap.set(`${studentId}::${subjectId}`, r);
      },
    });
  }
}
