import React, {useState , useEffect} from 'react' ; 
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './frontend/components/Navbar.js';
import Home from './frontend/components/Home.js';
import {LoginForm, RegisterForm} from './frontend/components/Form';
import './App.css';


function App() {
    const [logged, setLogged] = useState(false)
    useEffect(()=> {
        const token = localStorage.getItem("token")
        if (token) setLogged(true)
    },[])

    return ( <>
        <Router>
            <Navbar logged={logged} setLogged={setLogged} />
            <Routes>
            <Route path='/' element = { <Home logged={logged} setLogged={setLogged}/>} />
            <Route path='/login' element = { <LoginForm setLogged={setLogged}/>} />
            <Route path='/register' element = { <RegisterForm/>} />
            </Routes>
        </Router>
    </>
    );
}

export default App;

