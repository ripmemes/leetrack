import React, { useCallback, useEffect, useState } from 'react'

export const PostCard = ({ postCardURL, postCardName }) => {
    const [dailyChallenge, setDailyChallenge] = useState(null)
    const [statusCode, setStatusCode] = useState(null)
    const [error, setError] = useState(null)

    /* Toggle : 
    * 0 : Daily Challenge
    * 1 : Contests
    * 2 : Problem List
    */
    let toggle = -1
    if (postCardURL === 'api/daily') {
        toggle = 0
    } else if (postCardURL === 'api/contest') {
        toggle = 1
    } else if (postCardURL === 'api/problemlst') {
        toggle = 2
    }

    const handleFetch = useCallback(async () => {
        setDailyChallenge(null)
        setError(null)

        try {
            const response = await fetch(`http://localhost:5000/${postCardURL}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })

            setStatusCode(response.status)

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.error || 'Network response was not ok')
            }

            const result = await response.json()
            console.log('Fetching is successful')

            if (toggle === 0) {
                setDailyChallenge(result)
            }
        } catch (error) {
            console.error('Fetching error:', error)
            setError(error.message)
        }
    }, [postCardURL, toggle])

    useEffect(() => {
        handleFetch()
    }, [handleFetch])

    return (
        <div className="w-full">
            {error ? (
                <div className="bg-red-50 border border-red-300 rounded-lg p-6">
                    <div className="flex items-start gap-3">
                        <div className="text-xl font-bold text-red-600">⚠</div>
                        <div>
                            <h3 className="font-bold text-red-900">Error Loading Daily Challenge</h3>
                            <p className="text-red-700 text-sm mt-1">{error}</p>
                            {statusCode && <p className="text-red-700 text-xs mt-2">Status: {statusCode}</p>}
                        </div>
                    </div>
                </div>
            ) : dailyChallenge ? (
                <div className="space-y-4">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900">{postCardName || 'Daily Challenge'}</h2>
                            <p className="text-gray-600 text-sm mt-1">Today's LeetCode challenge:</p>
                        </div>
                    </div>

                    <div className="group bg-white border border-gray-300 rounded-lg p-5 hover:shadow-md hover:border-orange-400 transition-all duration-300 cursor-pointer">
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="inline-block px-3 py-1 bg-orange-50 border border-orange-300 rounded text-orange-700 text-xs font-bold">
                                        DAILY
                                    </div>
                                    <h3 className="text-base font-semibold text-gray-900 group-hover:text-orange-600 transition-colors">
                                        {dailyChallenge.date}
                                    </h3>
                                </div>

                                <div className="space-y-2 mt-3">
                                    <div className="flex items-center gap-2 text-gray-700">
                                        <span className="font-medium text-gray-900">Problem:</span>
                                        <span className="text-sm text-gray-600">{dailyChallenge.question.title}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="ml-4 flex-shrink-0">
                                <a
                                    href={`https://leetcode.com${dailyChallenge.link}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-block bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-xs font-bold transition-colors duration-200"
                                >
                                    VIEW
                                </a>
                            </div>
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
                        <p className="text-gray-700 font-medium">Loading daily challenge...</p>
                    </div>
                </div>
            )}
        </div>
    )
}

export const Daily = () => {
    return <PostCard postCardURL="api/daily" postCardName={"Daily Challenge"} />
}