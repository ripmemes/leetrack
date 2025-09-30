import React ,{useState, useEffect} from 'react'
import {Daily} from './PostCard.js'
import ContestBar from './ContestBar.js'
import ProblemLst from './ProblemLst.js'
import AIComponent from './AIComponent.js';

function Home({logged,setLogged , userId}){

    useEffect(() => {
        const token = localStorage.getItem("token")
        if (!token){
            return
        }

        fetch("http://localhost:5000/",{
            headers:{
                "Authorization" : "Bearer " + token
            }
        })
        .then(res => {
            if (!res.ok) throw new Error("Not authorized")
            return res.json()
        })
        .then(data=>setLogged(true))
        .catch(()=> window.location.href="/login")
    },[])


    return (
    <div className="bg-gray-100 min-h-screen flex justify-center">
        {!logged && <div>PLACEHOLDER PRESENTATION PAGE</div>}
        { logged && <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-6xl px-4">
            <div><ContestBar></ContestBar></div>
            <div className=""><Daily/></div>
            <div className="bg-slate-200 border rounded-lg "><ProblemLst/></div>
            <div><AIComponent userId={userId}/>{userId}</div>
        </div>  }
    </div>  
    )
}


export default Home