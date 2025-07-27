import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import './index.css';
import App from './App.jsx';
import SavedCaptions from './SavedCaptions.jsx';
import Layout from './Layout.jsx';
import { Toaster } from "@/components/ui/toaster";
import { AuthProvider } from './AuthContext.jsx';
import LoginPage from './LoginPage.jsx'; // Import LoginPage
import RegisterPage from './RegisterPage.jsx'; // Import RegisterPage
import ProtectedRoute from './ProtectedRoute.jsx'; // Import ProtectedRoute

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      {
        path: "/",
        element: <ProtectedRoute><App /></ProtectedRoute>,
      },
      {
        path: "/saved",
        element: <ProtectedRoute><SavedCaptions /></ProtectedRoute>,
      },
    ],
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    element: <RegisterPage />,
  },
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
      <Toaster />
    </AuthProvider>
  </StrictMode>,
);