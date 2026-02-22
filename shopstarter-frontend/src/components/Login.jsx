import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

const Login = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({ email: '', password: '' });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        try {
            const response = await api.post('/auth/login/', formData);
            
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
            
            const userRole = response.data.user.role;
            switch(userRole) {
                case 'ADMIN':
                    navigate('/admin/dashboard');
                    break;
                case 'VENDOR':
                    navigate('/vendor/dashboard');
                    break;
                case 'CUSTOMER':
                    navigate('/customer/dashboard');
                    break;
                default:
                    navigate('/');
            }
        } catch (error) {
            if (error.response) {
                setErrors(error.response.data);
            } else {
                setErrors({ general: 'Error de conexión' });
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <h2>Iniciar Sesión</h2>
            {errors.general && <div className="error-message">{errors.general}</div>}
            {errors.non_field_errors && <div className="error-message">{errors.non_field_errors}</div>}
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <input
                        type="email"
                        name="email"
                        placeholder="Email"
                        value={formData.email}
                        onChange={handleChange}
                    />
                    {errors.email && <span className="error">{errors.email}</span>}
                </div>
                
                <div className="form-group">
                    <input
                        type="password"
                        name="password"
                        placeholder="Contraseña"
                        value={formData.password}
                        onChange={handleChange}
                    />
                    {errors.password && <span className="error">{errors.password}</span>}
                </div>
                
                <button type="submit" disabled={loading}>
                    {loading ? 'Iniciando...' : 'Iniciar Sesión'}
                </button>
            </form>
            <p>¿No tienes cuenta? <Link to="/register">Regístrate</Link></p>
        </div>
    );
};

export default Login;