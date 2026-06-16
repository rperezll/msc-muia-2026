import type { Signal, Type } from '@angular/core';

export type DialogActionVariant = 'default' | 'outline' | 'ghost' | 'destructive';
export type DialogActionSize = 'sm' | 'default' | 'lg';

export interface DialogAction {
  label: string;
  onClick: () => void;
  icon?: Type<unknown>;
  disabled?: boolean;
  isLoading?: Signal<boolean>;
  variant?: DialogActionVariant;
  size?: DialogActionSize;
  classNames?: string;
}

export interface DialogClassNames {
  overlay?: string;
  container?: string;
  content?: string;
  showDivider?: boolean;
  showHeader?: boolean;
}

export interface DialogOptions {
  closeBtn?: boolean;
  title?: string;
  description?: string;
  actions?: DialogAction[];
  classNames?: DialogClassNames;
  disableCloseOverlay?: boolean;
  data?: Record<string, unknown>;
}

export interface DialogWithComponent extends DialogOptions {
  component: Type<unknown>;
}
