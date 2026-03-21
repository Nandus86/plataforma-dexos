import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatTableModule, MatButtonModule, 
    MatIconModule, MatCardModule, MatChipsModule, MatDialogModule, 
    MatSnackBarModule
  ],
  template: `
    <div class="page-container p-4">
      <div class="header-section mb-4 d-flex justify-content-between align-items-center">
        <div>
          <h1 class="h3 mb-1">Terminais de Biometria</h1>
          <p class="text-secondary text-sm">Gerencie os leitores Hikvision registrados no sistema.</p>
        </div>
        <div class="d-flex gap-2">
            <button mat-stroked-button color="primary" (click)="loadGatewayDevices()">
                <mat-icon>refresh</mat-icon> Atualizar Lista
            </button>
        </div>
      </div>

      <div class="row g-4">
        <!-- Lista de Dispositivos Registrados -->
        <div class="col-md-8">
          <mat-card class="premium-card">
            <mat-card-header class="p-4 bg-light border-bottom">
              <mat-card-title class="m-0 h5">Terminais Registrados</mat-card-title>
            </mat-card-header>
            <mat-card-content class="p-0">
               <div class="table-container p-3">
                <table mat-table [dataSource]="devices" class="w-100 table-hover">
                  
                  <ng-container matColumnDef="name">
                    <th mat-header-cell *matHeaderCellDef> Nome </th>
                    <td mat-cell *matCellDef="let d"> 
                        <div class="fw-bold">{{ d.name }}</div>
                        <div class="text-xs text-muted font-monospace">{{ d.dev_index }}</div>
                    </td>
                  </ng-container>

                  <ng-container matColumnDef="status">
                    <th mat-header-cell *matHeaderCellDef> Status </th>
                    <td mat-cell *matCellDef="let d"> 
                        <mat-chip-set>
                            <mat-chip [color]="d.is_active ? 'primary' : 'warn'" highlighted>
                                {{ d.is_active ? 'Ativo' : 'Inativo' }}
                            </mat-chip>
                        </mat-chip-set>
                    </td>
                  </ng-container>

                  <ng-container matColumnDef="actions">
                    <th mat-header-cell *matHeaderCellDef> Ações </th>
                    <td mat-cell *matCellDef="let d"> 
                        <button mat-icon-button color="warn" (click)="deleteDevice(d.id)" matTooltip="Remover">
                            <mat-icon>delete</mat-icon>
                        </button>
                    </td>
                  </ng-container>

                  <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
                  <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
                </table>

                <div *ngIf="devices.length === 0" class="text-center p-5">
                    <mat-icon class="large-icon text-muted">router</mat-icon>
                    <p class="mt-3">Nenhum dispositivo encontrado no banco de dados.</p>
                </div>
               </div>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- Dispositivos Pendentes no Gateway -->
        <div class="col-md-4">
            <mat-card class="premium-card glass border-primary">
                <mat-card-header class="p-4 border-bottom">
                    <mat-card-title class="m-0 h5">Conexões Gateway</mat-card-title>
                </mat-card-header>
                <mat-card-content class="p-4">
                    <p class="small text-muted mb-4">Terminais detectados automaticamente pelo Hik Gateway:</p>
                    
                    <div class="gateway-list">
                        <div *ngFor="let dev of gatewayDevices" class="dev-item p-3 mb-2 border rounded shadow-sm d-flex justify-content-between align-items-center bg-white">
                            <div class="d-flex flex-column">
                                <span class="small font-monospace mb-1">{{ dev.UUID || dev.devIndex }}</span>
                                <span class="text-xs badge bg-info-subtle text-info w-fit">{{ dev.deviceModel || 'Hikvision Terminal' }}</span>
                            </div>
                            <button mat-mini-fab color="primary" (click)="registerDevice(dev)" matTooltip="Registrar no Sistema">
                                <mat-icon>add</mat-icon>
                            </button>
                        </div>
                    </div>

                    <div *ngIf="gatewayDevices.length === 0" class="text-center p-4">
                        <mat-icon class="text-muted mb-2">find_in_page</mat-icon>
                        <p class="small text-muted mb-3">Nenhum terminal pendente encontrado no cache.</p>
                        <button mat-stroked-button color="primary" (click)="addManualDevice()">
                            <mat-icon>add</mat-icon> Adicionar Manualmente
                        </button>
                    </div>
                </mat-card-content>
            </mat-card>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .premium-card { border-radius: 16px; overflow: hidden; border: 1px solid rgba(0,0,0,0.05); transition: transform 0.2s; }
    .glass { background: rgba(255,255,255,0.7); backdrop-filter: blur(8px); }
    .large-icon { font-size: 64px; width: 64px; height: 64px; opacity: 0.3; }
    .text-xs { font-size: 0.7rem; }
    .w-fit { width: fit-content; }
    .dev-item:hover { border-color: var(--mat-primary-button-state-layer-color) !important; }
    .font-monospace { letter-spacing: -0.5px; }
  `]
})
export class DevicesComponent implements OnInit {
  devices: any[] = [];
  gatewayDevices: any[] = [];
  displayedColumns = ['name', 'status', 'actions'];

  constructor(private api: ApiService, private snack: MatSnackBar) {}

  ngOnInit(): void {
    this.loadDevices();
    this.loadGatewayDevices();
  }

  loadDevices() {
    this.api.get<any[]>('/devices/').subscribe(res => this.devices = res);
  }

  loadGatewayDevices() {
    this.api.get<any>('/devices/gateway/connected-devices').subscribe({
      next: (res) => {
        if (res.data && res.data.DeviceList && res.data.DeviceList.Device) {
            let list = Array.isArray(res.data.DeviceList.Device) ? res.data.DeviceList.Device : [res.data.DeviceList.Device];
            // Filter out already registered
            this.gatewayDevices = list.filter((g: any) => !this.devices.some((d: any) => d.dev_index === g.UUID));
        } else {
            this.gatewayDevices = [];
        }
      },
      error: () => this.snack.open('Erro ao conectar com o Gateway', 'OK', { duration: 3000 })
    });
  }

  registerDevice(dev: any) {
    const name = prompt('Nome para este dispositivo?', 'Novo Aparelho');
    if (!name) return;

    this.api.post('/devices/', {
      name: name,
      dev_index: dev.UUID,
      is_active: true
    }).subscribe({
      next: () => {
        this.snack.open('Dispositivo registrado!', 'OK', { duration: 3000 });
        this.loadDevices();
        this.loadGatewayDevices();
      },
      error: (e: any) => this.snack.open('Erro ao registrar: ' + (e.error?.detail || e.message), 'OK', { duration: 3000 })
    });
  }

  addManualDevice() {
    const devIndex = prompt('Informe o UUID (devIndex) do terminal, conforme exibido nos logs:', '');
    if (!devIndex) return;
    this.registerDevice({ UUID: devIndex, deviceModel: 'Terminal Hikvision' });
  }

  deleteDevice(id: string) {
    if (!confirm('Deseja realmente remover este dispositivo?')) return;
    this.api.delete(`/devices/${id}`).subscribe({
      next: () => {
        this.snack.open('Dispositivo removido.', 'OK', { duration: 2000 });
        this.loadDevices();
      }
    });
  }
}
