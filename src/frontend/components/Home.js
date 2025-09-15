import React from 'react'
import {Daily} from './PostCard.js'
import ContestBar from './ContestBar.js'
import ProblemLst from './ProblemLst.js'
// For overview, after authenticating 
function Home(){
    // TOP LEFT : Contests
    // BOTTOM LEFT : Problem list : 10 at a time 
    // RIGHT : Daily Challenge

    return (
    <div className="relative grid grid-cols-2 bg-gray-100 ">
        <div><ContestBar></ContestBar></div>
        <div className="h-28"><Daily/></div>
        <div className="bg-slate-600"><ProblemLst/></div>
    </div>   
    )
}


export default Home