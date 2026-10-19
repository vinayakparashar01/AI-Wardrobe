import React, { useState } from "react";
import {
  Bell,
  Bookmark,
  Heart,
  Home as HomeIcon,
  LogOut,
  Menu,
  Shirt,
  Sparkles,
  X,
} from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { SearchInput } from "./UI";

const primaryNavItems = [
  { to: "/", label: "Home", icon: HomeIcon, end: true },
  { to: "/wardrobe", label: "Wardrobe", icon: Shirt, end: false },
  { to: "/outfits", label: "Outfits", icon: Sparkles, end: false },
];

function AppSidebar({ mobileOpen, onCloseMobile }) {
  return (
    <aside className={`page-sidebar ${mobileOpen ? "mobile-open" : ""}`}>
      {/* Mobile close button */}
      <div className="sidebar-mobile-header">
        <span className="brand-mark-small">A</span>
        <strong>AI Wardrobe</strong>
        <button
          type="button"
          className="sidebar-close-btn"
          onClick={onCloseMobile}
          aria-label="Close menu"
        >
          <X size={18} />
        </button>
      </div>


      {/* Main navigation */}
      <div className="sidebar-nav-group">
        {primaryNavItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `sidebar-pill-link ${isActive ? "active" : ""}`
            }
            onClick={onCloseMobile}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>

      {/* AI Stylist Spotlight */}
      <div className="sidebar-nav-group">
        <div className="sidebar-group-label">AI STYLIST</div>
        <NavLink
          to="/stylist"
          className={({ isActive }) =>
            `sidebar-pill-link active-pink ${isActive ? "active" : ""}`
          }
          onClick={onCloseMobile}
        >
          <Sparkles size={18} />
          <span>AI Stylist</span>
        </NavLink>
      </div>


      {/* Your Closet shortcuts */}
      <div className="sidebar-nav-group">
        <div className="sidebar-group-label">YOUR CLOSET</div>
        <Link
          to="/wardrobe?sort=recent"
          className="sidebar-pill-link"
          onClick={onCloseMobile}
        >
          <Shirt size={18} />
          <span>Recently added</span>
        </Link>
        <Link
          to="/outfits?favorite=1"
          className="sidebar-pill-link"
          onClick={onCloseMobile}
        >
          <Bookmark size={18} />
          <span>Saved looks</span>
        </Link>
        <Link
          to="/outfits/new"
          className="sidebar-pill-link"
          onClick={onCloseMobile}
        >
          <Sparkles size={18} />
          <span>Create outfit</span>
        </Link>
      </div>
    </aside>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/wardrobe?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div className="app-shell">
      {/* Top Header */}
      <header className="top-header">
        <div className="brand" onClick={() => navigate("/")}>
          <span className="brand-mark">A</span>
          <span>AI Wardrobe</span>
        </div>

        <form className="header-search-form" onSubmit={handleSearchSubmit}>
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search your wardrobe…"
            onClear={() => setSearchQuery("")}
            size="normal"
          />
        </form>

        <div className="header-actions">

          <button
            className="icon-button"
            aria-label="Saved outfits"
            onClick={() => navigate("/outfits?favorite=1")}
            title="Saved Favorite Outfits"
          >
            <Heart size={19} />
          </button>

          <button
            className="icon-button"
            aria-label="Notifications"
            onClick={() => alert("All notifications caught up!")}
            title="Notifications"
          >
            <Bell size={19} />
          </button>

          <button
            className="profile-chip"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="User profile menu"
          >
            <span className="avatar">
              {(user?.name || user?.email || "U")[0].toUpperCase()}
            </span>
            <span className="profile-name">{user?.name || "Profile"}</span>
          </button>

          {menuOpen && (
            <div className="profile-menu">
              <div className="menu-user">{user?.email}</div>
              <button
                onClick={() => {
                  setMenuOpen(false);
                  logout();
                }}
              >
                <LogOut size={16} /> Log out
              </button>
            </div>
          )}

          <button
            className="mobile-menu"
            onClick={() => setMobileSidebarOpen(true)}
            aria-label="Open mobile menu"
          >
            <Menu size={22} />
          </button>
        </div>
      </header>

      {/* Main App Frame */}
      <div className="page-frame">
        <AppSidebar
          mobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
        />
        <main className="page-content">
          <Outlet />
        </main>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="mobile-nav">
        {primaryNavItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}>
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
        <NavLink to="/stylist">
          <Sparkles size={18} />
          <span>Stylist</span>
        </NavLink>
      </nav>
    </div>
  );
}
