import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from './Button';

function Navbar({logged,setLogged}) {
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



    useEffect(()=>{
        const token = localStorage.getItem("token")
        if (token){
            setLogged(true)
        }
    }, [])

    useEffect(() => {
        showButton();

        window.addEventListener('resize', showButton);

        return () => {
            window.removeEventListener('resize', showButton);
        };
    }, []);


    return (
        <>
            <nav className="bg-gradient-to-r from-neutral-900 to-neutral-800 h-20 flex justify-center items-center sticky top-0 z-[999]" >
                <div className="flex justify-between items-center h-20 w-full max-w-[1500px] px-6">
                    <Link to="/" className="text-white text-2xl font-bold flex items-center cursor-pointer" onClick={closeMobileMenu}>
                        Leetrack 
                        {/* <i className="fa-solid fa-house ml-2"></i> */}
                    </Link>
                    <div className='text-white text-2xl cursor-pointer md:hidden' onClick={handleClick}>
                        {/* <i className={click ? 'fas fa-times' : 'fas fa-bars'} /> */}
                        placeholder
                    </div>
                    <ul className={`absolute md:static top-20 left-0 w-full md:w-auto bg-neutral-900 md:bg-transparent 
                        flex flex-col md:flex-row md:space-x-6 
                        transition-all duration-500 ease-in-out 
                        ${click ? "left-0 opacity-100" : "left-[-100%] opacity-0 md:opacity-100"}`} >
                        <li>
                            <Link to='/' className='text-white px-4 py-2 block hover:border-b-4 hover:border-white transition duration-200' onClick={closeMobileMenu}>
                                Home
                            </Link>
                        </li>
                        {!logged && 
                        
                        <><li>
                            <Link to='/login' className='text-white px-4 py-2 block hover:border-b-4 hover:border-white transition duration-200' onClick={closeMobileMenu}>
                                Login
                            </Link>
                        </li>
                        <li>
                            <Link to='/register' className='text-white px-4 py-2 block hover:border-b-4 hover:border-white transition duration-200' onClick={closeMobileMenu}>
                                Register
                            </Link>
                        </li></>
                         }
                         {logged && 
                         <li>
                            <Link to='/' className="text-white px-4 py-2 block hover:border-b-4 hover:border-white transition duration-200" onClick={()=>{
                                localStorage.removeItem("token")
                                setLogged(false)
                            }}>
                            Logout</Link></li>}
                    </ul>
                    {/* {button && <Button buttonStyle='btn--outline'>Register</Button>} */}
                </div>
            </nav>
        </>
    )
}


export default Navbar