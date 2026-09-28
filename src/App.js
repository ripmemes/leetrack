import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './frontend/components/Navbar.js';
import Home from './frontend/components/Home.js';
import DashboardPage from './frontend/components/dashboard/DashboardPage.js';
import { LoginForm, RegisterForm } from './frontend/components/Form';
import './App.css';


function App() {
    const [logged, setLogged] = useState(false)
    const [userId, setUserId] = useState(null)
    useEffect(() => {
        const token = localStorage.getItem("token")
        if (token) setLogged(true)
    }, [])

    return (<>
        <Router>
            <Navbar logged={logged} setLogged={setLogged} />
            <Routes>
                <Route path='/' element={<Home logged={logged} setLogged={setLogged} userId={userId} />} />
                <Route path="/dashboard" element={<DashboardPage logged={logged} />} />
                <Route path='/login' element={<LoginForm setLogged={setLogged} setUserId={setUserId} />} />
                <Route path='/register' element={<RegisterForm />} />
            </Routes>
        </Router>
    </>
    );
}

export default App;

