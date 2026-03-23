import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { animate, query, style, transition, trigger, group } from '@angular/animations';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div [@routeAnimation]="getAnimationData(routerOutlet)">
      <router-outlet #routerOutlet="outlet"></router-outlet>
    </div>
  `,
  styles: [':host { display: block; height: 100%; }'],
  animations: [
    trigger('routeAnimation', [
      transition('* <=> *', [
        query(':enter', [
          style({ position: 'absolute', top: 0, left: 0, width: '100%', opacity: 0 })
        ], { optional: true }),
        query(':leave', [
          style({ position: 'absolute', top: 0, left: 0, width: '100%', opacity: 1 }),
        ], { optional: true }),
        group([
          query(':leave', [
            animate('0.3s ease-out', style({ opacity: 0 }))
          ], { optional: true }),
          query(':enter', [
            animate('0.4s ease-out', style({ opacity: 1 }))
          ], { optional: true })
        ])
      ])
    ])
  ]
})
export class App {
  getAnimationData(routerOutlet: RouterOutlet) {
    return routerOutlet.activatedRouteData['animation'];
  }
}
