
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ApiService } from '../../../core/services/api.service';

interface LessonPlan {
  id: string;
  class_group_subject_id: string;
  date: string;
  topic: string;
  content?: string;
  activity_type: 'none' | 'exam' | 'work' | 'other';
  other_activity_reason?: string;
  max_score?: number;
  class_order?: number;
  description?: string;
  class_orders?: number[];
}

interface Attendance {
  id: string;
  student_id: string;
  student_name?: string; // added by frontend mapping
  present: boolean;
  enrollment_id: string;
}

interface Grade {
  id: string;
  enrollment_id: string;
  student_id: string; // mapped via enrollment
  student_name?: string;
  value: number;
}

@Component({
  selector: 'app-lesson-plans',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatCardModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule, MatDatepickerModule,
    MatNativeDateModule, MatTabsModule, MatCheckboxModule, MatSnackBarModule,
    MatProgressSpinnerModule, MatTooltipModule, MatExpansionModule, MatChipsModule,
    MatDividerModule, MatSlideToggleModule, MatProgressBarModule
  ],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><mat-icon>menu_book</mat-icon> Planos de Aula</h1>
          <p class="page-subtitle">Gerencie aulas, frequências e notas</p>
        </div>
      </div>

      <!-- Filters / Context Selection -->
      <div class="filter-card glass-card">
        <div class="filter-row">
            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>Turma</mat-label>
              <mat-select [(ngModel)]="selectedGroupId" (selectionChange)="onGroupChange()">
                @for (g of groups; track g.id) {
                  <mat-option [value]="g.id">{{ g.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>Disciplina</mat-label>
              <mat-select [(ngModel)]="selectedSubjectId" (selectionChange)="onSubjectChange()" [disabled]="!selectedGroupId">
                @for (s of subjects; track s.id) {
                  <mat-option [value]="s.id">{{ s.subject_name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <button mat-raised-button color="primary" (click)="toggleForm()" [disabled]="!selectedSubjectId" class="btn-gold">
              <mat-icon>add</mat-icon> Nova Aula
            </button>
        </div>
      </div>

      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }

      <div class="content-row">
        <!-- New/Edit Form -->
        <div class="form-section animate-fade-in" *ngIf="showForm">
           <mat-card class="glass-card form-card">
              <mat-card-header>
                 <mat-card-title>{{ editing ? 'Editar' : 'Novo' }} Plano de Aula</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                 <div class="form-grid">
                    <mat-form-field appearance="outline">
                       <mat-label>Data</mat-label>
                       <input matInput [matDatepicker]="picker" [(ngModel)]="form.date" required>
                       <mat-datepicker-toggle matIconSuffix [for]="picker"></mat-datepicker-toggle>
                       <mat-datepicker #picker></mat-datepicker>
                    </mat-form-field>

                    <mat-form-field appearance="outline">
                       <mat-label>Aula</mat-label>
                       <mat-select [(ngModel)]="form.selected_class_order" required>
                         @for (cs of classSchedules; track cs.order) {
                           <mat-option [value]="cs.order">{{ cs.order }}ª Aula ({{ cs.start_time }} - {{ cs.end_time }})</mat-option>
                         }
                         @if (classSchedules.length === 0) {
                           <mat-option disabled>Selecione uma turma com horários configurados</mat-option>
                         }
                       </mat-select>
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline">
                        <mat-label>Tópico / Assunto</mat-label>
                        <input matInput [(ngModel)]="form.topic" required placeholder="Ex: Introdução à Teologia">
                    </mat-form-field>

                    <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Conteúdo Programático</mat-label>
                        <textarea matInput [(ngModel)]="form.content" rows="3"></textarea>
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Descrição / Objetivos</mat-label>
                        <textarea matInput [(ngModel)]="form.description" rows="2"></textarea>
                    </mat-form-field>

                    <mat-form-field appearance="outline">
                       <mat-label>Tipo de Atividade</mat-label>
                       <mat-select [(ngModel)]="form.activity_type">
                          <mat-option value="none">Aula Normal</mat-option>
                          <mat-option value="exam">Avaliação / Prova</mat-option>
                          <mat-option value="work">Trabalho</mat-option>
                          <mat-option value="other">Outros</mat-option>
                       </mat-select>
                    </mat-form-field>

                    <div *ngIf="form.activity_type === 'other'">
                        <mat-form-field appearance="outline" class="full-width">
                            <mat-label>Motivo / Descrição da Atividade</mat-label>
                            <input matInput [(ngModel)]="form.other_activity_reason" required>
                        </mat-form-field>
                    </div>

                    <div *ngIf="form.activity_type !== 'none'">
                        <mat-form-field appearance="outline">
                            <mat-label>Nota Máxima</mat-label>
                            <input matInput type="number" [(ngModel)]="form.max_score">
                        </mat-form-field>
                    </div>
                 </div>
              </mat-card-content>
              <mat-card-actions align="end">
                 <button mat-button (click)="showForm = false">Cancelar</button>
                 <button mat-raised-button color="primary" (click)="save()" class="btn-gold">Salvar</button>
              </mat-card-actions>
           </mat-card>
        </div>

        <!-- Lessons List -->
        <div class="lessons-list" *ngIf="!loading && selectedSubjectId">
           @if (lessons.length === 0) {
              <div class="empty-state">
                 <mat-icon>event_note</mat-icon>
                 <p>Nenhuma aula registrada para esta disciplina.</p>
              </div>
           }
           @else {
              <div class="summary-bar">
                 <span><strong>Total Planejado:</strong> {{ totalLessonsUsed }} / {{ subjectWorkload }} aulas/horas</span>
                 <mat-progress-bar mode="determinate" [value]="(totalLessonsUsed / (subjectWorkload || 1)) * 100"></mat-progress-bar>
              </div>
             <mat-accordion multi>
                @for (l of lessons; track l.id) {
                   <mat-expansion-panel class="lesson-panel" [class.activity-highlight]="l.activity_type !== 'none'" 
                        (opened)="loadLessonDetails(l)">
                      <mat-expansion-panel-header>
                         <mat-panel-title>
                            <span class="date-badge">{{ l.date | date:'dd/MM' }}</span>
                            <span class="topic-text">{{ l.topic }}</span>
                         </mat-panel-title>
                         <mat-panel-description>
                            <span class="class-orders-badge" *ngIf="l.class_orders && l.class_orders.length > 0">
                                {{ formatClassOrders(l.class_orders) }} Aula
                            </span>
                            <span class="activity-tag" *ngIf="l.activity_type !== 'none'" [ngClass]="l.activity_type">
                                {{ getActivityLabel(l.activity_type) }}
                            </span>
                         </mat-panel-description>
                      </mat-expansion-panel-header>

                      <!-- Detail Tabs -->
                      <mat-tab-group animationDuration="0ms">
                         <!-- Info Tab -->
                         <mat-tab label="Conteúdo">
                            <div class="tab-content">
                               <p><strong>Conteúdo:</strong> {{ l.content || 'N/A' }}</p>
                               <p><strong>Descrição:</strong> {{ l.description || 'N/A' }}</p>
                               <p><strong>Aulas Selecionadas:</strong> {{ formatClassOrders(l.class_orders) }} ({{ (l.class_orders || []).length }} aula(s))</p>
                               <div *ngIf="l.activity_type !== 'none'">
                                  <p><strong>Atividade:</strong> {{ getActivityLabel(l.activity_type) }}</p>
                                  <p *ngIf="l.other_activity_reason"><strong>Motivo:</strong> {{ l.other_activity_reason }}</p>
                                  <p><strong>Nota Máxima:</strong> {{ l.max_score }}</p>
                               </div>
                               <div class="actions-row">
                                  <button mat-stroked-button color="primary" (click)="edit(l)">Editar Dados</button>
                                  <button mat-stroked-button color="warn" (click)="deletePlan(l)">
                                     <mat-icon>delete</mat-icon> Apagar
                                  </button>
                               </div>
                            </div>
                         </mat-tab>

                         <!-- Attendance Tab -->
                         <mat-tab label="Frequência">
                            <div class="tab-content">
                               <div *ngIf="loadingDetails" class="spinner-sm"><mat-spinner diameter="20"></mat-spinner></div>
                               <div *ngIf="!loadingDetails">
                                  <table class="simple-table" *ngIf="attendanceMatrix.length > 0">
                                     <thead>
                                        <tr>
                                           <th>Estudante</th>
                                           @for (order of (l.class_orders || [1]); track order) {
                                              <th class="text-center">{{ order }}ª Aula</th>
                                           }
                                        </tr>
                                     </thead>
                                     <tbody>
                                        @for (row of attendanceMatrix; track row.student_id) {
                                           <tr>
                                              <td>{{ row.student_name }}
                                                  <div style="font-size: 0.8em; color: gray;" *ngIf="hasAbsences(row, l.class_orders)">
                                                      Falta Registrada
                                                  </div>
                                              </td>
                                              @for (order of (l.class_orders || [1]); track order) {
                                                  <td class="text-center" [class.absent]="!row.attendances[order].present">
                                                      <mat-slide-toggle 
                                                          [(ngModel)]="row.attendances[order].present" 
                                                          (change)="updateAttendance(row.attendances[order], l.id, order)">
                                                      </mat-slide-toggle>
                                                      <div style="margin-top: 4px;">
                                                          <input class="bare-input" style="width: 80px; text-align: center; font-size: 0.85em;" placeholder="Obs..." 
                                                                 [(ngModel)]="row.attendances[order].observation" 
                                                                 (blur)="updateAttendance(row.attendances[order], l.id, order)">
                                                      </div>
                                                  </td>
                                              }
                                           </tr>
                                        }
                                     </tbody>
                                  </table>
                                  <div *ngIf="attendanceMatrix.length === 0" class="empty-state">
                                      Nenhum estudante matriculado nesta disciplina.
                                  </div>
                               </div>
                            </div>
                         </mat-tab>

                         <!-- Grades Tab (if activity) -->
                         <mat-tab label="Notas" *ngIf="l.activity_type !== 'none'">
                            <div class="tab-content">
                               <div *ngIf="loadingDetails" class="spinner-sm"><mat-spinner diameter="20"></mat-spinner></div>
                               <div *ngIf="!loadingDetails">
                                  <table class="simple-table">
                                     <thead>
                                        <tr>
                                           <th>Estudante</th>
                                           <th>Nota (Max: {{ l.max_score }})</th>
                                           <th>Obs</th>
                                        </tr>
                                     </thead>
                                     <tbody>
                                        @for (row of attendanceMatrix; track row.student_id) {
                                           <tr *ngIf="row.grade">
                                              <td>{{ row.student_name }}</td>
                                              <td>
                                                 <input type="number" class="grade-input" [(ngModel)]="row.grade.value" 
                                                        [max]="l.max_score ?? 10" min="0" (blur)="updateGrade(row.grade, l.id, row.enrollment_id)">
                                              </td>
                                              <td>
                                                  <input class="bare-input" placeholder="..." [(ngModel)]="row.grade.observations" (blur)="updateGrade(row.grade, l.id, row.enrollment_id)">
                                              </td>
                                           </tr>
                                        }
                                     </tbody>
                                  </table>
                               </div>
                            </div>
                         </mat-tab>
                      </mat-tab-group>

                   </mat-expansion-panel>
                }
             </mat-accordion>
           }
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./lesson-plans.component.scss'],
})
export class LessonPlansComponent implements OnInit {
  groups: any[] = [];
  selectedGroupId: string = '';

  subjects: any[] = [];
  selectedSubjectId: string = '';
  subjectWorkload = 0;
  totalLessonsUsed = 0;
  classSchedules: any[] = [];

  lessons: LessonPlan[] = [];
  loading = false;

  // Form
  showForm = false;
  editing: LessonPlan | null = null;
  form: any = {
    date: new Date(), topic: '', content: '', description: '',
    activity_type: 'none', other_activity_reason: '', max_score: 10,
    selected_class_order: null
  };

  // Details mapped into standard format
  attendanceMatrix: any[] = [];
  loadingDetails = false;

  constructor(
    private api: ApiService,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.loadGroups();
  }

  loadGroups() {
    this.api.get<any[]>('/class-groups/').subscribe({
      next: d => this.groups = d
    });
  }

  onGroupChange() {
    this.selectedSubjectId = '';
    this.subjects = [];
    this.lessons = [];
    this.classSchedules = [];
    if (!this.selectedGroupId) return;

    // Load subjects for group
    this.api.get<any[]>(`/class-groups/${this.selectedGroupId}/subjects/`).subscribe({
      next: d => this.subjects = d
    });

    // Load class schedules from the group's academic period
    const group = this.groups.find(g => g.id === this.selectedGroupId);
    if (group && group.academic_period_id) {
      this.api.get<any>(`/academic-periods/${group.academic_period_id}`).subscribe({
        next: period => {
          this.classSchedules = (period.class_schedules || []).sort((a: any, b: any) => a.order - b.order);
        }
      });
    }
  }

  onSubjectChange() {
    const s = this.subjects.find(x => x.id === this.selectedSubjectId);
    this.subjectWorkload = s ? (s.workload_hours || 0) : 0;
    this.loadLessons();
  }

  loadLessons() {
    if (!this.selectedSubjectId) return;
    this.loading = true;
    this.api.get<LessonPlan[]>('/lesson-plans/', { class_group_subject_id: this.selectedSubjectId }).subscribe({
      next: d => {
        this.lessons = d;
        this.loading = false;
        this.calculateTotalUsed();
      },
      error: () => this.loading = false
    });
  }

  calculateTotalUsed() {
    this.totalLessonsUsed = this.lessons.reduce((acc, curr) => acc + (curr.class_orders?.length || 0), 0);
  }

  formatClassOrders(orders: number[] | undefined): string {
    if (!orders || orders.length === 0) return 'Nenhuma';
    return orders.sort((a, b) => a - b).map(o => o + 'ª').join(', ');
  }

  toggleForm() {
    this.showForm = !this.showForm;
    if (this.showForm && !this.editing) {
      this.form = {
        date: new Date(), topic: '', content: '', description: '',
        activity_type: 'none', other_activity_reason: '', max_score: 10,
        selected_class_order: null
      };
    }
  }

  edit(l: LessonPlan) {
    this.editing = l;
    this.form = { ...l };
    this.form.date = new Date(l.date);
    this.form.selected_class_order = l.class_orders && l.class_orders.length > 0 ? l.class_orders[0] : null;
    this.showForm = true;
  }

  save() {
    if (!this.selectedSubjectId) return;

    const payload: any = {
      ...this.form,
      class_group_subject_id: this.selectedSubjectId
    };

    // Wrap selected_class_order into class_orders array
    payload.class_orders = payload.selected_class_order ? [payload.selected_class_order] : [];
    delete payload.selected_class_order;

    // Explicitly remove matrix_subject_id to rely on backend resolution
    delete payload.matrix_subject_id;

    const obs = this.editing
      ? this.api.put(`/lesson-plans/${this.editing.id}`, payload)
      : this.api.post('/lesson-plans/', payload);

    obs.subscribe({
      next: () => {
        this.snackBar.open('Salvo com sucesso!', 'OK', { duration: 2000 });
        this.showForm = false;
        this.editing = null;
        this.loadLessons();
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro ao salvar', 'Fechar', { duration: 3000 })
    });
  }

  deletePlan(l: LessonPlan) {
    if (!confirm('Tem certeza que deseja apagar este plano de aula? Frequências e notas vinculadas serão apagadas também.')) return;
    this.api.delete(`/lesson-plans/${l.id}`).subscribe({
      next: () => {
        this.snackBar.open('Plano de aula apagado!', 'OK', { duration: 2000 });
        this.loadLessons();
      },
      error: () => this.snackBar.open('Erro ao apagar', 'X', { duration: 3000 })
    });
  }

  getMatrixSubjectId() {
    // Deprecated helper, but keeping if needed for other logic
    const s = this.subjects.find(x => x.id === this.selectedSubjectId);
    return s ? s.subject_id : null;
  }

  getActivityLabel(type: string): string {
    const map: any = { none: 'Normal', exam: 'Avaliação', work: 'Trabalho', other: 'Outros' };
    return map[type] || type;
  }

  // Details Loading (Attendance / Grades)
  loadLessonDetails(l: LessonPlan) {
    if (!l.id) return;
    this.loadingDetails = true;

    // We need endpoints for fetching attendance/grades by lesson plan.
    // I didn't create specifics in `lesson_plans.py` yet.
    // I should assume backend endpoints exist or create them.
    // I originally planned `lesson_plans.py` CRUD.
    // I need to add `GET /lesson-plans/{id}/attendance` and `GET /lesson-plans/{id}/grades`.

    // Let's implement them in frontend expecting them. I will add them to backend shortly.
    this.api.get<any>(`/lesson-plans/${l.id}/details`).subscribe({
      next: d => {
        const classOrders = l.class_orders || [1];

        // Build matrix
        this.attendanceMatrix = d.students.map((s: any) => {
          const row: any = {
            student_id: s.id,
            student_name: s.name,
            enrollment_id: s.enrollment_id,
            attendances: {},
            grade: null
          };

          for (let order of classOrders) {
            const existing = d.attendance.find((a: any) => a.enrollment_id === s.enrollment_id && a.class_order_item === order);
            if (existing) {
              row.attendances[order] = existing;
            } else {
              row.attendances[order] = {
                enrollment_id: s.enrollment_id,
                class_order_item: order,
                present: false, // Default: absent until check-in or manual present
                observation: ''
              };
            }
          }

          const g = d.grades.find((x: any) => x.enrollment_id === s.enrollment_id);
          row.grade = g ? g : { enrollment_id: s.enrollment_id, value: null, observations: '' };

          return row;
        });

        this.loadingDetails = false;
      },
      error: () => this.loadingDetails = false
    });
  }

  hasAbsences(row: any, orders: number[] | undefined): boolean {
    const list = orders || [1];
    return list.some(o => !row.attendances[o]?.present);
  }

  updateAttendance(att: any, lessonPlanId: string, order: number) {
    const payload = {
      enrollment_id: att.enrollment_id,
      lesson_plan_id: lessonPlanId,
      class_order_item: order,
      class_date: new Date().toISOString(), // Used if creating new
      present: att.present,
      checkin_method: 'manual',
      observation: att.observation || ''
    };

    if (att.id) {
      // PUT
      this.api.put(`/attendance/${att.id}`, payload).subscribe({
        error: () => this.snackBar.open('Erro ao salvar presença', 'X')
      });
    } else {
      // POST
      this.api.post(`/attendance/`, payload).subscribe({
        next: (res: any) => { att.id = res.id; }, // Save generated ID
        error: () => this.snackBar.open('Erro ao salvar nova presença', 'X')
      });
    }
  }

  updateGrade(grade: any, lessonPlanId: string, enrollmentId: string) {
    if (grade.value === null || grade.value === '') return;

    if (grade.id) {
      this.api.put(`/grades/${grade.id}`, { value: grade.value, observations: grade.observations || '' }).subscribe({
        error: (err: any) => this.showDetailedError(err, 'Erro ao salvar nota')
      });
    } else {
      const payload = {
        enrollment_id: enrollmentId,
        lesson_plan_id: lessonPlanId,
        evaluation_name: 'Atividade em Aula',
        value: grade.value,
        max_value: 10,
        observations: grade.observations || ''
      };
      this.api.post(`/grades/`, payload).subscribe({
        next: (res: any) => { grade.id = res.id; },
        error: (err: any) => this.showDetailedError(err, 'Erro ao salvar nova nota')
      });
    }
  }

  private showDetailedError(err: any, fallback: string) {
    let errMsg = fallback;
    if (err?.error?.detail) {
      if (Array.isArray(err.error.detail)) {
        errMsg = err.error.detail.map((e: any) => e.msg).join(', ');
      } else if (typeof err.error.detail === 'string') {
        errMsg = err.error.detail;
      } else {
        errMsg = JSON.stringify(err.error.detail);
      }
    }
    this.snackBar.open(errMsg, 'X', { duration: 4000 });
  }
}
