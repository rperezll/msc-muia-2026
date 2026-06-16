import type { EnvironmentProviders, Type } from '@angular/core';
import type { DialogRef } from '@angular/cdk/dialog';
import type { DialogActionVariant, DialogOptions } from './dialog-options';
import {
  Injectable,
  inject,
  Injector,
  makeEnvironmentProviders,
  importProvidersFrom,
} from '@angular/core';
import { Dialog, DialogModule } from '@angular/cdk/dialog';
import { Overlay } from '@angular/cdk/overlay';
import { DialogComponent } from './dialog.component';

export interface ConfirmOptions {
  title: string;
  description?: string;
  confirmLabel?: string;
  confirmVariant?: DialogActionVariant;
  cancelLabel?: string;
}

@Injectable({ providedIn: 'root' })
export class DialogService {
  private readonly dialog = inject(Dialog);
  private readonly overlay = inject(Overlay);
  private readonly injector = inject(Injector);

  open<Result = unknown>(component: Type<unknown>, options: DialogOptions = {}): DialogRef<Result> {
    return this.dialog.open<Result>(DialogComponent, {
      injector: this.injector,
      positionStrategy: this.overlay.position().global(),
      hasBackdrop: false,
      data: { component, ...options } satisfies Record<string, unknown>,
    });
  }

  confirm(options: ConfirmOptions): DialogRef<boolean> {
    const ref: DialogRef<boolean> = this.dialog.open<boolean>(DialogComponent, {
      injector: this.injector,
      positionStrategy: this.overlay.position().global(),
      hasBackdrop: false,
      data: {
        title: options.title,
        description: options.description,
        closeBtn: false,
        disableCloseOverlay: true,
        actions: [
          {
            label: options.cancelLabel ?? 'Cancel',
            variant: 'ghost' as DialogActionVariant,
            onClick: () => ref.close(false),
          },
          {
            label: options.confirmLabel ?? 'Confirm',
            variant: (options.confirmVariant ?? 'destructive') as DialogActionVariant,
            onClick: () => ref.close(true),
          },
        ],
      } satisfies DialogOptions,
    });

    return ref;
  }
}

export function provideDialog(): EnvironmentProviders {
  return makeEnvironmentProviders([importProvidersFrom(DialogModule), DialogService]);
}
