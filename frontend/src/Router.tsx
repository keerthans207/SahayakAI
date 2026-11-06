import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { MainLayout } from './components/layout/MainLayout';

import { DashboardPage } from './pages/DashboardPage';

import { AssistantPage } from './pages/AssistantPage';

import { SchemesPage } from './pages/SchemesPage';

import { SchemeDetailsPage } from './pages/SchemeDetailsPage';

import { EligibilityPage } from './pages/EligibilityPage';

import { DocumentsPage } from './pages/DocumentsPage';

import { ApplicationsPage } from './pages/ApplicationsPage';

import { ApplicationDetailsPage } from './pages/ApplicationDetailsPage';

import { ProfilePage } from './pages/ProfilePage';

import { SettingsPage } from './pages/SettingsPage';



export const Router = () => {

  return (

    <BrowserRouter>

      <Routes>

        {/* Default route - Dashboard */}

        <Route

          path="/"

          element={

            <MainLayout>

              <DashboardPage />

            </MainLayout>

          }

        />



        <Route

          path="/dashboard"

          element={

            <MainLayout>

              <DashboardPage />

            </MainLayout>

          }

        />



        <Route

          path="/assistant"

          element={

            <MainLayout>

              <AssistantPage />

            </MainLayout>

          }

        />



        <Route

          path="/schemes"

          element={

            <MainLayout>

              <SchemesPage />

            </MainLayout>

          }

        />



        <Route

          path="/schemes/:id"

          element={

            <MainLayout>

              <SchemeDetailsPage />

            </MainLayout>

          }

        />



        <Route

          path="/eligibility"

          element={

            <MainLayout>

              <EligibilityPage />

            </MainLayout>

          }

        />



        <Route

          path="/documents"

          element={

            <MainLayout>

              <DocumentsPage />

            </MainLayout>

          }

        />



        <Route

          path="/applications"

          element={

            <MainLayout>

              <ApplicationsPage />

            </MainLayout>

          }

        />



        <Route

          path="/applications/:id"

          element={

            <MainLayout>

              <ApplicationDetailsPage />

            </MainLayout>

          }

        />



        <Route

          path="/profile"

          element={

            <MainLayout>

              <ProfilePage />

            </MainLayout>

          }

        />



        <Route

          path="/settings"

          element={

            <MainLayout>

              <SettingsPage />

            </MainLayout>

          }

        />



        {/* Fallback */}

        <Route path="*" element={<Navigate to="/" replace />} />

      </Routes>

    </BrowserRouter>

  );

};
