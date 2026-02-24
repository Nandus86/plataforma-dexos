import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { ApiService } from '../../../core/services/api.service';

interface Course {
  id: string;
  name: string;
  code: string;
  matrices?: CurriculumMatrix[];
}

interface Subject {
  id: string;
  name: string;
  code: string;
  workload_hours: number;
}

interface MatrixSubject {
  id: string;
  matrix_id: string;
  subject_id: string;
  semester: number;
  is_active: boolean;
  subject_name?: string;
  subject_code?: string;
  workload_hours?: number;
}

interface CurriculumMatrix {
  id: string;
  course_id: string;
  name: string;
  year: number;
  is_active: boolean;
  subjects?: MatrixSubject[];
}

@Component({
  selector: 'app-matrices',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatExpansionModule,
    MatTableModule,
    MatButtonModule
  ],
  templateUrl: './matrices.component.html',
  styleUrls: ['./matrices.component.scss']
})
export class MatricesComponent implements OnInit {
  courses: Course[] = [];
  matrices: CurriculumMatrix[] = [];

  loading: boolean = false;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) { }

  ngOnInit(): void {
    this.loadAllData();
  }

  loadAllData(): void {
    this.loading = true;
    this.api.get<Course[]>('/courses/').subscribe({
      next: (courses) => {
        this.courses = courses;
        if (this.courses.length === 0) {
          this.loading = false;
          return;
        }

        let loadedCourses = 0;

        this.courses.forEach(course => {
          this.api.get<any[]>(`/courses/${course.id}/matrices/`).subscribe({
            next: (matrices) => {
              (course as any).matrices = matrices;

              if (matrices.length === 0) {
                loadedCourses++;
                if (loadedCourses === this.courses.length) {
                  this.loading = false;
                  this.cdr.detectChanges();
                }
                return;
              }

              let loadedMatrices = 0;
              matrices.forEach(matrix => {
                this.api.get<any[]>(`/courses/matrices/${matrix.id}/subjects/`).subscribe({
                  next: (subjects) => {
                    matrix.subjects = subjects;
                    loadedMatrices++;
                    if (loadedMatrices === matrices.length) {
                      loadedCourses++;
                      if (loadedCourses === this.courses.length) {
                        this.loading = false;
                        this.cdr.detectChanges();
                      }
                    }
                  },
                  error: () => {
                    loadedMatrices++;
                    if (loadedMatrices === matrices.length) {
                      loadedCourses++;
                      if (loadedCourses === this.courses.length) {
                        this.loading = false;
                        this.cdr.detectChanges();
                      }
                    }
                  }
                });
              });
            },
            error: () => {
              loadedCourses++;
              if (loadedCourses === this.courses.length) {
                this.loading = false;
                this.cdr.detectChanges();
              }
            }
          });
        });
      },
      error: (err) => {
        console.error('Error loading data:', err);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  // Removed explicit selection logic since we load all now.
}
