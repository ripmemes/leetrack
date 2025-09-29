import React, {useEffect, useState} from 'react'
export const PostCard = ({postCardURL,postCardName}) => {
    const [dailyChallenge,setDailyChallenge] = useState(null)
    
    const [statusCode, setStatusCode] = useState(null)
    const [error, setError] = useState(null)
    /* Toggle : 
    * 0 : Daily Challenge
    * 1 : Contests
    * 2 : Problem List
    */
    let toggle = -1 
    if (postCardURL === "api/daily"){
        toggle = 0 
    } else if ( postCardURL === "api/contest") {
        toggle = 1 
    } else if (postCardURL === "api/problemlst"){
        toggle = 2
    }
    const handleFetch = async () => {
        setDailyChallenge(null)
        
        try {
            const response = await fetch(`http://localhost:5000/${postCardURL}`, {
                method : 'GET',
                headers : {
                    'Content-Type' : 'application/json'
                }
            })

            setStatusCode(response.status)

            if (!response.ok){
                const errorData = await response.json()
                throw new Error(errorData.error || 'Network response was not ok')
            }

            const result = await response.json()
            console.log('Fetching is successful')
            if (toggle == 0){
                setDailyChallenge(result)
            }
        }

        catch (error) {
            console.error('Fetching error:' , error)
            setError(error.message)
        }
    }

    useEffect( () => {
        handleFetch()
    }, [])

    return (<>
        <div name ="Container" className="flex flex-col w-full bg-gray-100">
            
            <p>Status code : {statusCode}</p>
            
            { error ? (
                <div className ="fixed left-0 right-0 z-50">
                    <div role="alert" aria-live="assertove" className= "bg-red-400 text-white py-3 px-4 text-center shadow-md">Error : {error} </div>
                </div>
            ) : 


            (dailyChallenge ?(
            
            <div className="w-full p-4">
            
                <div className="absolute top-4 right-36 w-1/4 min-w-[280px] max-w-sm"> 
                <div className="rounded-2xl shadow-lg overflow-hidden border border-slate-200 bg-white">
                    <div className=" bg-orange-500 text-white px-4 py-3"><a href={`https://leetcode.com${dailyChallenge.link}`} className="font-semibold text-lg hover:underline" >{toggle==0 ? "Today's Challenge:" : null}{dailyChallenge.date}</a></div>
                    <div className="bg-slate-50 px-4 py-3"><p className = "text-slate-700 font-medium italic"> {dailyChallenge.question.title} </p></div>
                </div>
                </div>
            </div>) : 

                 (<div className=" absolute top-36 right-16 p-4 w-1/4 min-w-[280px] max-w-sm flex justify-center items-center bg-orange-500 rounded-xl shadow-md"><div className="">Loading Daily Challenge...</div></div>)  )
            }   
        </div>
    </>)
}

export const Daily = () => {
    return (<PostCard postCardURL="api/daily" postCardName={"Daily Challenge"}/>)
}