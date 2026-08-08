import { Component, Inject, OnInit, Optional, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-student-dossier',
  standalone: true,
  imports: [
    CommonModule, MatDialogModule, MatButtonModule, MatIconModule,
    MatProgressSpinnerModule, MatTabsModule, MatExpansionModule, MatChipsModule
  ],
  template: `
    <div class="dialog-header" *ngIf="isDialog">
      <h2 mat-dialog-title><mat-icon>account_circle</mat-icon> Dossiê 360º</h2>
      <button mat-icon-button mat-dialog-close><mat-icon>close</mat-icon></button>
    </div>
    
    <mat-dialog-content>
      @if (loading) {
        <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div>
      } @else if (data) {
        <div class="dossier-profile">
          <div class="avatar">{{ data.student.name.charAt(0) }}</div>
          <div class="info">
            <h3>{{ data.student.name }}</h3>
            <p>{{ data.student.email }}</p>
            <mat-chip-set>
              <mat-chip highlighted>Matrículas: {{ data.enrollments_count }}</mat-chip>
            </mat-chip-set>
          </div>
        </div>

        <mat-tab-group class="dossier-tabs">
          <mat-tab label="Desempenho">
            <div class="tab-padding">
              <div class="summary-card glass-card" style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <p>Total de notas lançadas: <strong>{{ data.grades.length }}</strong></p>
                </div>
                @if (performanceAverage !== null) {
                  <div style="text-align: right;">
                    <span style="font-size: 12px; color: #888; text-transform: uppercase;">Aproveitamento</span>
                    <h3 style="margin: 0; color: #F0D97A;" [class.text-danger]="performanceAverage < 60">{{ performanceAverage | number:'1.0-1' }}%</h3>
                  </div>
                }
              </div>
              
              @if (data.grades.length > 0) {
                <div class="grades-list mt-3">
                  <h4 class="section-title">Avaliações</h4>
                  @for (g of data.grades; track g.id) {
                    <div class="list-item-card glass-card">
                      <div class="item-header">
                        <span class="item-title">{{ g.evaluation_name }}</span>
                        <span class="item-value" [class.text-danger]="g.value < (g.max_value * 0.6)">{{ g.value }} / {{ g.max_value }}</span>
                      </div>
                      <div class="item-footer text-muted">
                        <small><mat-icon inline>calendar_today</mat-icon> {{ g.date | date:'shortDate' }}</small>
                      </div>
                    </div>
                  }
                </div>
              }
            </div>
          </mat-tab>
          
          <mat-tab label="Frequência">
            <div class="tab-padding">
              <div class="summary-card glass-card">
                <p>Total de registros de chamada: <strong>{{ data.attendances.length }}</strong></p>
              </div>
              
              @if (data.attendances.length > 0) {
                <div class="attendances-list mt-3">
                  <h4 class="section-title">Aulas e Frequência</h4>
                  @for (a of data.attendances; track a.id) {
                    <div class="list-item-card glass-card">
                      <div class="item-header">
                        <span class="item-title"><mat-icon inline>class</mat-icon> Aula dia {{ a.class_date | date:'shortDate' }}</span>
                        <span [class]="'badge badge-' + (a.present ? 'success' : 'danger')">
                          {{ a.present ? 'Presente' : 'Falta' }}
                        </span>
                      </div>
                      @if(a.observation) {
                        <p class="mt-2 text-muted"><small>{{ a.observation }}</small></p>
                      }
                    </div>
                  }
                </div>
              }
            </div>
          </mat-tab>
          
          <mat-tab label="Ocorrências">
            <div class="tab-padding">
              @if (data.occurrences.length === 0) {
                <p class="text-muted">Nenhuma ocorrência registrada.</p>
              } @else {
                <mat-accordion>
                  @for (o of data.occurrences; track o.id) {
                    <mat-expansion-panel>
                      <mat-expansion-panel-header>
                        <mat-panel-title>
                          <span [class]="'occ-badge occ-' + o.type">{{ o.type | uppercase }}</span>
                          {{ o.title }}
                        </mat-panel-title>
                        <mat-panel-description>{{ o.date | date:'dd/MM/yyyy' }}</mat-panel-description>
                      </mat-expansion-panel-header>
                      <p>{{ o.description }}</p>
                    </mat-expansion-panel>
                  }
                </mat-accordion>
              }
            </div>
          </mat-tab>

          <mat-tab label="Intervenções">
            <div class="tab-padding">
              @if (data.interventions.length === 0) {
                <p class="text-muted">Nenhuma intervenção registrada.</p>
              } @else {
                <div class="interventions-list">
                  @for (i of data.interventions; track i.id) {
                    <div class="intervention-card glass-card">
                      <div class="i-header">
                        <h4>{{ i.title }}</h4>
                        <span [class]="'status-badge status-' + i.status">{{ i.status }}</span>
                      </div>
                      <p><strong>Descrição:</strong> {{ i.description }}</p>
                      @if(i.action_plan) { <p><strong>Plano de Ação:</strong> {{ i.action_plan }}</p> }
                      <small class="text-muted">{{ i.created_at | date:'medium' }}</small>
                    </div>
                  }
                </div>
              }
            </div>
          </mat-tab>
        </mat-tab-group>
      }
    </mat-dialog-content>
  `,
  styles: [`
    .dialog-header { display: flex; justify-content: space-between; align-items: center; padding: 0 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    h2 { margin: 0; display: flex; align-items: center; gap: 8px; color: #D4AF37; }
    .loading-center { display: flex; justify-content: center; padding: 40px; }
    
    .dossier-profile { display: flex; gap: 24px; align-items: center; padding: 24px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 16px; }
    .avatar { width: 80px; height: 80px; border-radius: 50%; background: #D4AF37; color: #121212; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: bold; }
    .info h3 { margin: 0 0 4px 0; font-size: 24px; color: #F5F5F5; }
    .info p { margin: 0 0 12px 0; color: #B3B3B3; }
    
    .dossier-tabs { margin-top: 16px; }
    .tab-padding { padding: 16px 0; }
    .text-muted { color: #888; }
    
    .occ-badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 12px; }
    .occ-praise { background: #4CAF50; color: white; }
    .occ-warning { background: #FF9800; color: white; }
    .occ-complaint { background: #F44336; color: white; }
    .occ-observation { background: #2196F3; color: white; }
    
    .interventions-list { display: flex; flex-direction: column; gap: 16px; }
    .intervention-card { padding: 16px; }
    .i-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .i-header h4 { margin: 0; color: #F0D97A; }
    .status-badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; }
    .status-open { background: rgba(244,67,54,0.2); color: #F44336; }
    .status-in_progress { background: rgba(255,152,0,0.2); color: #FF9800; }
    .status-resolved { background: rgba(76,175,80,0.2); color: #4CAF50; }
    
    .summary-card { padding: 12px 16px; margin-bottom: 16px; }
    .summary-card p { margin: 0; font-size: 16px; }
    .section-title { margin-top: 24px; margin-bottom: 12px; color: #F0D97A; font-weight: 500; }
    
    .grades-list, .attendances-list { display: flex; flex-direction: column; gap: 12px; }
    .list-item-card { padding: 12px 16px; display: flex; flex-direction: column; gap: 8px; }
    .item-header { display: flex; justify-content: space-between; align-items: center; }
    .item-title { font-weight: 500; display: flex; align-items: center; gap: 8px; }
    .item-title mat-icon { font-size: 18px; width: 18px; height: 18px; color: #F0D97A; }
    .item-value { font-weight: bold; font-size: 16px; }
    .item-footer { display: flex; align-items: center; gap: 4px; }
    
    .text-danger { color: #F44336; }
    .mt-2 { margin-top: 8px; }
    .mt-3 { margin-top: 16px; }
    
    .badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .badge-success { background: rgba(76,175,80,0.2); color: #4CAF50; }
    .badge-danger { background: rgba(244,67,54,0.2); color: #F44336; }
  `]
})
export class StudentDossierComponent implements OnInit, OnChanges {
  @Input() studentId?: string;
  loading = true;
  data: any = null;
  isDialog = false;

  constructor(
    @Optional() public dialogRef: MatDialogRef<StudentDossierComponent>,
    @Optional() @Inject(MAT_DIALOG_DATA) public dialogData: { studentId: string },
    private api: ApiService
  ) {
    this.isDialog = !!dialogRef;
  }

  ngOnInit() {
    this.loadData();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['studentId'] && !changes['studentId'].firstChange) {
      this.loadData();
    }
  }

  loadData() {
    const id = this.studentId || (this.dialogData ? this.dialogData.studentId : null);
    if (!id) return;
    
    this.loading = true;
    this.api.get<any>(`/coordination/students/${id}/dossier`).subscribe({
      next: (res: any) => {
        this.data = res;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  get performanceAverage(): number | null {
    if (!this.data || !this.data.grades || this.data.grades.length === 0) return null;
    
    let totalScore = 0;
    let maxScore = 0;
    
    for (const g of this.data.grades) {
      if (g.value !== null && g.max_value) {
        totalScore += g.value;
        maxScore += g.max_value;
      }
    }
    
    if (maxScore === 0) return null;
    return (totalScore / maxScore) * 100;
  }
}
