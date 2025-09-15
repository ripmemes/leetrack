import React from 'react' ; 
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './frontend/components/Navbar.js';
import Home from './frontend/components/Home.js';
import {LoginForm, RegisterForm} from './frontend/components/Form';
import './App.css';


function App() {
    return ( <>
        <Router>
            <Navbar />
            <Routes>
            <Route path='/' element = { <Home/>} />
            <Route path='/login' element = { <LoginForm/>} />
            <Route path='/register' element = { <RegisterForm/>} />
            </Routes>
        </Router>
    </>
    );
}

export default App;

