import React from 'react';
import { TopBar } from './TopBar';
import { SideNav } from './SideNav';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-background">
      <TopBar />
      <div className="flex">
        <SideNav />
        <main className="flex-1 p-6 ml-64">
          {children}
        </main>
      </div>
    </div>
  );
};
