import React, { useEffect } from 'react'
import { Daily } from './PostCard.js'
import ContestBar from './ContestBar.js'
import ProblemLst from './ProblemLst.js'
import AIComponent from './AIComponent.js'

function Home({ logged, setLogged, userId }) {
    useEffect(() => {
        const token = localStorage.getItem('token')
        if (!token) {
            return
        }

        fetch('http://localhost:5000/', {
            headers: {
                Authorization: 'Bearer ' + token
            }
        })
            .then((res) => {
                if (!res.ok) throw new Error('Not authorized')
                return res.json()
            })
            .then(() => setLogged(true))
            .catch(() => window.location.href = '/login')
    }, [setLogged])

    return (
        <div className="min-h-screen bg-gray-100">
            {!logged && <div>PLACEHOLDER PRESENTATION PAGE</div>}

            {logged && (
                <>
                    <div className="mx-auto w-full max-w-[1500px] px-6 sm:px-8 lg:px-12 py-6">
                        <div className="grid grid-cols-1 gap-6 xl:gap-8 lg:grid-cols-[1.8fr_0.9fr]">
                            <div className="space-y-6">
                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <ContestBar />
                                </div>
                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <ProblemLst />
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <Daily />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="fixed bottom-5 right-5 z-50">
                        <AIComponent userId={userId} />
                    </div>
                </>
            )}
        </div>
    )
}

export default Home