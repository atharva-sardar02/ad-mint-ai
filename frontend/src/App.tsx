/**
 * Main App component with React Router setup.
 */
import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Navbar } from "./components/layout/Navbar";
import { Login } from "./routes/Auth/Login";
import { Register } from "./routes/Auth/Register";
import { Dashboard } from "./routes/Dashboard";
import { Gallery } from "./routes/Gallery";
import { Profile } from "./routes/Profile";
import "./App.css";

/**
 * App component.
 */
function App() {
  const loadUser = useAuthStore((state) => state.loadUser);
  const [isLoading, setIsLoading] = React.useState(true);

  // Load user on app initialization
  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      try {
        await loadUser();
      } finally {
        setIsLoading(false);
      }
    };
    initializeAuth();
  }, [loadUser]);

  // Show loading state during token validation
  if (isLoading) {
    return (
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/gallery"
            element={
              <ProtectedRoute>
                <Gallery />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
