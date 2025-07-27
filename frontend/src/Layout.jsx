import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Globe, Folder, LogOut, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from './AuthContext';
import { Button } from "@/components/ui/button";

function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex flex-col h-screen bg-[#0f0f0f] text-white">
      <main className="flex-1 pb-[4rem] pt-[8rem] px-[20rem] overflow-y-auto no-scrollbar">
        <Outlet />
      </main>
      <aside className="w-full flex items-center space-x-6 mx-auto justify-center py-6 bg-gray-900 border-t border-gray-700">
        {user ? (
          <>
            <NavLink to="/" className={({ isActive }) => `p-2 rounded-lg ${isActive ? 'bg-gray-700' : ''}`}>
              <Globe className="h-6 w-6" />
            </NavLink>
            <NavLink to="/saved" className={({ isActive }) => `p-2 rounded-lg ${isActive ? 'bg-gray-700' : ''}`}>
              <Folder className="h-6 w-6" />
            </NavLink>
            <Button variant="ghost" size="icon" onClick={handleLogout} className="p-2 rounded-lg">
              <LogOut className="h-6 w-6" />
            </Button>
          </>
        ) : (
          <>
            <NavLink to="/login" className={({ isActive }) => `p-2 rounded-lg ${isActive ? 'bg-gray-700' : ''}`}>
              <LogIn className="h-6 w-6" />
            </NavLink>
            <NavLink to="/register" className={({ isActive }) => `p-2 rounded-lg ${isActive ? 'bg-gray-700' : ''}`}>
              <UserPlus className="h-6 w-6" />
            </NavLink>
          </>
        )}
      </aside>
    </div>
  );
}

export default Layout;
