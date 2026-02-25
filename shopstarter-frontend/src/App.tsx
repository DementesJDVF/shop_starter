import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Register from './components/Register';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';

const AdminDashboard = () => <h1>Dashboard Admin</h1>;
const VendorDashboard = () => <h1>Dashboard Vendedor</h1>;
const CustomerDashboard = () => <h1>Dashboard Cliente</h1>;
const Unauthorized = () => <h1>No autorizado</h1>;

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/register" element={<Register />} />
                <Route path="/login" element={<Login />} />
                
                <Route path="/admin/dashboard" element={
                    <ProtectedRoute allowedRoles={['ADMIN']}>
                        <AdminDashboard />
                    </ProtectedRoute>
                } />
                
                <Route path="/vendedor/dashboard" element={
                    <ProtectedRoute allowedRoles={['VENDEDOR', 'ADMIN']}>
                        <VendorDashboard />
                    </ProtectedRoute>
                } />
                
                <Route path="/cliente/dashboard" element={
                    <ProtectedRoute allowedRoles={['CLIENTE', 'VENDEDOR', 'ADMIN']}>
                        <CustomerDashboard />
                    </ProtectedRoute>
                } />
                
                <Route path="/unauthorized" element={<Unauthorized />} />
                <Route path="/" element={<Navigate to="/login" />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
