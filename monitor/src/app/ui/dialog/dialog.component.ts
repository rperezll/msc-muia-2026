import type { OnInit } from '@angular/core';
import type { DialogWithComponent, DialogActionVariant, DialogActionSize } from './dialog-options';
import { Component, inject, Injector, ViewChild, ViewContainerRef } from '@angular/core';
import { NgComponentOutlet } from '@angular/common';
import { DialogRef, DIALOG_DATA } from '@angular/cdk/dialog';
import { LucideX } from '@lucide/angular';
import { cn } from '../../utils/cn';

@Component({
  selector: 'app-dialog',
  imports: [NgComponentOutlet, LucideX],
  styles: [
    `
      :host {
        display: contents;
      }

      .dialog-overlay {
        animation: overlay-enter 150ms ease-out both;
      }
      .dialog-panel {
        animation: panel-enter 200ms cubic-bezier(0.16, 1, 0.3, 1) both;
      }

      @keyframes overlay-enter {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }

      @keyframes panel-enter {
        from {
          opacity: 0;
          transform: translate(-50%, -48%) scale(0.97);
        }
        to {
          opacity: 1;
          transform: translate(-50%, -50%) scale(1);
        }
      }
    `,
  ],
  template: `
    <div
      class="dialog-overlay"
      tabindex="0"
      role="presentation"
      (click)="onOverlayClick()"
      (keydown.enter)="onOverlayClick()"
      (keydown.escape)="onOverlayClick()"
      [class]="
        cn(
          'fixed inset-0 z-50 bg-surface-base/70 backdrop-blur-sm',
          dialogOptions.classNames?.overlay
        )
      "
    ></div>

    <div
      class="dialog-panel"
      role="dialog"
      aria-modal="true"
      [attr.aria-labelledby]="dialogOptions.title ? titleId : undefined"
      [attr.aria-describedby]="dialogOptions.description ? descId : undefined"
      tabindex="-1"
      [class]="
        cn(
          'fixed left-[50%] top-[50%] z-50',
          'w-[calc(100%-2rem)] max-w-lg',
          'rounded-xl border border-border-default bg-surface-raised shadow-2xl',
          'grid gap-0',
          dialogOptions.classNames?.container
        )
      "
    >
      @if (dialogOptions.classNames?.showHeader !== false) {
        <header class="flex items-start justify-between gap-4 px-6 pt-6">
          <div class="flex flex-col gap-1">
            @if (dialogOptions.title) {
              <h2 [id]="titleId" class="text-base font-semibold tracking-tight text-neutral-100">
                {{ dialogOptions.title }}
              </h2>
            }
            @if (dialogOptions.description) {
              <p [id]="descId" class="text-sm text-neutral-300 leading-relaxed">
                {{ dialogOptions.description }}
              </p>
            }
          </div>

          @if (dialogOptions.closeBtn) {
            <button
              type="button"
              title="Close"
              aria-label="Close dialog"
              (click)="dialogRef.close()"
              class="shrink-0 rounded-md p-1 text-neutral-300 transition-colors hover:bg-surface-overlay hover:text-neutral-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <svg lucideX [size]="16" [strokeWidth]="2"></svg>
            </button>
          }
        </header>
      }

      @if (dialogOptions.classNames?.showDivider) {
        <div class="mx-6 mt-4 border-t border-dashed border-border-default"></div>
      }

      <main
        [class]="
          cn(
            'overflow-y-auto px-6',
            dialogOptions.classNames?.showHeader !== false ? 'pt-4' : 'pt-6',
            dialogOptions.actions?.length ? 'pb-4' : 'pb-6',
            dialogOptions.classNames?.content
          )
        "
      >
        <ng-container #container></ng-container>
      </main>

      @if (dialogOptions.actions?.length) {
        <footer class="flex justify-end gap-2 border-t border-border-default px-6 py-4">
          @for (action of dialogOptions.actions; track action.label) {
            <button
              type="button"
              (click)="action.onClick()"
              [disabled]="action.disabled || (action.isLoading && action.isLoading())"
              [class]="
                cn(actionClass(action.variant, action.size), action.classNames, 'cursor-pointer')
              "
            >
              @if (action.isLoading && action.isLoading()) {
                <span
                  class="mr-1.5 inline-block size-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
                  aria-hidden="true"
                ></span>
              } @else if (action.icon) {
                <ng-container [ngComponentOutlet]="action.icon" />
              }
              <span>{{ action.label }}</span>
            </button>
          }
        </footer>
      }
    </div>
  `,
})
export class DialogComponent implements OnInit {
  @ViewChild('container', { read: ViewContainerRef, static: true })
  container!: ViewContainerRef;

  protected readonly cn = cn;

  protected readonly titleId = `dialog-title-${crypto.randomUUID().slice(0, 8)}`;
  protected readonly descId = `dialog-desc-${crypto.randomUUID().slice(0, 8)}`;

  readonly dialogOptions: DialogWithComponent = inject(DIALOG_DATA);
  readonly dialogRef = inject(DialogRef<DialogComponent>);
  private readonly injector = inject(Injector);

  ngOnInit(): void {
    if (!this.dialogOptions.component) return;

    const componentRef = this.container.createComponent(this.dialogOptions.component, {
      injector: this.injector,
    });

    if (this.dialogOptions.data) {
      for (const [key, value] of Object.entries(this.dialogOptions.data)) {
        componentRef.setInput(key, value);
      }
    }
  }

  protected onOverlayClick(): void {
    if (!this.dialogOptions.disableCloseOverlay) {
      this.dialogRef.close();
    }
  }

  protected actionClass(
    variant: DialogActionVariant = 'default',
    size: DialogActionSize = 'default',
  ): string {
    const base =
      'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors ' +
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ' +
      'disabled:pointer-events-none disabled:opacity-40';

    const variants: Record<DialogActionVariant, string> = {
      default: 'bg-accent text-surface-base hover:bg-accent/85',
      outline:
        'border border-border-default text-neutral-200 hover:bg-surface-overlay hover:text-neutral-100',
      ghost: 'text-neutral-200 hover:bg-surface-overlay hover:text-neutral-100',
      destructive: 'bg-status-error text-white hover:bg-status-error/85',
    };

    const sizes: Record<DialogActionSize, string> = {
      sm: 'h-8 px-3 text-xs',
      default: 'h-9 px-4 text-sm',
      lg: 'h-10 px-5 text-base',
    };

    return cn(base, variants[variant], sizes[size]);
  }
}
