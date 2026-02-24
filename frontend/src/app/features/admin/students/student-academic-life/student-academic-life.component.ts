import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../../../core/services/api.service';

@Component({
  selector: 'app-student-academic-life',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule
  ],
  template: `
    <div class="dialog-container glass-card">
      <h2 mat-dialog-title>
        <mat-icon>school</mat-icon> 
        Vida Acadêmica
      </h2>
      
      <div mat-dialog-content class="dialog-content custom-scrollbar">
        <div class="user-info">
            <h3>{{ data.user.name }}</h3>
            <span class="registration">Matrícula: {{ data.user.registration_number || 'N/A' }}</span>
        </div>

        @if (loading) {
          <div class="loading-center">
            <mat-spinner diameter="40"></mat-spinner>
          </div>
        } @else {
          
          <div class="timeline">
            @if (enrollments.length === 0) {
              <div class="empty-state">
                <mat-icon>history</mat-icon>
                <p>Nenhuma matrícula registrada na história deste aluno.</p>
              </div>
            } @else {
              @for (enrollment of enrollments; track enrollment.id) {
                <div class="timeline-item animate-fade-in">
                  <div class="timeline-icon" [ngClass]="'status-' + enrollment.status">
                    <mat-icon>{{ getStatusIcon(enrollment.status) }}</mat-icon>
                  </div>
                  <div class="timeline-content">
                    <div class="header-row">
                      <h4>{{ enrollment.course_name || 'Curso Desconhecido' }}</h4>
                      <mat-chip [ngClass]="'status-chip status-' + enrollment.status">
                        {{ statusLabel(enrollment.status) }}
                      </mat-chip>
                    </div>
                    <p class="period-info">
                      <strong>Matrícula:</strong> {{ enrollment.enrollment_code || 'S/ Código' }}<br>
                      <strong>Ano Letivo:</strong> {{ enrollment.academic_period_name || 'N/A' }} ({{ enrollment.year }})
                    </p>
                    <div class="breaks">
                      @if (enrollment.period_breaks && enrollment.period_breaks.length > 0) {
                        <p><strong>Períodos Liberados:</strong></p>
                        <div class="chips-container">
                          @for (pb of enrollment.period_breaks; track pb.id) {
                            <span class="break-chip">{{ pb.name }}</span>
                          }
                        </div>
                      } @else {
                         <p><strong>Períodos:</strong> Integral / Nenhum especificado</p>
                      }
                    </div>
                  </div>
                </div>
              }
            }
          </div>

        }
      </div>

      <div mat-dialog-actions align="end" class="dialog-actions">
        <button mat-button mat-dialog-close>Fechar</button>
      </div>
    </div>
  `,
  styleUrls: ['./student-academic-life.component.scss']
})
export class StudentAcademicLifeComponent implements OnInit {
  loading = false;
  enrollments: any[] = [];

  constructor(
    public dialogRef: MatDialogRef<StudentAcademicLifeComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    if (this.data.user && this.data.user.id) {
      this.loadHistory();
    }
  }

  loadHistory() {
    this.loading = true;
    this.api.get<any[]>('/academic/enrollments/', { student_id: this.data.user.id }).subscribe({
      next: (data) => {
        // Sort enrollments descending by year and creation date
        this.enrollments = data.sort((a, b) => {
          if (a.year !== b.year) return b.year - a.year;
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        this.loading = false;
      },
      error: () => this.loading = false
    });
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Ativo', completed: 'Concluído', failed: 'Reprovado',
      locked: 'Trancado', inactive: 'Inativo', transferred: 'Transferido'
    };
    return labels[status] || status;
  }

  getStatusIcon(status: string): string {
    const icons: Record<string, string> = {
      active: 'check_circle', completed: 'emoji_events', failed: 'cancel',
      locked: 'lock', inactive: 'person_off', transferred: 'transfer_within_a_station'
    };
    return icons[status] || 'info';
  }
}
