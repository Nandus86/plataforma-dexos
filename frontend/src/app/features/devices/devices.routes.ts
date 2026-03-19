import { Routes } from '@angular/router';

export const DEVICE_ROUTES: Routes = [
    {
        path: '',
        loadComponent: () => import('./devices.component').then(m => m.DevicesComponent),
    },
    {
        path: 'sync',
        loadComponent: () => import('./sync/sync.component').then(m => m.SyncComponent),
    },
    {
        path: 'migrate',
        loadComponent: () => import('./migrate/migrate.component').then(m => m.MigrateComponent),
    }
];
