import { Component, ElementRef, OnDestroy, ViewChild, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { BrowserQRCodeReader, IScannerControls } from '@zxing/browser';
import { finalize } from 'rxjs';

import { ApiService } from '../../core/api/api.service';
import { mensagemErro } from '../../core/utils/erro-api';

@Component({
  selector: 'lnf-leitura-qrcode',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './leitura-qrcode.html',
  styleUrl: './leitura-qrcode.scss',
})
export class LeituraQrcode implements OnDestroy {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly leitor = new BrowserQRCodeReader();
  private controles?: IScannerControls;
  private leituraEmAndamento = false;

  @ViewChild('video') private video?: ElementRef<HTMLVideoElement>;

  readonly url = new FormControl('', { nonNullable: true, validators: [Validators.required] });
  readonly cameraAtiva = signal(false);
  readonly enviando = signal(false);
  readonly erro = signal<string | null>(null);
  readonly avisoHttps = !window.isSecureContext && window.location.hostname !== 'localhost';

  async iniciarCamera(): Promise<void> {
    this.erro.set(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      this.erro.set('A câmera não está disponível neste navegador. Use o campo para colar o link.');
      return;
    }
    if (!this.video) return;

    try {
      this.pararCamera();
      this.cameraAtiva.set(true);
      this.controles = await this.leitor.decodeFromVideoDevice(
        undefined,
        this.video.nativeElement,
        (resultado) => {
          if (!resultado || this.leituraEmAndamento) return;
          this.leituraEmAndamento = true;
          this.url.setValue(resultado.getText());
          this.pararCamera();
          this.enviar();
        },
      );
    } catch (erro) {
      this.cameraAtiva.set(false);
      this.erro.set(this.mensagemErroCamera(erro));
    }
  }

  pararCamera(): void {
    this.controles?.stop();
    this.controles = undefined;
    this.cameraAtiva.set(false);
  }

  enviar(): void {
    this.url.markAsTouched();
    if (this.url.invalid || this.enviando()) return;

    this.enviando.set(true);
    this.erro.set(null);
    this.api
      .criarLeitura(this.url.value.trim())
      .pipe(
        finalize(() => {
          this.enviando.set(false);
          this.leituraEmAndamento = false;
        }),
      )
      .subscribe({
        next: (leitura) => {
          if (!leitura.nota) {
            this.erro.set(
              leitura.erro_consulta ?? 'A leitura foi registrada, mas a nota não foi encontrada.',
            );
            return;
          }
          void this.router.navigate(['/notas', leitura.nota.chave, 'revisao']);
        },
        error: (erro) => this.erro.set(mensagemErro(erro)),
      });
  }

  ngOnDestroy(): void {
    this.pararCamera();
  }

  private mensagemErroCamera(erro: unknown): string {
    if (erro instanceof DOMException && erro.name === 'NotAllowedError') {
      return 'O acesso à câmera foi negado. Autorize a câmera no navegador e tente novamente.';
    }
    return 'Não foi possível iniciar a câmera. Verifique as permissões ou cole o link abaixo.';
  }
}
