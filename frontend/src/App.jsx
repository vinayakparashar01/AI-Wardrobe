import React from "react";
import {Navigate,Route,Routes} from "react-router-dom";
import {AuthProvider,useAuth} from "./auth";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import Wardrobe from "./pages/Wardrobe";
import ClothingDetails from "./pages/ClothingDetails";
import Outfits from "./pages/Outfits";
import CreateOutfit from "./pages/CreateOutfit";
import OutfitDetails from "./pages/OutfitDetails";
function Protected({children}){const{user,loading}=useAuth();if(loading)return <div className="app-loading">Loading your studio…</div>;return user?children:<Navigate to="/login" replace/>}
function AppRoutes(){return <Routes><Route path="/login" element={<Login/>}/><Route path="/register" element={<Register/>}/><Route path="*" element={<Protected><Layout/></Protected>}><Route index element={<Home/>}/><Route path="wardrobe" element={<Wardrobe/>}/><Route path="wardrobe/:id" element={<ClothingDetails/>}/><Route path="outfits" element={<Outfits/>}/><Route path="outfits/new" element={<CreateOutfit/>}/><Route path="outfits/:id" element={<OutfitDetails/>}/></Route></Routes>}export default function App(){return <AuthProvider><AppRoutes/></AuthProvider>}
