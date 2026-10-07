declare module 'bootstrap/js/dist/offcanvas' {
  export default class Offcanvas {
    static getOrCreateInstance(element: HTMLElement): Offcanvas;
    hide(): void;
    dispose(): void;
  }
}
