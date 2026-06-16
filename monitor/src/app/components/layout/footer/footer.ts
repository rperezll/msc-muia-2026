import { Component } from '@angular/core';

@Component({
  selector: 'app-footer',
  template: `
    <footer
      class="flex items-center justify-between px-6 h-10 border-t border-border-default bg-surface-raised text-sm text-neutral-300"
    >
      <span class="text-neutral-400">© Roberto Pérez Llanos | GPL v3</span>
      <span class="font-mono text-neutral-400">msc-muia-2026</span>
    </footer>
  `,
})
export class FooterComponent {}
