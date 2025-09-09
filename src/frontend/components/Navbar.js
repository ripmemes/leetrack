import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from './Button';
import './Navbar.css'

function Navbar() {
    const [click, setClick] = useState(false);
    const [button, setButton] = useState(true);

    const handleClick = () => setClick(!click)
    const closeMobileMenu = () => setClick(false)

    const showButton = () => {
        if (window.innerWidth <= 960) {
            setButton(false);
        } else {
            setButton(true);
        }
    };

    useEffect(() => {
        showButton();

        window.addEventListener('resize', showButton);

        return () => {
            window.removeEventListener('resize', showButton);
        };
    }, []);


    return (
        <>
            <nav className="navbar " >
                <div className="navbar-container">
                    <Link to="/" className="navbar-logo" onClick={closeMobileMenu}>
                        Leetrack <i className="fa-solid fa-house"></i>
                    </Link>
                    <div className='menu-icon' onClick={handleClick}>
                        {/* <i className={click ? 'fas fa-times' : 'fas fa-bars'} /> */}
                        <p className="temp">Menu icon</p>
                    </div>
                    <ul className={click ? 'nav-menu active' : 'nav-menu'} >
                        <li className='nav-item'>
                            <Link to='/' className='nav-links' onClick={closeMobileMenu}>
                                Home
                            </Link>
                        </li>
                        <li className='nav-item'>
                            <Link to='/login' className='nav-links' onClick={closeMobileMenu}>
                                Login
                            </Link>
                        </li>
                        <li className='nav-item'>
                            <Link to='/register' className='nav-links' onClick={closeMobileMenu}>
                                Register
                            </Link>
                        </li>
                    </ul>
                    {/* {button && <Button buttonStyle='btn--outline'>Register</Button>} */}
                </div>
            </nav>
        </>
    )
}


export default Navbar