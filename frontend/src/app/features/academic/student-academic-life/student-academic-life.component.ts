import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-student-academic-life',
  imports: [CommonModule, MatIconModule, RouterModule],
  templateUrl: './student-academic-life.component.html',
  styleUrl: './student-academic-life.component.scss',
})
export class StudentAcademicLifeComponent implements OnInit {
  enrollments: any[] = [];
  loading = true;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<any>('/academic/enrollments/').subscribe({
      next: (res) => {
        this.enrollments = res.items || [];
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }
}
