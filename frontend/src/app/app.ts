import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import Offcanvas from 'bootstrap/js/dist/offcanvas';
import { TemaService } from './core/services/tema.service';

@Component({
  selector: 'lnf-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
})
export class App implements AfterViewInit, OnDestroy {
  readonly tema = inject(TemaService);
  readonly menuAberto = signal(false);
  private readonly painel = viewChild.required<ElementRef<HTMLElement>>('menu');
  private instancia?: Offcanvas;
  private readonly aoAbrir = () => this.menuAberto.set(true);
  private readonly aoFechar = () => this.menuAberto.set(false);

  constructor() {
    inject(Router)
      .events.pipe(takeUntilDestroyed())
      .subscribe((evento) => {
        if (evento instanceof NavigationEnd) this.fecharMenu();
      });
  }

  ngAfterViewInit() {
    const elemento = this.painel().nativeElement;
    this.instancia = Offcanvas.getOrCreateInstance(elemento);
    elemento.addEventListener('show.bs.offcanvas', this.aoAbrir);
    elemento.addEventListener('hide.bs.offcanvas', this.aoFechar);
  }

  fecharMenu() {
    this.instancia?.hide();
  }

  ngOnDestroy() {
    const elemento = this.painel().nativeElement;
    elemento.removeEventListener('show.bs.offcanvas', this.aoAbrir);
    elemento.removeEventListener('hide.bs.offcanvas', this.aoFechar);
    const instancia = this.instancia;
    if (elemento.hasAttribute('aria-modal')) {
      elemento.addEventListener('hidden.bs.offcanvas', () => instancia?.dispose(), { once: true });
      instancia?.hide();
    } else {
      instancia?.dispose();
    }
  }
}
