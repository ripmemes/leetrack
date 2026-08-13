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
        <div className="w-full">
            {contests ? (
                <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900">Upcoming Contests</h2>
                            <p className="text-gray-600 text-sm mt-1">Participate in LeetCode contests to sharpen your skills</p>
                        </div>
                    </div>
                    
                    {contests.length === 0 ? (
                        <div className="bg-white border border-gray-300 rounded-lg p-8 text-center">
                            <p className="text-gray-600 font-medium">No upcoming contests at the moment</p>
                        </div>
                    ) : (
                        contests.map((element, index) => (
                            <div 
                                key={element.title}
                                className="group bg-white border border-gray-300 rounded-lg p-5 hover:shadow-md hover:border-orange-400 transition-all duration-300 cursor-pointer"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        {/* Contest Title with Status */}
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="inline-block px-3 py-1 bg-orange-50 border border-orange-300 rounded text-orange-700 text-xs font-bold">
                                                CONTEST
                                            </div>
                                            <h3 className="text-base font-semibold text-gray-900 group-hover:text-orange-600 transition-colors">
                                                {element.title}
                                            </h3>
                                        </div>
                                        
                                        {/* Contest Details */}
                                        <div className="space-y-2 mt-3">
                                            <div className="flex items-center gap-2 text-gray-700">
                                                <span className="font-medium text-gray-900">Start Time:</span>
                                                <span className="text-sm text-gray-600">
                                                    {new Date(element.startTime * 1000).toLocaleString()}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2 text-gray-700">
                                                <span className="font-medium text-gray-900">Duration:</span>
                                                <span className="text-sm text-gray-600">
                                                    {Math.floor(element.duration / 60)} minutes
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {/* CTA Button */}
                                    <div className="ml-4 flex-shrink-0">
                                        <button className="inline-block bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-xs font-bold transition-colors duration-200">
                                            VIEW
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            ) : error ? (
                <div className="bg-red-50 border border-red-300 rounded-lg p-6">
                    <div className="flex items-start gap-3">
                        <div className="text-xl font-bold text-red-600">⚠</div>
                        <div>
                            <h3 className="font-bold text-red-900">Error Loading Contests</h3>
                            <p className="text-red-700 text-sm mt-1">{error}</p>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="bg-white border border-gray-300 rounded-lg p-8">
                    <div className="flex items-center justify-center gap-3">
                        <div className="animate-spin">
                            <svg className="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        </div>
                        <p className="text-gray-700 font-medium">Loading contests...</p>
                    </div>
                </div>
            )}
        </div>
    )

}

export default ContestBar