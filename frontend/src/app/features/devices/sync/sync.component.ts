import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-sync',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatButtonModule, MatIconModule, 
    MatCardModule, MatCheckboxModule, MatProgressBarModule, MatSnackBarModule
  ],
  template: `
    <div class="page-container p-4">
      <div class="header-section mb-4">
        <h1 class="h3 mb-1">Sincronização em Massa</h1>
        <p class="text-secondary text-sm">Envie todos os cadastros do sistema para os terminais selecionados.</p>
      </div>

      <mat-card class="premium-card p-4">
        <div class="mb-4">
          <h2 class="h5 mb-3">1. Selecione os Terminais de Destino</h2>
          <div class="row g-3">
            <div *ngFor="let d of devices" class="col-md-3">
              <mat-card class="border border-light h-100 shadow-sm device-selector" 
                        [class.selected]="selectedDevices[d.id]"
                        (click)="toggleDevice(d.id)">
                <mat-card-content class="p-3 d-flex align-items-center gap-3">
                  <mat-checkbox [checked]="selectedDevices[d.id]" (change)="toggleDevice(d.id)" (click)="$event.stopPropagation()"></mat-checkbox>
                  <div>
                    <div class="fw-bold">{{ d.name }}</div>
                    <div class="text-xs text-muted font-monospace">{{ d.dev_index }}</div>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </div>
          <div *ngIf="devices.length === 0" class="text-center p-4 bg-light rounded mt-3">
              Nenhum terminal disponível para sincronização.
          </div>
        </div>

        <div class="mb-4" *ngIf="syncing">
          <h2 class="h5 mb-3">2. Progresso da Sincronização</h2>
          <mat-progress-bar mode="determinate" [value]="progress"></mat-progress-bar>
          <p class="mt-2 text-primary fw-bold text-center">{{ progress }}% concluído</p>
        </div>

        <div class="d-flex justify-content-end gap-2">
            <button mat-flat-button color="primary" [disabled]="syncing || getSelectedCount() === 0" (click)="startSync()">
                <mat-icon>cloud_upload</mat-icon> 
                {{ syncing ? 'Sincronizando...' : 'Iniciar Sincronização (' + getSelectedCount() + ')' }}
            </button>
        </div>
      </mat-card>

      <div class="mt-4 alert alert-info py-2 px-3 d-flex align-items-center gap-2 border-0 shadow-sm" style="background: #e1f5fe; border-radius: 8px;">
          <mat-icon style="color: #0288d1;">info</mat-icon>
          <span class="small" style="color: #01579b;">A sincronização enviará Nome e Employee ID (RA) de todos os alunos ativos. Fotos e digitais devem ser migradas individualmente ou cadastradas no terminal.</span>
      </div>
    </div>
  `,
  styles: [`
    .premium-card { border-radius: 16px; border: 1px solid rgba(0,0,0,0.05); }
    .device-selector { cursor: pointer; transition: all 0.2s; border-radius: 12px; }
    .device-selector:hover { border-color: var(--mat-primary-button-state-layer-color) !important; background: rgba(0,0,0,0.01); }
    .device-selector.selected { border-color: #3f51b5 !important; background: rgba(63, 81, 181, 0.05); }
    .text-xs { font-size: 0.75rem; }
  `]
})
export class SyncComponent implements OnInit {
  devices: any[] = [];
  selectedDevices: { [key: string]: boolean } = {};
  syncing = false;
  progress = 0;

  constructor(private api: ApiService, private snack: MatSnackBar) {}

  ngOnInit(): void {
    this.api.get<any[]>('/devices/').subscribe(res => {
        this.devices = res.filter(d => d.is_active);
    });
  }

  toggleDevice(id: string) {
    this.selectedDevices[id] = !this.selectedDevices[id];
  }

  getSelectedCount() {
    return Object.values(this.selectedDevices).filter(v => v).length;
  }

  startSync() {
    const selectedIds = Object.keys(this.selectedDevices).filter(id => this.selectedDevices[id]);
    this.syncing = true;
    this.progress = 0;

    const query = selectedIds.map(id => `device_ids=${id}`).join('&');
    this.api.post(`/devices/sync-all?${query}`, {}).subscribe({
      next: () => {
        this.progress = 100;
        this.snack.open('Sincronização iniciada com sucesso!', 'OK', { duration: 3000 });
        setTimeout(() => {
            this.syncing = false;
            this.progress = 0;
        }, 2000);
      },
      error: () => {
        this.syncing = false;
        this.snack.open('Falha ao iniciar sincronização', 'OK', { duration: 3000 });
      }
    });
  }
}
