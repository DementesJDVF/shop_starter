import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

const Register = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        password_confirm: '',
        role: 'CLIENTE'
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const validate = () => {
        let tempErrors = {};
        if (!formData.username) tempErrors.username = "Usuario requerido";
        if (!formData.email) tempErrors.email = "Email requerido";
        if (!/\S+@\S+\.\S+/.test(formData.email)) tempErrors.email = "Email inválido";
        if (formData.password.length < 8) tempErrors.password = "Mínimo 8 caracteres";
        if (formData.password !== formData.password_confirm) {
            tempErrors.password_confirm = "Las contraseñas no coinciden";
        }
        setErrors(tempErrors);
        return Object.keys(tempErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validate()) return;

        setLoading(true);
        try {
            await api.post('/auth/register/', formData);
            alert('Registro exitoso. Por favor inicia sesión.');
            navigate('/login');
        } catch (error) {
            if (error.response) {
                setErrors(error.response.data);
            } else {
                setErrors({ general: 'Error de conexión con el servidor' });
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <h2>Registro</h2>
            {errors.general && <div className="error-message">{errors.general}</div>}
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <input
                        type="text"
                        name="username"
                        placeholder="Usuario"
                        value={formData.username}
                        onChange={handleChange}
                    />
                    {errors.username && <span className="error">{errors.username}</span>}
                </div>
                
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
                        placeholder="Contraseña (mín. 8 caracteres)"
                        value={formData.password}
                        onChange={handleChange}
                    />
                    {errors.password && <span className="error">{errors.password}</span>}
                </div>
                
                <div className="form-group">
                    <input
                        type="password"
                        name="password_confirm"
                        placeholder="Confirmar contraseña"
                        value={formData.password_confirm}
                        onChange={handleChange}
                    />
                    {errors.password_confirm && <span className="error">{errors.password_confirm}</span>}
                </div>
                
                <div className="form-group">
                    <label>Rol:</label>
                    <select name="role" value={formData.role} onChange={handleChange}>
                        <option value="CLIENTE">Cliente</option>
                        <option value="VENDEDOR">Vendedor</option>
                        <option value="ADMIN">Admin</option>
                    </select>
                </div>
                
                <button type="submit" disabled={loading}>
                    {loading ? 'Registrando...' : 'Registrarse'}
                </button>
            </form>
            <p>¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link></p>
        </div>
    );
};

export default Register;
