/// <reference types="vite/client" />



declare module 'react-dom/client' {

  export * from 'react-dom';

  export interface Root {

    render(children: React.ReactNode): void;

    unmount(): void;

  }

  export function createRoot(container: Element | DocumentFragment): Root;

  export function hydrateRoot(container: Element | DocumentFragment, children: React.ReactNode): Root;

}



interface ImportMetaEnv {

  readonly VITE_API_BASE_URL: string;

  readonly VITE_API_URL: string;

}



interface ImportMeta {

  readonly env: ImportMetaEnv;

}
