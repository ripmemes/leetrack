import React, { useEffect , useState } from 'react'

function ContestBar(){
    const [contests, setContests] = useState(null)
    const [error, setError] = useState(null)


    const handleFetch = async () => {
        setContests(null)
        try{
            const response = await fetch('http://localhost:5000/api/contest', {
                method : 'GET',
                headers : {
                    'Content-Type' : 'application/json'
                }
            })

            if (!response.ok){
                const errorData = await response.json()
                throw new Error(errorData.error || 'Network response was not ok')
            }

            const result = await response.json()
            console.log('Fetching is successful')
            setContests(result)
            
        } catch (error) {
            console.error('Fetching error:' , error)
            setError(error.message)
        }
    }

    useEffect( () => {
            handleFetch()
    }, [])

    return (
        <div>
        { contests ? 
            <div className="relative flex flex-col bg-center w-full bg-green-500 border rounded-lg shadow-sm">
                {contests.map((element) => (
                    <div className="text-white py-4 mx-4 px-5 m-12" key={element.title}>
                        <div>Title: {element.title}</div>
                        {/* <div>Slug: {element.titleSlug}</div> */}
                        <div>Starts at: {new Date(element.startTime * 1000).toLocaleString()}</div>
                        <div>Duration : {element.duration /60} minutes</div>
                    </div>
                ))}
            <div className="absolute"></div>

             </div>  : 
            
            (<div className="relative flex flex-col bg-center w-full bg-green-400">
                Loading Contests...</div>)}
        
        </div>
        
    )

}

export default ContestBar