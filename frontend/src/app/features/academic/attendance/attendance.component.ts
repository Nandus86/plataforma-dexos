import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTableModule } from '@angular/material/table';
import { MatExpansionModule } from '@angular/material/expansion';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

interface ClassGroup {
  id: string;
  name: string;
  course_name: string;
  academic_period_id: string;
}

interface Subject {
  id: string; // GroupSubject ID
  subject_id: string;
  subject_name: string;
  workload_hours: number;
}

interface LessonPlan {
  id: string;
  date: string;
  topic: string;
  class_orders: number[];
  activity_type: string;
}

@Component({
  selector: 'app-attendance',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatTableModule,
    MatExpansionModule
  ],
  templateUrl: './attendance.component.html',
  styleUrls: ['./attendance.component.scss'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({height: '0px', minHeight: '0'})),
      state('expanded', style({height: '*'})),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ]
})
export class AttendanceComponent implements OnInit {
  groups: ClassGroup[] = [];
  selectedGroupId: string = '';

  subjects: Subject[] = [];
  selectedSubjectId: string = '';

  lessons: LessonPlan[] = [];
  selectedLesson: LessonPlan | null = null;

  attendanceMatrix: any[] = [];

  loadingGroups = false;
  loadingLessons = false;
  loadingDetails = false;

  // Student specific
  enrollments: any[] = [];
  selectedEnrollmentId: string = '';
  boletim: any = null;
  expandedElement: any | null = null;
  columnsToDisplay: string[] = ['subject_name', 'faltas'];

  constructor(
    private api: ApiService, 
    private snackBar: MatSnackBar,
    public auth: AuthService
  ) { }

  get isStudent(): boolean {
    return this.auth.userRole === 'estudante';
  }

  ngOnInit() {
    if (!this.isStudent) {
      this.loadGroups();
    } else {
      if (this.auth.currentUser) {
        this.loadStudentEnrollments(this.auth.currentUser.id);
      }
    }
  }

  loadGroups() {
    this.loadingGroups = true;
    this.api.get<ClassGroup[]>('/class-groups/').subscribe({
      next: (data) => {
        this.groups = data;
        this.loadingGroups = false;
      },
      error: () => this.loadingGroups = false
    });
  }

  onGroupChange() {
    this.selectedSubjectId = '';
    this.subjects = [];
    this.lessons = [];
    this.selectedLesson = null;
    this.attendanceMatrix = [];

    if (!this.selectedGroupId) return;

    this.api.get<Subject[]>(`/class-groups/${this.selectedGroupId}/subjects/`).subscribe({
      next: (data) => {
        this.subjects = data;
      }
    });
  }

  onSubjectChange() {
    this.lessons = [];
    this.selectedLesson = null;
    this.attendanceMatrix = [];
    this.loadLessons();
  }

  loadLessons() {
    if (!this.selectedSubjectId) return;
    this.loadingLessons = true;
    this.api.get<LessonPlan[]>('/lesson-plans/', { class_group_subject_id: this.selectedSubjectId }).subscribe({
      next: (data) => {
        this.lessons = data;
        this.loadingLessons = false;
      },
      error: () => {
        this.loadingLessons = false;
      }
    });
  }

  selectLesson(lesson: LessonPlan) {
    this.selectedLesson = lesson;
    this.loadLessonDetails(lesson);
  }

  loadLessonDetails(lesson: LessonPlan) {
    if (!lesson.id) return;
    this.loadingDetails = true;
    this.attendanceMatrix = [];

    this.api.get<any>(`/lesson-plans/${lesson.id}/details`).subscribe({
      next: (d) => {
        const classOrders = lesson.class_orders || [1];

        this.attendanceMatrix = d.students.map((s: any) => {
          const row: any = {
            student_id: s.id,
            student_name: s.name,
            enrollment_id: s.enrollment_id,
            attendances: {}
          };

          for (let order of classOrders) {
            const existing = d.attendance.find((a: any) => a.enrollment_id === s.enrollment_id && a.class_order_item === order);
            if (existing) {
              row.attendances[order] = existing;
            } else {
              row.attendances[order] = {
                enrollment_id: s.enrollment_id,
                class_order_item: order,
                present: false,
                observation: ''
              };
            }
          }
          return row;
        });

        this.loadingDetails = false;
      },
      error: () => {
        this.loadingDetails = false;
        this.snackBar.open('Erro ao carregar estudantes e presença', 'X');
      }
    });
  }

  updateAttendance(att: any, order: number) {
    if (this.isStudent) return;
    if (!this.selectedLesson) return;

    const payload = {
      enrollment_id: att.enrollment_id,
      lesson_plan_id: this.selectedLesson.id,
      class_order_item: order,
      class_date: new Date().toISOString(),
      present: att.present,
      checkin_method: 'manual',
      observation: att.observation || ''
    };

    if (att.id) {
      this.api.put(`/attendance/${att.id}`, payload).subscribe({
        error: () => this.snackBar.open('Erro ao atualizar presença', 'X')
      });
    } else {
      this.api.post(`/attendance/`, payload).subscribe({
        next: (res: any) => { att.id = res.id; },
        error: () => this.snackBar.open('Erro ao salvar presença', 'X')
      });
    }
  }

  // --- Student Flow ---

  loadStudentEnrollments(studentId: string) {
    this.loadingGroups = true;
    this.api.get<any>(`/academic/enrollments/?student_id=${studentId}`).subscribe({
      next: data => {
        this.enrollments = data.items || [];
        this.loadingGroups = false;

        if (this.enrollments.length > 0) {
          const active = this.enrollments.find(e => e.status === 'active') || this.enrollments[0];
          this.selectedEnrollmentId = active.id;
          this.loadBoletim();
        }
      },
      error: () => this.loadingGroups = false
    });
  }

  onEnrollmentChange() {
    if (this.selectedEnrollmentId) this.loadBoletim();
  }

  loadBoletim() {
    if (!this.selectedEnrollmentId) return;
    this.loadingDetails = true;
    this.api.get<any>(`/academic/boletim/${this.selectedEnrollmentId}`).subscribe({
      next: d => {
        this.boletim = d;
        this.expandedElement = null;
        this.loadingDetails = false;
      },
      error: () => {
        this.boletim = null;
        this.loadingDetails = false;
      }
    });
  }
}

